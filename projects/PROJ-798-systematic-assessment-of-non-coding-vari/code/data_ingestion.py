import json
import os
import hashlib
import logging
import gzip
import shutil
import ftplib
import urllib.request
import ssl
from pathlib import Path
from typing import Optional, List, Tuple

from config import ensure_data_dirs, DATA_RAW_DIR, DATA_DERIVED_DIR
from utils import calculate_file_checksum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# JASPAR 2024 CORE non-redundant URL (human)
JASPAR_URL = "https://jaspar.elixr.no/download/data/2024/CORE/JASPAR2024_CORE_non_redundant_pfms_jaspar.txt"
JASPAR_OUTPUT = DATA_RAW_DIR / "jaspar_pwm.txt"

def log_source_lineage(source_name: str, file_path: str, checksum: str, notes: str = ""):
    """Append source lineage info to data/raw/source_log.txt"""
    ensure_data_dirs()
    log_path = DATA_RAW_DIR / "source_log.txt"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{source_name}] {file_path} | SHA256: {checksum} | {notes}\n")
    logger.info(f"Logged source lineage: {source_name}")

def download_file_http(url: str, output_path: Path) -> str:
    """Download a file from HTTP/HTTPS and return its SHA256 checksum."""
    ensure_data_dirs()
    logger.info(f"Downloading from {url} to {output_path}")
    
    # Create a custom SSL context that doesn't verify certificates (for robustness in some envs)
    # In a production setting, one might want to use verify=True and a CA bundle.
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(url, context=ssl_context, timeout=60) as response:
            with open(output_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
        
        checksum = calculate_file_checksum(output_path)
        logger.info(f"Download complete. Checksum: {checksum}")
        return checksum
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        raise

def download_jaspar_pwms() -> str:
    """
    Download JASPAR CORE PWMs for human TFs.
    URL: https://jaspar.elixr.no/download/data/2024/CORE/JASPAR2024_CORE_non_redundant_pfms_jaspar.txt
    Saves to data/raw/jaspar_pwm.txt
    Returns the path to the downloaded file.
    """
    ensure_data_dirs()
    
    output_path = JASPAR_OUTPUT
    
    if not output_path.exists():
        try:
            checksum = download_file_http(JASPAR_URL, output_path)
            log_source_lineage(
                source_name="JASPAR_CORE_2024",
                file_path=str(output_path),
                checksum=checksum,
                notes="Downloaded non-redundant PWMs for human TFs"
            )
        except Exception as e:
            logger.error(f"Failed to download JASPAR PWMs: {e}")
            raise
    else:
        logger.info(f"JASPAR PWM file already exists at {output_path}. Skipping download.")
        checksum = calculate_file_checksum(output_path)
        log_source_lineage(
            source_name="JASPAR_CORE_2024_LOCAL",
            file_path=str(output_path),
            checksum=checksum,
            notes="File already present locally"
        )

    return str(output_path)

# Placeholder stubs for other functions mentioned in API surface to ensure importability
# These would be implemented in their respective tasks (T010, T010a, T011, T013, etc.)

def download_ftp_file(ftp_url: str, output_path: Path):
    raise NotImplementedError("Implementation for T010/T010a/T011")

def list_ftp_directory(ftp_path: str) -> List[str]:
    raise NotImplementedError("Implementation for T010")

def find_common_snps_file(directory_listing: List[str]) -> Optional[str]:
    raise NotImplementedError("Implementation for T010")

def download_dbSNP_common_snps() -> str:
    raise NotImplementedError("Implementation for T010")

def download_1000Genomes_snps() -> str:
    raise NotImplementedError("Implementation for T010a")

def download_regulatory_regions() -> str:
    raise NotImplementedError("Implementation for T011")

def load_snps_from_vcf(vcf_path: str) -> List:
    raise NotImplementedError("Implementation for T012/T013")

def load_regulatory_regions(bed_path: str) -> List:
    raise NotImplementedError("Implementation for T013")

def intersect_snps_with_regions(snps: List, regions: List) -> List:
    raise NotImplementedError("Implementation for T013")

def main():
    """Main entry point for data ingestion tasks."""
    logger.info("Starting data ingestion pipeline...")
    try:
        # T010: Download dbSNP (not implemented in this task)
        # snps_path = download_dbSNP_common_snps()
        
        # T010a: Download 1000 Genomes (not implemented in this task)
        # genomes_path = download_1000Genomes_snps()
        
        # T010b: Download JASPAR PWMs
        jaspar_path = download_jaspar_pwms()
        logger.info(f"JASPAR PWMs downloaded to: {jaspar_path}")
        
        # T011: Download regulatory regions (not implemented in this task)
        # reg_path = download_regulatory_regions()
        
        logger.info("Data ingestion phase complete.")
    except Exception as e:
        logger.error(f"Data ingestion failed: {e}")
        raise

if __name__ == "__main__":
    main()