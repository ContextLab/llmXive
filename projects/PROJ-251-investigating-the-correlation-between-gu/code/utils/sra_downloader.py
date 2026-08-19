"""
SRA Downloader utilities.
"""
import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional

class DataUnavailableError(Exception):
    pass

def get_sra_run_ids(accession: str) -> List[str]:
    return []

def prefetch_sra_run(run_id: str):
    pass

def fasterq_dump(run_id: str, output_dir: Path):
    pass

def download_fastq_for_study(accession: str, output_dir: Path):
    pass

def run_strategy_b():
    pass
