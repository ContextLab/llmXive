"""
HISAT2 Preprocessing Wrapper

Aligns trimmed FASTQ files to a reference genome using HISAT2.
Produces BAM files in the data/processed/aligned/ directory.

Dependency: HISAT2 must be installed (T003b-hisat2).
Skip if --mode synthetic (checked via data/synthetic/.mode_active).
"""

import os
import sys
import subprocess
import argparse
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger
from src.utils.config import get_data_path
from src.utils.provenance import record_provenance, ArtifactType, get_provenance_tracker

logger = get_logger(__name__)


def check_hisat2_available() -> bool:
    """Check if HISAT2 is installed and accessible."""
    try:
        result = subprocess.run(
            ["hisat2", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False
        )
        if result.returncode == 0:
            version_info = result.stdout.decode("utf-8").strip()
            logger.info(f"HISAT2 found: {version_info}")
            return True
        else:
            logger.error(f"HISAT2 check failed: {result.stderr.decode('utf-8')}")
            return False
    except FileNotFoundError:
        logger.error("HISAT2 command not found. Please install via T003b-hisat2.")
        return False


def is_synthetic_mode() -> bool:
    """Check if the pipeline is running in synthetic mode."""
    synthetic_marker = Path("data/synthetic/.mode_active")
    return synthetic_marker.exists()


def run_hisat2(
    input_r1: Path,
    input_r2: Path,
    genome_index: Path,
    output_bam: Path,
    threads: int = 4,
    gff: Optional[Path] = None
) -> bool:
    """
    Run HISAT2 alignment.

    Args:
        input_r1: Path to trimmed R1 FASTQ
        input_r2: Path to trimmed R2 FASTQ
        genome_index: Path to HISAT2 genome index prefix
        output_bam: Path for output BAM file
        threads: Number of CPU threads
        gff: Optional GFF/GTF file for spliced alignment

    Returns:
        True if successful, False otherwise.
    """
    if not input_r1.exists():
        logger.error(f"Input R1 file not found: {input_r1}")
        return False
    if not input_r2.exists():
        logger.error(f"Input R2 file not found: {input_r2}")
    if not genome_index.exists():
        logger.error(f"Genome index not found: {genome_index}")
        return False

    output_dir = output_bam.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "hisat2",
        "-p", str(threads),
        "-x", str(genome_index),
        "-1", str(input_r1),
        "-2", str(input_r2),
        "-S", str(output_bam)
    ]

    if gff and gff.exists():
        cmd.extend(["--gff", str(gff)])

    logger.info(f"Running HISAT2: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        # HISAT2 outputs alignment stats to stderr
        stderr_output = result.stderr.decode("utf-8")
        logger.info(f"HISAT2 alignment stats:\n{stderr_output}")

        if output_bam.exists() and output_bam.stat().st_size > 0:
            logger.info(f"Alignment successful: {output_bam}")
            return True
        else:
            logger.error("Output BAM file is missing or empty.")
            return False

    except subprocess.CalledProcessError as e:
        logger.error(f"HISAT2 alignment failed with return code {e.returncode}")
        if e.stderr:
            logger.error(f"Error output: {e.stderr.decode('utf-8')}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during HISAT2 alignment: {e}")
        return False


def process_study_hisat2(
    accession_id: str,
    trimmed_dir: Path,
    output_dir: Path,
    genome_index: Path,
    threads: int = 4
) -> Optional[Path]:
    """
    Process a single study by aligning its trimmed FASTQ files.

    Args:
        accession_id: Study accession ID
        trimmed_dir: Directory containing trimmed FASTQ files
        output_dir: Directory to write BAM files
        genome_index: Path to HISAT2 genome index
        threads: Number of threads

    Returns:
        Path to output BAM file if successful, None otherwise.
    """
    r1_file = trimmed_dir / f"{accession_id}_R1_trimmed.fastq.gz"
    r2_file = trimmed_dir / f"{accession_id}_R2_trimmed.fastq.gz"

    if not r1_file.exists() or not r2_file.exists():
        logger.warning(f"Trimmed files not found for {accession_id}. Skipping.")
        return None

    output_bam = output_dir / f"{accession_id}.bam"

    success = run_hisat2(
        input_r1=r1_file,
        input_r2=r2_file,
        genome_index=genome_index,
        output_bam=output_bam,
        threads=threads
    )

    if success:
        record_provenance(
            artifact_type=ArtifactType.ALIGNED_BAM,
            artifact_path=str(output_bam),
            source_files=[str(r1_file), str(r2_file)],
            tool_name="hisat2",
            tool_version="unknown",
            parameters={"threads": threads}
        )
        return output_bam
    return None


def main():
    """Main entry point for HISAT2 preprocessing."""
    parser = argparse.ArgumentParser(description="Align trimmed FASTQ files using HISAT2")
    parser.add_argument(
        "--genome-index",
        type=str,
        required=True,
        help="Path to HISAT2 genome index prefix"
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=4,
        help="Number of CPU threads (default: 4)"
    )
    parser.add_argument(
        "--accession-ids",
        type=str,
        nargs="*",
        help="Specific accession IDs to process (optional, processes all if not provided)"
    )
    parser.add_argument(
        "--trimmed-dir",
        type=str,
        default=None,
        help="Directory containing trimmed FASTQ files (default: auto-detected)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory for output BAM files (default: auto-detected)"
    )

    args = parser.parse_args()

    # Check synthetic mode
    if is_synthetic_mode():
        logger.info("Synthetic mode detected. Skipping HISAT2 alignment.")
        print("SKIPPED: Synthetic mode active. No real data to align.")
        return 0

    # Check HISAT2 availability
    if not check_hisat2_available():
        logger.error("HISAT2 is not available. Please install it first.")
        return 1

    # Resolve paths
    data_path = get_data_path()
    trimmed_dir = Path(args.trimmed_dir) if args.trimmed_dir else data_path / "processed" / "trimmed"
    output_dir = Path(args.output_dir) if args.output_dir else data_path / "processed" / "aligned"
    genome_index = Path(args.genome_index)

    if not trimmed_dir.exists():
        logger.error(f"Trimmed directory not found: {trimmed_dir}")
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine which studies to process
    accession_ids = args.accession_ids
    if not accession_ids:
        # Find all trimmed FASTQ pairs
        r1_files = list(trimmed_dir.glob("*_R1_trimmed.fastq.gz"))
        accession_ids = [f.stem.replace("_R1_trimmed", "") for f in r1_files]
        logger.info(f"Found {len(accession_ids)} studies to process.")

    if not accession_ids:
        logger.warning("No studies found to process.")
        return 0

    success_count = 0
    failure_count = 0

    for accession_id in accession_ids:
        logger.info(f"Processing {accession_id}...")
        result = process_study_hisat2(
            accession_id=accession_id,
            trimmed_dir=trimmed_dir,
            output_dir=output_dir,
            genome_index=genome_index,
            threads=args.threads
        )
        if result:
            success_count += 1
        else:
            failure_count += 1

    logger.info(f"Alignment complete: {success_count} successful, {failure_count} failed.")

    # Write summary report
    summary = {
        "timestamp": datetime.now().isoformat(),
        "tool": "hisat2",
        "genome_index": str(genome_index),
        "threads": args.threads,
        "total_processed": len(accession_ids),
        "successful": success_count,
        "failed": failure_count,
        "outputs": [
            str(output_dir / f"{aid}.bam")
            for aid in accession_ids
            if (output_dir / f"{aid}.bam").exists()
        ]
    }

    summary_path = data_path / "manifests" / "hisat2_alignment_report.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Summary report written to {summary_path}")

    return 0 if failure_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
