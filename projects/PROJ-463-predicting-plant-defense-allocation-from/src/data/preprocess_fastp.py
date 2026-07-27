"""
Wrapper for fastp to preprocess FASTQ files.

This script trims and filters FASTQ files using fastp.
It skips execution if running in synthetic mode (flagged by data/synthetic/.mode_active).
"""
import os
import sys
import subprocess
import json
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add project root to path if not already present
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger
from src.utils.schemas import ManifestEntry, ProvenanceInfo, DataManifest
from src.utils.config import get_data_path

logger = get_logger(__name__)


def check_fastp_available() -> bool:
    """Check if fastp is installed and available in PATH."""
    try:
        result = subprocess.run(
            ["fastp", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"fastp version: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.error(f"fastp not found or failed to run: {e}")
        return False


def is_synthetic_mode() -> bool:
    """Check if the pipeline is running in synthetic mode."""
    data_path = get_data_path()
    mode_flag = Path(data_path) / "synthetic" / ".mode_active"
    return mode_flag.exists()


def run_fastp(
    input_r1: str,
    input_r2: str,
    output_r1: str,
    output_r2: str,
    json_report: str,
    threads: int = 4
) -> bool:
    """
    Run fastp on paired-end FASTQ files.
    
    Args:
        input_r1: Path to input R1 FASTQ file (gzipped)
        input_r2: Path to input R2 FASTQ file (gzipped)
        output_r1: Path to output R1 FASTQ file (gzipped)
        output_r2: Path to output R2 FASTQ file (gzipped)
        json_report: Path to output JSON report
        threads: Number of threads to use
        
    Returns:
        True if successful, False otherwise
    """
    # Ensure output directories exist
    Path(output_r1).parent.mkdir(parents=True, exist_ok=True)
    Path(output_r2).parent.mkdir(parents=True, exist_ok=True)
    Path(json_report).parent.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        "fastp",
        "-i", input_r1,
        "-I", input_r2,
        "-o", output_r1,
        "-O", output_r2,
        "--thread", str(threads),
        "--json", json_report,
        "--html", json_report.replace(".json", ".html")
    ]
    
    logger.info(f"Running fastp command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        logger.info("fastp completed successfully")
        logger.debug(f"fastp stdout: {result.stdout}")
        if result.stderr:
            logger.debug(f"fastp stderr: {result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"fastp failed with return code {e.returncode}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        return False


def process_fastq_file(
    accession_id: str,
    data_dir: Path,
    threads: int = 4
) -> Optional[Dict[str, Any]]:
    """
    Process a single FASTQ pair for a given accession ID.
    
    Args:
        accession_id: The study accession ID
        data_dir: Base data directory
        threads: Number of threads for fastp
        
    Returns:
        Dictionary with output paths and report path, or None if failed/skipped
    """
    raw_dir = data_dir / "raw"
    processed_trimmed_dir = data_dir / "processed" / "trimmed"
    
    # Check for input files
    input_r1 = raw_dir / f"{accession_id}_R1.fastq.gz"
    input_r2 = raw_dir / f"{accession_id}_R2.fastq.gz"
    
    if not input_r1.exists():
        logger.warning(f"Input R1 file not found: {input_r1}")
        return None
    if not input_r2.exists():
        logger.warning(f"Input R2 file not found: {input_r2}")
        return None
    
    # Define output paths
    output_r1 = processed_trimmed_dir / f"{accession_id}_R1_trimmed.fastq.gz"
    output_r2 = processed_trimmed_dir / f"{accession_id}_R2_trimmed.fastq.gz"
    json_report = str(processed_trimmed_dir / f"{accession_id}_fastp_report.json")
    
    # Run fastp
    success = run_fastp(
        str(input_r1),
        str(input_r2),
        str(output_r1),
        str(output_r2),
        json_report,
        threads
    )
    
    if not success:
        logger.error(f"Failed to process {accession_id}")
        return None
    
    # Verify outputs exist
    if not output_r1.exists() or not output_r2.exists():
        logger.error(f"Output files not created for {accession_id}")
        return None
    
    logger.info(f"Successfully processed {accession_id}: {output_r1.name}, {output_r2.name}")
    
    return {
        "accession_id": accession_id,
        "output_r1": str(output_r1),
        "output_r2": str(output_r2),
        "report": json_report
    }


def main():
    """Main entry point for the fastp preprocessing script."""
    parser = argparse.ArgumentParser(
        description="Preprocess FASTQ files using fastp"
    )
    parser.add_argument(
        "--accession-id",
        type=str,
        help="Specific accession ID to process (optional, if not provided processes all)"
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=4,
        help="Number of threads to use for fastp (default: 4)"
    )
    args = parser.parse_args()
    
    # Check for synthetic mode
    if is_synthetic_mode():
        logger.info("Synthetic mode detected. Skipping fastp preprocessing.")
        return
    
    # Check if fastp is available
    if not check_fastp_available():
        logger.error("fastp is not available. Please install it (see T003b-fastp).")
        sys.exit(1)
    
    data_path = get_data_path()
    data_dir = Path(data_path)
    
    # Determine which accession IDs to process
    accession_ids = []
    if args.accession_id:
        accession_ids = [args.accession_id]
    else:
        # Scan data/raw for FASTQ files
        raw_dir = data_dir / "raw"
        if raw_dir.exists():
            for f in raw_dir.glob("*_R1.fastq.gz"):
                accession_id = f.stem.replace("_R1", "")
                accession_ids.append(accession_id)
    
    if not accession_ids:
        logger.warning("No FASTQ files found to process in data/raw/")
        return
    
    logger.info(f"Processing {len(accession_ids)} study/studies")
    
    results = []
    for accession_id in accession_ids:
        result = process_fastq_file(accession_id, data_dir, args.threads)
        if result:
            results.append(result)
    
    logger.info(f"Completed preprocessing. Successfully processed: {len(results)}/{len(accession_ids)}")
    
    if len(results) < len(accession_ids):
        logger.warning("Some studies failed to process.")
        sys.exit(1)


if __name__ == "__main__":
    main()