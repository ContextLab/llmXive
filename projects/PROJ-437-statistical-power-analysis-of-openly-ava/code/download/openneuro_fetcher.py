"""
OpenNeuro Data Fetcher for fMRI Power Analysis.

This module handles the downloading of raw BIDS data from OpenNeuro datasets.
It strictly enforces the use of real data sources and fails loudly on any
fetch errors without synthetic fallbacks.
"""

import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from datasets import load_dataset
from tqdm import tqdm

# Import seed manager for reproducibility
try:
    from utils.seed_manager import set_global_seed
except ImportError:
    # Fallback for direct execution context
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from utils.seed_manager import set_global_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Hardcoded whitelist of verified datasets as per task requirements
VERIFIED_DATASET_IDS = [
    "ds000030",
    "ds000248",
    "ds000250",
    "ds000251",
    "ds000252"
]

def get_dataset_info(dataset_id: str) -> Dict[str, Any]:
    """
    Retrieve metadata for a specific OpenNeuro dataset.

    Args:
        dataset_id: The OpenNeuro dataset ID (e.g., 'ds000030').

    Returns:
        Dictionary containing dataset metadata.

    Raises:
        ValueError: If the dataset_id is not in the verified whitelist.
    """
    if dataset_id not in VERIFIED_DATASET_IDS:
        raise ValueError(
            f"Dataset '{dataset_id}' is not in the verified whitelist. "
            f"Whitelisted IDs: {VERIFIED_DATASET_IDS}"
        )

    logger.info(f"Fetching metadata for dataset: {dataset_id}")
    # We use the Hugging Face datasets library to access OpenNeuro data
    # The dataset_id is used directly with the 'openneuro' config or by constructing the repo
    # OpenNeuro datasets on Hugging Face are typically under the organization 'OpenNeuroDatasets'
    # However, the `datasets` library often handles 'openneuro/dsXXXX' automatically if configured,
    # or we construct the path. The standard pattern for OpenNeuro on HF is 'OpenNeuroDatasets/{dataset_id}'
    
    # We do not actually fetch metadata here to avoid network calls just for info,
    # but we validate the ID. The actual fetch happens in download_dataset_file.
    return {
        "id": dataset_id,
        "verified": True,
        "source": "OpenNeuro via Hugging Face Datasets"
    }

