import os
import logging
import requests
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple

from utils.logging_config import get_logger
from utils.config import get_sra_accession, get_research_path

logger = get_logger(__name__)

class DataUnavailableError(Exception):
    """Raised when real data cannot be fetched from the source."""
    pass

def fetch_otu_table(accession: str, output_path: Path) -> None:
    """
    Fetch pre-processed OTU table for the given SRP accession.
    
    Strategy:
    1. Check if a pre-processed CSV exists in a known GitHub mirror for this study
       (common for SRA studies that publish analysis code).
    2. If not, attempt to construct a standard SRA FTP path.
    3. If that fails, raise DataUnavailableError.
    
    Note: Since SRA raw data is FASTQ, we rely on the study authors having
    published a processed OTU table (CSV/BIOM) in their repository or as a
    supplementary file. This function attempts to find that.
    """
    logger.info(f"Attempting to fetch OTU table for accession {accession}")
    
    # Strategy 1: Check common GitHub mirrors for processed data
    # Many microbiome studies host processed tables in GitHub repos
    github_patterns = [
        f"https://raw.githubusercontent.com/{accession.lower()}/main/otutable.csv",
        f"https://raw.githubusercontent.com/{accession.lower()}/master/otutable.csv",
        f"https://raw.githubusercontent.com/microbiome/{accession.lower()}/main/otutable.csv",
    ]
    
    for url in github_patterns:
        try:
            logger.debug(f"Trying GitHub URL: {url}")
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                df = pd.read_csv(pd.io.common.BytesIO(response.content))
                # Validate basic structure
                if 'subject_id' in df.columns:
                    df.to_csv(output_path, index=False)
                    logger.info(f"Successfully fetched OTU table from {url}")
                    return
        except Exception as e:
            logger.debug(f"Failed to fetch from {url}: {e}")
            continue
    
    # Strategy 2: Try NCBI SRA FTP for processed files (rare, but possible)
    # Standard SRA FTP structure usually contains raw data, but some studies
    # include processed tables in supplementary directories
    ftp_base = f"ftp://ftp-trace.ncbi.nlm.nih.gov/sra/sra-instant/reads/ByStudy/sra/SRP/{accession}"
    
    # We can't easily parse FTP without FTP libraries, so we try a direct download
    # of a likely file name if it exists
    likely_files = [
        f"{ftp_base}/processed_otu_table.csv",
        f"{ftp_base}/otu_table.csv",
        f"{ftp_base}/supplementary/otutable.csv",
    ]
    
    for url in likely_files:
        try:
            logger.debug(f"Trying FTP URL: {url}")
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                df = pd.read_csv(pd.io.common.BytesIO(response.content))
                if 'subject_id' in df.columns:
                    df.to_csv(output_path, index=False)
                    logger.info(f"Successfully fetched OTU table from {url}")
                    return
        except Exception as e:
            logger.debug(f"Failed to fetch from {url}: {e}")
            continue
    
    # If we get here, no real data was found
    raise DataUnavailableError(
        f"Could not fetch pre-processed OTU table for accession {accession}. "
        "No real data source found. Please verify the accession or check if "
        "the study has published processed data elsewhere."
    )

