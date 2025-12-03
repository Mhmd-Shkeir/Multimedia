import io
import os
from pathlib import Path
from urllib.parse import quote

from bson import ObjectId
from flask import Flask, jsonify, request, send_file
from werkzeug.utils import secure_filename

from ai.image_model import predict_class
from ai.price_model import predict_price_for_slug
from ai.slug_selector import get_slug_for_class
from faiss_search import search_in_class
from inventory import add_or_update_inventory, find_inventory, fs, inventory_col
from is_a_sneaker import is_sneaker
from product_info import get_product_info

# ----------------------------------
# CONFIG
# ----------------------------------
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

DATA_ROOT = BASE_DIR / "Scraping_part" / "goat_data"
FAISS_CACHE = BASE_DIR / "faiss_cache"
FAISS_CACHE.mkdir(exist_ok=True)

ALLOWED_EXT = {"jpg", "jpeg", "png"}

CONFIDENCE_LOW = 0.45
CONFIDENCE_HIGH = 0.70


def confidence_level(score: float):
    if score >= CONFIDENCE_HIGH:
        return "high"
    if score >= CONFIDENCE_LOW:
        return "medium"
    return "low"


def normalize_similar_items(items):
    """
    Convert FAISS results to frontend-friendly shape without serving images.
    """
    return [
        {
            "path": item["path"],
            "slug": item.get("slug"),
            "class_name": item.get("class_name"),
            "filename": item.get("filename"),
            "score": item.get("score"),
            "url": f"/similar?path={quote(_relative_to_data_root(item['path']))}",
        }
        for item in items
    ]


def convert_for_json(obj):
    import numpy as np

    if isinstance(obj, dict):
        return {k: convert_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_for_json(x) for x in obj]
    if isinstance(obj, tuple):
        return [convert_for_json(x) for x in obj]
    if isinstance(obj, (np.float32, np.float64)):
        return float(obj)
    if isinstance(obj, (np.int32, np.int64)):
        return int(obj)
    if isinstance(obj, Path):
        return str(obj)
    return obj


def _relative_to_data_root(path_str: str) -> str:
    """
    Return path relative to DATA_ROOT if possible; otherwise return as-is.
    """
    p = Path(path_str).resolve()
    try:
        return str(p.relative_to(DATA_ROOT.resolve()).as_posix())
    except Exception:
        return str(p.as_posix())


# ----------------------------------
# FLASK APP
# ----------------------------------
app = Flask(
    __name__,
    static_folder=str(BASE_DIR / "frontend" / "build" / "static"),
    static_url_path="/static",
)
app.config["UPLOAD_FOLDER"] = str(UPLOAD_DIR)
REACT_BUILD = BASE_DIR / "frontend" / "build"


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    """
    Serve React production build if present; otherwise return simple API hint.
    """
    if REACT_BUILD.exists():
        target = REACT_BUILD / path
        if target.is_file():
            return send_file(target)
        index_file = REACT_BUILD / "index.html"
        if index_file.exists():
            return send_file(index_file)
    return jsonify(
        {
            "status": "ok",
            "message": "Frontend build not found. Use npm start (port 3000) or npm run build.",
            "api": ["/health", "/predict", "/inventory", "/add-to-inventory"],
        }
    )


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/predict", methods=["POST"])
def predict():
    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    ext = file.filename.split(".")[-1].lower()
    if ext not in ALLOWED_EXT:
        return jsonify({"error": "Unsupported file type"}), 400

    # persist upload for debugging / FAISS query
    filename = secure_filename(file.filename)
    save_path = UPLOAD_DIR / filename
    file.save(save_path)

    rebuild_index = request.args.get("rebuild_index") in {"1", "true", "True", "yes"}

    response = {"image_path": str(save_path)}

    # 1) Sneaker gate
    gate = is_sneaker(save_path)
    response["sneaker_check"] = gate
    if not gate["is_sneaker"]:
        response.update(
            {
                "status": "not_sneaker",
                "decision": "stop",
                "message": "Uploaded image is not recognized as a sneaker.",
            }
        )
        return jsonify(response)

    # 2) Classification
    pred = predict_class(save_path)
    class_name = pred["class_name"]
    conf = float(pred["confidence"])
    level = confidence_level(conf)

    response.update(
        {
            "class_name": class_name,
            "brand": pred["brand"],
            "model_name": pred["model_name"],
            "product_name": f"{pred['brand']} {pred['model_name']}".strip(),
            "product_type": class_name,
            "confidence": conf,
            "confidence_level": level,
        }
    )

    # 3) Similarity search (FAISS over scraped images)
    try:
        similar = search_in_class(
            query_img=save_path,
            class_name=class_name,
            top_k=5,
            use_query_augmentation=True,
            augment_index=False,
            rebuild_index=rebuild_index,
        )
        response["similar_images"] = {"items": normalize_similar_items(similar), "source": "cache"}
    except Exception as exc:
        response["similar_images"] = {"items": [], "source": "error", "message": str(exc)}

    # 4) Choose slug & price prediction
    try:
        slug = get_slug_for_class(class_name)
        response["slug_used"] = slug
        price, feature_row = predict_price_for_slug(slug)
        response["predicted_price"] = round(float(price), 2)
        response["retail_price_usd"] = feature_row.get("retail_price_usd")
        response["release_age"] = feature_row.get("release_age")
        response["silhouette"] = feature_row.get("silhouette")
    except Exception as exc:
        response["pricing_error"] = str(exc)

    # 5) Product info from CSV (read-only display; override brand/model/retail if available)
    info = get_product_info(class_name)
    response["product_info"] = info
    if info:
        response["brand"] = info.get("brand") or response.get("brand")
        response["product_name"] = info.get("product_name") or response.get("product_name")
        response["retail_price_usd"] = info.get("retail_price_usd") or response.get("retail_price_usd")
        response["silhouette"] = info.get("silhouette") or response.get("silhouette")

    # 6) Inventory lookup
    response["inventory"] = find_inventory(class_name=class_name, slug=response.get("slug_used"))

    if level == "low":
        response["status"] = "low_confidence"
        response["decision"] = "manual_check"
        response["message"] = "Confidence below 45%; please confirm or override."
    else:
        response["status"] = "ok"
        response["decision"] = "continue"

    return jsonify(convert_for_json(response))


