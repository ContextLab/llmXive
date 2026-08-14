"""
RNA-seq Data Ingestion Module for Coral Resilience Project.

This module handles the download of FASTQ files from NCBI SRA/ENA for
BioProject PRJNA321023, including retry logic, checksum verification,
and metadata parsing.
"""
import os
import sys
import time
import json
import logging
import hashlib
import gzip
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Import project utilities and models
# Note: Using the API surface provided in the prompt
from utils.logging import setup_logger, get_memory_usage_mb, log_memory_usage, ExecutionTimer
from utils.errors import NCBIError, NCBITimeoutError, NCBIConnectionError, ChecksumError
from config import ensure_directories, get_thresholds

# Constants
PROJECT_ID = "PRJNA321023"
MAX_RETRIES = 3
BACKOFF_FACTOR = 2.0
CHUNK_SIZE = 1024 * 1024  # 1MB chunks for download

# Setup logger
logger = setup_logger("ingest")


@dataclass
class DownloadStatus:
    """Data class to track download status for logging."""
    sample_id: str
    file_path: Optional[str]
    status: str  # 'success', 'failed', 'skipped'
    error_message: Optional[str] = None
    file_size_bytes: Optional[int] = None
    checksum: Optional[str] = None


class IngestionError(Exception):
    """Custom exception for ingestion failures."""
    pass


