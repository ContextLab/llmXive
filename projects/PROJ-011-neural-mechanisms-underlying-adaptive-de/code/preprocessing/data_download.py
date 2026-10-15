"""
Data Download Module for OpenNeuro ds003694.

Fetches the specified dataset using the openneuro-py library.
Implements strict fail-loudly safety: no synthetic fallbacks.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Any, List, Set, Tuple, Dict, Optional
import json

# Import openneuro-py; raise clear error if missing
try:
    import openneuro
    from openneuro import download
except ImportError as exc:
    raise ImportError(
        "The 'openneuro-py' package is required for data download. "
        "Please install it via: pip install openneuro-py"
    ) from exc

from utils.io import ensure_dir, save_yaml, save_json
from utils.logger import get_logger

logger = get_logger(__name__)

DATASET_ID = "ds003694"
EXCLUSIONS_FILE = "exclusions.yaml"
MANIFEST_FILE = "dataset_manifest.json"

class DataDownloadError(Exception):
    """Custom exception for data download failures."""
    pass

def download_dataset(dataset_id: str, target_dir: Path) -> None:
    """
    Download the full OpenNeuro dataset to ``target_dir``.

    Parameters
    ----------
    dataset_id : str
        OpenNeuro dataset identifier (e.g., ``ds003694``).
    target_dir : Path
        Directory where the dataset will be stored.
    """
    logger.info(f"Starting download of OpenNeuro dataset {dataset_id} → {target_dir}")
    ensure_dir(target_dir)
    try:
        # ``download`` handles authentication and the actual HTTP requests.
        # ``update=False`` skips re-downloading if files already exist.
        download.download(
            dataset=dataset_id,
            output_dir=str(target_dir),
            update=False,
            delete=False,
        )
        logger.info("Dataset download completed successfully.")
    except Exception as e:
        raise DataDownloadError(f"Failed to download dataset {dataset_id}: {e}") from e

def check_participant_assets(participant_id: str, raw_dir: Path) -> Tuple[bool, Optional[str]]:
    """
    Verify that a participant directory contains the required NIfTI and behavioral files.

    Returns
    -------
    (bool, Optional[str])
        ``True`` and ``None`` if the assets are present,
        otherwise ``False`` and a string explaining the missing asset.
    """
    sub_dir = raw_dir / participant_id
    if not sub_dir.is_dir():
        return False, "Participant directory missing"

    # Expected file patterns based on the ds003694 specification
    func_dir = sub_dir / "func"
    beh_dir = sub_dir / "beh"

    nii_pattern = f"{participant_id}_task-social_bold.nii.gz"
    if not any(f.is_file() for f in func_dir.glob(nii_pattern)):
        return False, f"Missing NIfTI ({nii_pattern})"

    beh_pattern = f"{participant_id}_task-social_beh.tsv"
    if not any(f.is_file() for f in beh_dir.glob(beh_pattern)):
        return False, f"Missing behavioral logs ({beh_pattern})"

    return True, None

def scan_participants(raw_dir: Path) -> Tuple[Dict[str, str], int]:
    """
    Scan ``raw_dir`` for participant sub‑directories, validate assets,
    and collect exclusion information.

    Returns
    -------
    (exclusions, total_scanned)
        ``exclusions`` – mapping ``participant_id → reason`` for participants that fail validation.
        ``total_scanned`` – total number of ``sub-`` directories examined.
    """
    exclusions: Dict[str, str] = {}
    total_scanned = 0

    if not raw_dir.is_dir():
        raise DataDownloadError(f"Raw data directory {raw_dir} does not exist after download.")

    for entry in raw_dir.iterdir():
        if entry.is_dir() and entry.name.startswith("sub-"):
            total_scanned += 1
            is_valid, reason = check_participant_assets(entry.name, raw_dir)
            if not is_valid:
                exclusions[entry.name] = reason
                logger.warning(f"Excluding {entry.name}: {reason}")
            else:
                logger.info(f"Participant {entry.name} passed validation.")

    logger.info(f"Scanned {total_scanned} participants; {len(exclusions)} exclusions recorded.")
    return exclusions, total_scanned

def write_exclusions_file(exclusions: Dict[str, str], total_scanned: int, path: Path) -> None:
    """
    Write the exclusions dictionary (including the total scanned count) to a YAML file.
    """
    ensure_dir(path.parent)
    data = {
        "excluded_participants": exclusions,
        "total_scanned": total_scanned,
    }
    save_yaml(data, path)
    logger.info(f"Exclusions written to {path}")

def write_manifest(dataset_id: str, download_path: Path, path: Path) -> None:
    """
    Write a simple JSON manifest describing the download.
    """
    ensure_dir(path.parent)
    manifest = {
        "dataset_id": dataset_id,
        "download_path": str(download_path),
        "downloaded": True,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Dataset manifest written to {path}")

def main(args: Optional[argparse.Namespace] = None) -> None:
    """
    Entry point for the data‑download script.
    """
    if args is None:
        parser = argparse.ArgumentParser(description="Download OpenNeuro ds003694")
        parser.add_argument(
            "--dataset",
            type=str,
            default=DATASET_ID,
            help="OpenNeuro dataset identifier (default: ds003694)",
        )
        parser.add_argument(
            "--output-dir",
            type=str,
            default="data/raw",
            help="Directory to store the downloaded raw data",
        )
        parser.add_argument(
            "--state-dir",
            type=str,
            default="state",
            help="Directory for state artefacts (exclusions, manifest)",
        )
        args = parser.parse_args()

    raw_dir = Path(args.output_dir)
    state_dir = Path(args.state_dir)

    logger.info(
        f"Configuration → dataset={args.dataset}, raw_dir={raw_dir}, state_dir={state_dir}"
    )

    # 1. Download the dataset
    try:
        download_dataset(args.dataset, raw_dir)
    except DataDownloadError as e:
        logger.error(str(e))
        sys.exit(1)

    # 2. Scan participants and collect exclusions
    try:
        exclusions, total_scanned = scan_participants(raw_dir)
    except DataDownloadError as e:
        logger.error(str(e))
        sys.exit(1)

    # 3. Write exclusions YAML
    exclusions_path = state_dir / EXCLUSIONS_FILE
    write_exclusions_file(exclusions, total_scanned, exclusions_path)

    # 4. Write dataset manifest JSON
    manifest_path = state_dir / MANIFEST_FILE
    write_manifest(args.dataset, raw_dir, manifest_path)

    logger.info("Data download and validation completed successfully.")

if __name__ == "__main__":
    main()