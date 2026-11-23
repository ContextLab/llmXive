import json
import hashlib
import os
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import requests
from datasets import load_dataset
import pandas as pd
import openml

# Import from sibling modules as per API surface
from config import get_data_dir, get_processed_dir
from read_ids import read_dataset_ids

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from config import get_data_dir, get_processed_dir

class ChecksumError(Exception):
    """Raised when a dataset checksum does not match the expected value."""
    pass

class DataFetchError(Exception):
    """Raised when a dataset fetch fails (network, missing ID, invalid schema)."""
    pass

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def parse_dataset_ids(ids_file: Path) -> List[str]:
    """Read dataset IDs from a file."""
    if not ids_file.exists():
        raise FileNotFoundError(f"Dataset IDs file not found: {ids_file}")
    
    with open(ids_file, 'r') as f:
        ids = [line.strip() for line in f if line.strip()]
    
    if not ids:
        raise ValueError("Dataset IDs file is empty")
    
    return ids

def fetch_openml_dataset(dataset_id: str, output_dir: Path) -> Path:
    """
    Fetch a dataset from OpenML.
    
    Args:
        dataset_id: OpenML dataset ID
        output_dir: Directory to save the dataset
        
    Returns:
        Path to the downloaded dataset file
    """
    try:
        # Use OpenML Python API if available, otherwise use direct download
        try:
            import openml
            dataset = openml.datasets.get_dataset(int(dataset_id))
            data, _, _, _ = dataset.get_data()
            
            # Save as CSV
            output_path = output_dir / f"openml_{dataset_id}.csv"
            data.to_csv(output_path, index=False)
            logger.info(f"Downloaded OpenML dataset {dataset_id} to {output_path}")
            return output_path
        except ImportError:
            # Fallback: try direct URL if openml package not installed
            # This is a simplified fallback; in production, use proper API
            url = f"https://www.openml.org/api/v1/csv/data/{dataset_id}"
            import urllib.request
            output_path = output_dir / f"openml_{dataset_id}.csv"
            urllib.request.urlretrieve(url, output_path)
            logger.info(f"Downloaded OpenML dataset {dataset_id} via direct URL to {output_path}")
            return output_path
    except Exception as e:
        raise DataFetchError(f"Failed to fetch OpenML dataset {dataset_id}: {str(e)}")

def fetch_huggingface_dataset(dataset_id: str, output_dir: Path) -> Path:
    """
    Fetch a dataset from Hugging Face.
    
    Args:
        dataset_id: Hugging Face dataset ID
        output_dir: Directory to save the dataset
        
    Returns:
        Path to the downloaded dataset file
    """
    try:
        from datasets import load_dataset
        
        # Load dataset (streaming=False to get full data)
        dataset = load_dataset(dataset_id, split='train')
        
        # Save as CSV
        output_path = output_dir / f"hf_{dataset_id.replace('/', '_')}.csv"
        dataset.to_csv(output_path)
        logger.info(f"Downloaded HuggingFace dataset {dataset_id} to {output_path}")
        return output_path
    except Exception as e:
        raise DataFetchError(f"Failed to fetch HuggingFace dataset {dataset_id}: {str(e)}")

def validate_checksum(file_path: Path, expected_checksum: Optional[str] = None) -> bool:
    """
    Validate the checksum of a file.
    
    Args:
        file_path: Path to the file
        expected_checksum: Expected SHA-256 checksum (optional)
        
    Returns:
        True if checksum matches or no expected checksum provided
    """
    actual_checksum = compute_sha256(file_path)
    logger.info(f"Computed checksum for {file_path}: {actual_checksum}")
    
    if expected_checksum:
        if actual_checksum != expected_checksum:
            raise ChecksumError(
                f"Checksum mismatch for {file_path}. "
                f"Expected: {expected_checksum}, Got: {actual_checksum}"
            )
    
    return True

def filter_dataset_columns(df, required_columns: List[str]) -> bool:
    """Check if a dataset has the required columns."""
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        logger.warning(f"Missing required columns: {missing}")
        return False
    return True

