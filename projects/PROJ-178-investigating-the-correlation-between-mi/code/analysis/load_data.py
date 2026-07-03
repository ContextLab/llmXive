"""
Data Acquisition Module for Mitochondrial Aging Correlation Study.

This module handles the download and initial validation of:
1. Mitochondrial VCF files from the 1000 Genomes Project FTP.
2. Sample metadata (including age, sex, population) from the 1000 Genomes metadata panel.

Outputs are written to code/data/raw/.
"""
import os
import sys
import gzip
import shutil
import logging
from pathlib import Path
import requests
from tqdm import tqdm

# Import environment configuration for paths and URLs
from config.environment import get_ftp_urls, get_local_paths, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_dirs(data_path: Path) -> None:
    """
    Ensure the raw data directory exists.
    """
    if not data_path.exists():
        logger.info(f"Creating raw data directory: {data_path}")
        data_path.mkdir(parents=True, exist_ok=True)

def download_mito_vcf(ftp_urls: dict, output_dir: Path, chunk_size: int = 8192) -> Path:
    """
    Download the mitochondrial VCF file (chrM) from the 1000 Genomes FTP.

    Args:
        ftp_urls: Dictionary containing 'mito_vcf' URL.
        output_dir: Directory to save the downloaded file.
        chunk_size: Chunk size for streaming download.

    Returns:
        Path to the downloaded .vcf.gz file.
    """
    url = ftp_urls.get('mito_vcf')
    if not url:
        raise ValueError("Mito VCF URL not found in environment configuration.")

    filename = "1000G_mito.vcf.gz"
    output_path = output_dir / filename

    if output_path.exists():
        logger.info(f"VCF file already exists at {output_path}. Skipping download.")
        return output_path

    logger.info(f"Downloading mitochondrial VCF from {url}...")
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            
            with open(output_path, 'wb') as f, tqdm(
                desc=filename,
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
            ) as pbar:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download VCF: {e}")
        if output_path.exists():
            output_path.unlink()
        raise e

    logger.info(f"Successfully downloaded VCF to {output_path}")
    return output_path

def download_metadata(ftp_urls: dict, output_dir: Path, chunk_size: int = 8192) -> Path:
    """
    Download the sample metadata panel from the 1000 Genomes FTP.

    Args:
        ftp_urls: Dictionary containing 'metadata' URL.
        output_dir: Directory to save the downloaded file.
        chunk_size: Chunk size for streaming download.

    Returns:
        Path to the downloaded metadata CSV file.
    """
    url = ftp_urls.get('metadata')
    if not url:
        raise ValueError("Metadata URL not found in environment configuration.")

    filename = "1000G_metadata.csv"
    output_path = output_dir / filename

    if output_path.exists():
        logger.info(f"Metadata file already exists at {output_path}. Skipping download.")
        return output_path

    logger.info(f"Downloading metadata panel from {url}...")
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            
            with open(output_path, 'wb') as f, tqdm(
                desc=filename,
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
            ) as pbar:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download metadata: {e}")
        if output_path.exists():
            output_path.unlink()
        raise e

    logger.info(f"Successfully downloaded metadata to {output_path}")
    return output_path

def validate_age_column(metadata_path: Path) -> bool:
    """
    Validate that the 'age' column exists in the metadata file.
    This is a critical gate for the analysis.

    Args:
        metadata_path: Path to the metadata CSV file.

    Returns:
        True if 'age' column exists, False otherwise.
    """
    import pandas as pd
    
    try:
        # Read only the header to check columns
        df = pd.read_csv(metadata_path, nrows=0)
        columns = df.columns.tolist()
        
        if 'age' not in columns:
            logger.error(f"CRITICAL: 'age' column missing in {metadata_path}. Available columns: {columns}")
            return False
        
        logger.info(f"Validation passed: 'age' column found in {metadata_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error validating metadata file: {e}")
        return False

def main():
    """
    Main entry point for data acquisition.
    Downloads VCF and metadata, then validates the age column.
    """
    # Get configuration
    urls = get_ftp_urls()
    paths = get_local_paths()
    
    raw_dir = paths['raw_data_dir']
    ensure_dirs(raw_dir)

    try:
        # 1. Download Mitochondrial VCF
        vcf_path = download_mito_vcf(urls, raw_dir)
        
        # 2. Download Metadata
        metadata_path = download_metadata(urls, raw_dir)
        
        # 3. Validate Age Column (Critical Gate)
        if not validate_age_column(metadata_path):
            logger.critical("Data Availability Gate Failed: Age column missing. Pipeline halted.")
            sys.exit(1)
        
        logger.info("Data acquisition and initial validation complete.")
        print(f"Artifacts ready: {vcf_path}, {metadata_path}")

    except Exception as e:
        logger.critical(f"Data acquisition failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()