@app.route("/add-to-inventory", methods=["POST"])
@app.route("/inventory/add", methods=["POST"])
def add_inventory():
    data = request.get_json(force=True) or {}

    class_name = data.get("class_name")
    slug = data.get("slug") or data.get("slug_used")
    if not class_name or not slug:
        return jsonify({"error": "class_name and slug are required"}), 400

    product = {
        "slug": slug,
        "class_name": class_name,
        "brand": data.get("brand"),
        "model": data.get("model") or data.get("model_name"),
        "product_name": data.get("product_name"),
        "product_type": data.get("product_type"),
    }

    quantity = int(data.get("quantity", 1))
    price_modified = data.get("price")
    price_predicted = data.get("price_predicted") or data.get("predicted_price")

    # Optional: attach uploaded image bytes
    image_bytes = None
    if "image_path" in data and data["image_path"]:
        try:
            image_bytes = Path(data["image_path"]).read_bytes()
        except Exception:
            image_bytes = None

    result = add_or_update_inventory(
        product,
        quantity=quantity,
        price_modified=price_modified,
        price_predicted=price_predicted,
        image_bytes=image_bytes,
    )

    return jsonify(result)


@app.route("/inventory", methods=["GET"])
def list_inventory():
    items = []
    for item in inventory_col.find({}):
        item["_id"] = str(item["_id"])
        if item.get("image_gridfs_id"):
            item["image_gridfs_id"] = str(item["image_gridfs_id"])
        items.append(item)
    return jsonify(convert_for_json(items))


@app.route("/image/<image_id>")
def get_image(image_id):
    try:
        gridout = fs.get(ObjectId(image_id))
    except Exception:
        return jsonify({"error": "not found"}), 404
    return send_file(io.BytesIO(gridout.read()), mimetype=gridout.content_type)


@app.route("/similar")
def serve_similar():
    rel_path = request.args.get("path")
    if not rel_path:
        return jsonify({"error": "missing path"}), 400

    # Normalize separators
    rel_path_clean = rel_path.replace("\\", "/")
    target_path = (DATA_ROOT / rel_path_clean).resolve()

    # Security: ensure inside DATA_ROOT
    try:
        target_path.relative_to(DATA_ROOT.resolve())
    except Exception:
        return jsonify({"error": "forbidden"}), 403

    if not target_path.exists():
        return jsonify({"error": "not found"}), 404

    return send_file(target_path, mimetype="image/jpeg")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
