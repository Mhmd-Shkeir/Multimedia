from pathlib import Path
import json
import torch
import torch.nn.functional as F
from torchvision import models
import torch.nn as nn

from .utils import load_image

BASE_DIR = Path(__file__).resolve().parent
# Model lives at repo root; class indices sit next to this file
MODEL_PATH = BASE_DIR.parent / "best_resnet50_sneakers.pt"
CLASS_INDICES_PATH = BASE_DIR / "class_indices.json"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load class mapping
with open(CLASS_INDICES_PATH, "r") as f:
    class_to_idx = json.load(f)

idx_to_class = {v: k for k, v in class_to_idx.items()}


def _split_brand_model(class_name: str):
    """Convert class name like 'adidas_samba' to ('Adidas','Samba')."""
    parts = class_name.split("_")
    brand_raw = parts[0]
    brand = brand_raw.capitalize()
    model_tokens = parts[1:]
    model = " ".join(t.capitalize() for t in model_tokens)
    return brand, model


# ----------------------------------------------------
# BUILD RESNET50 ARCHITECTURE WITH CUSTOM FC HEAD
# ----------------------------------------------------

# 1) Base ResNet50 backbone
_model = models.resnet50(weights=None)

# 2) Replace the final FC layer with the EXACT architecture matching your weights
#    State_dict shows:
#       fc.0 = Linear(2048 → 512)
#       fc.1 = ReLU()
#       fc.2 = (no weights) → Identity
#       fc.3 = Linear(512 → num_classes)
_model.fc = nn.Sequential(
    nn.Linear(2048, 512),           # fc.0
    nn.ReLU(),                      # fc.1
    nn.Identity(),                  # fc.2
    nn.Linear(512, len(class_to_idx))  # fc.3
)

# 3) Load your saved state_dict
state_dict = torch.load(MODEL_PATH, map_location=device)
_model.load_state_dict(state_dict)   # THIS WILL NOW WORK

# 4) Move to device + set eval mode
_model = _model.to(device)
_model.eval()


# ----------------------------------------------------
# CLASS PREDICTION FUNCTION
# ----------------------------------------------------

def predict_class(image_path):
    """
    Predict sneaker class from image path.
    Returns:
        {
          "class_name": ...,
          "brand": ...,
          "model_name": ...,
          "confidence": float,
          "class_index": int,
        }
    """
    with torch.no_grad():
        x = load_image(image_path).to(device)
        logits = _model(x)
        probs = F.softmax(logits, dim=1)
        conf, idx = probs.max(dim=1)
        idx = int(idx.item())
        conf = float(conf.item())

    class_name = idx_to_class[idx]
    brand, model_name = _split_brand_model(class_name)

    return {
        "class_name": class_name,
        "brand": brand,
        "model_name": model_name,
        "confidence": conf,
        "class_index": idx,
    }
