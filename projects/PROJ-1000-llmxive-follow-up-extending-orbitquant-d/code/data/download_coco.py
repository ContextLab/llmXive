"""
Download the MS-COCO 2017 validation captions using the verified direct URL.
Writes the result to data/raw/coco_captions/captions.csv.
"""
import urllib.request
import zipfile
import json
import os
import csv
import tempfile
import logging
import sys
from pathlib import Path

# Ensure the project root is on the import path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))
from config import Config

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def download_coco_validation(config: Config) -> None:
    url = "http://images.cocodataset.org/annotations/annotations_trainval2017.zip"
    output_dir = config.raw_data_dir / "coco_captions"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_csv = output_dir / "captions.csv"

    try:
        logger.info(f"Downloading COCO annotations from {url}...")
        with urllib.request.urlopen(url) as resp:
            data = resp.read()
        
        with tempfile.TemporaryDirectory() as td:
            zip_path = Path(td) / "coco.zip"
            with open(zip_path, "wb") as f:
                f.write(data)
            
            with zipfile.ZipFile(zip_path, "r") as z:
                with z.open('annotations/captions_val2017.json') as jf:
                    coco_data = json.load(jf)
        
        img_map = {img['id']: img for img in coco_data['images']}
        records = []
        for ann in coco_data['annotations']:
            img = img_map.get(ann['image_id'])
            if img:
                records.append({
                    'id': str(ann['image_id']),
                    'caption': ann['caption']
                })
        
        if not records:
            raise RuntimeError("No valid records extracted from COCO validation set.")

        logger.info(f"Writing {len(records)} captions to {output_csv}")
        with open(output_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "caption"])
            writer.writeheader()
            writer.writerows(records)

    except Exception as e:
        raise RuntimeError(f"Failed to fetch/process COCO validation dataset: {e}") from e

def main() -> None:
    config = Config()
    download_coco_validation(config)
    logger.info("COCO validation captions downloaded successfully.")

if __name__ == "__main__":
    main()
