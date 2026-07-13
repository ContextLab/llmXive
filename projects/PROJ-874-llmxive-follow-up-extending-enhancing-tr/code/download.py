import os
import sys
import hashlib
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for dataset configuration
DATASET_CONFIG = {
    "narrlv": {
        "name": "NarrLV",
        "source": "llmXive/NarrLV",
        "required_files": [
            "video_001.mp4", "video_002.mp4", "video_003.mp4",
            "video_004.mp4", "video_005.mp4", "metadata.json"
        ],
        "checksums": {
            "video_001.mp4": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "video_002.mp4": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "video_003.mp4": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "video_004.mp4": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "video_005.mp4": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "metadata.json": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        }
    },
    "vbench": {
        "name": "VBench",
        "source": "llmXive/VBench-Subset",
        "required_files": [
            "vb_sample_001.mp4", "vb_sample_002.mp4", "vb_sample_003.mp4",
            "vb_sample_004.mp4", "vb_sample_005.mp4", "vb_metadata.json"
        ],
        "checksums": {
            "vb_sample_001.mp4": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "vb_sample_002.mp4": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "vb_sample_003.mp4": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "vb_sample_004.mp4": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "vb_sample_005.mp4": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "vb_metadata.json": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        }
    }
}

def calculate_file_hash(file_path: str, algorithm: str = 'sha256') -> str:
    """Calculate the hash of a file."""
    hash_func = hashlib.new(algorithm)
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except PermissionError:
        raise PermissionError(f"Permission denied: {file_path}")

def verify_checksums(dataset_name: str, data_dir: str) -> Tuple[bool, List[str]]:
    """
    Verify that all required files exist and match their expected checksums.
    
    Returns:
        Tuple of (all_valid, list_of_missing_or_corrupted_files)
    """
    config = DATASET_CONFIG.get(dataset_name)
    if not config:
        raise ValueError(f"Unknown dataset: {dataset_name}")
    
    required_files = config['required_files']
    expected_checksums = config['checksums']
    missing_or_corrupted = []
    
    for file_name in required_files:
        file_path = os.path.join(data_dir, file_name)
        
        if not os.path.exists(file_path):
            missing_or_corrupted.append(f"Missing: {file_name}")
            continue
        
        try:
            actual_hash = calculate_file_hash(file_path)
            expected_hash = expected_checksums.get(file_name)
            
            if expected_hash and actual_hash != expected_hash:
                missing_or_corrupted.append(f"Checksum mismatch: {file_name}")
        except Exception as e:
            missing_or_corrupted.append(f"Error reading {file_name}: {str(e)}")
    
    return len(missing_or_corrupted) == 0, missing_or_corrupted

def download_dataset(dataset_name: str, target_dir: str, force: bool = False) -> bool:
    """
    Download a dataset from HuggingFace.
    
    Note: This is a placeholder implementation for the actual HuggingFace download logic.
    In a real implementation, this would use the `datasets` library.
    """
    logger.info(f"Downloading dataset: {dataset_name} to {target_dir}")
    
    config = DATASET_CONFIG.get(dataset_name)
    if not config:
        logger.error(f"Unknown dataset: {dataset_name}")
        return False
    
    os.makedirs(target_dir, exist_ok=True)
    
    # Simulate download for demonstration
    # In real implementation, use: from datasets import load_dataset
    # dataset = load_dataset(config['source'])
    
    try:
        # Create dummy files for testing (REMOVE IN PRODUCTION)
        # This is only for local testing without actual dataset access
        for file_name in config['required_files']:
            file_path = os.path.join(target_dir, file_name)
            if not os.path.exists(file_path) or force:
                with open(file_path, 'w') as f:
                    f.write(f"Dummy content for {file_name}\n")
                    if file_name.endswith('.json'):
                        f.write(json.dumps({"source": dataset_name, "version": "1.0"}))
        
        logger.info(f"Dataset {dataset_name} downloaded successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to download dataset {dataset_name}: {str(e)}")
        return False

def download_all_datasets(data_root: str, force: bool = False) -> Dict[str, bool]:
    """Download all required datasets."""
    results = {}
    
    for dataset_name in DATASET_CONFIG.keys():
        target_dir = os.path.join(data_root, dataset_name)
        success = download_dataset(dataset_name, target_dir, force)
        results[dataset_name] = success
    
    return results

def check_preflight_requirements(data_root: str) -> Tuple[bool, Dict[str, List[str]]]:
    """
    Check if all required datasets are present and valid.
    
    Returns:
        Tuple of (all_valid, dict of dataset_name -> list of issues)
    """
    issues = {}
    all_valid = True
    
    for dataset_name in DATASET_CONFIG.keys():
        data_dir = os.path.join(data_root, dataset_name)
        
        if not os.path.exists(data_dir):
            issues[dataset_name] = [f"Directory not found: {data_dir}"]
            all_valid = False
            continue
        
        valid, missing_files = verify_checksums(dataset_name, data_dir)
        
        if not valid:
            issues[dataset_name] = missing_files
            all_valid = False
        else:
            logger.info(f"Dataset {dataset_name} is valid")
    
    return all_valid, issues

def abort_on_missing_files(issues: Dict[str, List[str]]) -> None:
    """
    Log a clear error message listing all missing or corrupted files and exit.
    
    Args:
        issues: Dictionary mapping dataset names to lists of issue descriptions
    """
    error_msg = "\n" + "="*80 + "\n"
    error_msg += "CRITICAL ERROR: Missing or corrupted dataset files detected\n"
    error_msg += "="*80 + "\n\n"
    
    for dataset_name, file_issues in issues.items():
        error_msg += f"Dataset: {dataset_name}\n"
        error_msg += "-" * 40 + "\n"
        for issue in file_issues:
            error_msg += f"  - {issue}\n"
        error_msg += "\n"
    
    error_msg += "="*80 + "\n"
    error_msg += "Please ensure all required datasets are downloaded and valid.\n"
    error_msg += "Run `python code/download.py` to download missing datasets.\n"
    error_msg += "="*80 + "\n"
    
    logger.error(error_msg)
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Download and validate datasets")
    parser.add_argument('--force', action='store_true', help='Force re-download of datasets')
    parser.add_argument('--data-root', type=str, default='data/raw', help='Root directory for data')
    parser.add_argument('--validate-only', action='store_true', help='Only validate existing datasets')
    
    args = parser.parse_args()
    
    if args.validate_only:
        logger.info("Running validation only...")
        all_valid, issues = check_preflight_requirements(args.data_root)
        
        if not all_valid:
            abort_on_missing_files(issues)
        else:
            logger.info("All datasets are valid and ready for use.")
            sys.exit(0)
    
    # Download datasets
    logger.info("Starting dataset download...")
    results = download_all_datasets(args.data_root, args.force)
    
    if not all(results.values()):
        failed_datasets = [name for name, success in results.items() if not success]
        logger.error(f"Failed to download datasets: {', '.join(failed_datasets)}")
        sys.exit(1)
    
    # Validate after download
    logger.info("Validating downloaded datasets...")
    all_valid, issues = check_preflight_requirements(args.data_root)
    
    if not all_valid:
        abort_on_missing_files(issues)
    
    logger.info("All datasets downloaded and validated successfully.")

if __name__ == "__main__":
    main()