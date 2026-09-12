"""
Download data script with strict verified source check.

This script implements a strict "Verified Source" check before any network call.
It queries verified_sources_hypothetical.json or verified_sources.json.
If no verified source is found and the dataset is not marked as 'hypothetical',
the script halts with an error.
"""
import os
import sys
import hashlib
import logging
import argparse
import json
from pathlib import Path
from urllib.request import urlretrieve
from urllib.error import URLError, HTTPError
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_config, get_data_path, get_random_seed
from logging_config import setup_logging

def setup_logger(name):
    """Set up a logger for this module."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger = setup_logging(name)
    return logger

def calculate_sha256(filepath):
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_verified_sources():
    """Load verified sources from JSON files."""
    sources = []
    project_root = Path(__file__).parent
    
    # Check for hypothetical sources first
    hypothetical_path = project_root / "verified_sources_hypothetical.json"
    if hypothetical_path.exists():
        try:
            with open(hypothetical_path, 'r') as f:
                data = json.load(f)
                sources.extend(data.get('sources', []))
        except Exception as e:
            logger = logging.getLogger('download_data')
            logger.warning(f"Could not load hypothetical sources: {e}")
    
    # Check for verified sources
    verified_path = project_root / "verified_sources.json"
    if verified_path.exists():
        try:
            with open(verified_path, 'r') as f:
                data = json.load(f)
                sources.extend(data.get('sources', []))
        except Exception as e:
            logger = logging.getLogger('download_data')
            logger.warning(f"Could not load verified sources: {e}")
    
    return sources

def verify_manifest(dataset_id, logger):
    """Verify the dataset manifest exists and contains required fields."""
    # For hypothetical mode, we skip actual manifest verification
    # In real mode, this would check the BIDS manifest
    logger.info(f"Manifest verification skipped for hypothetical dataset: {dataset_id}")
    return True

def check_disk_space(required_gb, logger):
    """Check if there is enough disk space."""
    data_path = Path(get_data_path())
    if not data_path.exists():
        data_path.mkdir(parents=True, exist_ok=True)
    
    total, used, free = shutil.disk_usage(data_path)
    free_gb = free / (2**30)
    
    if free_gb < required_gb:
        logger.error(f"Insufficient disk space. Required: {required_gb}GB, Available: {free_gb:.2f}GB")
        raise RuntimeError(f"Insufficient disk space. Required: {required_gb}GB, Available: {free_gb:.2f}GB")
    
    logger.info(f"Disk space check passed. Available: {free_gb:.2f}GB")
    return True

def download_dataset(dataset_id, output_path, logger):
    """
    Download the dataset.
    
    In hypothetical mode, this creates a mock dataset structure.
    In real mode, this would download from the verified source.
    """
    sources = load_verified_sources()
    source_info = next((s for s in sources if s['id'] == dataset_id), None)
    
    if not source_info:
        logger.error(f"No verified source found for dataset: {dataset_id}")
        raise RuntimeError(f"No verified source found for dataset: {dataset_id}")
    
    if source_info.get('status') == 'hypothetical':
        logger.warning("Hypothetical mode enabled. Creating mock dataset structure.")
        
        # Create mock directory structure
        mock_path = Path(output_path) / dataset_id
        mock_path.mkdir(parents=True, exist_ok=True)
        
        # Create minimal BIDS structure
        (mock_path / "dataset_description.json").write_text(json.dumps({
            "Name": "Mock Visual Attention Dataset",
            "BIDSVersion": "1.8.0",
            "DatasetType": "raw"
        }, indent=2))
        
        (mock_path / "participants.tsv").write_text("participant_id\tage\tsex\nsub-01\t25\tM\nsub-02\t30\tF\n")
        
        # Create a minimal events file
        tasks_path = mock_path / "sub-01" / "func"
        tasks_path.mkdir(parents=True, exist_ok=True)
        (tasks_path / "sub-01_task-rsvp_events.tsv").write_text(
            "onset\tduration\ttrial_type\tstimulus_id\tvalence\n0\t1000\trsvp\timg_001\tpositive\n1000\t1000\trsvp\timg_002\tnegative\n"
        )
        
        logger.info(f"Mock dataset created at: {mock_path}")
        return True
    
    # Real download logic would go here
    # For now, we assume hypothetical mode is always used for this project
    logger.error(f"Real download not implemented for dataset: {dataset_id}")
    raise RuntimeError(f"Real download not implemented for dataset: {dataset_id}")

def main():
    """Main entry point for the download script."""
    parser = argparse.ArgumentParser(description='Download dataset for visual attention study')
    parser.add_argument('--dataset-id', default='ds001435', help='Dataset ID to download')
    parser.add_argument('--output-dir', default=None, help='Output directory for dataset')
    args = parser.parse_args()
    
    # Set up logging
    logger = setup_logger('download_data')
    logger.info(f"Starting download for dataset: {args.dataset_id}")
    
    try:
        # Check verified sources first
        sources = load_verified_sources()
        source_info = next((s for s in sources if s['id'] == args.dataset_id), None)
        
        if not source_info:
            logger.error(f"No verified source found for dataset: {args.dataset_id}")
            logger.error("ERROR: No verified source found for ds001435")
            raise RuntimeError(f"No verified source found for dataset: {args.dataset_id}")
        
        # Check if hypothetical mode
        if source_info.get('status') == 'hypothetical':
            logger.warning("WARNING: Hypothetical mode enabled")
        
        # Determine output path
        if args.output_dir:
            output_path = Path(args.output_dir)
        else:
            output_path = Path(get_data_path()) / 'raw'
        
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Check disk space (estimate 1GB for mock, more for real)
        check_disk_space(1, logger)
        
        # Verify manifest (skipped for hypothetical)
        if source_info.get('status') != 'hypothetical':
            verify_manifest(args.dataset_id, logger)
        
        # Download dataset
        download_dataset(args.dataset_id, output_path, logger)
        
        logger.info(f"Dataset download completed successfully for: {args.dataset_id}")
        
    except Exception as e:
        logger.error(f"Fatal error during download: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()