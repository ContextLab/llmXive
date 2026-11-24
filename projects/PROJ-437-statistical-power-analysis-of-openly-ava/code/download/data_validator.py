"""
Data Validator
--------------
Minimal validator for downloaded OpenNeuro datasets. It implements a
**fail‑loudly** policy: any problem raises an exception; no synthetic
fallback or silent skipping is performed.
"""

import json
import logging
import sys
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def validate_bids_structure(dataset_root: Path) -> None:
    """
    Validate that ``dataset_root`` contains at least the minimal BIDS
    directories (e.g., ``sub-XX`` folders and a ``dataset_description.json``).

    Parameters
    ----------
    dataset_root : Path
        Path to the extracted dataset directory.

    Raises
    ------
    FileNotFoundError
        If required BIDS components are missing.
    """
    if not dataset_root.is_dir():
        raise FileNotFoundError(f"Dataset root directory does not exist: {dataset_root}")

    # Very lightweight check: at least one subject folder and dataset_description.json
    subject_dirs = [p for p in dataset_root.iterdir() if p.is_dir() and p.name.startswith("sub-")]
    desc_file = dataset_root / "dataset_description.json"

    if not subject_dirs:
        raise FileNotFoundError(f"No subject directories (sub-*) found in {dataset_root}")

    if not desc_file.is_file():
        raise FileNotFoundError(f"Missing required BIDS file: {desc_file}")

    logger.info(f"BIDS structure validated for dataset at {dataset_root} (subjects: {len(subject_dirs)})")

def write_manifest(downloaded_paths: List[Path], manifest_path: Path) -> None:
    """
    Helper to write a simple JSON manifest of downloaded datasets.

    Parameters
    ----------
    downloaded_paths : List[Path]
        List of dataset root directories.
    manifest_path : Path
        Destination JSON file.
    """
    manifest = {"downloaded_datasets": [str(p) for p in downloaded_paths]}
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    logger.info(f"Download manifest written to {manifest_path}")
