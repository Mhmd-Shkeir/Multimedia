from pathlib import Path
from datetime import datetime

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
PRODUCTS_CSV = BASE_DIR / "products_nodup.csv"

# load once
_products_df = pd.read_csv(PRODUCTS_CSV)

# make lookup by slug for speed
if "slug" in _products_df.columns:
    _products_df = _products_df.set_index("slug")


def _compute_release_age(release_date_str: str):
    """
    release_date_str: e.g. '4/8/2022' or NaN
    returns age in years (float) or None
    """
    if pd.isna(release_date_str):
        return None

    try:
        # try month/day/year
        dt = datetime.strptime(str(release_date_str), "%m/%d/%Y")
    except ValueError:
        try:
            dt = datetime.fromisoformat(str(release_date_str))
        except Exception:
            return None

    days = (datetime.now() - dt).days
    return days / 365.25


def get_features_for_slug(slug: str) -> dict:
    """
    Return feature dict for CatBoost model, based on products_nodup.csv.
    Adjust column names here if they differ slightly in your file.
    """
    if slug not in _products_df.index:
        raise KeyError(f"Slug '{slug}' not found in products_nodup.csv")

    row = _products_df.loc[slug]

    # adjust these names if your CSV uses slightly different ones
    class_name = row["class_name"]
    brand = row["brand"]
    silhouette = row["silhouette"]
    # header looks like 'retail_pric...' in Excel; most likely 'retail_price_usd'
    retail_price = row.get("retail_price_usd", row.get("retail_price", None))
    release_date = row.get("release_date", None)

    release_age = _compute_release_age(release_date)

    features = {
        "class_name": class_name,
        "brand": brand,
        "silhouette": silhouette,
        "retail_price_usd": float(retail_price) if retail_price is not None else None,
        "release_age": release_age,
    }

    return features
