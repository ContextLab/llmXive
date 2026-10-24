"""
01_ingest_and_filter.py
-----------------------

Ingests images from Open Images V6 using the verified FiftyOne zoo loader.
Filters records by tags ('conflict', 'social'), downloads/copies images,
computes SHA-256 checksums, and writes a candidate CSV.

Conforms to contracts/dataset.schema.yaml.
"""

import argparse
import hashlib
import json
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import pandas as pd

# Project-specific imports
from data_prep import DataFetchError
from llmxive_toolkit import paths, get_logger

# Use the verified real data source recipe
try:
    import fiftyone as fo
    import fiftyone.zoo as foz
except ImportError as exc:
    # This will be caught in ingest_and_filter and raise DataFetchError
    fo = None
    foz = None

log = get_logger(__name__)

# Configuration defaults
DEFAULT_TAGS = ["conflict", "social"]
DEFAULT_NUM_SAMPLES = 200
RANDOM_SEED = 42

def _sha256_checksum(file_path: Path) -> str:
    """Calculate the SHA-256 checksum of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _record_has_tag(sample: Any, tags: List[str]) -> bool:
    """
    Check if the FiftyOne sample has any of the target tags.
    FiftyOne samples typically store labels in the 'labels' field.
    """
    # Access labels from the sample
    labels = getattr(sample, "labels", [])
    if not labels:
        # Try to check if it's a dict (if .to_dict() was used)
        if isinstance(sample, dict):
            labels = sample.get("labels", [])
        else:
            return False
    
    lower_labels = [str(lbl).lower() for lbl in labels]
    return any(tag.lower() in lower_labels for tag in tags)

def ingest_and_filter(
    num_samples: int = DEFAULT_NUM_SAMPLES,
    tags: List[str] = DEFAULT_TAGS,
    output_csv: Path = None,
    checksum_path: Path = None,
) -> None:
    """Main ingestion routine using verified FiftyOne source."""
    # Prepare output locations
    raw_dir = paths.data("raw")
    processed_dir = paths.data("processed")
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    if output_csv is None:
        output_csv = processed_dir / "candidates_filtered.csv"
    if checksum_path is None:
        checksum_path = raw_dir / "checksums.json"

    if foz is None:
        raise DataFetchError("FiftyOne is not installed; cannot access verified data source.")

    try:
        log.info("Loading Open Images V6 via FiftyOne zoo dataset (verified source).")
        # Load a larger subset to ensure we find enough matching tags
        # Using split="train" as per tasks.md, but validation is also verified.
        dataset = foz.load_zoo_dataset(
            "open-images-v6",
            split="train",
            max_samples=num_samples * 10, 
            dataset_name="tmp_open_images_v6",
        )
    except Exception as exc:
        raise DataFetchError(f"Unable to load Open Images dataset via FiftyOne: {exc}") from exc

    selected: List[Dict[str, Any]] = []
    checksums: Dict[str, str] = {}

    # Iterate and filter
    for sample in dataset:
        if not _record_has_tag(sample, tags):
            continue

        # Derive stable ID
        image_id = str(sample.id)
        
        # Resolve local path (FiftyOne handles downloads)
        source_path = Path(sample.filepath)
        if not source_path.is_file():
            log.warning("Image file %s does not exist – skipping.", source_path)
            continue

        # Destination in our raw folder
        image_path = raw_dir / f"{image_id}.jpg"
        try:
            shutil.copy2(source_path, image_path)
        except Exception as e:
            log.warning("Failed to copy image %s: %s", source_path, e)
            continue

        # Compute checksum
        checksum = _sha256_checksum(image_path)
        checksums[image_id] = checksum

        # Build CSV row conforming to contracts/dataset.schema.yaml
        # We use to_dict() to capture metadata
        meta = sample.to_dict()
        row = {
            "scenario_id": image_id,
            "original_image_path": str(image_path),
            "metadata": json.dumps(meta),
            "ambiguity_score": 0.0,
            "ambiguity_label": False,
        }
        selected.append(row)

        if len(selected) >= num_samples:
            break

    if not selected:
        raise DataFetchError("No candidate images matched the filtering criteria.")

    # Deterministic shuffle to avoid order bias
    selected_df = pd.DataFrame(selected)
    selected_df = selected_df.sample(frac=1, random_state=RANDOM_SEED).reset_index(drop=True)

    # Write CSV
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    selected_df.to_csv(output_csv, index=False)

    # Write checksums JSON
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    with open(checksum_path, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2, sort_keys=True)

    log.info("Ingestion complete – %d candidates written to %s", len(selected_df), output_csv)
    log.info("Checksums written to %s", checksum_path)

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest and filter image datasets.")
    parser.add_argument(
        "--num-samples",
        type=int,
        default=DEFAULT_NUM_SAMPLES,
        help="Maximum number of candidate images to keep.",
    )
    parser.add_argument(
        "--max-scenarios",
        type=int,
        help="Alias for --num-samples.",
    )
    parser.add_argument(
        "--tags",
        nargs="+",
        default=DEFAULT_TAGS,
        help="List of tags to filter images by.",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Path to write the filtered candidates CSV.",
    )
    return parser

def main() -> None:
    args = _build_arg_parser().parse_args()
    num_samples = args.max_scenarios if args.max_scenarios is not None else args.num_samples
    output_path = Path(args.output) if args.output else paths.data("processed") / "candidates_filtered.csv"
    ingest_and_filter(num_samples=num_samples, tags=args.tags, output_csv=output_path)

if __name__ == "__main__":
    main()
