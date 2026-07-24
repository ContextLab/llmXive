"""
SRA Downloader Module

Utilities for downloading data from NCBI SRA (Sequence Read Archive).
Supports both programmatic access via esearch/efetch and the fasterq-dump tool.
"""
import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional

from utils.logging_config import get_logger, log_error_context

logger = get_logger(__name__)

class DataUnavailableError(Exception):
    """Raised when required data cannot be retrieved from SRA."""
    pass

def get_sra_run_ids(study_accession: str) -> List[str]:
    """
    Fetch SRA run IDs associated with a study accession using esearch.
    
    Args:
        study_accession: SRA study accession (e.g., SRP053178)
        
    Returns:
        List of run IDs (e.g., SRR123456)
        
    Raises:
        DataUnavailableError: If no runs are found or esearch fails
    """
    logger.info(f"Fetching run IDs for study: {study_accession}")
    
    try:
        # Search for runs in the study
        esearch_cmd = f'esearch -db sra -query "{study_accession}"'
        efetch_cmd = 'efetch -format runinfo'
        cut_cmd = 'cut -d, -f1'
        
        # Run the pipeline
        search_proc = subprocess.run(
            esearch_cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=True,
            timeout=60
        )
        
        fetch_proc = subprocess.run(
            efetch_cmd,
            shell=True,
            input=search_proc.stdout,
            capture_output=True,
            text=True,
            check=True,
            timeout=120
        )
        
        cut_proc = subprocess.run(
            cut_cmd,
            shell=True,
            input=fetch_proc.stdout,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse run IDs (skip header)
        run_ids = [
            line.strip() for line in cut_proc.stdout.strip().split('\n')
            if line.strip() and line.strip() != 'Run'
        ]
        
        if not run_ids:
            raise DataUnavailableError(
                f"No run IDs found for study {study_accession}. "
                "The study may not exist or may be private."
            )
        
        logger.info(f"Found {len(run_ids)} run IDs for {study_accession}")
        for rid in run_ids[:5]:
            logger.debug(f"  - {rid}")
        if len(run_ids) > 5:
            logger.debug(f"  ... and {len(run_ids) - 5} more")
        
        return run_ids
        
    except subprocess.TimeoutExpired:
        raise DataUnavailableError(f"Timeout fetching run IDs for {study_accession}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to fetch run IDs: {e.stderr}")
        log_error_context("sra_esearch_failure", str(e.stderr))
        raise DataUnavailableError(
            f"Failed to fetch run IDs for {study_accession}: {e.stderr}"
        )

def prefetch_sra_run(run_id: str, output_dir: Path) -> Path:
    """
    Prefetch a single SRA run using prefetch command.
    
    Args:
        run_id: SRA run ID (e.g., SRR123456)
        output_dir: Directory to store downloaded data
        
    Returns:
        Path to the downloaded .sra file
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cmd = ["prefetch", run_id, "-O", str(output_dir)]
    
    logger.info(f"Prefetching {run_id}...")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=3600
        )
        logger.debug(f"Prefetch stdout: {result.stdout}")
        
        # Find the downloaded .sra file
        sra_files = list(output_dir.glob(f"{run_id}/*.sra"))
        if not sra_files:
            # Try direct location
            sra_files = list(output_dir.glob(f"{run_id}.sra"))
        
        if sra_files:
            return sra_files[0]
        else:
            raise RuntimeError(f"Prefetch completed but no .sra file found for {run_id}")
            
    except subprocess.TimeoutExpired:
        raise DataUnavailableError(f"Timeout prefetching {run_id}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Prefetch failed for {run_id}: {e.stderr}")
        log_error_context("sra_prefetch_failure", str(e.stderr))
        raise DataUnavailableError(f"Failed to prefetch {run_id}: {e.stderr}")

def fasterq_dump(sra_path: Path, output_dir: Path) -> List[Path]:
    """
    Convert SRA file to FASTQ using fasterq-dump.
    
    Args:
        sra_path: Path to the .sra file
        output_dir: Directory for FASTQ output
        
    Returns:
        List of paths to generated FASTQ files
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        "fasterq-dump",
        "--outdir", str(output_dir),
        "--split-files",  # Split paired-end reads
        "--skip-technical",
        "--readids",
        "--progress",
        str(sra_path)
    ]
    
    logger.info(f"Converting {sra_path.name} to FASTQ...")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=7200
        )
        logger.debug(f"fasterq-dump stdout: {result.stdout}")
        
        # Find generated FASTQ files
        fastq_files = sorted(output_dir.glob("*.fastq"))
        if not fastq_files:
            fastq_files = sorted(output_dir.glob("*.fastq.gz"))
        
        if fastq_files:
            logger.info(f"Generated {len(fastq_files)} FASTQ files")
            return fastq_files
        else:
            raise RuntimeError(f"fasterq-dump completed but no FASTQ files found")
            
    except subprocess.TimeoutExpired:
        raise DataUnavailableError(f"Timeout converting {sra_path.name}")
    except subprocess.CalledProcessError as e:
        logger.error(f"fasterq-dump failed: {e.stderr}")
        log_error_context("fasterq_dump_failure", str(e.stderr))
        raise DataUnavailableError(f"Failed to convert {sra_path.name}: {e.stderr}")

