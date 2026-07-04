"""
Download OULAD dataset from the Open University Learning Analytics Dataset repository.

This script fetches the raw dataset from the official source and saves it to
the data/raw/ directory. It also generates checksums for data integrity verification.

FR-001: Download OULAD data from https://analyse.kmi.open.ac.uk/open_dataset
"""
import os
import sys
import tarfile
import tempfile
import shutil
from pathlib import Path
from urllib.request import urlretrieve
from urllib.error import URLError, HTTPError

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import load_config, get_config_value
from logging_config import setup_logger, get_logger, info, error, warning, debug
from checksums import compute_sha256, save_checksums
from schema import load_schema_from_file, assert_valid_schema


# Constants
OULAD_URL = "https://analyse.kmi.open.ac.uk/open_dataset/OULAD.zip"
DATASET_NAME = "OULAD"

def download_oulad_data(output_dir: Path, logger=None) -> bool:
    """
    Download the OULAD dataset from the official source.
    
    Args:
        output_dir: Directory to save the downloaded data
        logger: Logger instance for logging progress
        
    Returns:
        True if download was successful, False otherwise
    """
    if logger is None:
        logger = get_logger(__name__)
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    zip_path = output_dir / "OULAD.zip"
    extracted_dir = output_dir / "OULAD"
    
    # Check if already downloaded
    if extracted_dir.exists() and any(extracted_dir.iterdir()):
        info(logger, f"Dataset already exists at {extracted_dir}. Skipping download.")
        return True
    
    info(logger, f"Downloading OULAD dataset from {OULAD_URL}")
    info(logger, f"Saving to {zip_path}")
    
    try:
        # Download the file
        urlretrieve(OULAD_URL, zip_path)
        info(logger, "Download completed successfully.")
    except HTTPError as e:
        error(logger, f"HTTP error while downloading: {e.code} {e.reason}")
        if zip_path.exists():
            zip_path.unlink()
        return False
    except URLError as e:
        error(logger, f"URL error while downloading: {e.reason}")
        if zip_path.exists():
            zip_path.unlink()
        return False
    except Exception as e:
        error(logger, f"Unexpected error while downloading: {str(e)}")
        if zip_path.exists():
            zip_path.unlink()
        return False
    
    # Extract the zip file
    info(logger, f"Extracting dataset to {extracted_dir}")
    try:
        with tarfile.open(zip_path, 'r:*') as tar_ref:
            # Extract to a temporary directory first to handle nested structure
            with tempfile.TemporaryDirectory() as tmp_dir:
                tar_ref.extractall(tmp_dir)
                
                # Find the actual content directory (might be nested)
                tmp_path = Path(tmp_dir)
                content_dirs = [d for d in tmp_path.iterdir() if d.is_dir()]
                
                if not content_dirs:
                    # If no directories, maybe it's just files
                    for f in tmp_path.iterdir():
                        if f.is_file() and f.name != "OULAD.zip":
                            shutil.move(str(f), str(extracted_dir / f.name))
                else:
                    # Move contents from the first directory to extracted_dir
                    source_dir = content_dirs[0]
                    if source_dir.name != "OULAD":
                        # Rename if needed
                        target_dir = extracted_dir
                        target_dir.mkdir(parents=True, exist_ok=True)
                        for item in source_dir.iterdir():
                            shutil.move(str(item), str(target_dir / item.name))
                    else:
                        # Move contents
                        extracted_dir.mkdir(parents=True, exist_ok=True)
                        for item in source_dir.iterdir():
                            shutil.move(str(item), str(extracted_dir / item.name))
                
        info(logger, "Extraction completed successfully.")
    except Exception as e:
        error(logger, f"Error during extraction: {str(e)}")
        if extracted_dir.exists():
            shutil.rmtree(extracted_dir)
        if zip_path.exists():
            zip_path.unlink()
        return False
    
    # Clean up zip file
    if zip_path.exists():
        zip_path.unlink()
        info(logger, "Cleaned up temporary zip file.")
    
    # Verify extraction
    if not extracted_dir.exists() or not any(extracted_dir.iterdir()):
        error(logger, "Extraction failed: No files found in destination directory.")
        return False
    
    info(logger, f"Dataset successfully downloaded and extracted to {extracted_dir}")
    return True


def generate_checksums(data_dir: Path, logger=None) -> bool:
    """
    Generate checksums for all files in the downloaded dataset.
    
    Args:
        data_dir: Directory containing the dataset
        logger: Logger instance
        
    Returns:
        True if checksums were generated successfully
    """
    if logger is None:
        logger = get_logger(__name__)
    
    info(logger, f"Generating checksums for dataset in {data_dir}")
    
    try:
        checksums = compute_checksums_for_directory(data_dir)
        
        # Save checksums
        checksum_file = data_dir.parent / "checksums" / "oulad_raw.json"
        checksum_file.parent.mkdir(parents=True, exist_ok=True)
        save_checksums(checksums, str(checksum_file))
        
        info(logger, f"Checksums saved to {checksum_file}")
        return True
    except Exception as e:
        error(logger, f"Error generating checksums: {str(e)}")
        return False


def main():
    """Main entry point for the download script."""
    # Initialize logger
    logger = setup_logger(__name__)
    info(logger, "Starting OULAD dataset download process.")
    
    # Load configuration
    try:
        config = load_config()
        raw_data_dir = Path(config.get('paths', {}).get('raw_data', 'data/raw'))
    except Exception as e:
        error(logger, f"Failed to load configuration: {str(e)}")
        sys.exit(1)
    
    # Resolve to absolute path relative to project root
    project_root = Path(__file__).parent.parent
    raw_data_dir = project_root / raw_data_dir
    
    # Download dataset
    success = download_oulad_data(raw_data_dir, logger)
    if not success:
        error(logger, "Failed to download OULAD dataset.")
        sys.exit(1)
    
    # Generate checksums
    if not generate_checksums(raw_data_dir, logger):
        warning(logger, "Failed to generate checksums, but dataset was downloaded.")
    
    info(logger, "OULAD dataset download process completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
