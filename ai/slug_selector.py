from pathlib import Path
import random

# project root = .../sneaker_app
PROJECT_ROOT = Path(__file__).resolve().parents[1]
GOAT_DATA_ROOT = PROJECT_ROOT / "Scraping_part" / "goat_data"


def get_slug_for_class(class_name: str) -> str:
    """
    Given class_name e.g. 'adidas_samba', look in:
        Scraping_part/goat_data/adidas_samba/
    and return one subfolder name (GOAT slug).
    """
    class_dir = GOAT_DATA_ROOT / class_name
    if not class_dir.exists():
        raise FileNotFoundError(f"Class folder not found: {class_dir}")

    candidates = [p.name for p in class_dir.iterdir() if p.is_dir()]
    if not candidates:
        raise FileNotFoundError(f"No slug folders in {class_dir}")

    # deterministic: always pick the first sorted slug to keep predictions stable
    candidates.sort()
    return candidates[0]