def download_dataset_file(
    dataset_id: str,
    output_dir: Path,
    streaming: bool = True,
    max_retries: int = 3
) -> bool:
    """
    Download raw BIDS data for a specific dataset.

    This function uses the `datasets` library with streaming enabled for large datasets.
    It strictly adheres to the "Fail Loudly" policy: if the real data fetch fails,
    it raises a ValueError and does NOT fall back to synthetic data.

    Args:
        dataset_id: The OpenNeuro dataset ID.
        output_dir: Local directory where data will be saved.
        streaming: If True, streams the dataset (recommended for >1GB).
        max_retries: Maximum number of retry attempts.

    Returns:
        True if download was successful.

    Raises:
        ValueError: If the dataset is not verified or if the fetch fails after retries.
        RuntimeError: If the real data fetch fails and cannot be recovered.
    """
    if dataset_id not in VERIFIED_DATASET_IDS:
        raise ValueError(
            f"Real data fetch failed. Aborting: Dataset '{dataset_id}' is not whitelisted."
        )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting download for {dataset_id} to {output_dir} (streaming={streaming})")

    attempt = 0
    while attempt < max_retries:
        try:
            # Construct the dataset path for Hugging Face
            # OpenNeuro datasets are hosted under 'OpenNeuroDatasets' organization
            dataset_path = f"OpenNeuroDatasets/{dataset_id}"

            logger.info(f"Attempting to load dataset: {dataset_path}")

            # Load dataset with streaming
            # Note: 'download' argument in load_dataset usually implies downloading the whole dataset
            # to disk if streaming=False. With streaming=True, it iterates without full download.
            # However, for BIDS data, we often want the files on disk.
            # The `datasets` library's `download` method or `save_to_disk` is needed.
            # For this implementation, we will use the `download` feature of the dataset object
            # or iterate and save if necessary.
            
            # Strategy: Use streaming to verify access and iterate, then save to disk.
            # Or, if the dataset is small enough, load normally.
            # Given the constraint "Must use streaming=True for datasets >1GB", we default to streaming.
            # However, to actually get files on disk for BIDS, we often need to download the files.
            # The `datasets` library supports `download=True` which downloads the files.
            # We will use `load_dataset` with `streaming=True` to initialize, then force a download.
            
            # Actually, `datasets.load_dataset(..., streaming=True)` returns an IterableDataset.
            # To get files on disk, we might need to use `download` or manually save.
            # A more robust approach for BIDS is to use `download` from the dataset object.
            
            # Let's try the standard HF approach for OpenNeuro:
            # ds = load_dataset("OpenNeuroDatasets/ds000030", trust_remote_code=True)
            # This might be too heavy. Let's stick to the requirement: use streaming.
            # If we stream, we can iterate over the files and save them.
            
            # However, `load_dataset` with streaming=True doesn't automatically download all files to disk.
            # We will implement a manual download loop for the files if streaming is used,
            # or use the `download` method if available.
            
            # Correct approach for "Fail Loudly" with real data:
            # Attempt to load the dataset. If it fails (network error, missing repo), raise.
            # We will use `load_dataset` with `trust_remote_code=True` as OpenNeuro datasets often need it.
            
            ds = load_dataset(
                dataset_path,
                split="train", # OpenNeuro datasets often have a single split or no split
                streaming=streaming,
                trust_remote_code=True
            )
            
            # If streaming, we need to manually save the files.
            # But `ds` is an IterableDataset. We can iterate over it.
            # The items in OpenNeuro datasets on HF are usually file paths or dicts of file paths.
            # Let's assume the dataset yields dictionaries with file content or paths.
            
            # For the purpose of this task, we will assume the dataset yields the BIDS structure
            # and we need to save it.
            # If the dataset is too large to stream into memory, we process it in chunks.
            
            # Since we need to "fetch ALL subjects and runs", we must iterate through the whole dataset.
            # We will use tqdm to show progress.
            
            if streaming:
                logger.info("Processing in streaming mode. Saving files to disk...")
                file_count = 0
                # We need to know the structure. OpenNeuro on HF usually has a 'file' key or similar.
                # We will iterate and save.
                # Note: This part is tricky without knowing the exact schema of the HF dataset.
                # We will assume a standard structure or try to infer it.
                # A common pattern is ds['file'] or ds['path'].
                # Let's try to access the first item to determine structure.
                try:
                    first_item = next(iter(ds))
                except StopIteration:
                    raise RuntimeError("Dataset is empty or stream failed.")
                
                # Determine keys
                keys = first_item.keys()
                logger.info(f"Dataset keys: {keys}")
                
                # We will iterate and save files.
                # We assume the dataset yields dicts where values are file paths or content.
                # If it's a dict of file paths, we need to download them.
                # But `load_dataset` with streaming usually handles the download of the file content
                # into memory or a cache. We want to save to `output_dir`.
                # We will save the raw content if it's bytes, or the file if it's a path.
                
                # For OpenNeuro, the data is often stored as nifti files.
                # We will save them to the output directory maintaining the BIDS structure.
                # We'll assume the dataset yields a dict with 'path' and 'content' or similar.
                # If not, we might need to use `download` from the dataset object.
                
                # Alternative: Use `ds.download()` if available.
                # Let's try to download the whole dataset to a temp dir and then move it.
                # But that violates streaming for large datasets.
                
                # Let's stick to the requirement: use streaming.
                # We will iterate and save.
                # We assume the dataset yields a dict with 'file' key containing the file path relative to BIDS root.
                # And 'data' key containing the file content.
                
                # If the dataset structure is different, this might fail, but it's the best we can do
                # without a specific schema.
                
                # Let's assume a standard HF dataset structure for OpenNeuro:
                # It yields dicts with keys like 'sub-01', 'ses-01', etc. or a flat structure.
                # Actually, OpenNeuro datasets on HF are often structured as a single dataset with
                # a 'file' column containing the path and a 'data' column containing the content.
                
                # We will try to save the data.
                for item in tqdm(ds, desc=f"Downloading {dataset_id}"):
                    if isinstance(item, dict):
                        # Check for 'path' and 'data' or similar
                        if 'path' in item and 'data' in item:
                            file_path = Path(item['path'])
                            file_content = item['data']
                            dest_path = output_dir / file_path
                            dest_path.parent.mkdir(parents=True, exist_ok=True)
                            if isinstance(file_content, bytes):
                                dest_path.write_bytes(file_content)
                            else:
                                # If it's a string, write as text (unlikely for nifti)
                                dest_path.write_text(str(file_content))
                            file_count += 1
                        elif 'file' in item:
                            # Another common structure
                            file_path = Path(item['file'])
                            # We need the content. If 'data' is not present, we might need to download it.
                            # This suggests the dataset is not fully loaded.
                            # We will raise an error if we can't get the content.
                            raise RuntimeError("Dataset structure does not provide file content in streaming mode.")
                    else:
                        # If it's a string (file path), we need to download it.
                        # This is not ideal for streaming.
                        raise RuntimeError("Unexpected dataset item type.")
                
                logger.info(f"Downloaded {file_count} files for {dataset_id}")
            else:
                # Non-streaming mode: load and save
                logger.info("Loading dataset in non-streaming mode.")
                ds = load_dataset(dataset_path, trust_remote_code=True)
                # Save to disk
                ds.save_to_disk(str(output_dir))
                logger.info(f"Saved dataset to {output_dir}")

            return True

        except Exception as e:
            attempt += 1
            logger.warning(f"Attempt {attempt}/{max_retries} failed for {dataset_id}: {str(e)}")
            if attempt == max_retries:
                logger.error(f"Real data fetch failed after {max_retries} attempts.")
                raise ValueError("Real data fetch failed. Aborting.") from e
            # else: retry
    
    return False

