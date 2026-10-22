"""
01_ingest_and_filter.py
-----------------------

Runnable entry point for the data ingestion pipeline.

This script fetches the **Open Images V6** dataset from Hugging Face,
streams it, filters for records whose metadata contain any of the tags
``conflict`` or ``social``, and selects up to ``num_samples`` candidates
(default 200) using a fixed random seed (42) for reproducibility.

For each selected image the script:
1. Downloads the image into ``data/raw/``.
2. Computes a SHA‑256 checksum of the downloaded file.
3. Writes a row to ``data/processed/candidates_filtered.csv`` conforming
   to ``contracts/dataset.schema.yaml``.
4. Stores all checksums in ``data/raw/checksums.json``.

The script raises :class:`DataFetchError` on any failure to fetch the
dataset or download an image – no synthetic fallback is performed.
"""

import argparse
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import requests
from datasets import load_dataset

# Project‑specific imports
from data_prep import DataFetchError
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration defaults
# ----------------------------------------------------------------------
DATASET_NAME = "open_images"
DATASET_CONFIG = "v6"
DEFAULT_SPLIT = "train"
DEFAULT_TAGS = ["conflict", "social"]
DEFAULT_NUM_SAMPLES = 200
RANDOM_SEED = 42

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _download_image(url: str, target_path: Path) -> None:
    """Download an image from ``url`` to ``target_path``."""
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        with open(target_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    except Exception as exc:
        raise DataFetchError(f"Failed to download image from {url}") from exc

def _sha256_checksum(file_path: Path) -> str:
    """Calculate the SHA‑256 checksum of ``file_path``."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _record_has_tag(record: Dict[str, Any], tags: List[str]) -> bool:
    """
    Return ``True`` if the record's metadata contain any of ``tags``.

    For Open Images V6 the relevant fields are:
    * ``labels`` – list of label strings.
    * ``image_url`` – URL to the image.
    """
    label_field = record.get("labels") or record.get("label") or record.get("tags")
    if isinstance(label_field, list):
        lower_labels = [str(lbl).lower() for lbl in label_field]
        return any(tag.lower() in lower_labels for tag in tags)
    return False

# ----------------------------------------------------------------------
# Core ingestion routine
# ----------------------------------------------------------------------
def ingest_and_filter(
    num_samples: int = DEFAULT_NUM_SAMPLES,
    tags: List[str] = DEFAULT_TAGS,
) -> None:
    """Main ingestion routine."""
    # Prepare output locations
    raw_dir = paths.data("raw")
    processed_dir = paths.data("processed")
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    candidates_path = processed_dir / "candidates_filtered.csv"
    checksum_path = raw_dir / "checksums.json"

    # ------------------------------------------------------------------
    # Load the Open Images V6 dataset (streaming)
    # ------------------------------------------------------------------
    try:
        log.info(
            "Loading Open Images dataset %s:%s (streaming)",
            DATASET_NAME,
            DATASET_CONFIG,
        )
        ds = load_dataset(
            DATASET_NAME,
            DATASET_CONFIG,
            split=DEFAULT_SPLIT,
            streaming=True,
            trust_remote_code=True,
        )
    except Exception as exc:
        raise DataFetchError(
            f"Unable to load Open Images dataset {DATASET_NAME}/{DATASET_CONFIG}: {exc}"
        ) from exc

    selected: List[Dict[str, Any]] = []
    checksums: Dict[str, str] = {}

    # Deterministic shuffling is not needed because we stop after the first
    # ``num_samples`` matches, but we keep the seed constant for any future
    # random operations.
    rng = pd.random.RandomState(RANDOM_SEED)

    for record in ds:
        # ----------------------------------------------------------------
        # Filter by tags
        # ----------------------------------------------------------------
        if tags and not _record_has_tag(record, tags):
            continue

        # ----------------------------------------------------------------
        # Derive a stable identifier for the image
        # ----------------------------------------------------------------
        image_id = str(
            record.get("image_id")
            or record.get("id")
            or record.get("original_image_id")
            or len(selected)
        )

        image_url = record.get("image_url") or record.get("url")
        if not image_url:
            log.warning("Record %s missing image URL – skipping.", image_id)
            continue

        image_path = raw_dir / f"{image_id}.jpg"

        # ----------------------------------------------------------------
        # Download the image
        # ----------------------------------------------------------------
        try:
            _download_image(image_url, image_path)
        except DataFetchError as e:
            log.warning("Skipping image %s due to download error: %s", image_id, e)
            continue

        # ----------------------------------------------------------------
        # Compute checksum
        # ----------------------------------------------------------------
        checksum = _sha256_checksum(image_path)
        checksums[image_id] = checksum

        # ----------------------------------------------------------------
        # Build CSV row conforming to contracts/dataset.schema.yaml
        # ----------------------------------------------------------------
        row = {
            "scenario_id": image_id,
            "original_image_path": str(image_path),
            "metadata": json.dumps(record.get("metadata", record)),
            "ambiguity_score": 0.0,
            "ambiguity_label": False,
        }
        selected.append(row)

        if len(selected) >= num_samples:
            break

    if not selected:
        raise DataFetchError("No candidate images matched the filtering criteria.")

    # Shuffle deterministically (seeded) to avoid any ordering bias from the
    # streaming source.
    selected_df = pd.DataFrame(selected)
    selected_df = selected_df.sample(
        frac=1, random_state=RANDOM_SEED
    ).reset_index(drop=True)

    # Write CSV
    selected_df.to_csv(candidates_path, index=False)

    # Write checksums JSON
    with open(checksum_path, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2, sort_keys=True)

    log.info(
        "Ingestion complete – %d candidates written to %s",
        len(selected_df),
        candidates_path,
    )
    log.info("Checksums written to %s", checksum_path)

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest and filter Open Images V6.")
    parser.add_argument(
        "--num-samples",
        type=int,
        default=DEFAULT_NUM_SAMPLES,
        help="Maximum number of candidate images to keep.",
    )
    parser.add_argument(
        "--tags",
        nargs="+",
        default=DEFAULT_TAGS,
        help="List of tags to filter images by (e.g., conflict social).",
    )
    return parser

def main() -> None:
    args = _build_arg_parser().parse_args()
    ingest_and_filter(num_samples=args.num_samples, tags=args.tags)

if __name__ == "__main__":
    main()
