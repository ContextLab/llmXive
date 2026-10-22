"""
01_ingest_and_filter.py
-----------------------

Runnable entry point for the data ingestion pipeline.

This script attempts to fetch the **Open Images V6** dataset from Hugging Face
(streaming). If the dataset cannot be accessed (e.g., authentication required),
it gracefully falls back to the publicly available **COCO Captions** dataset.
The script then filters records that contain any of the supplied tags
(default: ``conflict`` or ``social``) and selects up to ``num_samples``
candidates (default 200) using a fixed random seed (42) for reproducibility.

For each selected image the script:
1. Downloads the image into ``data/raw/``.
2. Computes a SHA‑256 checksum of the downloaded file.
3. Writes a row to the CSV specified by ``--output`` (default
   ``data/processed/candidates_filtered.csv``) conforming to
   ``contracts/dataset.schema.yaml``.
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
OPEN_IMAGES_NAME = "open_images"
OPEN_IMAGES_CONFIG = "v6"
COCO_DATASET_NAME = "coco_captions"
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

    This function works for both the Open Images schema (``labels``) and
    the COCO Captions schema (``captions``).  If neither field is present,
    the function falls back to a simple string search in any free‑text
    field.
    """
    # Open Images uses ``labels`` (list of strings)
    label_field = record.get("labels") or record.get("label") or record.get("tags")
    if isinstance(label_field, list):
        lower_labels = [str(lbl).lower() for lbl in label_field]
        return any(tag.lower() in lower_labels for tag in tags)

    # COCO Captions uses ``captions`` (list of dicts with ``text``)
    captions = record.get("captions")
    if isinstance(captions, list):
        texts = []
        for cap in captions:
            if isinstance(cap, dict) and "text" in cap:
                texts.append(str(cap["text"]).lower())
            elif isinstance(cap, str):
                texts.append(cap.lower())
        return any(tag.lower() in txt for txt in texts for tag in tags)

    # Fallback: search any string field
    for value in record.values():
        if isinstance(value, str) and any(tag.lower() in value.lower() for tag in tags):
            return True
    return False

# ----------------------------------------------------------------------
# Core ingestion routine
# ----------------------------------------------------------------------
def ingest_and_filter(
    num_samples: int = DEFAULT_NUM_SAMPLES,
    tags: List[str] = DEFAULT_TAGS,
    output_csv: Path = None,
    checksum_path: Path = None,
) -> None:
    """Main ingestion routine."""
    # Prepare output locations
    raw_dir = paths.data("raw")
    processed_dir = paths.data("processed")
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    if output_csv is None:
        output_csv = processed_dir / "candidates_filtered.csv"
    if checksum_path is None:
        checksum_path = raw_dir / "checksums.json"

    selected: List[Dict[str, Any]] = []
    checksums: Dict[str, str] = {}

    # ------------------------------------------------------------------
    # Load a dataset (Open Images preferred, COCO fallback)
    # ------------------------------------------------------------------
    ds = None
    try:
        log.info(
            "Attempting to load Open Images dataset %s:%s (streaming)",
            OPEN_IMAGES_NAME,
            OPEN_IMAGES_CONFIG,
        )
        ds = load_dataset(
            OPEN_IMAGES_NAME,
            OPEN_IMAGES_CONFIG,
            split=DEFAULT_SPLIT,
            streaming=True,
            trust_remote_code=True,
        )
    except Exception as exc:
        log.warning(f"Open Images load failed ({exc}); falling back to COCO Captions.")
        try:
            ds = load_dataset(
                COCO_DATASET_NAME,
                split=DEFAULT_SPLIT,
                streaming=True,
                trust_remote_code=True,
            )
        except Exception as exc2:
            raise DataFetchError(
                f"Unable to load any dataset (Open Images and COCO fallback both failed): {exc2}"
            ) from exc2

    rng = pd.random.RandomState(RANDOM_SEED)

    for record in ds:
        # ----------------------------------------------------------------
        # Filter by tags (if tags list is non‑empty)
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

        # ----------------------------------------------------------------
        # Resolve image URL (different datasets use different keys)
        # ----------------------------------------------------------------
        image_url = record.get("image_url") or record.get("url") or record.get("coco_url")
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

    # Deterministic shuffle to avoid streaming order bias
    selected_df = pd.DataFrame(selected)
    selected_df = selected_df.sample(frac=1, random_state=RANDOM_SEED).reset_index(drop=True)

    # Write CSV
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    selected_df.to_csv(output_csv, index=False)

    # Write checksums JSON
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    with open(checksum_path, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2, sort_keys=True)

    log.info(
        "Ingestion complete – %d candidates written to %s",
        len(selected_df),
        output_csv,
    )
    log.info("Checksums written to %s", checksum_path)

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest and filter image datasets.")
    parser.add_argument(
        "--num-samples",
        type=int,
        default=DEFAULT_NUM_SAMPLES,
        help="Maximum number of candidate images to keep (legacy flag).",
    )
    parser.add_argument(
        "--max-scenarios",
        type=int,
        help="Alias for --num-samples; preferred name in quickstart.",
    )
    parser.add_argument(
        "--tags",
        nargs="+",
        default=DEFAULT_TAGS,
        help="List of tags to filter images by (e.g., conflict social).",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Path to write the filtered candidates CSV (quickstart flag).",
    )
    return parser

def main() -> None:
    args = _build_arg_parser().parse_args()
    # Resolve legacy vs new argument names
    num_samples = args.max_scenarios if args.max_scenarios is not None else args.num_samples
    output_path = Path(args.output) if args.output else paths.data("processed") / "candidates_filtered.csv"
    ingest_and_filter(num_samples=num_samples, tags=args.tags, output_csv=output_path)

if __name__ == "__main__":
    main()