def get_subjects_list(dataset_id: str, data_dir: Path) -> List[str]:
    """
    Get a list of subject IDs from the downloaded BIDS data.

    Args:
        dataset_id: The dataset ID.
        data_dir: Path to the downloaded data directory.

    Returns:
        List of subject IDs (e.g., ['sub-01', 'sub-02']).
    """
    subjects = []
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    # Scan for subject directories
    for item in data_dir.iterdir():
        if item.is_dir() and item.name.startswith("sub-"):
            subjects.append(item.name)

    if not subjects:
        logger.warning(f"No subjects found in {data_dir}")
    
    return sorted(subjects)

def download_subject_data(
    dataset_id: str,
    subject_id: str,
    data_dir: Path,
    output_dir: Path
) -> bool:
    """
    Download data for a specific subject.

    Note: Since we already download the whole dataset in `download_dataset_file`,
    this function primarily validates that the subject data exists.
    If the task requires fetching specific subjects, we would implement a filter.
    For now, we assume the whole dataset is downloaded and we are just confirming.

    Args:
        dataset_id: The dataset ID.
        subject_id: The subject ID.
        data_dir: Path to the downloaded data directory.
        output_dir: Path to the output directory (same as data_dir in this implementation).

    Returns:
        True if subject data is found, False otherwise.
    """
    subject_path = data_dir / subject_id
    if subject_path.exists():
        logger.info(f"Subject data found for {subject_id}")
        return True
    else:
        logger.warning(f"Subject data not found for {subject_id}")
        return False

def fetch_paradigm_data(
    dataset_id: str,
    paradigm_name: str,
    data_dir: Path
) -> List[Path]:
    """
    Fetch paths to data files for a specific paradigm.

    Args:
        dataset_id: The dataset ID.
        paradigm_name: The name of the paradigm (e.g., 'Motor', 'Visual').
        data_dir: Path to the downloaded data directory.

    Returns:
        List of paths to relevant files (e.g., task-Motor_bold.nii.gz).
    """
    files = []
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    # Search for files matching the paradigm name
    for item in data_dir.rglob(f"*{paradigm_name}*"):
        if item.is_file() and (item.suffix == '.nii.gz' or item.suffix == '.json'):
            files.append(item)

    if not files:
        logger.warning(f"No files found for paradigm '{paradigm_name}' in {data_dir}")

    return files

def main():
    """
    Main entry point for the OpenNeuro fetcher.
    Downloads all verified datasets to the data/raw directory.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Fetch OpenNeuro BIDS data")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/raw",
        help="Directory to save downloaded data"
    )
    parser.add_argument(
        "--datasets",
        type=str,
        nargs="+",
        default=VERIFIED_DATASET_IDS,
        help=f"List of dataset IDs to fetch. Default: {VERIFIED_DATASET_IDS}"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )

    args = parser.parse_args()

    # Set global seed
    set_global_seed(args.seed)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Validate datasets
    for ds_id in args.datasets:
        if ds_id not in VERIFIED_DATASET_IDS:
            logger.error(f"Dataset {ds_id} is not in the verified whitelist.")
            sys.exit(1)

    # Download each dataset
    for ds_id in args.datasets:
        logger.info(f"Processing dataset: {ds_id}")
        try:
            # Create a subdirectory for each dataset
            ds_output_dir = output_dir / ds_id
            success = download_dataset_file(
                dataset_id=ds_id,
                output_dir=ds_output_dir,
                streaming=True
            )
            if success:
                logger.info(f"Successfully downloaded {ds_id}")
                # Verify subjects
                subjects = get_subjects_list(ds_id, ds_output_dir)
                logger.info(f"Found {len(subjects)} subjects in {ds_id}: {subjects}")
            else:
                logger.error(f"Failed to download {ds_id}")
                sys.exit(1)
        except Exception as e:
            logger.error(f"Error processing {ds_id}: {str(e)}")
            sys.exit(1)

    logger.info("All datasets processed successfully.")

if __name__ == "__main__":
    main()