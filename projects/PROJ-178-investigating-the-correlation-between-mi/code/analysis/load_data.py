import os
import sys
import gzip
import shutil
import logging
from pathlib import Path
import requests
from tqdm import tqdm
import pandas as pd
from urllib.parse import urlparse

# Ensure we can import from the project root if running as a script
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from config.environment import get_ftp_urls, ensure_directories

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_dirs():
    """Ensure raw data directories exist."""
    dirs = ensure_directories()
    raw_dir = dirs.get('raw')
    if raw_dir and not raw_dir.exists():
        raw_dir.mkdir(parents=True, exist_ok=True)
    return raw_dir

def download_mito_vcf(output_dir: Path):
    """
    Download mitochondrial VCF from 1000 Genomes FTP.
    
    The 1000 Genomes Phase 3 data is hosted on FTP. We target the 
    specific chrM VCF file. Note: 1000 Genomes data is often split
    by chromosome and population. We fetch the combined chrM VCF if available,
    or a representative one.
    
    Source: ftp://ftp.1000genomes.ebi.ac.uk/vol1/ftp/phase3/
    """
    urls = get_ftp_urls()
    # Using the specific chrM VCF path for Phase 3
    # Note: Direct FTP downloads in Python often require 'ftputil' or 'wget'. 
    # Here we use requests with a fallback or a direct HTTP mirror if available.
    # The 1000 Genomes FTP is often accessible via http too for specific files.
    
    # Standard Phase 3 chrM VCF location
    base_url = "ftp://ftp.1000genomes.ebi.ac.uk/vol1/ftp/phase3/20130502.release/"
    # The actual file is usually split. We will try to fetch the master chrM VCF 
    # or the index if the full file is too large to stream directly without special FTP libs.
    # For robustness in this script, we attempt to fetch the specific chrM VCF from the 
    # release folder. If the exact file structure varies, we might need to download 
    # per-population and merge, but the task asks for "the" VCF.
    # Let's try the consolidated chrM file if it exists in the release, otherwise 
    # we might need to download a subset. 
    # Actually, 1000G Phase 3 VCFs are usually per-chromosome. 
    # File: ALL.chrM.phase3_integrated.vcf.gz
    
    filename = "ALL.chrM.phase3_integrated.vcf.gz"
    url = f"{base_url}{filename}"
    
    local_path = output_dir / filename
    
    if local_path.exists():
        logger.info(f"File {local_path} already exists. Skipping download.")
        return local_path

    logger.info(f"Downloading {filename} from {url}...")
    
    try:
        # Using wget via subprocess is often more reliable for FTP than requests
        # but to keep dependencies minimal (only requests/tqdm), we try requests first.
        # requests does not support FTP directly in newer versions without extra handlers,
        # so we will assume an HTTP mirror or use a generic download helper.
        # However, 1000 Genomes FTP is accessible via http for many files.
        http_url = url.replace("ftp://", "http://")
        
        response = requests.get(http_url, stream=True, timeout=120)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(local_path, 'wb') as f, tqdm(
            desc=filename,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
                    
        logger.info(f"Downloaded {local_path}")
        return local_path
        
    except Exception as e:
        logger.error(f"Failed to download VCF: {e}")
        raise RuntimeError(f"Could not download mitochondrial VCF. {e}")

def download_metadata(output_dir: Path):
    """
    Download the 1000 Genomes metadata panel containing age, sex, population, etc.
    
    The metadata is typically available as a TSV or CSV file on the FTP site.
    We target the 'Sample Information' file which contains phenotypic data.
    """
    # The metadata file for 1000 Genomes Phase 3
    # URL: ftp://ftp.1000genomes.ebi.ac.uk/vol1/ftp/phase3/20130502.release/integrated_call_samples_v3.20130502.ALL.panel
    # This file contains population, super_population, etc.
    # Age data is NOT in the standard 1000 Genomes panel (they are anonymous).
    # However, the task specification implies age data exists or must be derived.
    # In many research contexts using 1000G for aging, they use a specific subset 
    # or a derived dataset where age is imputed or available from a linked study.
    # Since the task requires "real data" and "age column", we must fetch the 
    # canonical panel first. If age is missing, the pipeline halts (T007A).
    # We will download the standard panel file.
    
    base_url = "ftp://ftp.1000genomes.ebi.ac.uk/vol1/ftp/phase3/20130502.release/"
    filename = "integrated_call_samples_v3.20130502.ALL.panel"
    url = f"{base_url}{filename}"
    
    local_path = output_dir / filename
    
    if local_path.exists():
        logger.info(f"Metadata file {local_path} already exists. Skipping download.")
        return local_path

    logger.info(f"Downloading metadata {filename}...")
    
    try:
        http_url = url.replace("ftp://", "http://")
        response = requests.get(http_url, stream=True, timeout=120)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(local_path, 'wb') as f, tqdm(
            desc=filename,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
                    
        logger.info(f"Downloaded {local_path}")
        return local_path
        
    except Exception as e:
        logger.error(f"Failed to download metadata: {e}")
        raise RuntimeError(f"Could not download metadata panel. {e}")

def validate_age_column(metadata_path: Path):
    """
    Check if the 'age' column exists in the metadata.
    If not, log error and raise a critical error to halt the pipeline.
    """
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found at {metadata_path}")
        
    # The standard 1000G panel does NOT have an 'age' column.
    # It has: sample_id, population, super_population, etc.
    # If the project spec assumes age is present, we must check.
    # If it's missing, we halt as per T007A.
    
    try:
        df = pd.read_csv(metadata_path, sep='\t')
    except Exception as e:
        # Try comma if tab fails
        try:
            df = pd.read_csv(metadata_path, sep=',')
        except Exception as e2:
            raise ValueError(f"Could not parse metadata file: {e2}")
    
    columns = df.columns.tolist()
    logger.info(f"Metadata columns: {columns}")
    
    if 'age' not in columns:
        logger.error("CRITICAL: 'age' column is missing from the metadata panel.")
        logger.error("The pipeline cannot proceed without age data for correlation analysis.")
        # We do not return a value here, we raise an exception to halt execution
        raise RuntimeError("Pipeline HALTED: 'age' column missing from metadata.")
    
    logger.info("Age column found. Validation passed.")
    return df

def main():
    """
    Main entry point for data acquisition.
    Downloads VCF and Metadata, validates age column.
    """
    ensure_directories()
    raw_dir = ensure_dirs()
    
    logger.info("Starting data acquisition phase...")
    
    try:
        vcf_path = download_mito_vcf(raw_dir)
        meta_path = download_metadata(raw_dir)
        
        # Validate age column immediately
        validate_age_column(meta_path)
        
        logger.info("Data acquisition and initial validation complete.")
        print(f"VCF downloaded to: {vcf_path}")
        print(f"Metadata downloaded to: {meta_path}")
        
    except RuntimeError as e:
        logger.critical(str(e))
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error during data acquisition: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
