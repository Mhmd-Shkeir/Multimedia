import pandas as pd

# point to ai/products_nodup.csv (scraped data)
CSV_PATH = "ai/products_nodup.csv"

# Column names from your screenshot
CLASS_COLUMN = "class_name"
NAME_COLUMN = "title"
BRAND_COLUMN = "brand"
RETAIL_COLUMN = "retail_price_usd"
LOWEST_COLUMN = "lowest_price_usd"
URL_COLUMN = "product_url"
RELEASE_COLUMN = "release_date"
SILHOUETTE_COLUMN = "silhouette"

# Load CSV once
try:
    df = pd.read_csv(CSV_PATH)
    print("[CSV] Loaded products_nodup.csv successfully")
except FileNotFoundError:
    df = None
    print(f"[CSV] ERROR: File {CSV_PATH} not found")


def get_product_info(class_name: str) -> dict:
    if df is None:
        return _empty_result(class_name)

    if CLASS_COLUMN not in df.columns:
        return _empty_result(class_name)

    # Filter by predicted class
    rows = df[df[CLASS_COLUMN] == class_name]

    if rows.empty:
        return _empty_result(class_name)

    r = rows.iloc[0]

    def safe(col):
        return r[col] if col in df.columns else None

    return {
        "class_name": class_name,
        "product_name": safe(NAME_COLUMN),
        "brand": safe(BRAND_COLUMN),
        "retail_price_usd": _to_number(safe(RETAIL_COLUMN)),
        "lowest_price_usd": _to_number(safe(LOWEST_COLUMN)),
        "silhouette": safe(SILHOUETTE_COLUMN),
        "release_date": safe(RELEASE_COLUMN),
        "url": safe(URL_COLUMN),
    }


def _to_number(val):
    try:
        return float(val)
    except Exception:
        return None


def _empty_result(class_name):
    return {
        "class_name": class_name,
        "product_name": None,
        "brand": None,
        "retail_price_usd": None,
        "lowest_price_usd": None,
        "silhouette": None,
        "release_date": None,
        "url": None,
    }