def download_fastq_for_study(
    study_accession: str,
    output_dir: Path,
    max_workers: int = 4
) -> List[Path]:
    """
    Download and convert all FASTQ files for a study.
    
    Args:
        study_accession: SRA study accession
        output_dir: Output directory for FASTQ files
        max_workers: Maximum parallel downloads
        
    Returns:
        List of paths to downloaded FASTQ files
    """
    logger.info(f"Starting download for study {study_accession}")
    
    # Get run IDs
    run_ids = get_sra_run_ids(study_accession)
    
    if not run_ids:
        raise DataUnavailableError(f"No runs found for {study_accession}")
    
    all_fastq_files = []
    sra_cache_dir = output_dir / "sra_cache"
    sra_cache_dir.mkdir(parents=True, exist_ok=True)
    
    for i, run_id in enumerate(run_ids):
        logger.info(f"Processing {i+1}/{len(run_ids)}: {run_id}")
        
        try:
            # Prefetch
            sra_file = prefetch_sra_run(run_id, sra_cache_dir)
            
            # Convert to FASTQ
            fastq_dir = output_dir / "fastq_files"
            fastq_files = fasterq_dump(sra_file, fastq_dir)
            
            all_fastq_files.extend(fastq_files)
            
        except DataUnavailableError as e:
            logger.warning(f"Skipping {run_id} due to error: {e}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error processing {run_id}: {e}")
            continue
    
    if not all_fastq_files:
        raise DataUnavailableError(
            f"No FASTQ files were successfully downloaded for {study_accession}"
        )
    
    logger.info(f"Successfully downloaded {len(all_fastq_files)} FASTQ files")
    return all_fastq_files

def run_strategy_b(study_accession: str, output_dir: Path) -> List[Path]:
    """
    Execute Strategy B: Download raw FASTQ files from NCBI SRA.
    
    This is the main entry point for Strategy B data acquisition.
    
    Args:
        study_accession: SRA study accession (e.g., SRP053178)
        output_dir: Directory to store downloaded FASTQ files
        
    Returns:
        List of paths to downloaded FASTQ files
        
    Raises:
        DataUnavailableError: If data cannot be retrieved
    """
    logger.info(f"Executing Strategy B for study: {study_accession}")
    
    try:
        return download_fastq_for_study(study_accession, output_dir)
    except DataUnavailableError:
        raise
    except Exception as e:
        logger.error(f"Strategy B failed: {e}")
        log_error_context("strategy_b_failure", str(e))
        raise DataUnavailableError(f"Strategy B failed: {e}")
