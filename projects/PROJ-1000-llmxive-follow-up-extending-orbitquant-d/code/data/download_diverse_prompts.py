"""
Fetch a diverse set of text prompts from the MS-COCO training set using the verified direct URL.
Writes the result to data/processed/diverse_prompts.csv.
"""
import urllib.request
import zipfile
import json
import os
import csv
import tempfile
import random
import logging
import sys
from pathlib import Path

# Ensure the project root is on the import path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))
from config import Config

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def fetch_diverse_prompts(config: Config, num_samples: int = 1000) -> None:
    url = "http://images.cocodataset.org/annotations/annotations_trainval2017.zip"
    output_path = config.processed_data_dir / "diverse_prompts.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        logger.info(f"Downloading COCO annotations for diverse prompts from {url}...")
        with urllib.request.urlopen(url) as resp:
            data = resp.read()
        
        with tempfile.TemporaryDirectory() as td:
            zip_path = Path(td) / "coco.zip"
            with open(zip_path, "wb") as f:
                f.write(data)
            
            with zipfile.ZipFile(zip_path, "r") as z:
                with z.open('annotations/captions_train2017.json') as jf:
                    coco_data = json.load(jf)
        
        # Use a fixed seed for reproducibility
        random.seed(42)
        all_annotations = coco_data['annotations']
        sampled_annotations = random.sample(all_annotations, min(num_samples, len(all_annotations)))
        
        records = []
        for i, ann in enumerate(sampled_annotations):
            records.append({
                "prompt_id": f"diverse_{i}",
                "caption": ann['caption'],
                "source": "coco_train2017"
            })
        
        if not records:
            raise RuntimeError("No valid captions extracted from COCO training set.")

        logger.info(f"Writing {len(records)} diverse prompts to {output_path}")
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["prompt_id", "caption", "source"])
            writer.writeheader()
            writer.writerows(records)

    except Exception as e:
        raise RuntimeError(f"Failed to fetch/process COCO training dataset for diverse prompts: {e}") from e

def main() -> None:
    config = Config()
    fetch_diverse_prompts(config)
    logger.info("Diverse prompts downloaded successfully.")

if __name__ == "__main__":
    main()
