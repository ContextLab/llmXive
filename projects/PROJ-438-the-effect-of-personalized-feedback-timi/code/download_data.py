"""
Download OULAD dataset from verified HuggingFace mirrors.

This script fetches the Open University Learning Analysis Dataset (OULAD)
from the HuggingFace Hub (verified source) and saves the raw files to
the project's data/raw directory.

Files downloaded:
- students_data.csv: Student demographic and registration data
- train.parquet: Learning events, assessments, and forum interactions

Output:
- data/raw/students_data.csv
- data/raw/train.parquet
"""
import os
import sys
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Import logging utilities from existing project module
from logging_config import get_logger, info, warning, error, debug
from config import load_config, get_oulad_urls

# Try to import huggingface_hub; if not available, fall back to requests
try:
    from huggingface_hub import hf_hub_download, list_repo_files
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    import requests
    from requests.exceptions import RequestException

# Project root path (relative to this script's location)
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

logger = get_logger(__name__)


def download_from_hf(
    repo_id: str,
    filename: str,
    output_path: Path,
    repo_type: str = "dataset",
    max_retries: int = 3
) -> bool:
    """
    Download a file from HuggingFace Hub.
    
    Args:
        repo_id: HuggingFace repository ID (e.g., 'OpenUniversity/OU-AD')
        filename: Name of the file to download
        output_path: Local path to save the file
        repo_type: Type of repository ('dataset' or 'model')
        max_retries: Maximum number of retry attempts
        
    Returns:
        True if download successful, False otherwise
        
    Raises:
        RuntimeError: If download fails after all retries
    """
    if not HF_AVAILABLE:
        raise RuntimeError(
            "huggingface_hub is not installed. "
            "Install it with: pip install huggingface_hub"
        )

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Downloading {filename} from {repo_id} (attempt {attempt}/{max_retries})")
            local_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                repo_type=repo_type,
                cache_dir=str(PROJECT_ROOT / "data" / "cache"),
                force_download=True
            )
            
            # Copy from cache to final destination
            shutil.copy2(local_path, output_path)
            logger.info(f"Successfully downloaded {filename} to {output_path}")
            return True
            
        except Exception as e:
            logger.warning(f"Attempt {attempt} failed: {str(e)}")
            if attempt == max_retries:
                error(f"Failed to download {filename} after {max_retries} attempts: {str(e)}")
                raise RuntimeError(f"Download failed: {str(e)}")
            # Exponential backoff could be added here
            import time
            time.sleep(2 ** attempt)
    
    return False


def download_from_url(
    url: str,
    output_path: Path,
    max_retries: int = 3
) -> bool:
    """
    Download a file from a direct URL using requests.
    
    Args:
        url: Direct download URL
        output_path: Local path to save the file
        max_retries: Maximum number of retry attempts
        
    Returns:
        True if download successful, False otherwise
        
    Raises:
        RuntimeError: If download fails after all retries
    """
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Downloading from {url} (attempt {attempt}/{max_retries})")
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file in chunks
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"Successfully downloaded to {output_path}")
            return True
            
        except RequestException as e:
            logger.warning(f"Attempt {attempt} failed: {str(e)}")
            if attempt == max_retries:
                error(f"Failed to download from {url} after {max_retries} attempts: {str(e)}")
                raise RuntimeError(f"Download failed: {str(e)}")
            import time
            time.sleep(2 ** attempt)
    
    return False


def download_oulad_data() -> Dict[str, Path]:
    """
    Download OULAD dataset from verified HuggingFace mirrors.
    
    According to Plan.md FR-001, we need:
    - students_data.csv: Student demographics
    - train.parquet: Learning events and interactions
    
    Returns:
        Dictionary mapping file names to their local paths
        
    Raises:
        RuntimeError: If any required file fails to download
    """
    # Ensure raw data directory exists
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Data directory ready: {DATA_RAW_DIR}")
    
    # Get download URLs from config
    config = load_config()
    urls = get_oulad_urls(config)
    
    downloaded_files = {}
    required_files = {
        "students_data.csv": "students_data.csv",
        "train.parquet": "train.parquet"
    }
    
    # Determine which method to use
    use_hf = HF_AVAILABLE and "huggingface" in str(urls.get("students_data", ""))
    
    for local_name, remote_name in required_files.items():
        output_path = DATA_RAW_DIR / local_name
        
        # Skip if file already exists (user can force re-download if needed)
        if output_path.exists():
            logger.info(f"File already exists, skipping: {output_path}")
            downloaded_files[local_name] = output_path
            continue
        
        try:
            if use_hf:
                # Extract repo_id and filename from config
                repo_id = urls.get("repo_id", "OpenUniversity/OU-AD")
                success = download_from_hf(
                    repo_id=repo_id,
                    filename=remote_name,
                    output_path=output_path
                )
            else:
                # Fall back to direct URL
                url = urls.get(local_name)
                if not url:
                    raise RuntimeError(f"No URL configured for {local_name}")
                success = download_from_url(url, output_path)
            
            if success:
                downloaded_files[local_name] = output_path
                logger.info(f"✓ Downloaded {local_name}")
            else:
                raise RuntimeError(f"Download failed for {local_name}")
                
        except Exception as e:
            error(f"Failed to download {local_name}: {str(e)}")
            raise
    
    return downloaded_files


def generate_checksums(file_paths: Dict[str, Path]) -> Dict[str, str]:
    """
    Generate SHA256 checksums for downloaded files.
    
    Args:
        file_paths: Dictionary mapping file names to their paths
        
    Returns:
        Dictionary mapping file names to their checksums
    """
    from checksums import compute_sha256
    
    checksums = {}
    for name, path in file_paths.items():
        checksum = compute_sha256(path)
        checksums[name] = checksum
        logger.info(f"Checksum for {name}: {checksum}")
    
    return checksums


def main():
    """
    Main entry point for downloading OULAD data.
    
    This function:
    1. Loads configuration for download URLs
    2. Downloads students_data.csv and train.parquet
    3. Generates checksums for verification
    4. Logs success/failure
    """
    logger.info("=" * 60)
    logger.info("Starting OULAD data download (Task T016)")
    logger.info("=" * 60)
    
    try:
        # Download files
        downloaded = download_oulad_data()
        
        # Generate checksums
        checksums = generate_checksums(downloaded)
        
        # Summary
        logger.info("=" * 60)
        logger.info("Download Summary:")
        for name, path in downloaded.items():
            logger.info(f"  {name}: {path.name} ({path.stat().st_size / 1024 / 1024:.2f} MB)")
        logger.info("=" * 60)
        logger.info("✓ OULAD data download completed successfully")
        
        return 0
        
    except Exception as e:
        error(f"Download failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
