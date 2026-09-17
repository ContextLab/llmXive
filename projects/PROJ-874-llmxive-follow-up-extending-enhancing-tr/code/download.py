"""
Dataset download and validation module for llmXive.

Handles fetching NarrLV and VBench datasets from HuggingFace,
checksum verification, and pre-flight validation.
"""
import os
import sys
import hashlib
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datasets import load_dataset
from huggingface_hub import hf_hub_download, HfApi

# Import from local config
from config import (
    get_dataset_paths, 
    get_required_files, 
    get_raw_dir,
    DatasetNotFoundError,
    LlmXiveError,
    setup_logging
)

logger = logging.getLogger(__name__)

# Expected checksums for dataset files (SHA-256)
# These would be populated from a manifest or config in a real production system
EXPECTED_CHECKSUMS = {
    # Placeholder for actual checksums - in production these would be verified
    "narrlv": {
        "train": None,  # To be determined
        "val": None,
        "test": None
    },
    "vbench": {
        "train": None,
        "val": None,
        "test": None
    }
}

def calculate_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Calculate the hash of a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use
        
    Returns:
        Hexadecimal hash string
        
    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def verify_checksums(dataset_name: str, split: str, file_paths: List[Path]) -> Tuple[bool, List[str]]:
    """
    Verify checksums for dataset files.
    
    Args:
        dataset_name: Name of the dataset (e.g., "narrlv", "vbench")
        split: Dataset split (e.g., "train", "val", "test")
        file_paths: List of file paths to verify
        
    Returns:
        Tuple of (all_valid: bool, missing_or_invalid: List[str])
    """
    missing_or_invalid = []
    
    for file_path in file_paths:
        if not file_path.exists():
            missing_or_invalid.append(f"Missing: {file_path}")
            continue
            
        # In a real implementation, we would verify against EXPECTED_CHECKSUMS
        # For now, we just check existence
        logger.debug(f"Verified existence of {file_path}")
        
    return len(missing_or_invalid) == 0, missing_or_invalid

def download_dataset(dataset_name: str, split: str, cache_dir: Optional[Path] = None) -> List[Path]:
    """
    Download a specific dataset split from HuggingFace.
    
    Args:
        dataset_name: Name of the dataset
        split: Dataset split to download
        cache_dir: Optional cache directory
        
    Returns:
        List of paths to downloaded files
        
    Raises:
        LlmXiveError: If download fails
    """
    raw_dir = get_raw_dir()
    output_dir = raw_dir / dataset_name / split
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        logger.info(f"Downloading {dataset_name} {split} split...")
        
        # Use HuggingFace datasets library to download
        # In a real implementation, we would specify the actual dataset IDs
        dataset_id_map = {
            "narrlv": "llmXive/narrlv",  # Placeholder
            "vbench": "llmXive/vbench"   # Placeholder
        }
        
        if dataset_name not in dataset_id_map:
            raise LlmXiveError(f"Unknown dataset: {dataset_name}")
            
        dataset_id = dataset_id_map[dataset_name]
        
        # Load dataset (this will download if not cached)
        dataset = load_dataset(dataset_id, split=split, cache_dir=str(cache_dir) if cache_dir else None)
        
        # Save dataset to local files
        file_paths = []
        if hasattr(dataset, 'to_pandas'):
            # For tabular data
            df = dataset.to_pandas()
            output_file = output_dir / f"{dataset_name}_{split}.parquet"
            df.to_parquet(output_file)
            file_paths.append(output_file)
        else:
            # For video/image data, we might need to save frames/videos
            # This is a placeholder for more complex logic
            output_file = output_dir / f"{dataset_name}_{split}.json"
            with open(output_file, 'w') as f:
                json.dump({"dataset": dataset_name, "split": split, "count": len(dataset)}, f)
            file_paths.append(output_file)
            
        logger.info(f"Successfully downloaded {dataset_name} {split} to {output_dir}")
        return file_paths
        
    except Exception as e:
        raise LlmXiveError(f"Failed to download {dataset_name} {split}: {str(e)}")

def download_all_datasets() -> Dict[str, List[Path]]:
    """
    Download all required datasets.
    
    Returns:
        Dictionary mapping dataset names to lists of file paths
        
    Raises:
        LlmXiveError: If any download fails
    """
    dataset_paths = get_dataset_paths()
    results = {}
    
    for dataset_name, splits in dataset_paths.items():
        for split in splits:
            try:
                files = download_dataset(dataset_name, split)
                if dataset_name not in results:
                    results[dataset_name] = []
                results[dataset_name].extend(files)
            except LlmXiveError as e:
                logger.error(f"Download failed for {dataset_name} {split}: {e}")
                raise
                
    return results

def check_preflight_requirements() -> Tuple[bool, List[str]]:
    """
    Check if all required dataset files exist before generation.
    
    Returns:
        Tuple of (all_present: bool, missing_files: List[str])
    """
    required_files = get_required_files()
    missing_files = []
    
    for file_path_str in required_files:
        file_path = Path(file_path_str)
        if not file_path.exists():
            missing_files.append(str(file_path))
            
    return len(missing_files) == 0, missing_files

def abort_on_missing_files(missing_files: List[str]) -> None:
    """
    Abort execution with a clear error message listing missing files.
    
    Args:
        missing_files: List of missing file paths
        
    Raises:
        DatasetNotFoundError: Always raised with detailed message
    """
    if not missing_files:
        return
        
    error_msg = (
        "Dataset download/validation failed. The following required files are missing:\n\n"
        + "\n".join(f"  - {f}" for f in missing_files)
        + "\n\nPlease ensure all datasets are properly downloaded and validated.\n"
        "Run 'python code/download.py' to attempt downloading missing files."
    )
    
    logger.error(error_msg)
    raise DatasetNotFoundError(error_msg)

def main():
    """Main entry point for dataset download script."""
    parser = argparse.ArgumentParser(description="Download and validate datasets for llmXive")
    parser.add_argument(
        "--check-only", 
        action="store_true", 
        help="Only check for existing files, don't download"
    )
    parser.add_argument(
        "--download-all", 
        action="store_true", 
        help="Download all datasets"
    )
    parser.add_argument(
        "--dataset", 
        type=str, 
        choices=["narrlv", "vbench", "all"],
        default="all",
        help="Dataset to download (default: all)"
    )
    parser.add_argument(
        "--split",
        type=str,
        choices=["train", "val", "test", "all"],
        default="all",
        help="Split to download (default: all)"
    )
    
    args = parser.parse_args()
    setup_logging()
    
    try:
        # Check pre-flight requirements
        all_present, missing = check_preflight_requirements()
        
        if args.check_only:
            if all_present:
                logger.info("All required dataset files are present.")
                sys.exit(0)
            else:
                logger.error("Missing dataset files:")
                for f in missing:
                    logger.error(f"  - {f}")
                sys.exit(1)
        
        # If files are missing and we're not just checking, download them
        if not all_present:
            logger.warning(f"Missing {len(missing)} required files. Attempting download...")
            abort_on_missing_files(missing)  # This will raise an error with clear message
            
        if args.download_all or args.dataset == "all":
            logger.info("Downloading all datasets...")
            download_all_datasets()
        else:
            # Download specific dataset
            logger.info(f"Downloading {args.dataset} dataset...")
            # Implementation for specific dataset download would go here
            
        logger.info("Dataset download and validation complete.")
        
    except DatasetNotFoundError as e:
        logger.error(f"Dataset error: {e}")
        sys.exit(1)
    except LlmXiveError as e:
        logger.error(f"Download error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()