"""
Download the MS-COCO 2017 validation captions and store them as a CSV file.

This script fetches the public COCO annotations JSON for the validation split,
extracts the image identifiers and captions, and writes them to
``data/raw/coco_captions/captions.csv``. A small metadata JSON file is also
written alongside the CSV.

All failures raise ``RuntimeError`` – no synthetic fallback is used.
"""
import csv
import json
import logging
import sys
import urllib.request
from pathlib import Path

# Ensure the project root is on the import path when the script is run directly
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Public URL for COCO 2017 validation captions
COCO_VAL_URL = (
    "https://raw.githubusercontent.com/COCO-SSD/COCO-SSD/master/annotations/"
    "captions_val2017.json"
)

def _download_json(url: str) -> dict:
    """Download a JSON file from ``url`` and return the parsed object."""
    try:
        with urllib.request.urlopen(url) as response:
            if response.status != 200:
                raise RuntimeError(f"HTTP error {response.status} while fetching {url}")
            data = response.read()
            return json.loads(data.decode("utf-8"))
    except Exception as e:
        raise RuntimeError(f"Failed to download JSON from {url}: {e}") from e

def _write_captions_csv(captions: list[dict], csv_path: Path) -> None:
    """Write a list of ``{'id': ..., 'caption': ...}`` dicts to ``csv_path``."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["id", "caption"])
        writer.writeheader()
        for entry in captions:
            writer.writerow(entry)

def main() -> None:
    """Entry point: download validation captions and write CSV + metadata."""
    config = Config()

    # Resolve output directories
    raw_coco_dir = config.raw_data_dir / "coco_captions"
    raw_coco_dir.mkdir(parents=True, exist_ok=True)

    output_csv = raw_coco_dir / "captions.csv"
    meta_file = raw_coco_dir / "metadata.json"

    logger.info(f"Downloading COCO validation captions from {COCO_VAL_URL}")
    json_data = _download_json(COCO_VAL_URL)

    # The JSON structure is {"annotations": [{"image_id": int, "caption": str}, ...]}
    if "annotations" not in json_data:
        raise RuntimeError("Unexpected JSON format: missing 'annotations' key")

    captions = [
        {"id": str(item["image_id"]), "caption": item["caption"].strip()}
        for item in json_data["annotations"]
        if isinstance(item.get("caption"), str) and "image_id" in item
    ]

    if not captions:
        raise RuntimeError("No captions were extracted from the downloaded JSON")

    logger.info(f"Writing {len(captions)} captions to {output_csv}")
    _write_captions_csv(captions, output_csv)

    metadata = {
        "source_url": COCO_VAL_URL,
        "num_records": len(captions),
        "csv_path": str(output_csv),
    }
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"COCO validation captions downloaded successfully to {output_csv}")

if __name__ == "__main__":
    main()
