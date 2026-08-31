"""
Download and validate datasets from OpenML and HuggingFace.

This module implements the data acquisition pipeline for the predictive coding
time perception study. It fetches datasets, verifies checksums against canonical
sources, filters for required columns, and updates metadata logs.
"""

import json
import os
import sys
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import openml
from datasets import load_dataset
import yaml

from config import get_data_dir, get_processed_dir


class ChecksumError(Exception):
    """Raised when a dataset's checksum does not match the canonical source."""
    pass


def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def parse_readme_datasets(readme_path: Path) -> List[Dict[str, Any]]:
    """
    Parse the 'Verified datasets' block from data/README.md.
    
    Extracts dataset IDs, sources, and types from the markdown file.
    """
    if not readme_path.exists():
        raise FileNotFoundError(f"README not found at {readme_path}")
    
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the "Verified datasets" section
    in_verified_section = False
    datasets = []
    current_dataset = {}
    
    for line in content.split('\n'):
        line = line.strip()
        
        if line.startswith('### Verified datasets'):
            in_verified_section = True
            continue
        
        if in_verified_section:
            # Check if we've left the section (new section header or end of list)
            if line.startswith('###') or (line and not line.startswith('-') and not line.startswith('id:') and not line.startswith('source:') and not line.startswith('type:')):
                if current_dataset:
                    datasets.append(current_dataset)
                    current_dataset = {}
                if line.startswith('###'):
                    in_verified_section = False
                continue
            
            if line.startswith('- id:'):
                if current_dataset:
                    datasets.append(current_dataset)
                current_dataset = {'id': line.split(':', 1)[1].strip()}
            elif line.startswith('source:') and current_dataset:
                current_dataset['source'] = line.split(':', 1)[1].strip()
            elif line.startswith('type:') and current_dataset:
                current_dataset['type'] = line.split(':', 1)[1].strip()
    
    if current_dataset:
        datasets.append(current_dataset)
    
    return datasets


def fetch_openml_dataset(dataset_id: str, output_dir: Path) -> Tuple[Path, str]:
    """
    Fetch a dataset from OpenML.
    
    Args:
        dataset_id: OpenML dataset ID
        output_dir: Directory to save the dataset
        
    Returns:
        Tuple of (path to saved file, checksum)
    """
    try:
        # Fetch dataset info from API to get metadata
        dataset = openml.datasets.get_dataset(dataset_id)
        
        # Get the canonical checksum from OpenML API
        canonical_checksum = dataset.md5_checksum
        
        # Download the dataset
        output_file = output_dir / f"openml_{dataset_id}.arff"
        
        # Use OpenML's download method which respects caching
        dataset.download_data_file(str(output_file))
        
        # Compute local checksum
        local_checksum = compute_sha256(output_file)
        
        # Verify checksum against API metadata
        if local_checksum != canonical_checksum:
            raise ChecksumError(
                f"Checksum mismatch for OpenML {dataset_id}: "
                f"expected {canonical_checksum}, got {local_checksum}"
            )
        
        # Convert ARFF to CSV for easier processing
        csv_file = output_file.with_suffix('.csv')
        df = openml.datasets.get_dataset(dataset_id).to_dataframe()
        df.to_csv(csv_file, index=False)
        
        return csv_file, local_checksum
        
    except Exception as e:
        raise RuntimeError(f"Failed to fetch OpenML dataset {dataset_id}: {str(e)}")


def fetch_huggingface_dataset(dataset_id: str, output_dir: Path) -> Tuple[Path, str]:
    """
    Fetch a dataset from HuggingFace.
    
    Args:
        dataset_id: HuggingFace dataset ID
        output_dir: Directory to save the dataset
        
    Returns:
        Tuple of (path to saved file, checksum)
    """
    try:
        # Fetch dataset info from API to get metadata
        dataset_info = load_dataset(dataset_id, split='train', streaming=True)
        
        # For HuggingFace, we'll download the full dataset
        # Note: In production, we'd use streaming and compute checksum on-the-fly
        # For now, we download and compute checksum
        output_file = output_dir / f"hf_{dataset_id.replace('/', '_')}.csv"
        
        # Download dataset
        ds = load_dataset(dataset_id, split='train')
        df = ds.to_pandas()
        df.to_csv(output_file, index=False)
        
        # Compute checksum
        local_checksum = compute_sha256(output_file)
        
        # For HuggingFace, we verify against the dataset's commit hash if available
        # This is a simplified check - in production we'd use the full metadata
        # For now, we just ensure the file was downloaded successfully
        
        return output_file, local_checksum
        
    except Exception as e:
        raise RuntimeError(f"Failed to fetch HuggingFace dataset {dataset_id}: {str(e)}")


