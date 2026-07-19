import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional
import time

# Import config for paths and API keys
from code.utils.config import get_ncbi_api_key, get_raw_path, ensure_directories
from code.utils.logging_config import get_logger, log_error_context

logger = get_logger(__name__)

def get_sra_run_ids(accession: str) -> List[str]:
    """
    Fetches the list of SRA run IDs associated with a Study Accession (SRP)
    using the NCBI E-utilities (ESearch) API.
    
    Args:
        accession: The SRA Study Accession (e.g., 'SRP053178').
        
    Returns:
        A list of SRA Run IDs (e.g., ['SRR123456', ...]).
        
    Raises:
        RuntimeError: If the API call fails or returns no results.
    """
    api_key = get_ncbi_api_key()
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    
    params = {
        "db": "sra",
        "term": f"{accession}[ACCN]",
        "retmode": "json",
        "retmax": 10000,
        "usehistory": "y"
    }
    
    if api_key:
        params["api_key"] = api_key

    logger.info(f"Fetching run IDs for study {accession} from NCBI E-utilities...")
    
    try:
        # Using urllib for standard library compliance without extra deps
        import urllib.request
        import urllib.parse
        import json

        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        
        with urllib.request.urlopen(url, timeout=60) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        if "esearchresult" not in data:
            raise RuntimeError("Invalid response structure from NCBI E-utilities.")
            
        id_list = data["esearchresult"].get("idlist", [])
        
        if not id_list:
            raise RuntimeError(f"No run IDs found for study {accession}.")
            
        logger.info(f"Found {len(id_list)} run IDs for {accession}.")
        return id_list
        
    except Exception as e:
        log_error_context("Failed to fetch SRA run IDs", error=e)
        raise RuntimeError(f"Failed to fetch run IDs for {accession}: {str(e)}")

def prefetch_sra_run(run_id: str, output_dir: Path) -> bool:
    """
    Downloads the SRA dataset for a specific run ID using 'prefetch'.
    This downloads the .sra file to the local cache.
    
    Args:
        run_id: The SRA Run ID (e.g., 'SRR123456').
        output_dir: Directory to store the .sra file.
        
    Returns:
        True if successful, False otherwise.
    """
    logger.info(f"Prefetching {run_id}...")
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        "prefetch",
        "--option-file", "https://sra-download.bioncb.nih.gov/sra-kits/sra-toolkit.cfg",
        "-O", str(output_dir),
        run_id
    ]
    
    try:
        # Run with timeout to prevent hanging
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout per file
        )
        
        if result.returncode == 0:
            logger.info(f"Successfully prefetched {run_id}.")
            return True
        else:
            logger.error(f"prefetch failed for {run_id}: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout while prefetching {run_id}.")
        return False
    except FileNotFoundError:
        logger.error("sra-tools (prefetch) not found. Please install sra-tools.")
        raise RuntimeError("sra-tools not found. Install via 'conda install -c bioconda sra-tools' or 'pip install sra-tools'.")

def fasterq_dump(run_id: str, sra_dir: Path, output_dir: Path) -> Optional[Path]:
    """
    Converts a prefetched .sra file to FASTQ using 'fasterq-dump'.
    
    Args:
        run_id: The SRA Run ID.
        sra_dir: Directory containing the .sra file.
        output_dir: Directory to write the .fastq files.
        
    Returns:
        Path to the generated .fastq file, or None if failed.
    """
    logger.info(f"Converting {run_id} to FASTQ...")
    
    sra_file = sra_dir / f"{run_id}.sra"
    if not sra_file.exists():
        logger.error(f"Source .sra file not found: {sra_file}")
        return None
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        "fasterq-dump",
        "--split-files", # Handles paired-end if present
        "--outdir", str(output_dir),
        str(sra_file)
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=7200 # 2 hour timeout per file
        )
        
        if result.returncode == 0:
            # fasterq-dump usually creates .fastq files in the output dir
            # Find the most recently modified .fastq file in the dir
            fastq_files = list(output_dir.glob(f"{run_id}_*.fastq"))
            if not fastq_files:
                # Fallback for single end
                fastq_files = list(output_dir.glob(f"{run_id}.fastq"))
            
            if fastq_files:
                logger.info(f"Generated FASTQ: {fastq_files[0]}")
                return fastq_files[0]
            else:
                logger.warning(f"fasterq-dump returned 0 but no FASTQ found in {output_dir}")
                return None
        else:
            logger.error(f"fasterq-dump failed for {run_id}: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout while converting {run_id}.")
        return None
    except FileNotFoundError:
        logger.error("sra-tools (fasterq-dump) not found.")
        raise RuntimeError("sra-tools not found.")

def download_fastq_for_study(accession: str) -> List[Path]:
    """
    Orchestrates the download of all FASTQ files for a given study accession.
    1. Fetches run IDs.
    2. Prefetches .sra files.
    3. Converts to FASTQ.
    
    Args:
        accession: The SRA Study Accession.
        
    Returns:
        List of paths to the generated FASTQ files.
        
    Raises:
        RuntimeError: If the process fails completely.
    """
    raw_path = get_raw_path()
    ensure_directories()
    
    sra_cache = raw_path / "sra_cache"
    sra_cache.mkdir(parents=True, exist_ok=True)
    
    fastq_output = raw_path / "fastq"
    fastq_output.mkdir(parents=True, exist_ok=True)
    
    run_ids = get_sra_run_ids(accession)
    logger.info(f"Starting download process for {len(run_ids)} runs.")
    
    downloaded_fastqs = []
    failed_runs = []
    
    for i, run_id in enumerate(run_ids):
        logger.info(f"Processing [{i+1}/{len(run_ids)}]: {run_id}")
        
        # Step 1: Prefetch
        if not prefetch_sra_run(run_id, sra_cache):
            failed_runs.append(run_id)
            continue
            
        # Step 2: Convert
        fastq_path = fasterq_dump(run_id, sra_cache, fastq_output)
        
        if fastq_path and fastq_path.exists():
            downloaded_fastqs.append(fastq_path)
        else:
            failed_runs.append(run_id)
            
    if failed_runs:
        logger.warning(f"Failed to process {len(failed_runs)} runs: {failed_runs}")
        
    if not downloaded_fastqs:
        raise RuntimeError("Strategy B Failed: No FASTQ files were successfully downloaded.")
        
    logger.info(f"Successfully downloaded {len(downloaded_fastqs)} FASTQ files.")
    return downloaded_fastqs

def run_strategy_b(accession: str = "SRP053178") -> List[Path]:
    """
    Entry point for Strategy B: Download raw FASTQ files.
    
    Args:
        accession: The study accession to process.
        
    Returns:
        List of paths to downloaded FASTQ files.
    """
    logger.info(f"Executing Strategy B for accession: {accession}")
    try:
        return download_fastq_for_study(accession)
    except Exception as e:
        logger.error(f"Strategy B failed: {str(e)}")
        raise