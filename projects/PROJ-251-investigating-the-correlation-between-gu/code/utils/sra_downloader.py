import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional

from utils.logging_config import get_logger

logger = get_logger(__name__)

class DataUnavailableError(Exception):
    """Raised when requested real data is not available."""
    pass

def get_sra_run_ids(accession: str) -> List[str]:
    """
    Retrieves SRA run IDs for a given study accession.
    Note: This is a placeholder for actual SRA API logic.
    In a real implementation, this would call the SRA Toolkit or NCBI API.
    """
    # For the purpose of this task, we assume the accession is a study ID (SRP...)
    # and we would need to resolve it to runs.
    # Since we are fetching pre-processed data, we might not need individual runs
    # if the pre-processed table is already aggregated.
    # This function is kept for API compatibility.
    return []

def prefetch_sra_run(run_id: str, output_dir: Path) -> Path:
    """
    Prefetches an SRA run using fasterq-dump or similar.
    """
    raise NotImplementedError("Raw SRA prefetching is not used in Strategy A (pre-processed).")

def fasterq_dump(run_id: str, output_dir: Path) -> Path:
    """
    Runs fasterq-dump for a specific run.
    """
    raise NotImplementedError("Raw SRA dump is not used in Strategy A.")

def download_fastq_for_study(accession: str, output_dir: Path) -> List[Path]:
    """
    Downloads all FASTQ files for a study.
    """
    raise NotImplementedError("Raw FASTQ download is not used in Strategy A.")

def run_strategy_b(accession: str, output_dir: Path) -> Tuple[Path, Path]:
    """
    Strategy B: Download raw FASTQ and process with DADA2/QIIME2.
    Not used for T011a (Strategy A).
    """
    raise NotImplementedError("Strategy B is not implemented in this file.")
