"""
FAISS similarity search scoped per class using CLIP embeddings.
Builds/loads per-class indices under faiss_cache and searches top-k images.
"""
from pathlib import Path
from typing import Dict, Tuple, List
import pickle
import random

import faiss
import numpy as np
import torch
from PIL import Image, ImageEnhance
from transformers import CLIPModel, CLIPProcessor


BASE_DIR = Path(__file__).resolve().parent
DATA_ROOT = BASE_DIR / "Scraping_part" / "goat_data"
INDEX_CACHE_DIR = BASE_DIR / "faiss_cache"
INDEX_CACHE_DIR.mkdir(exist_ok=True)
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# ==== MODEL ====
def _load_clip():
    model_name = "openai/clip-vit-base-patch32"
    try:
        m = CLIPModel.from_pretrained(
            model_name,
            use_safetensors=True,
            local_files_only=True,
        ).to(DEVICE)
        p = CLIPProcessor.from_pretrained(
            model_name,
            use_fast=True,
            local_files_only=True,
        )
        return m, p
    except Exception:
        m = CLIPModel.from_pretrained(
            model_name,
            use_safetensors=True,
        ).to(DEVICE)
        p = CLIPProcessor.from_pretrained(model_name, use_fast=True)
        return m, p


clip_model, clip_processor = _load_clip()

# Cache for indices in memory
_index_cache: Dict[str, Tuple[faiss.Index, List[str]]] = {}


# ==== AUGMENTATION ====
def augment_image(img: Image.Image, strength: str = "light") -> List[Image.Image]:
    """Apply random augmentations to image."""
    augmented: List[Image.Image] = []
    augmented.append(img)

    if strength in ["light", "medium", "heavy"]:
        enhancer = ImageEnhance.Brightness(img)
        augmented.append(enhancer.enhance(random.uniform(0.85, 1.15)))

        enhancer = ImageEnhance.Contrast(img)
        augmented.append(enhancer.enhance(random.uniform(0.9, 1.1)))

    if strength in ["medium", "heavy"]:
        enhancer = ImageEnhance.Color(img)
        augmented.append(enhancer.enhance(random.uniform(0.9, 1.1)))

        augmented.append(img.rotate(random.uniform(-10, 10), fillcolor=(255, 255, 255)))

        w, h = img.size
        crop_size = int(min(w, h) * random.uniform(0.85, 0.95))
        left = random.randint(0, w - crop_size)
        top = random.randint(0, h - crop_size)
        cropped = img.crop((left, top, left + crop_size, top + crop_size))
        augmented.append(cropped.resize((w, h), Image.LANCZOS))

    if strength == "heavy":
        augmented.append(img.transpose(Image.FLIP_LEFT_RIGHT))

        enhancer = ImageEnhance.Sharpness(img)
        augmented.append(enhancer.enhance(random.uniform(0.8, 1.2)))

    return augmented


def embed_image(path: Path, augment: bool = False, aug_strength: str = "light") -> np.ndarray:
    """Embed image with optional augmentation."""
    img = Image.open(path).convert("RGB")

    if not augment:
        inputs = clip_processor(images=img, return_tensors="pt").to(DEVICE)
        with torch.no_grad():
            emb = clip_model.get_image_features(**inputs)
        v = emb[0].cpu().numpy()
        return v / np.linalg.norm(v)

    imgs = augment_image(img, strength=aug_strength)
    embeddings = []

    for aug_img in imgs:
        inputs = clip_processor(images=aug_img, return_tensors="pt").to(DEVICE)
        with torch.no_grad():
            emb = clip_model.get_image_features(**inputs)
        v = emb[0].cpu().numpy()
        embeddings.append(v / np.linalg.norm(v))

    return np.mean(embeddings, axis=0)


def build_class_index(class_dir: Path, augment_index: bool = False, aug_per_image: int = 5):
    """
    Build FAISS index for a class. Optionally augment each image multiple times.
    """
    vectors, paths = [], []

    for slug_dir in class_dir.iterdir():
        if not slug_dir.is_dir():
            continue
        for ext in ("*.jpg", "*.jpeg", "*.png"):
            for img_path in slug_dir.glob(ext):
                try:
                    if not augment_index:
                        v = embed_image(img_path)
                        vectors.append(v.astype("float32"))
                        paths.append(str(img_path))
                    else:
                        img = Image.open(img_path).convert("RGB")
                        augmented_imgs = augment_image(img, strength="medium")
                        for aug_img in augmented_imgs[:aug_per_image]:
                            inputs = clip_processor(images=aug_img, return_tensors="pt").to(DEVICE)
                            with torch.no_grad():
                                emb = clip_model.get_image_features(**inputs)
                            v = emb[0].cpu().numpy()
                            v_norm = v / np.linalg.norm(v)
                            vectors.append(v_norm.astype("float32"))
                            paths.append(str(img_path))
                except Exception as e:
                    print(f"[FAISS] Skip {img_path}: {e}")

    if not vectors:
        raise RuntimeError(f"No images found under {class_dir.resolve()}")

    arr = np.stack(vectors)
    faiss.normalize_L2(arr)

    index = faiss.IndexFlatIP(arr.shape[1])
    index.add(arr)

    unique_images = len(set(paths))
    print(f"[FAISS] Indexed {len(paths)} embeddings ({unique_images} unique) for {class_dir.name}")
    return index, paths


def get_or_build_index(class_name: str, rebuild: bool = False, augment_index: bool = False):
    """Get cached index or build new one (and cache to disk)."""
    if class_name in _index_cache and not rebuild:
        return _index_cache[class_name]

    cache_file = INDEX_CACHE_DIR / f"{class_name}.pkl"

    if cache_file.exists() and not rebuild:
        print(f"[FAISS] Loading cached index for {class_name}")
        with open(cache_file, "rb") as f:
            index_data = pickle.load(f)
        _index_cache[class_name] = (
            faiss.deserialize_index(index_data["index"]),
            index_data["paths"],
        )
        return _index_cache[class_name]

    class_dir = DATA_ROOT / class_name
    index, paths = build_class_index(class_dir, augment_index=augment_index)

    with open(cache_file, "wb") as f:
        pickle.dump({"index": faiss.serialize_index(index), "paths": paths}, f)

    _index_cache[class_name] = (index, paths)
    return index, paths


def search_in_class(
    query_img: Path,
    class_name: str,
    top_k: int = 5,
    use_query_augmentation: bool = True,
    augment_index: bool = False,
    rebuild_index: bool = False,
):
    """Search for similar images inside one class."""
    index, paths = get_or_build_index(class_name, rebuild=rebuild_index, augment_index=augment_index)

    if use_query_augmentation:
        qvec = embed_image(Path(query_img), augment=True, aug_strength="medium")
    else:
        qvec = embed_image(Path(query_img))

    qvec = qvec.astype("float32").reshape(1, -1)
    faiss.normalize_L2(qvec)

    search_k = top_k * 10 if augment_index else top_k
    sims, idxs = index.search(qvec, search_k)

    seen_paths: Dict[str, float] = {}
    for i, score in zip(idxs[0], sims[0]):
        path = paths[i]
        if path not in seen_paths or score > seen_paths[path]:
            seen_paths[path] = score

    results = sorted(seen_paths.items(), key=lambda x: x[1], reverse=True)[:top_k]

    items = []
    for path, score in results:
        p = Path(path)
        items.append(
            {
                "path": path,
                "score": float(score),
                "slug": p.parent.name,
                "class_name": p.parent.parent.name,
                "filename": p.name,
            }
        )
    return items