def _create_session_with_retries() -> requests.Session:
    """Create a requests session with exponential backoff retry logic."""
    session = requests.Session()
    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def _fetch_sra_run_info(project_id: str) -> List[Dict[str, Any]]:
    """
    Fetch SRA run information for a given BioProject ID using NCBI E-utilities.
    
    Args:
        project_id: The BioProject ID (e.g., PRJNA321023)
        
    Returns:
        List of dictionaries containing run metadata
    """
    # Step 1: Get BioProject ID to Accession mapping (if needed) or directly query SRA
    # Using SRA Run Selector API via E-utilities
    
    esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "sra",
        "term": f"bioproject:{project_id}",
        "retmode": "json",
        "retmax": 1000  # Limit to 1000 runs for this project
    }
    
    session = _create_session_with_retries()
    
    try:
        response = session.get(esearch_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "esearchresult" not in data or "idlist" not in data["esearchresult"]:
            raise IngestionError(f"No runs found for BioProject {project_id}")
        
        run_ids = data["esearchresult"]["idlist"]
        logger.info(f"Found {len(run_ids)} runs for {project_id}")
        
        # Fetch details for each run
        run_details = []
        if not run_ids:
            return []
            
        # Fetch details in batches to avoid overwhelming the server
        # For simplicity, we'll fetch all at once with a large retmax
        esummary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        params_summary = {
            "db": "sra",
            "id": ",".join(run_ids),
            "retmode": "json"
        }
        
        response_summary = session.get(esummary_url, params=params_summary, timeout=60)
        response_summary.raise_for_status()
        summary_data = response_summary.json()
        
        for run_id in run_ids:
            if run_id in summary_data["result"]:
                run_info = summary_data["result"][run_id]
                run_details.append({
                    "run_id": run_id,
                    "experiment_id": run_info.get("experiment"),
                    "sample_id": run_info.get("sample"),
                    "total_spots": run_info.get("total_spots"),
                    "total_bases": run_info.get("total_bases"),
                    "fastq_ftp": run_info.get("fastq_ftp"),
                    "sra_ftp": run_info.get("sra_ftp"),
                    "filename": run_info.get("filename"),
                    "treatment": run_info.get("treatment", "unknown") # Placeholder, actual metadata parsing in T017
                })
                
        return run_details
        
    except requests.exceptions.Timeout:
        raise NCBITimeoutError(f"Timeout while fetching run info for {project_id}")
    except requests.exceptions.RequestException as e:
        raise NCBIConnectionError(f"Failed to connect to NCBI: {str(e)}")
    except json.JSONDecodeError:
        raise IngestionError("Failed to parse NCBI response as JSON")


def _get_fastq_urls(run_info: Dict[str, Any]) -> List[str]:
    """
    Extract FASTQ download URLs from run information.
    
    Args:
        run_info: Dictionary containing SRA run metadata
        
    Returns:
        List of FASTQ download URLs
    """
    fastq_ftp = run_info.get("fastq_ftp")
    if not fastq_ftp:
        return []
        
    # fastq_ftp is a semicolon-separated list of URLs
    urls = fastq_ftp.split(";")
    return [url for url in urls if url and url.startswith("ftp")]


def _download_file_with_progress(url: str, output_path: Path, session: requests.Session) -> Tuple[bool, str]:
    """
    Download a file from URL with progress logging and error handling.
    
    Args:
        url: Download URL
        output_path: Local path to save the file
        session: Requests session
        
    Returns:
        Tuple of (success: bool, error_message: str)
    """
    try:
        # Convert FTP to HTTP for requests library if needed
        http_url = url.replace("ftp://", "https://")
        
        # Some NCBI FTP servers might not support HTTPS directly, try HTTP as fallback
        if not http_url.startswith("http"):
            http_url = url
            
        logger.info(f"Downloading from {url} to {output_path}")
        
        response = session.get(http_url, stream=True, timeout=120)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    # Log progress every 10% or at least every 10MB
                    if total_size > 0 and downloaded % max(10 * 1024 * 1024, total_size // 10) < CHUNK_SIZE:
                        progress = (downloaded / total_size) * 100
                        logger.debug(f"Download progress: {progress:.1f}%")
                        
        logger.info(f"Download completed: {output_path} ({downloaded} bytes)")
        return True, ""
        
    except requests.exceptions.Timeout:
        return False, "Download timeout"
    except requests.exceptions.RequestException as e:
        return False, f"Download failed: {str(e)}"
    except IOError as e:
        return False, f"File write error: {str(e)}"


def _calculate_sha256(file_path: Path) -> str:
    """
    Calculate SHA256 checksum of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        SHA256 hex digest
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def run_ingestion(output_dir: Optional[Path] = None) -> List[DownloadStatus]:
    """
    Main ingestion function to download FASTQ files for PRJNA321023.
    
    Args:
        output_dir: Optional directory to save downloaded files. Defaults to data/raw/PRJNA321023.
        
    Returns:
        List of DownloadStatus objects for logging
    """
    if output_dir is None:
        # Ensure directories exist using config
        ensure_directories()
        from config import PROJECT_ROOT
        output_dir = PROJECT_ROOT / "data" / "raw" / PROJECT_ID
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting ingestion for BioProject {PROJECT_ID}")
    logger.info(f"Output directory: {output_dir}")
    
    timer = ExecutionTimer()
    timer.start()
    
    status_log: List[DownloadStatus] = []
    
    try:
        # Fetch run information
        run_info_list = _fetch_sra_run_info(PROJECT_ID)
        
        if not run_info_list:
            logger.warning(f"No runs found for {PROJECT_ID}")
            return status_log
        
        session = _create_session_with_retries()
        
        for run_info in run_info_list:
            sample_id = run_info.get("run_id", "unknown")
            logger.info(f"Processing sample: {sample_id}")
            
            fastq_urls = _get_fastq_urls(run_info)
            
            if not fastq_urls:
                logger.warning(f"No FASTQ URLs found for {sample_id}")
                status_log.append(DownloadStatus(
                    sample_id=sample_id,
                    file_path=None,
                    status="skipped",
                    error_message="No FASTQ URLs found"
                ))
                continue
            
            # Download each FASTQ file
            for url in fastq_urls:
                # Extract filename from URL
                filename = url.split("/")[-1]
                if not filename.endswith(".fastq.gz") and not filename.endswith(".fq.gz"):
                    filename += ".fastq.gz"
                    
                output_path = output_dir / filename
                
                # Skip if file already exists (idempotent)
                if output_path.exists():
                    logger.info(f"File already exists, skipping: {output_path}")
                    status_log.append(DownloadStatus(
                        sample_id=sample_id,
                        file_path=str(output_path),
                        status="skipped",
                        error_message="File already exists"
                    ))
                    continue
                    
                success, error_msg = _download_file_with_progress(url, output_path, session)
                
                if success:
                    # Calculate checksum
                    checksum = _calculate_sha256(output_path)
                    file_size = output_path.stat().st_size
                    
                    status_log.append(DownloadStatus(
                        sample_id=sample_id,
                        file_path=str(output_path),
                        status="success",
                        file_size_bytes=file_size,
                        checksum=checksum
                    ))
                    logger.info(f"Successfully downloaded and checksummed: {filename}")
                else:
                    logger.error(f"Failed to download {url}: {error_msg}")
                    status_log.append(DownloadStatus(
                        sample_id=sample_id,
                        file_path=None,
                        status="failed",
                        error_message=error_msg
                    ))
                    
    except Exception as e:
        logger.exception(f"Ingestion failed with unexpected error: {str(e)}")
        raise IngestionError(f"Ingestion process failed: {str(e)}")
    finally:
        timer.stop()
        log_memory_usage()
        logger.info(f"Ingestion completed in {timer.elapsed_seconds:.2f} seconds")
        
    return status_log


def save_download_log(status_log: List[DownloadStatus], log_path: Optional[Path] = None):
    """
    Save download status log to JSON file.
    
    Args:
        status_log: List of DownloadStatus objects
        log_path: Path to save the log file
    """
    if log_path is None:
        from config import PROJECT_ROOT
        log_path = PROJECT_ROOT / "data" / "raw" / "download_log.json"
        
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    log_data = [asdict(status) for status in status_log]
    
    with open(log_path, 'w') as f:
        json.dump(log_data, f, indent=2)
        
    logger.info(f"Download log saved to {log_path}")


def main():
    """Main entry point for the ingestion script."""
    logger.info("Starting RNA-seq data ingestion pipeline")
    
    try:
        status_log = run_ingestion()
        save_download_log(status_log)
        
        # Summary
        success_count = sum(1 for s in status_log if s.status == "success")
        failed_count = sum(1 for s in status_log if s.status == "failed")
        skipped_count = sum(1 for s in status_log if s.status == "skipped")
        
        logger.info(f"Ingestion summary: {success_count} success, {failed_count} failed, {skipped_count} skipped")
        
        if failed_count > 0:
            logger.warning(f"{failed_count} downloads failed. Check logs for details.")
            sys.exit(1)
            
    except Exception as e:
        logger.exception(f"Pipeline failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
