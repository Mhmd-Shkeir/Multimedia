"""
Minimal inventory helper backed by MongoDB + optional GridFS.
Uses env var MONGO_URI (defaults to localhost). Collection: inventory.
"""
import os
from datetime import datetime
from typing import Optional

from bson import ObjectId
from pymongo import MongoClient
from gridfs import GridFS


MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/sneaker_ai_v2")
client = MongoClient(MONGO_URI)

try:
    db_name = client.get_default_database().name
except Exception:
    db_name = "sneaker_ai_v2"

db = client[db_name]
fs = GridFS(db, collection="images")
inventory_col = db["inventory"]


def _now():
    return datetime.utcnow()


def find_inventory(class_name: Optional[str] = None, slug: Optional[str] = None):
    """Find inventory by class_name or slug."""
    query = {}
    if class_name:
        query["class_name"] = class_name
    if slug:
        query["slug"] = slug
    if not query:
        return {"exists": False}

    doc = inventory_col.find_one(query)
    if not doc:
        return {"exists": False}

    return {
        "exists": True,
        "id": str(doc.get("_id")),
        "slug": doc.get("slug"),
        "product_id": doc.get("product_id"),
        "product_name": doc.get("product_name"),
        "product_type": doc.get("product_type"),
        "current_quantity": doc.get("quantity", 0),
        "price_predicted": doc.get("price_predicted"),
        "price_modified": doc.get("price_modified"),
        "brand": doc.get("brand"),
        "model": doc.get("model"),
        "image_gridfs_id": str(doc.get("image_gridfs_id")) if doc.get("image_gridfs_id") else None,
    }


def add_or_update_inventory(
    product: dict,
    quantity: int = 1,
    price_modified: float = None,
    price_predicted: float = None,
    image_bytes: bytes = None,
    content_type: str = "image/jpeg",
):
    """
    Upsert inventory entry, optionally storing the image in GridFS.
    product keys expected: class_name, slug, brand, model, product_name, product_type
    """
    image_gridfs_id = None
    if image_bytes:
        image_gridfs_id = fs.put(image_bytes, content_type=content_type)

    now = _now()
    existing = inventory_col.find_one({"slug": product.get("slug")})

    if existing:
        new_qty = existing.get("quantity", 0) + quantity
        inventory_col.update_one(
            {"_id": existing["_id"]},
            {
                "$set": {
                    "quantity": new_qty,
                    "updated_at": now,
                    "price_predicted": price_predicted
                    if price_predicted is not None
                    else existing.get("price_predicted"),
                    "price_modified": price_modified
                    if price_modified is not None
                    else existing.get("price_modified"),
                    "image_gridfs_id": image_gridfs_id
                    if image_gridfs_id is not None
                    else existing.get("image_gridfs_id"),
                }
            },
        )
        return {"status": "updated", "quantity": new_qty, "image_gridfs_id": image_gridfs_id}

    doc = {
        "product_name": product.get("product_name") or product.get("model"),
        "product_type": product.get("product_type") or product.get("class_name"),
        "slug": product.get("slug"),
        "class_name": product.get("class_name"),
        "brand": product.get("brand"),
        "model": product.get("model"),
        "image_gridfs_id": image_gridfs_id,
        "price_predicted": price_predicted,
        "price_modified": price_modified,
        "quantity": quantity,
        "date_added": now,
        "updated_at": now,
    }

    res = inventory_col.insert_one(doc)
    return {"status": "inserted", "quantity": quantity, "image_gridfs_id": str(image_gridfs_id)}
