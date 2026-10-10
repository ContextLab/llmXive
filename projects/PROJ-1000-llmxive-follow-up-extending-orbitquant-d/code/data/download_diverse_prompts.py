"""
Fetch a diverse set of text prompts from the MS-COCO 2017 training captions
and write them to ``data/processed/diverse_prompts.csv``.

The script downloads the public COCO training annotations JSON, randomly
samples a configurable number of captions, and stores them with a simple
identifier and source reference.

All failures raise ``RuntimeError`` – no synthetic fallback is used.
"""
import csv
import json
import logging
import random
import sys
import urllib.request
from pathlib import Path
from typing import List, Dict

# Ensure the project root is on the import path when the script is run directly
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Public URL for COCO 2017 training captions
COCO_TRAIN_URL = (
    "https://raw.githubusercontent.com/COCO-SSD/COCO-SSD/master/annotations/"
    "captions_train2017.json"
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

def _write_prompts_csv(prompts: List[Dict[str, str]], csv_path: Path) -> None:
    """Write prompts to ``csv_path`` with columns id, caption, source."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "caption", "source"])
        writer.writeheader()
        writer.writerows(prompts)

def fetch_diverse_prompts(num_samples: int = 1000) -> List[Dict[str, str]]:
    """
    Fetches diverse text prompts from the COCO training split.

    Args:
        num_samples: Desired number of prompt records (default 1000).

    Returns:
        List of dictionaries with keys ``id``, ``caption``, ``source``.
    """
    logger.info(f"Downloading COCO training captions from {COCO_TRAIN_URL}")
    json_data = _download_json(COCO_TRAIN_URL)

    if "annotations" not in json_data:
        raise RuntimeError("Unexpected JSON format: missing 'annotations' key")

    all_captions = [
        {"id": f"train_{idx}", "caption": item["caption"].strip(), "source": "coco_train2017"}
        for idx, item in enumerate(json_data["annotations"])
        if isinstance(item.get("caption"), str)
    ]

    if not all_captions:
        raise RuntimeError("No captions were extracted from the training JSON")

    # Randomly sample the requested number of prompts
    if len(all_captions) > num_samples:
        sampled = random.sample(all_captions, num_samples)
    else:
        sampled = all_captions

    logger.info(f"Fetched {len(sampled)} diverse prompts")
    return sampled

def main() -> None:
    """Entry point: fetch prompts and write them to CSV."""
    try:
        prompts = fetch_diverse_prompts(num_samples=1000)
        output_path = Path("data/processed/diverse_prompts.csv")
        _write_prompts_csv(prompts, output_path)

        # Verify output
        if not output_path.is_file():
            raise RuntimeError(f"Output file {output_path} was not created")
        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            if not rows:
                raise RuntimeError("Output CSV is empty")
            required = {"id", "caption", "source"}
            if not required.issubset(set(rows[0].keys())):
                raise RuntimeError(f"Missing required columns in {output_path}")
            if not any(r["caption"].strip() for r in rows):
                raise RuntimeError("All captions are empty")
        logger.info("Diverse prompts download completed successfully.")
    except Exception as e:
        logger.error(f"Diverse prompts download failed: {e}")
        raise

if __name__ == "__main__":
    main()