def fetch_serology_metadata(accession: str, output_path: Path) -> None:
    """
    Fetch serology metadata (titers) for the given SRP accession.
    
    Similar strategy to fetch_otu_table: look for published CSV files
    in GitHub repos or supplementary directories.
    """
    logger.info(f"Attempting to fetch serology metadata for accession {accession}")
    
    # Strategy 1: Check common GitHub mirrors
    github_patterns = [
        f"https://raw.githubusercontent.com/{accession.lower()}/main/serology.csv",
        f"https://raw.githubusercontent.com/{accession.lower()}/master/serology.csv",
        f"https://raw.githubusercontent.com/microbiome/{accession.lower()}/main/serology.csv",
    ]
    
    for url in github_patterns:
        try:
            logger.debug(f"Trying GitHub URL: {url}")
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                df = pd.read_csv(pd.io.common.BytesIO(response.content))
                # Validate basic structure
                if 'subject_id' in df.columns and ('titer_baseline' in df.columns or 'titer_pre' in df.columns):
                    df.to_csv(output_path, index=False)
                    logger.info(f"Successfully fetched serology metadata from {url}")
                    return
        except Exception as e:
            logger.debug(f"Failed to fetch from {url}: {e}")
            continue
    
    # Strategy 2: Try NCBI SRA FTP
    ftp_base = f"ftp://ftp-trace.ncbi.nlm.nih.gov/sra/sra-instant/reads/ByStudy/sra/SRP/{accession}"
    
    likely_files = [
        f"{ftp_base}/serology.csv",
        f"{ftp_base}/serology_metadata.csv",
        f"{ftp_base}/supplementary/serology.csv",
    ]
    
    for url in likely_files:
        try:
            logger.debug(f"Trying FTP URL: {url}")
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                df = pd.read_csv(pd.io.common.BytesIO(response.content))
                if 'subject_id' in df.columns:
                    df.to_csv(output_path, index=False)
                    logger.info(f"Successfully fetched serology metadata from {url}")
                    return
        except Exception as e:
            logger.debug(f"Failed to fetch from {url}: {e}")
            continue
    
    raise DataUnavailableError(
        f"Could not fetch serology metadata for accession {accession}. "
        "No real data source found."
    )

def write_sra_status(status: str, use_synthetic: bool, accession: Optional[str] = None) -> None:
    """
    Write the SRA status JSON file to data/research/sra_status.json
    """
    research_path = get_research_path()
    research_path.mkdir(parents=True, exist_ok=True)
    
    status_file = research_path / "sra_status.json"
    status_data = {
        "status": status,
        "use_synthetic": use_synthetic
    }
    if accession:
        status_data["accession"] = accession
        
    with open(status_file, 'w') as f:
        import json
        json.dump(status_data, f, indent=2)
    
    logger.info(f"Wrote SRA status to {status_file}: {status_data}")

def fetch_strategy_a_data() -> Tuple[Path, Path]:
    """
    Main entry point for Strategy A: Fetch pre-processed OTU table and serology metadata.
    
    Returns:
        Tuple of (otutable_path, serology_path)
        
    Raises:
        DataUnavailableError: If real data cannot be fetched
    """
    accession = get_sra_accession()
    if not accession:
        raise DataUnavailableError("SRA_ACCESSION is not set in config. Cannot fetch data.")
    
    logger.info(f"Starting Strategy A fetch for accession: {accession}")
    
    raw_path = Path("data/raw")
    raw_path.mkdir(parents=True, exist_ok=True)
    
    otu_path = raw_path / "otutable.csv"
    serology_path = raw_path / "serology.csv"
    
    try:
        fetch_otu_table(accession, otu_path)
        fetch_serology_metadata(accession, serology_path)
        
        write_sra_status("real_data_found", False, accession)
        logger.info("Successfully fetched all real data for Strategy A")
        
        return otu_path, serology_path
        
    except DataUnavailableError as e:
        logger.error(f"Real data fetch failed: {e}")
        write_sra_status("fetch_failed", True, accession)
        raise
    except Exception as e:
        logger.error(f"Unexpected error during fetch: {e}")
        write_sra_status("fetch_failed", True, accession)
        raise DataUnavailableError(f"Failed to fetch data: {e}")

def main():
    """
    CLI entry point for Strategy A data fetch.
    """
    logging.basicConfig(level=logging.INFO)
    
    try:
        otu_path, serology_path = fetch_strategy_a_data()
        print(f"OTU table saved to: {otu_path}")
        print(f"Serology metadata saved to: {serology_path}")
        return 0
    except DataUnavailableError as e:
        print(f"ERROR: {e}")
        print("Real data not available. Pipeline will need to use synthetic data fallback.")
        return 1
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