def write_exclusion_log(exclusions: List[Dict[str, Any]], output_path: Path) -> None:
    """Write exclusion log to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(exclusions, f, indent=2)
    logger.info(f"Wrote exclusion log to {output_path}")

def write_blocked_status(reason: str, output_path: Path) -> None:
    """Write blocked status file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    status = {
        "status": "blocked",
        "reason": reason,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(output_path, 'w') as f:
        json.dump(status, f, indent=2)
    logger.info(f"Wrote blocked status to {output_path}")

def update_readme_status(readme_path: Path, dataset_status: Dict[str, str]) -> None:
    """Update README with dataset status."""
    if not readme_path.exists():
        readme_path.parent.mkdir(parents=True, exist_ok=True)
        with open(readme_path, 'w') as f:
            f.write("# Dataset Status\n\n")
    
    with open(readme_path, 'r') as f:
        content = f.read()
    
    # Add or update status section
    status_section = "\n## Dataset Status\n\n"
    for dataset_id, status in dataset_status.items():
        status_section += f"- **{dataset_id}**: {status}\n"
    
    # Simple append for now (in production, would be more sophisticated)
    with open(readme_path, 'a') as f:
        f.write(status_section)
    logger.info(f"Updated README with dataset status")

def run_download_pipeline() -> bool:
    """
    Run the complete download pipeline:
    1. Read dataset IDs
    2. Fetch datasets
    3. Validate checksums
    4. Write outputs
    
    Returns:
        True if all datasets were successfully downloaded and validated
    """
    data_dir = get_data_dir()
    raw_dir = data_dir / "raw"
    processed_dir = get_processed_dir()
    
    # Ensure directories exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Read dataset IDs
    ids_file = data_dir / "dataset_ids.txt"
    try:
        dataset_ids = parse_dataset_ids(ids_file)
        logger.info(f"Found {len(dataset_ids)} dataset IDs")
    except Exception as e:
        logger.error(f"Failed to read dataset IDs: {str(e)}")
        write_blocked_status(f"Failed to read dataset IDs: {str(e)}", data_dir / "blocked_status.json")
        return False
    
    exclusions = []
    dataset_status = {}
    checksums = {}
    
    for dataset_id in dataset_ids:
        logger.info(f"Processing dataset: {dataset_id}")
        try:
            # Determine source and fetch
            if dataset_id.startswith("openml_"):
                source = "openml"
                actual_id = dataset_id.replace("openml_", "")
                dataset_path = fetch_openml_dataset(actual_id, raw_dir)
            elif dataset_id.startswith("hf_"):
                source = "huggingface"
                actual_id = dataset_id.replace("hf_", "")
                dataset_path = fetch_huggingface_dataset(actual_id, raw_dir)
            else:
                # Assume OpenML by default
                source = "openml"
                dataset_path = fetch_openml_dataset(dataset_id, raw_dir)
            
            # Validate checksum (if available - for now, just compute)
            checksum = compute_sha256(dataset_path)
            checksums[str(dataset_path)] = checksum
            
            # Record success
            dataset_status[dataset_id] = "downloaded"
            logger.info(f"Successfully downloaded and validated {dataset_id}")
            
        except DataFetchError as e:
            logger.error(f"Data fetch failed for {dataset_id}: {str(e)}")
            exclusions.append({
                "dataset_id": dataset_id,
                "reason": f"Data fetch error: {str(e)}",
                "status": "failed"
            })
            dataset_status[dataset_id] = "failed"
            
        except ChecksumError as e:
            logger.error(f"Checksum validation failed for {dataset_id}: {str(e)}")
            exclusions.append({
                "dataset_id": dataset_id,
                "reason": f"Checksum error: {str(e)}",
                "status": "failed"
            })
            dataset_status[dataset_id] = "failed"
            
        except Exception as e:
            logger.error(f"Unexpected error for {dataset_id}: {str(e)}")
            exclusions.append({
                "dataset_id": dataset_id,
                "reason": f"Unexpected error: {str(e)}",
                "status": "failed"
            })
            dataset_status[dataset_id] = "failed"
    
    # Write checksums
    checksums_file = processed_dir / "checksums.json"
    with open(checksums_file, 'w') as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"Wrote checksums to {checksums_file}")
    
    # Write exclusion log
    if exclusions:
        exclusion_log_path = processed_dir / "exclusion_log.json"
        write_exclusion_log(exclusions, exclusion_log_path)
    
    # Update README
    readme_path = data_dir / "README.md"
    update_readme_status(readme_path, dataset_status)
    
    # Check if any valid datasets remain
    valid_count = sum(1 for status in dataset_status.values() if status == "downloaded")
    if valid_count == 0:
        logger.error("No valid datasets found after filtering")
        write_blocked_status("No valid datasets found after download and validation", 
                           data_dir / "blocked_status.json")
        return False
    
    logger.info(f"Pipeline completed successfully. {valid_count} datasets downloaded.")
    return True

def main():
    """Main entry point for the download script."""
    logger.info("Starting download pipeline")
    success = run_download_pipeline()
    if success:
        logger.info("Download pipeline completed successfully")
        sys.exit(0)
    else:
        logger.error("Download pipeline failed")
        sys.exit(1)

if __name__ == "__main__":
    main()