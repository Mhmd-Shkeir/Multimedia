from pathlib import Path

import pandas as pd
from catboost import CatBoostRegressor

from .feature_extractor import get_features_for_slug

BASE_DIR = Path(__file__).resolve().parent

# Model file sits at repo root (sneaker_price_model.cbm)
PRICE_MODEL_PATH = BASE_DIR.parent / "sneaker_price_model.cbm"

_price_model = CatBoostRegressor()
if not PRICE_MODEL_PATH.exists():
    raise FileNotFoundError(f"Price model missing at {PRICE_MODEL_PATH}")
_price_model.load_model(str(PRICE_MODEL_PATH))

FEATURE_COLS = [
    "class_name",
    "brand",
    "silhouette",
    "retail_price_usd",
    "release_age",
]


def predict_price_for_slug(slug: str):
    """
    slug: GOAT slug string
    returns:
        price (float),
        feature_row (dict)  # good for debugging/returning to user
    """
    features = get_features_for_slug(slug)
    df = pd.DataFrame([[features[col] for col in FEATURE_COLS]], columns=FEATURE_COLS)
    price = float(_price_model.predict(df)[0])
    return price, features
