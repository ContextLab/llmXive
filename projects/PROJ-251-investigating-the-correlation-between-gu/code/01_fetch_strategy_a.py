import os
import sys
import logging
import pandas as pd
import requests
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from utils.config import get_sra_accession, get_research_path, get_raw_path
from utils.logging_config import get_logger

logger = get_logger(__name__)

class DataUnavailableError(Exception):
    """Raised when real data cannot be fetched from any source."""
    pass

class ConfigurationError(Exception):
    """Raised when configuration is missing or invalid."""
    pass

def format_ftp_url(accession: str) -> str:
    """Construct the FTP URL for SRA study data."""
    return f"ftp://ftp-trace.ncbi.nlm.nih.gov/sra/sra-instant/reads/ByStudy/sra/SRP/{accession}/"

def check_ftp_availability(base_url: str) -> bool:
    """Check if the FTP URL is accessible by attempting a HEAD request."""
    try:
        # SRA FTP often doesn't support HEAD, so we try a GET with a small range or just check existence
        # We'll try to list the directory content by appending a dummy file or just checking the root
        # For simplicity, we'll try to fetch a known file pattern or just the root listing
        # Since we can't easily list FTP via requests, we'll try to fetch a small file if we know the pattern
        # Alternatively, we can try to connect to the FTP server directly
        import ftplib
        ftp = ftplib.FTP('ftp-trace.ncbi.nlm.nih.gov')
        ftp.login()
        # Try to change to the directory
        try:
            ftp.cwd(base_url.replace("ftp://ftp-trace.ncbi.nlm.nih.gov/", ""))
            ftp.quit()
            return True
        except ftplib.error_perm:
            ftp.quit()
            return False
    except Exception as e:
        logger.debug(f"FTP check failed for {base_url}: {e}")
        return False

def fetch_from_github_mirror(accession: str, output_dir: Path) -> Optional[Path]:
    """
    Attempt to fetch data from a known GitHub/GitLab mirror.
    This is a placeholder for specific mirror logic if a known mirror exists.
    For now, we'll check a generic pattern or return None if no specific mirror is configured.
    """
    # In a real scenario, we would have a list of known mirrors or read from study metadata.
    # Since T010 (SRA Search) should have identified a specific study, we might have a mirror URL.
    # For this implementation, we will not hardcode a mirror but log that we are checking.
    logger.info(f"Checking for GitHub/GitLab mirror for {accession}...")
    # Placeholder: In a real implementation, we would iterate through known mirrors.
    # For now, we return None to indicate no mirror was found (or not implemented yet).
    return None

def download_file(url: str, dest_path: Path) -> Path:
    """Download a file from a URL to a destination path."""
    logger.info(f"Downloading {url} to {dest_path}")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return dest_path
    except requests.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        raise

def validate_downloaded_files(otutable_path: Path, serology_path: Path) -> bool:
    """Validate that downloaded files are non-empty and have expected structure."""
    if not otutable_path.exists() or otutable_path.stat().st_size == 0:
        logger.error(f"OTU table file is missing or empty: {otutable_path}")
        return False
    if not serology_path.exists() or serology_path.stat().st_size == 0:
        logger.error(f"Serology file is missing or empty: {serology_path}")
        return False

    try:
        otu_df = pd.read_csv(otutable_path)
        sero_df = pd.read_csv(serology_path)

        # Basic validation: check for required columns
        # We expect subject_id in both
        if 'subject_id' not in otu_df.columns or 'subject_id' not in sero_df.columns:
            logger.error("Missing 'subject_id' column in one or both files.")
            return False

        # For OTU table, we expect at least one taxon column besides subject_id
        taxon_cols = [c for c in otu_df.columns if c != 'subject_id']
        if not taxon_cols:
            logger.error("No taxon columns found in OTU table.")
            return False

        # For serology, we expect titer_baseline and titer_post
        if 'titer_baseline' not in sero_df.columns or 'titer_post' not in sero_df.columns:
            logger.error("Missing titer columns in serology file.")
            return False

        logger.info("Downloaded files validated successfully.")
        return True
    except Exception as e:
        logger.error(f"Error validating downloaded files: {e}")
        return False

def write_sra_status(accession: Optional[str], status: str, use_synthetic: bool, research_path: Path) -> None:
    """Write the SRA status JSON file."""
    status_data = {
        "status": status,
        "use_synthetic": use_synthetic
    }
    if accession:
        status_data["accession"] = accession

    status_file = research_path / "sra_status.json"
    with open(status_file, 'w') as f:
        import json
        json.dump(status_data, f, indent=2)
    logger.info(f"Wrote SRA status to {status_file}")

