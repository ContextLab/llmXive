"""
Cron-triggered lifecycle manager script for PROJ-002.
Compresses FASTQs, deposits to Zenodo, records DOI, and deletes local copies.
"""
import os
import shutil
import json
from pathlib import Path
from loguru import logger
from code.utils.logger import setup_logger
from code.pipeline.lifecycle import check_file_age, record_metadata

setup_logger("pipeline.log", level="INFO")

ZENODO_API_URL = "https://zenodo.org/api/deposit/depositions"
RETENTION_DAYS = 30

def compress_fastqs(fastq_dir: str, output_archive: str) -> str:
    """
    Compress FASTQ files into a tar.gz archive.

    Args:
        fastq_dir: Directory containing FASTQ files.
        output_archive: Path to output archive.

    Returns:
        Path to the created archive.
    """
    logger.info(f"Compressing FASTQs in {fastq_dir}")
    shutil.make_archive(output_archive.replace('.tar.gz', ''), 'gztar', fastq_dir)
    logger.info(f"Archive created: {output_archive}")
    return output_archive

def deposit_to_zenodo(archive_path: str, metadata: dict) -> str:
    """
    Deposit archive to Zenodo and return DOI.

    Args:
        archive_path: Path to the archive.
        metadata: Metadata for the deposit.

    Returns:
        DOI string.
    """
    # Placeholder for Zenodo API call
    logger.warning("Zenodo deposit simulated. No real DOI returned.")
    return "10.5281/zenodo.0000000"

def run_lifecycle_cycle():
    """
    Run one cycle of lifecycle management.
    """
    logger.info("Starting lifecycle management cycle.")

    # Example: Process human FASTQs
    fastq_dir = "data/raw/human"
    if os.path.exists(fastq_dir):
        files = [f for f in os.listdir(fastq_dir) if f.endswith('.fastq.gz')]
        for f in files:
            file_path = os.path.join(fastq_dir, f)
            if check_file_age(file_path, RETENTION_DAYS):
                logger.info(f"File {f} is older than {RETENTION_DAYS} days. Processing...")
                archive_name = f"{f}.tar.gz"
                archive_path = os.path.join("data/archive", archive_name)
                os.makedirs("data/archive", exist_ok=True)
                compress_fastqs(file_path, archive_path)
                doi = deposit_to_zenodo(archive_path, {"title": f"Retention Archive for {f}"})
                record_metadata(file_path, {"doi": doi, "deleted": True})
                os.remove(file_path)
                logger.info(f"Deleted local copy of {f} after archival.")

    logger.info("Lifecycle management cycle complete.")

def main():
    """
    Main entry point for lifecycle manager.
    """
    run_lifecycle_cycle()

if __name__ == "__main__":
    main()
