"""
T012a: Implement data download pipeline for OpenNeuro datasets.

Fetches ds000030 and ds000273 using huggingface_hub.
Validates variable fit (wcst_perseverative_errors) and saves parquet files with checksums.
"""
import os
import sys
import hashlib
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

# Add parent to path for imports if running as script
if str(Path(__file__).resolve().parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from huggingface_hub import HfApi, hf_hub_download, list_repo_files
from config import get_config, get_dataset_ids
from utils.logging_config import setup_data_flow_logger, log_data_transition, log_exclusion_reason
from utils.resource_monitor import check_resource_limits, log_resource_snapshot

def setup_logger(name: str) -> logging.Logger:
    """Setup logger for this module."""
    return setup_data_flow_logger(name)

def calculate_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def fetch_dataset_metadata(api: HfApi, dataset_id: str) -> Dict[str, Any]:
    """Fetch metadata for a specific dataset."""
    try:
        # List files to ensure dataset exists and get structure
        files = list_repo_files(dataset_id, repo_type="dataset")
        return {
            "id": dataset_id,
            "exists": True,
            "file_count": len(files),
            "files": files[:50]  # Limit for logging
        }
    except Exception as e:
        log_exclusion_reason(f"Dataset {dataset_id} not accessible: {str(e)}")
        return {
            "id": dataset_id,
            "exists": False,
            "error": str(e)
        }

def verify_variable_fit(df: pd.DataFrame, dataset_id: str, target_column: str = "wcst_perseverative_errors") -> bool:
    """
    Verify that the required behavioral variable exists in the dataset.
    Returns True if column exists and has valid data, False otherwise.
    """
    if target_column not in df.columns:
        log_exclusion_reason(
            f"Dataset {dataset_id} excluded: Missing required column '{target_column}'"
        )
        return False
    
    # Check for valid data (non-null, numeric)
    if df[target_column].isnull().all():
        log_exclusion_reason(
            f"Dataset {dataset_id} excluded: Column '{target_column}' contains only null values"
        )
        return False
    
    return True

def download_dataset_files(
    dataset_id: str, 
    output_dir: Path, 
    config: Any,
    logger: logging.Logger
) -> Optional[Path]:
    """
    Download dataset files from HuggingFace Hub.
    Returns path to downloaded parquet file or None if failed.
    """
    logger.info(f"Processing dataset: {dataset_id}")
    
    # Check resource limits before download
    check_resource_limits()
    
    try:
        # Use huggingface_hub to download specific files
        # For OpenNeuro datasets, we typically need to download specific behavioral files
        # or the entire dataset structure. We'll target the TSV/CSV files containing behavioral data.
        
        api = HfApi()
        
        # List files to find behavioral data
        all_files = list_repo_files(dataset_id, repo_type="dataset")
        
        # Look for common behavioral data files
        behavioral_patterns = [
            "behav*.tsv", "behav*.csv", "participants.tsv", 
            "participants.csv", "*task*.tsv", "*task*.csv",
            "phenotype*.tsv", "phenotype*.csv"
        ]
        
        target_files = []
        for pattern in behavioral_patterns:
            for file in all_files:
                if pattern.lower() in file.lower():
                    target_files.append(file)
        
        if not target_files:
            # Fallback: try to download any TSV/CSV file
            for file in all_files:
                if file.endswith(('.tsv', '.csv')):
                    target_files.append(file)
                    if len(target_files) >= 3:  # Limit to first 3
                        break
        
        if not target_files:
            log_exclusion_reason(f"No behavioral data files found in {dataset_id}")
            return None
        
        # Download files
        downloaded_paths = []
        for file_path in target_files:
            local_path = hf_hub_download(
                repo_id=dataset_id,
                filename=file_path,
                repo_type="dataset",
                cache_dir=str(output_dir / "cache"),
                local_dir=str(output_dir / dataset_id)
            )
            downloaded_paths.append(Path(local_path))
        
        # Combine into single parquet file for processing
        dfs = []
        for path in downloaded_paths:
            try:
                if path.suffix == '.tsv':
                  df = pd.read_csv(path, sep='\t')
                elif path.suffix == '.csv':
                  df = pd.read_csv(path)
                else:
                  continue
                
                # Add dataset ID column
                df['dataset_id'] = dataset_id
                dfs.append(df)
                
            except Exception as e:
                logger.warning(f"Could not read {path}: {e}")
                continue
        
        if not dfs:
            log_exclusion_reason(f"Could not parse any data files from {dataset_id}")
            return None
        
        # Combine and save
        combined_df = pd.concat(dfs, ignore_index=True)
        
        # Verify variable fit
        if not verify_variable_fit(combined_df, dataset_id):
            return None
        
        # Save as parquet
        output_file = output_dir / f"{dataset_id}_behavioral.parquet"
        combined_df.to_parquet(output_file, index=False)
        
        # Calculate checksum
        checksum = calculate_file_checksum(output_file)
        
        # Log data transition
        log_data_transition(
            source=f"HuggingFace/{dataset_id}",
            destination=str(output_file),
            record_count=len(combined_df),
            checksum=checksum
        )
        
        logger.info(f"Successfully downloaded and saved {dataset_id} to {output_file}")
        return output_file
        
    except Exception as e:
        logger.error(f"Failed to download dataset {dataset_id}: {e}")
        log_exclusion_reason(f"Download failed for {dataset_id}: {str(e)}")
        return None

def save_metadata_and_checksums(
    results: List[Dict[str, Any]], 
    output_path: Path
):
    """Save download metadata and checksums to JSON."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def main():
    """Main entry point for data download pipeline."""
    logger = setup_logger("download_data")
    logger.info("Starting data download pipeline (T012a)")
    
    # Load configuration
    config = get_config()
    dataset_ids = get_dataset_ids()
    
    if not dataset_ids:
        logger.error("No dataset IDs found in configuration")
        sys.exit(1)
    
    # Ensure output directory exists
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    successful_downloads = 0
    
    for dataset_id in dataset_ids:
        logger.info(f"Processing {dataset_id}")
        
        # Fetch metadata
        metadata = fetch_dataset_metadata(HfApi(), dataset_id)
        
        if not metadata.get("exists"):
            results.append(metadata)
            continue
        
        # Download and process
        output_path = download_dataset_files(dataset_id, output_dir, config, logger)
        
        if output_path:
            successful_downloads += 1
            results.append({
                "dataset_id": dataset_id,
                "status": "success",
                "output_file": str(output_path),
                "checksum": calculate_file_checksum(output_path)
            })
        else:
            results.append({
                "dataset_id": dataset_id,
                "status": "failed",
                "reason": "Variable fit check failed or download error"
            })
    
    # Save metadata
    metadata_path = output_dir / "download_metadata.json"
    save_metadata_and_checksums(results, metadata_path)
    
    logger.info(f"Download pipeline complete. Success: {successful_downloads}/{len(dataset_ids)}")
    
    # Final resource check
    log_resource_snapshot()
    
    if successful_downloads == 0:
        logger.error("No datasets were successfully downloaded")
        sys.exit(1)

if __name__ == "__main__":
    main()
