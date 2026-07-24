"""
Script to execute Strategy B: Download raw FASTQ files for SRP053178.
Triggered only if Strategy A (pre-processed fetch) fails.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.sra_downloader import run_strategy_b, DataUnavailableError
from utils.logging_config import get_logger, log_error_context
from utils.config import get_raw_path

logger = get_logger(__name__)

def main():
    study_accession = "SRP053178"
    logger.info(f"Initiating Strategy B download for {study_accession}")

    try:
        # Check if data already exists to avoid re-downloading
        raw_dir = get_raw_path()
        fastq_dir = raw_dir / "fastq_files"
        
        if fastq_dir.exists() and any(fastq_dir.iterdir()):
            count = len(list(fastq_dir.iterdir()))
            logger.warning(f"FastQ directory already contains {count} files. Skipping download.")
            logger.info("To force re-download, remove files in data/raw/fastq_files/")
            return

        # Execute download
        fastq_files = run_strategy_b(study_accession)

        logger.info(f"SUCCESS: Downloaded {len(fastq_files)} FASTQ files to {fastq_dir}")
        for f in fastq_files:
            logger.info(f"  - {f.name}")

    except DataUnavailableError as e:
        log_error_context("Strategy B Failed", str(e))
        logger.critical(f"Data unavailable: {e}")
        sys.exit(1)
    except RuntimeError as e:
        log_error_context("Tool Error", str(e))
        logger.critical(f"Required tools missing or failed: {e}")
        sys.exit(1)
    except Exception as e:
        log_error_context("Unexpected Error", str(e))
        logger.exception("An unexpected error occurred")
        sys.exit(1)

if __name__ == "__main__":
    main()
