"""
Data Acquisition Module for Predictive Coding Time Perception Study.

This module handles the downloading of datasets from OpenML and HuggingFace,
validates them against Gate 0 constraints, and manages the data storage pipeline.
"""
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

import openml
from datasets import load_dataset

from config import get_data_dir, set_seed
from gate0 import (
    DataNotFoundError,
    parse_verified_datasets_block,
    validate_gate0,
    update_readme_with_gate_status,
)

# Ensure deterministic behavior
set_seed(42)


def parse_readme_datasets(readme_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Parse the 'Verified datasets' block from data/README.md.

    Args:
        readme_path: Optional path to README. Defaults to data/README.md.

    Returns:
        List of dataset metadata dictionaries.
    """
    if readme_path is None:
        readme_path = get_data_dir() / 'README.md'

    if not readme_path.exists():
        print(f"Warning: {readme_path} does not exist.", file=sys.stderr)
        return []

    content = readme_path.read_text(encoding='utf-8')
    return parse_verified_datasets_block(content)


def fetch_openml_dataset(
    dataset_id: int,
    raw_dir: Path,
    retry_attempts: int = 3,
    backoff_factor: int = 2
) -> Optional[Path]:
    """
    Fetch a dataset from OpenML and save it to the raw directory.

    Args:
        dataset_id: The OpenML dataset ID.
        raw_dir: Directory to save the dataset.
        retry_attempts: Number of retry attempts on failure.
        backoff_factor: Exponential backoff factor in seconds.

    Returns:
        Path to the saved dataset file, or None if failed.
    """
    raw_dir.mkdir(parents=True, exist_ok=True)
    output_file = raw_dir / f"openml_{dataset_id}.csv"

    if output_file.exists():
        print(f"Dataset {dataset_id} already exists at {output_file}. Skipping download.")
        return output_file

    for attempt in range(retry_attempts):
        try:
            print(f"Fetching OpenML dataset {dataset_id} (Attempt {attempt + 1}/{retry_attempts})...")
            # Explicitly request download to avoid lazy loading warnings
            dataset = openml.datasets.get_dataset(
                dataset_id,
                download_data=True,
                download_qualities=True,
                download_features_meta_data=True
            )
            
            # Get the data as a pandas DataFrame
            df, _ = dataset.get_data(dataset_format='dataframe')
            
            # Save to CSV
            df.to_csv(output_file, index=False)
            print(f"Successfully saved dataset {dataset_id} to {output_file}")
            return output_file

        except openml.exceptions.OpenMLServerError as e:
            print(f"OpenML Server Error for {dataset_id}: {e}", file=sys.stderr)
            if "Unknown dataset" in str(e):
                # This is a fatal error for this specific ID, don't retry
                print(f"Dataset {dataset_id} not found on OpenML.", file=sys.stderr)
                return None
        except Exception as e:
            print(f"Unexpected error fetching {dataset_id}: {e}", file=sys.stderr)
        
        if attempt < retry_attempts - 1:
            wait_time = backoff_factor ** attempt
            print(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)

    print(f"Failed to fetch dataset {dataset_id} after {retry_attempts} attempts.", file=sys.stderr)
    return None


def fetch_huggingface_dataset(
    dataset_id: str,
    raw_dir: Path,
    split: str = "train",
    trust_remote_code: bool = False
) -> Optional[Path]:
    """
    Fetch a dataset from HuggingFace and save it to the raw directory.

    Args:
        dataset_id: The HuggingFace dataset identifier (e.g., 'username/dataset').
        raw_dir: Directory to save the dataset.
        split: The dataset split to download.
        trust_remote_code: Whether to trust remote code in the dataset.

    Returns:
        Path to the saved dataset file, or None if failed.
    """
    raw_dir.mkdir(parents=True, exist_ok=True)
    # Sanitize dataset_id for filename
    safe_name = dataset_id.replace("/", "_").replace(":", "_")
    output_file = raw_dir / f"hf_{safe_name}.csv"

    if output_file.exists():
        print(f"Dataset {dataset_id} already exists at {output_file}. Skipping download.")
        return output_file

    try:
        print(f"Fetching HuggingFace dataset {dataset_id}...")
        ds = load_dataset(dataset_id, split=split, trust_remote_code=trust_remote_code)
        
        # Convert to pandas and save
        df = ds.to_pandas()
        df.to_csv(output_file, index=False)
        print(f"Successfully saved dataset {dataset_id} to {output_file}")
        return output_file

    except Exception as e:
        print(f"Failed to fetch HuggingFace dataset {dataset_id}: {e}", file=sys.stderr)
        return None


def validate_gate0(readme_path: Optional[Path] = None) -> bool:
    """
    Wrapper to run Gate 0 validation.

    Args:
        readme_path: Optional path to README.

    Returns:
        True if validation passes, False otherwise.
    """
    if readme_path is None:
        readme_path = get_data_dir() / 'README.md'

    try:
        content = readme_path.read_text(encoding='utf-8')
        datasets = parse_verified_datasets_block(content)
        validate_gate0(datasets)
        return True
    except DataNotFoundError as e:
        print(f"Gate 0 Validation Failed: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Gate 0 Unexpected Error: {e}", file=sys.stderr)
        return False


def write_gate_status(status_file: Path, status: str, details: List[str]) -> None:
    """
    Write the Gate 0 status to a JSON file for downstream consumption.

    Args:
        status_file: Path to the status JSON file.
        status: 'passed' or 'blocked'.
        details: List of status messages.
    """
    status_file.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "status": status,
        "details": details,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(status_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def run_download_pipeline(
    readme_path: Optional[Path] = None,
    status_file: Optional[Path] = None
) -> List[Path]:
    """
    Main pipeline for downloading datasets.

    1. Runs Gate 0 validation.
    2. If Gate 0 fails, updates status and halts.
    3. If Gate 0 passes, downloads all verified datasets.

    Args:
        readme_path: Path to data/README.md.
        status_file: Path to write gate0_status.json.

    Returns:
        List of paths to downloaded dataset files.
    """
    if readme_path is None:
        readme_path = get_data_dir() / 'README.md'
    
    if status_file is None:
        status_file = get_data_dir() / 'gate0_status.json'

    raw_dir = get_data_dir() / 'raw'
    raw_dir.mkdir(parents=True, exist_ok=True)

    # 1. Run Gate 0
    print("--- Running Gate 0 Validation ---")
    gate_passed = validate_gate0(readme_path)

    if not gate_passed:
        # Gate 0 failed: Fetch datasets again to get specific errors for status file
        # (Since validate_gate0 only checks metadata, we need to know WHICH ones failed if any)
        # However, per spec, Gate 0 halts if NO valid dataset is found in the pre-approved list.
        # We will report the generic failure here.
        update_readme_with_gate_status(readme_path, "Gate 0: Failed")
        write_gate_status(status_file, "blocked", ["Gate 0 validation failed: No valid datasets found."])
        print(f"Gate 0 status written to {status_file}: blocked")
        raise DataNotFoundError("Gate 0 validation failed. Halting download pipeline.")

    print("Gate 0 passed. Proceeding with download.")
    
    # 2. Parse and Download
    datasets_meta = parse_readme_datasets(readme_path)
    downloaded_paths: List[Path] = []
    errors: List[str] = []

    for meta in datasets_meta:
        ds_id = meta['id']
        source = meta['source'].lower()
        
        if source == 'openml':
            path = fetch_openml_dataset(ds_id, raw_dir)
        elif source == 'huggingface':
            path = fetch_huggingface_dataset(meta['id'], raw_dir) # id field holds string for HF
        else:
            errors.append(f"Unknown source '{source}' for dataset {ds_id}")
            continue

        if path:
            downloaded_paths.append(path)
        else:
            errors.append(f"Failed to fetch {ds_id} from {source}")

    # 3. Final Status Update
    if errors:
        status_msg = "blocked - " + "; ".join(errors)
        update_readme_with_gate_status(readme_path, status_msg)
        write_gate_status(status_file, "blocked", errors)
        print(f"Gate 0 status written to {status_file}: blocked - {errors}")
        # Even if some downloaded, if Gate 0 logic implies strict validity, we might halt.
        # But usually, partial success is okay if at least one valid dataset was found and processed.
        # However, the task says "If Gate 0 fails, halt". 
        # Here, Gate 0 (metadata check) passed, but fetch failed. 
        # We proceed with what we have, but log the failure.
        # If NO datasets were downloaded, we should raise.
        if not downloaded_paths:
            raise RuntimeError(f"No datasets could be downloaded. Errors: {errors}")
    else:
        update_readme_with_gate_status(readme_path, "Gate 0: Passed")
        write_gate_status(status_file, "passed", [f"Successfully downloaded {len(downloaded_paths)} datasets."])
        print(f"Gate 0 status written to {status_file}: passed")

    return downloaded_paths


def main() -> int:
    """
    CLI entry point for the download pipeline.
    """
    try:
        readme_path = get_data_dir() / 'README.md'
        status_file = get_data_dir() / 'gate0_status.json'
        
        paths = run_download_pipeline(readme_path, status_file)
        print(f"Download pipeline completed. {len(paths)} datasets ready.")
        return 0
    except DataNotFoundError as e:
        print(f"Halted due to Gate 0 failure: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Pipeline failed: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())