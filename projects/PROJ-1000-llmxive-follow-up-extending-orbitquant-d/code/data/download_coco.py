"""
Download the MS-COCO 2017 validation captions using the HuggingFace datasets library.
Writes the result to data/raw/coco_captions/captions.csv.
"""
import csv
import logging
import sys
from pathlib import Path
from typing import List, Dict

try:
    from datasets import load_dataset
except ImportError:
    raise RuntimeError("The 'datasets' library is required. Please run 'pip install datasets'.")

# Ensure the project root is on the import path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def download_coco_validation(config: Config) -> None:
    """
    Fetch the validation split of nlpconnect/coco_captions and save as CSV.
    """
    try:
        logger.info("Downloading MS-COCO validation set from HuggingFace (nlpconnect/coco_captions)...")
        dataset = load_dataset("nlpconnect/coco_captions", split="validation")
    except Exception as e:
        raise RuntimeError(f"Failed to fetch COCO validation dataset from HuggingFace: {e}") from e

    output_dir = config.raw_data_dir / "coco_captions"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_csv = output_dir / "captions.csv"

    captions = []
    for idx, item in enumerate(dataset):
        caption = item.get("caption")
        if isinstance(caption, str) and caption.strip():
            captions.append({"id": str(idx), "caption": caption.strip()})

    if not captions:
        raise RuntimeError("No valid captions were extracted from the COCO validation dataset.")

    logger.info(f"Writing {len(captions)} captions to {output_csv}")
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "caption"])
        writer.writeheader()
        writer.writerows(captions)

def load_coco_captions(config: Config) -> List[Dict[str, str]]:
    """
    Helper function to load the captions CSV produced by this script.
    """
    csv_path = config.raw_data_dir / "coco_captions" / "captions.csv"
    if not csv_path.is_file():
        raise RuntimeError(f"COCO captions CSV not found at {csv_path}. Run download_coco.py first.")
    
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]

def main() -> None:
    config = Config()
    download_coco_validation(config)
    logger.info("COCO validation captions downloaded successfully.")

if __name__ == "__main__":
    main()
