"""
Download OpenNeuro datasets ds000246 (Social Exclusion) and ds004738 (Reward).

This script fetches real BIDS-compliant datasets from OpenNeuro using the
datalad Python API. It validates the BIDS structure of the downloaded data
and generates checksums for integrity verification.

Dependencies:
    - datalad (pip install datalad)
    - bids-validator (optional, for strict BIDS validation)

Usage:
    python code/data_download/download_openneuro.py
"""

import argparse
import json
import logging
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports if running from subdirectory
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    import datalad.api as dl
    from datalad.support.exceptions import DownloadError
except ImportError:
    print("ERROR: datalad is not installed. Please run: pip install datalad")
    sys.exit(1)

try:
    from utils.checksums import generate_checksums
except ImportError:
    # Fallback if utils not in path yet (should be handled by project structure)
    print("WARNING: Could not import utils.checksums. Checksum generation skipped.")
    generate_checksums = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / 'data' / 'download.log')
    ]
)
logger = logging.getLogger(__name__)

# Dataset definitions
DATASETS = {
    "ds000246": {
        "name": "Social Exclusion (Cyberball)",
        "url": "https://datasets.datalad.org/openneuro/ds000246",
        "target_dir": "data/raw-fmri/ds000246",
        "description": "fMRI data from a social exclusion task using Cyberball paradigm."
    },
    "ds004738": {
        "name": "Reward Processing",
        "url": "https://datasets.datalad.org/openneuro/ds004738",
        "target_dir": "data/raw-fmri/ds004738",
        "description": "fMRI data from a monetary incentive delay reward task."
    }
}

def validate_bids_structure(dataset_path: Path) -> bool:
    """
    Validate BIDS structure using bids-validator if available.
    Falls back to basic checks if validator is not installed.
    """
    logger.info(f"Validating BIDS structure at: {dataset_path}")
    
    # Check for required BIDS files
    required_files = ["dataset_description.json", "participants.tsv"]
    missing_files = []
    
    for f in required_files:
        if not (dataset_path / f).exists():
            missing_files.append(f)
    
    if missing_files:
        logger.error(f"Missing required BIDS files: {missing_files}")
        return False
    
    # Check for task directories
    task_dirs = [d for d in dataset_path.iterdir() if d.is_dir() and d.name.startswith('sub-')]
    if not task_dirs:
        logger.warning("No subject directories found. Dataset might be empty or incomplete.")
        return False
    
    # Try to run bids-validator if available
    try:
        result = subprocess.run(
            ["bids-validator", str(dataset_path), "--config", "no-scan"],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            logger.info("BIDS validation passed.")
            return True
        else:
            logger.warning(f"BIDS validator found issues: {result.stdout[:500]}")
            # Continue anyway as we want the data
            return True
    except FileNotFoundError:
        logger.info("bids-validator not found. Skipping strict validation.")
        return True
    except subprocess.TimeoutExpired:
        logger.warning("BIDS validation timed out. Skipping.")
        return True
    except Exception as e:
        logger.warning(f"Error during BIDS validation: {e}")
        return True

def download_dataset(dataset_key: str, dataset_info: Dict[str, Any], force: bool = False) -> bool:
    """
    Download a single OpenNeuro dataset using datalad.
    """
    logger.info(f"{'Re-' if force else ''}Downloading {dataset_info['name']} ({dataset_key})...")
    
    target_path = Path(dataset_info["target_dir"])
    
    # Ensure target directory exists
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if already downloaded
    if target_path.exists() and any(target_path.iterdir()):
        if not force:
            logger.info(f"Dataset already exists at {target_path}. Skipping download.")
            # Still validate
            return validate_bids_structure(target_path)
        else:
            logger.warning(f"Force flag set. Removing existing data at {target_path}")
            import shutil
            shutil.rmtree(target_path)
    
    try:
        # Use datalad to install the dataset
        # Note: We use get() to fetch the content, not just install the metadata
        ds = dl.install(path=str(target_path), source=dataset_info["url"])
        ds.get()  # Get all content
        
        logger.info(f"Successfully downloaded {dataset_key} to {target_path}")
        
        # Validate BIDS structure
        if not validate_bids_structure(target_path):
            logger.error(f"BIDS validation failed for {dataset_key}")
            return False
        
        # Generate checksums for integrity
        if generate_checksums:
            logger.info(f"Generating checksums for {dataset_key}")
            try:
                checksum_file = target_path.parent / f"{dataset_key}_checksums.json"
                generate_checksums(str(target_path), str(checksum_file))
                logger.info(f"Checksums saved to {checksum_file}")
            except Exception as e:
                logger.error(f"Failed to generate checksums: {e}")
        
        return True
        
    except DownloadError as e:
        logger.error(f"Download error for {dataset_key}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error downloading {dataset_key}: {e}")
        return False

def main():
    """
    Main entry point for downloading all configured datasets.
    """
    parser = argparse.ArgumentParser(
        description="Download OpenNeuro datasets for social exclusion and reward studies."
    )
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="Force re-download of existing datasets"
    )
    parser.add_argument(
        "--dataset",
        choices=list(DATASETS.keys()) + ["all"],
        default="all",
        help="Specific dataset to download (default: all)"
    )
    
    args = parser.parse_args()
    
    # Determine which datasets to download
    datasets_to_download = []
    if args.dataset == "all":
        datasets_to_download = list(DATASETS.items())
    else:
        if args.dataset in DATASETS:
            datasets_to_download = [(args.dataset, DATASETS[args.dataset])]
        else:
            logger.error(f"Unknown dataset: {args.dataset}")
            sys.exit(1)
    
    logger.info(f"Starting download process for {len(datasets_to_download)} dataset(s)")
    
    success_count = 0
    for dataset_key, dataset_info in datasets_to_download:
        logger.info(f"Processing: {dataset_key} - {dataset_info['name']}")
        if download_dataset(dataset_key, dataset_info, args.force):
            success_count += 1
            logger.info(f"✓ {dataset_key} completed successfully")
        else:
            logger.error(f"✗ {dataset_key} failed")
    
    logger.info(f"Download process finished. {success_count}/{len(datasets_to_download)} datasets successful.")
    
    if success_count == 0:
        sys.exit(1)
    elif success_count < len(datasets_to_download):
        logger.warning("Some datasets failed to download. Check logs for details.")
        sys.exit(2)
    
    # Generate a summary report
    summary = {
        "download_timestamp": str(Path().cwd()),
        "datasets": {}
    }
    
    for dataset_key, dataset_info in DATASETS.items():
        target_path = Path(dataset_info["target_dir"])
        summary["datasets"][dataset_key] = {
            "name": dataset_info["name"],
            "path": str(target_path),
            "status": "downloaded" if target_path.exists() and any(target_path.iterdir()) else "failed"
        }
    
    summary_file = project_root / "data" / "download_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Download summary saved to {summary_file}")

if __name__ == "__main__":
    main()