def fetch_strategy_a(accession: str, raw_path: Path, research_path: Path) -> Tuple[Path, Path]:
    """
    Strategy A: Fetch pre-processed OTU table and serology metadata.
    Tries FTP first, then mirrors, then fails loudly.
    """
    otutable_path = raw_path / "otutable.csv"
    serology_path = raw_path / "serology.csv"

    # 1. Attempt direct FTP URL construction
    ftp_base = format_ftp_url(accession)
    logger.info(f"Attempting FTP fetch from {ftp_base}")

    # We need to find the actual CSV files. SRA often provides metadata or processed files in subdirectories.
    # For this task, we assume the processed files are directly available or in a known pattern.
    # Since SRA FTP structure can vary, we might need to search for files.
    # However, the task says "pre-processed OTU table", so we assume they are available as CSVs.
    # We'll try common patterns.
    possible_otu_files = [
        f"{ftp_base}otu_table.csv",
        f"{ftp_base}processed_otu_table.csv",
        f"{ftp_base}data/otu_table.csv",
        f"{ftp_base}otu_table.tsv",
    ]
    possible_sero_files = [
        f"{ftp_base}serology.csv",
        f"{ftp_base}serology_metadata.csv",
        f"{ftp_base}data/serology.csv",
        f"{ftp_base}serology.tsv",
    ]

    found_otu = None
    found_sero = None

    # Try to find OTU file
    for url in possible_otu_files:
        if check_ftp_availability(url.rsplit('/', 1)[0] + '/'):
            try:
                download_file(url, otutable_path)
                found_otu = otutable_path
                break
            except Exception:
                continue

    # Try to find Serology file
    for url in possible_sero_files:
        if check_ftp_availability(url.rsplit('/', 1)[0] + '/'):
            try:
                download_file(url, serology_path)
                found_sero = serology_path
                break
            except Exception:
                continue

    if found_otu and found_sero:
        if validate_downloaded_files(found_otu, found_sero):
            logger.info("Strategy A (FTP) succeeded.")
            write_sra_status(accession, "real_data_found", False, research_path)
            return found_otu, found_sero

    # 2. If FTP failed, attempt sratoolkit prefetch (if available)
    logger.info("FTP failed. Attempting sratoolkit prefetch...")
    try:
        import subprocess
        # Prefetch the study
        subprocess.run(['prefetch', accession], check=True, timeout=300)
        # Then convert to CSV using fasterq-dump or similar
        # This is complex and might require specific SRA tool versions.
        # For now, we'll skip this if not easily available and go to mirrors.
        logger.warning("sratoolkit prefetch not fully implemented or failed.")
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.info("sratoolkit not available or failed.")

    # 3. Attempt to fetch from a known GitHub/GitLab mirror
    logger.info("Attempting to fetch from GitHub/GitLab mirror...")
    # We don't have a specific mirror URL yet, so we return None for now.
    # In a real scenario, this would be populated from T010 results.
    mirror_result = fetch_from_github_mirror(accession, raw_path)
    if mirror_result:
        # Assume mirror_result is a tuple of (otu_path, sero_path) or similar
        # For simplicity, let's assume it returns the paths
        # We'll need to adapt based on actual mirror structure
        pass

    # If all methods fail, raise DataUnavailableError
    write_sra_status(accession, "no_real_data", True, research_path)
    raise DataUnavailableError(f"Failed to fetch data for accession {accession} from all sources.")

def main():
    """Main entry point for Strategy A."""
    logger.info("Starting Strategy A: Fetch pre-processed OTU table and serology metadata.")
    accession = get_sra_accession()
    if not accession:
        raise ConfigurationError("SRA_ACCESSION is not set in config. Please run T010 first.")

    raw_path = get_raw_path()
    research_path = get_research_path()

    try:
        otutable_path, serology_path = fetch_strategy_a(accession, raw_path, research_path)
        logger.info(f"Successfully fetched data. OTU table: {otutable_path}, Serology: {serology_path}")
    except DataUnavailableError as e:
        logger.error(f"Data unavailable: {e}")
        # If synthetic is allowed, we might proceed, but this task is Strategy A only.
        # The calling script (main pipeline) should handle the fallback to Strategy B.
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error in Strategy A: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
