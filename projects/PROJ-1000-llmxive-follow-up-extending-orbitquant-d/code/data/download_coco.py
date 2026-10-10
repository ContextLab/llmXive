"""
Download the MS-COCO 2017 validation captions and store them as a CSV file.

This script fetches the official COCO annotations archive, extracts the
validation captions JSON, parses the captions, and writes them to
``data/raw/coco_captions/captions.csv``. A small metadata JSON file is also
written alongside the CSV.

All failures raise ``RuntimeError`` – no synthetic fallback is used.
"""
import csv
import json
import logging
import ssl
import sys
import urllib.request
import zipfile
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

# Official COCO annotations archive containing both instance and caption files
COCO_ANNOTATIONS_ZIP_URL = (
    "https://images.cocodataset.org/annotations/annotations_trainval2017.zip"
)
# Local temporary path for the downloaded zip
TEMP_ZIP_PATH = Path("/tmp") / "coco_annotations.zip"

def _download_annotations_zip(url: str, dest: Path) -> None:
    """Download the COCO annotations zip file to ``dest``."""
    if dest.is_file():
        logger.info(f"Annotations zip already exists at {dest}")
        return
    logger.info(f"Downloading COCO annotations archive from {url}")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(url, context=ctx) as resp, open(dest, "wb") as out:
            out.write(resp.read())
    except Exception as e:
        raise RuntimeError(f"Failed to download COCO annotations zip: {e}") from e

def _extract_captions_json(zip_path: Path) -> Path:
    """
    Extract ``captions_val2017.json`` from the zip archive and return its path.
    The file is extracted into a temporary directory under ``/tmp``.
    """
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            # Find the caption file for the validation split
            caption_file = next(
                (f for f in z.namelist() if f.endswith("captions_val2017.json")),
                None,
            )
            if not caption_file:
                raise RuntimeError(
                    "captions_val2017.json not found inside the COCO annotations zip."
                )
            extract_dir = Path("/tmp") / "coco_extracted"
            extract_dir.mkdir(parents=True, exist_ok=True)
            z.extract(caption_file, extract_dir)
            return extract_dir / caption_file
    except zipfile.BadZipFile as e:
        raise RuntimeError(f"Corrupted zip file {zip_path}: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Failed to extract captions JSON: {e}") from e

def _load_captions(json_path: Path) -> list[dict]:
    """Load captions from the extracted JSON file."""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
            raise RuntimeError(f"Unable to read JSON from {json_path}: {e}") from e

    if "annotations" not in data:
        raise RuntimeError("Unexpected JSON format: missing 'annotations' key")

    captions = [
        {"id": str(item["image_id"]), "caption": item["caption"].strip()}
        for item in data["annotations"]
        if isinstance(item.get("caption"), str) and "image_id" in item
    ]

    if not captions:
        raise RuntimeError("No captions were extracted from the JSON file")
    return captions

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

    # 1. Download the annotations zip (if not already present)
    _download_annotations_zip(COCO_ANNOTATIONS_ZIP_URL, TEMP_ZIP_PATH)

    # 2. Extract the validation captions JSON
    captions_json_path = _extract_captions_json(TEMP_ZIP_PATH)

    # 3. Load captions from JSON
    captions = _load_captions(captions_json_path)

    # 4. Write captions to CSV
    logger.info(f"Writing {len(captions)} captions to {output_csv}")
    _write_captions_csv(captions, output_csv)

    # 5. Write a small metadata file for provenance
    metadata = {
        "source_url": COCO_ANNOTATIONS_ZIP_URL,
        "extracted_file": str(captions_json_path),
        "num_records": len(captions),
        "csv_path": str(output_csv),
    }
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"COCO validation captions downloaded successfully to {output_csv}")

if __name__ == "__main__":
    main()
