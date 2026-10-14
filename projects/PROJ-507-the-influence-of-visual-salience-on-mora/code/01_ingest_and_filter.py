"""
01_ingest_and_filter.py
-----------------------

Runnable entry point for the data ingestion pipeline.

This script fetches a real image dataset from Hugging Face (Visual Genome
by default, or a verified source if the environment variable
``VERIFIED_DATA_SOURCE`` is set). It streams the dataset, filters for
images whose metadata contains any of the tags ``social`` or ``conflict``,
and selects the first ``N`` candidates (default 10) using a fixed random
seed (42) for reproducibility.

For each selected image it:

1. Downloads the image into ``data/raw/``.
2. Computes a SHA‑256 checksum of the downloaded file.
3. Writes a row to ``data/processed/candidates_filtered.csv`` that
   conforms to ``contracts/dataset.schema.yaml``.
4. Stores the checksums in ``data/raw/sample_metadata.json``.

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
from datasets import load_dataset, DownloadConfig

# Project‑specific imports
from data_prep import DataFetchError
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

DEFAULT_DATASET = "visual_genome"
DEFAULT_SPLIT = "train"
DEFAULT_TAGS = ["social", "conflict"]
DEFAULT_NUM_SAMPLES = 10
RANDOM_SEED = 42


def _resolve_dataset_name() -> str:
    """Return the dataset name to load.

    If the environment variable ``VERIFIED_DATA_SOURCE`` is set, its value
    is interpreted as the exact Hugging Face dataset identifier to use.
    Otherwise the canonical Visual Genome dataset is used.
    """
    env_source = os.getenv("VERIFIED_DATA_SOURCE")
    if env_source:
        log.info("Using verified data source from environment: %s", env_source)
        return env_source
    log.info("No verified source set – defaulting to %s", DEFAULT_DATASET)
    return DEFAULT_DATASET


def _download_image(url: str, target_path: Path) -> None:
    """Download an image from ``url`` to ``target_path``.

    Raises:
        DataFetchError: If the request fails or the HTTP status is not 200.
    """
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


def _filter_candidate(record: Dict[str, Any], tags: List[str]) -> bool:
    """Return True if the record's metadata contains any of ``tags``.

    The Visual Genome dataset stores object names in ``objects`` – a list
    of dicts with a ``name`` field.  For other datasets we fall back to
    checking a generic ``metadata`` field if present.
    """
    # Visual Genome specific handling
    objects = record.get("objects")
    if isinstance(objects, list):
        names = [obj.get("name", "").lower() for obj in objects if isinstance(obj, dict)]
        return any(tag.lower() in names for tag in tags)

    # Generic fallback
    meta = record.get("metadata", {})
    if isinstance(meta, dict):
        # Look for a free‑form ``tags`` entry
        meta_tags = meta.get("tags", [])
        if isinstance(meta_tags, list):
            return any(tag.lower() in (t.lower() for t in meta_tags) for tag in tags)

    return False


def ingest_and_filter(
    num_samples: int = DEFAULT_NUM_SAMPLES,
    tags: List[str] = DEFAULT_TAGS,
) -> None:
    """Main ingestion routine.

    Downloads images, writes ``candidates_filtered.csv`` and a checksum
    JSON file.  All output paths are resolved via ``llmxive_toolkit.paths``.
    """
    dataset_name = _resolve_dataset_name()

    # Prepare output locations
    raw_dir = paths.data("raw")
    processed_dir = paths.data("processed")
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    candidates_path = processed_dir / "candidates_filtered.csv"
    checksum_path = raw_dir / "sample_metadata.json"

    # Stream the dataset – this keeps memory usage low.
    try:
        ds = load_dataset(
            dataset_name,
            split=DEFAULT_SPLIT,
            streaming=True,
            download_config=DownloadConfig(cache_dir=str(raw_dir)),
        )
    except Exception as exc:
        raise DataFetchError(f"Unable to load dataset '{dataset_name}'") from exc

    selected: List[Dict[str, Any]] = []
    checksums: Dict[str, str] = {}

    # Deterministic sampling: we simply take the first ``num_samples``
    # records that satisfy the tag filter.
    for record in ds:
        if not _filter_candidate(record, tags):
            continue

        # Visual Genome provides ``image_id`` and ``url`` fields.
        image_id = str(record.get("image_id") or record.get("id"))
        image_url = record.get("url")
        if not image_url:
            # If the record lacks a direct URL we cannot download it.
            log.warning("Record %s missing 'url' – skipping", image_id)
            continue

        image_filename = f"{image_id}.jpg"
        image_path = raw_dir / image_filename

        # Download the image (may raise DataFetchError)
        _download_image(image_url, image_path)

        checksum = _sha256_checksum(image_path)
        checksums[image_id] = checksum

        # Build the CSV row – fields required by the schema.
        row = {
            "scenario_id": image_id,
            "original_image_path": str(image_path),
            "metadata": json.dumps(record.get("metadata", {})),
            "ambiguity_score": 0.0,          # placeholder – to be filled later
            "ambiguity_label": False,        # placeholder – to be filled later
        }
        selected.append(row)

        if len(selected) >= num_samples:
            break

    if not selected:
        raise DataFetchError("No candidate images matched the filtering criteria.")

    # Write CSV
    df = pd.DataFrame(selected)
    df.to_csv(candidates_path, index=False)

    # Write checksums JSON
    with open(checksum_path, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2)

    log.info(
        "Ingestion complete – %d candidates written to %s",
        len(selected),
        candidates_path,
    )
    log.info("Checksums written to %s", checksum_path)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingest and filter image data for the visual salience pipeline."
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        default=DEFAULT_NUM_SAMPLES,
        help="Maximum number of candidate images to select (default: %(default)s).",
    )
    parser.add_argument(
        "--tags",
        nargs="+",
        default=DEFAULT_TAGS,
        help="Metadata tags used for filtering (default: %(default)s).",
    )
    return parser


def main() -> None:
    args = _build_arg_parser().parse_args()
    ingest_and_filter(num_samples=args.num_samples, tags=args.tags)


if __name__ == "__main__":
    main()
