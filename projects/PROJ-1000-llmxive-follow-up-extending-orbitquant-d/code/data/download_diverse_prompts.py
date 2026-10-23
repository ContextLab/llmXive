"""
Download a diverse set of prompts from at least two public caption collections.
Source 1: COCO 2017 Train annotations (publicly available zip).
Source 2: Conceptual Captions (HuggingFace dataset, public, no auth required).

The script writes a CSV file with columns: prompt_id, caption, source.
At least 150 prompts are required; otherwise it raises an error.
All errors are re‑raised as RuntimeError so the script exits non‑zero on failure.
"""

import os
import urllib.request
import zipfile
import tempfile
import random
import csv
import logging
from pathlib import Path

from pycocotools.coco import COCO
from datasets import load_dataset
from llmxive_toolkit import paths

# Configure module‑level logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)


def _download_coco_train_captions() -> list[dict]:
    """
    Download COCO 2017 *train* captions and return a list of annotation dicts.
    Each dict contains at least a ``caption`` field.
    """
    log.info("Fetching prompts from COCO 2017 Train...")
    coco_url = (
        "http://images.cocodataset.org/annotations/annotations_trainval2017.zip"
    )
    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_path = os.path.join(tmp_dir, "coco_train.zip")
        urllib.request.urlretrieve(coco_url, zip_path)

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp_dir)

        ann_file = os.path.join(tmp_dir, "annotations", "captions_train2017.json")
        if not os.path.exists(ann_file):
            raise FileNotFoundError(
                f"COCO train annotation file not found at expected location: {ann_file}"
            )

        coco = COCO(ann_file)
        ann_ids = coco.getAnnIds()
        anns = coco.loadAnns(ann_ids)

        # Sample up to 100 captions (or all if fewer)
        sample_size = min(100, len(anns))
        sampled = random.sample(anns, sample_size)

        records = []
        for i, ann in enumerate(sampled):
            records.append(
                {
                    "prompt_id": f"coco_{i}",
                    "caption": ann["caption"],
                    "source": "coco2017_train",
                }
            )
        return records


def _download_conceptual_captions() -> list[dict]:
    """
    Stream the ``conceptual_captions`` dataset from HuggingFace and collect
    up to 100 captions. The dataset is public and does **not** require an
    authentication token.
    """
    log.info("Fetching prompts from HuggingFace 'conceptual_captions' dataset...")
    # The dataset contains a ``caption`` field.
    ds = load_dataset("conceptual_captions", split="train", streaming=True)

    records = []
    for idx, item in enumerate(ds):
        if idx >= 100:
            break
        caption = item.get("caption")
        if caption:
            records.append(
                {
                    "prompt_id": f"conceptual_{idx}",
                    "caption": caption,
                    "source": "conceptual_captions",
                }
            )
    return records


def main() -> None:
    """
    Orchestrates the download of two caption collections, merges them,
    validates the total count, and writes the combined CSV to the project
    ``data/processed`` directory.
    """
    output_path = paths.data("processed", "diverse_prompts.csv")

    # Ensure reproducibility of the random sampling
    random.seed(42)

    try:
        records = []

        # 1️⃣ COCO train captions
        records.extend(_download_coco_train_captions())

        # 2️⃣ Conceptual Captions
        records.extend(_download_conceptual_captions())

        total = len(records)
        if total < 150:
            raise RuntimeError(
                f"Collected only {total} prompts; at least 150 are required."
            )

        # Write CSV (header + rows)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(
                csv_file, fieldnames=["prompt_id", "caption", "source"]
            )
            writer.writeheader()
            writer.writerows(records)

        log.info(f"Successfully wrote {total} diverse prompts to {output_path}")

    except Exception as exc:
        # Re‑raise as RuntimeError so the CLI exit code is non‑zero
        raise RuntimeError(f"Failed to download diverse prompts: {exc}") from exc


if __name__ == "__main__":
    main()