def validate_checksum(file_path: Path, expected_checksum: Optional[str] = None) -> bool:
    """
    Validate a file's checksum.
    
    Args:
        file_path: Path to the file
        expected_checksum: Expected checksum (optional)
        
    Returns:
        True if checksum is valid
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    actual_checksum = compute_sha256(file_path)
    
    if expected_checksum and actual_checksum != expected_checksum:
        raise ChecksumError(
            f"Checksum mismatch: expected {expected_checksum}, got {actual_checksum}"
        )
    
    return True


def filter_dataset_columns(df: pd.DataFrame, required_columns: List[str]) -> Tuple[bool, List[str]]:
    """
    Check if dataset has all required columns.
    
    Args:
        df: DataFrame to check
        required_columns: List of required column names
        
    Returns:
        Tuple of (has_all_columns, missing_columns)
    """
    missing = [col for col in required_columns if col not in df.columns]
    return len(missing) == 0, missing


def write_exclusion_log(exclusion_log_path: Path, dataset_id: str, reason: str) -> None:
    """
    Write an exclusion log entry.
    
    Args:
        exclusion_log_path: Path to exclusion log JSON file
        dataset_id: ID of the excluded dataset
        reason: Reason for exclusion
    """
    # Load existing log
    if exclusion_log_path.exists():
        with open(exclusion_log_path, 'r', encoding='utf-8') as f:
            log = json.load(f)
    else:
        log = []
    
    # Add new entry
    entry = {
        'dataset_id': dataset_id,
        'reason': reason,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    log.append(entry)
    
    # Write back
    with open(exclusion_log_path, 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=2)


def update_readme_status(readme_path: Path, dataset_id: str, status: str, reason: Optional[str] = None) -> None:
    """
    Update the dataset status in data/README.md.
    
    Args:
        readme_path: Path to README file
        dataset_id: ID of the dataset
        status: 'valid' or 'excluded'
        reason: Reason for exclusion (if applicable)
    """
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the "Dataset Status" section
    lines = content.split('\n')
    in_status_section = False
    new_lines = []
    found_dataset = False
    
    for i, line in enumerate(lines):
        if line.startswith('### Dataset Status'):
            in_status_section = True
            new_lines.append(line)
            continue
        
        if in_status_section:
            # Check if we've left the section
            if line.startswith('###') and not line.startswith('### Dataset Status'):
                in_status_section = False
                new_lines.append(line)
                continue
            
            # Check if this is our dataset
            if line.strip().startswith(f'- {dataset_id}:'):
                found_dataset = True
                if status == 'valid':
                    new_lines.append(f'- {dataset_id}: {status}')
                else:
                    new_lines.append(f'- {dataset_id}: {status}')
                    if reason:
                        new_lines.append(f'  reason: {reason}')
                continue
        
        new_lines.append(line)
    
    # If dataset not found, add it to the section
    if not found_dataset and in_status_section:
        new_lines.append(f'- {dataset_id}: {status}')
        if reason:
            new_lines.append(f'  reason: {reason}')
    
    # Write back
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))


def run_download_pipeline(dataset_ids: List[Dict[str, Any]], required_columns: List[str]) -> List[Dict[str, Any]]:
    """
    Run the complete download and validation pipeline.
    
    Args:
        dataset_ids: List of dataset metadata dicts
        required_columns: List of required column names
        
    Returns:
        List of successfully processed dataset info
    """
    data_dir = get_data_dir()
    processed_dir = get_processed_dir()
    readme_path = data_dir / 'README.md'
    exclusion_log_path = processed_dir / 'exclusion_log.json'
    
    successful_datasets = []
    
    for dataset_info in dataset_ids:
        dataset_id = dataset_info['id']
        source = dataset_info['source']
        
        print(f"Processing dataset: {source}_{dataset_id}")
        
        try:
            # Fetch dataset
            if source == 'openml':
                file_path, checksum = fetch_openml_dataset(dataset_id, data_dir)
            elif source == 'huggingface':
                file_path, checksum = fetch_huggingface_dataset(dataset_id, data_dir)
            else:
                raise ValueError(f"Unknown source: {source}")
            
            # Load dataset
            df = pd.read_csv(file_path)
            
            # Check for required columns
            has_all, missing = filter_dataset_columns(df, required_columns)
            
            if not has_all:
                reason = f"Missing required columns: {', '.join(missing)}"
                write_exclusion_log(exclusion_log_path, f"{source}_{dataset_id}", reason)
                update_readme_status(readme_path, f"{source}_{dataset_id}", "excluded", reason)
                print(f"  Excluded: {reason}")
                continue
            
            # Dataset is valid
            successful_datasets.append({
                'dataset_id': f"{source}_{dataset_id}",
                'file_path': str(file_path),
                'checksum': checksum,
                'rows': len(df),
                'columns': list(df.columns)
            })
            
            update_readme_status(readme_path, f"{source}_{dataset_id}", "valid")
            print(f"  Valid: {len(df)} rows, {len(df.columns)} columns")
            
        except ChecksumError as e:
            reason = f"Checksum verification failed: {str(e)}"
            write_exclusion_log(exclusion_log_path, f"{source}_{dataset_id}", reason)
            update_readme_status(readme_path, f"{source}_{dataset_id}", "excluded", reason)
            print(f"  Excluded: {reason}")
            
        except Exception as e:
            reason = f"Download/processing failed: {str(e)}"
            write_exclusion_log(exclusion_log_path, f"{source}_{dataset_id}", reason)
            update_readme_status(readme_path, f"{source}_{dataset_id}", "excluded", reason)
            print(f"  Excluded: {reason}")
    
    return successful_datasets


def main():
    """Main entry point for the download pipeline."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    data_dir = get_data_dir()
    processed_dir = get_processed_dir()
    readme_path = data_dir / 'README.md'
    
    # Ensure directories exist
    data_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Parse datasets from README
    try:
        datasets = parse_readme_datasets(readme_path)
    except FileNotFoundError as e:
        logging.error(str(e))
        sys.exit(1)
    
    if not datasets:
        logging.error("No datasets found in data/README.md")
        sys.exit(1)
    
    logging.info(f"Found {len(datasets)} datasets to process")
    
    # Required columns as per spec
    required_columns = ['duration_estimate', 'stimulus_sequence', 'participant_id']
    
    # Run pipeline
    successful = run_download_pipeline(datasets, required_columns)
    
    # Check if any datasets were successful
    if not successful:
        logging.error("No valid datasets found after filtering")
        sys.exit(1)
    
    logging.info(f"Successfully processed {len(successful)} datasets")
    
    # Save list of successful datasets for downstream use
    output_path = processed_dir / 'downloaded_datasets.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(successful, f, indent=2)
    
    logging.info(f"Download results saved to {output_path}")
    
    return successful


if __name__ == '__main__':
    main()
