"""
Preprocessing wrapper for fastp to trim and filter FASTQ files.

This module implements Task T012a:
- Runs fastp on downloaded FASTQ files from data/raw/
- Outputs trimmed FASTQ to data/processed/trimmed/
- Uses CPU-optimized, streaming modes
- Validates fastp installation before execution
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.config import get_data_path
from src.utils.logger import get_logger
from src.utils.provenance import (
    get_provenance_tracker,
    record_provenance,
    ArtifactType,
    ProvenanceRecord
)
from src.utils.schemas import ManifestEntry, DataManifest

logger = get_logger(__name__)

def check_fastp_available() -> Tuple[bool, Optional[str]]:
    """
    Check if fastp is installed and available in PATH.
    
    Returns:
        Tuple of (is_available, version_string or None)
    """
    try:
        result = subprocess.run(
            ["fastp", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            logger.info(f"fastp is available: {version}")
            return True, version
        else:
            logger.error(f"fastp returned error code: {result.returncode}")
            return False, None
    except FileNotFoundError:
        logger.error("fastp not found in PATH. Please install fastp first (see T003b-fastp)")
        return False, None
    except subprocess.TimeoutExpired:
        logger.error("fastp version check timed out")
        return False, None

def run_fastp(
    input_fastq: Path,
    output_fastq: Path,
    output_json: Path,
    threads: int = 4,
    compression_level: int = 6,
    cut_front: bool = True,
    cut_tail: bool = True,
    cut_window_size: int = 4,
    cut_min_len: int = 50,
    detect_adapter: bool = True,
    adapter_sequence: Optional[str] = None
) -> bool:
    """
    Run fastp on a single FASTQ file.
    
    Args:
        input_fastq: Path to input FASTQ file (can be .gz)
        output_fastq: Path for output trimmed FASTQ file
        output_json: Path for fastp JSON report
        threads: Number of CPU threads to use
        compression_level: gzip compression level (1-9)
        cut_front: Cut bases from the front of reads
        cut_tail: Cut bases from the tail of reads
        cut_window_size: Window size for sliding window trimming
        cut_min_len: Minimum read length to keep
        detect_adapter: Auto-detect adapter sequences
        adapter_sequence: Optional specific adapter sequence
        
    Returns:
        True if successful, False otherwise
    """
    # Ensure output directory exists
    output_fastq.parent.mkdir(parents=True, exist_ok=True)
    
    # Build fastp command with CPU-optimized, streaming parameters
    cmd = [
        "fastp",
        "-i", str(input_fastq),
        "-o", str(output_fastq),
        "-j", str(output_json),
        "-w", str(threads),  # threads
        "--thread_limit", str(threads),
        "--compression", str(compression_level),
        "--cut_front" if cut_front else "",
        "--cut_tail" if cut_tail else "",
        "--cut_window_size", str(cut_window_size),
        "--cut_min_len", str(cut_min_len),
        "--detect_adapter_for_pe" if detect_adapter else "",
        "--length_required", str(cut_min_len),
        "--disable_trim_poly_g",  # Disable poly-G trimming for non-Illumina data
        "--overrepresentation_analysis",
        "--qualified_quality_phred", "20",
        "--unqualified_percent_limit", "40",
        "--n_base_limit", "5",
        "--low_complexity_filter",
        "--json", str(output_json),
        "--html", str(output_json).replace(".json", ".html")
    ]
    
    # Remove empty strings from command
    cmd = [arg for arg in cmd if arg]
    
    # Add adapter sequence if provided
    if adapter_sequence:
        cmd.extend(["--adapter_sequence", adapter_sequence])
    
    logger.info(f"Running fastp command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout per file
        )
        
        if result.returncode != 0:
            logger.error(f"fastp failed with return code {result.returncode}")
            logger.error(f"stdout: {result.stdout}")
            logger.error(f"stderr: {result.stderr}")
            return False
        
        # Verify output file was created
        if not output_fastq.exists():
            logger.error(f"Output file {output_fastq} was not created")
            return False
        
        logger.info(f"fastp completed successfully for {input_fastq.name}")
        logger.info(f"Output written to {output_fastq}")
        
        return True
        
    except subprocess.TimeoutExpired:
        logger.error(f"fastp timed out for {input_fastq}")
        return False
    except Exception as e:
        logger.error(f"Error running fastp: {str(e)}")
        return False

def process_fastq_file(
    input_path: Path,
    output_dir: Path,
    threads: int = 4
) -> Optional[Dict]:
    """
    Process a single FASTQ file through fastp.
    
    Args:
        input_path: Path to input FASTQ file
        output_dir: Directory for output files
        threads: Number of threads to use
        
    Returns:
        Dict with processing results or None if failed
    """
    # Extract accession ID from filename
    accession_id = input_path.stem
    if accession_id.endswith('_R1'):
        accession_id = accession_id[:-3]
    elif accession_id.endswith('_R2'):
        accession_id = accession_id[:-3]
    
    # Define output paths
    output_fastq = output_dir / f"{accession_id}_R1_trimmed.fastq.gz"
    output_json = output_dir / f"{accession_id}_fastp_report.json"
    
    logger.info(f"Processing {input_path.name} -> {output_fastq.name}")
    
    success = run_fastp(
        input_fastq=input_path,
        output_fastq=output_fastq,
        output_json=output_json,
        threads=threads
    )
    
    if not success:
        logger.error(f"Failed to process {input_path.name}")
        return None
    
    # Calculate checksum of output
    import hashlib
    sha256_hash = hashlib.sha256()
    with open(output_fastq, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    checksum = sha256_hash.hexdigest()
    
    # Parse fastp JSON report for metrics
    metrics = {}
    try:
        with open(output_json, 'r') as f:
            report = json.load(f)
            metrics = {
                "total_reads_before": report.get("summary", {}).get("before_filtering", {}).get("total_reads", 0),
                "total_reads_after": report.get("summary", {}).get("after_filtering", {}).get("total_reads", 0),
                "read1_filtered": report.get("summary", {}).get("after_filtering", {}).get("read1_filtered", 0),
                "quality_filtered": report.get("summary", {}).get("after_filtering", {}).get("quality_filtered", 0),
                "adapter_filtered": report.get("summary", {}).get("after_filtering", {}).get("adapter_filtered", 0),
            }
    except Exception as e:
        logger.warning(f"Could not parse fastp report: {e}")
    
    return {
        "accession_id": accession_id,
        "input_file": str(input_path),
        "output_file": str(output_fastq),
        "report_file": str(output_json),
        "checksum": checksum,
        "metrics": metrics,
        "timestamp": datetime.utcnow().isoformat()
    }

def main():
    """
    Main entry point for fastp preprocessing.
    
    Usage:
        python -m src.data.preprocess_fastp --input data/raw/GSM1234567_1.fastq.gz --output-dir data/processed/trimmed
        python -m src.data.preprocess_fastp --input-dir data/raw/ --output-dir data/processed/trimmed
    """
    parser = argparse.ArgumentParser(description="Preprocess FASTQ files with fastp")
    parser.add_argument(
        "--input", "-i",
        type=Path,
        help="Path to single input FASTQ file"
    )
    parser.add_argument(
        "--input-dir", "-d",
        type=Path,
        help="Directory containing input FASTQ files"
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=None,
        help="Output directory for trimmed FASTQ files (default: data/processed/trimmed)"
    )
    parser.add_argument(
        "--threads", "-t",
        type=int,
        default=4,
        help="Number of CPU threads (default: 4)"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["real", "synthetic"],
        default="real",
        help="Processing mode (default: real)"
    )
    
    args = parser.parse_args()
    
    # Check fastp availability
    is_available, version = check_fastp_available()
    if not is_available:
        logger.error("fastp is not available. Please install it first.")
        sys.exit(1)
    
    # Determine output directory
    if args.output_dir is None:
        data_path = get_data_path()
        args.output_dir = data_path / "processed" / "trimmed"
    
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Collect input files
    input_files: List[Path] = []
    if args.input:
        if not args.input.exists():
            logger.error(f"Input file not found: {args.input}")
            sys.exit(1)
        input_files.append(args.input)
    elif args.input_dir:
        if not args.input_dir.exists():
            logger.error(f"Input directory not found: {args.input_dir}")
            sys.exit(1)
        # Find all FASTQ files (including .gz)
        input_files = list(args.input_dir.glob("*.fastq.gz")) + list(args.input_dir.glob("*.fq.gz"))
        if not input_files:
            logger.warning(f"No FASTQ files found in {args.input_dir}")
            sys.exit(0)
    else:
        logger.error("Either --input or --input-dir must be specified")
        sys.exit(1)
    
    logger.info(f"Processing {len(input_files)} FASTQ file(s) with {args.threads} threads")
    
    # Process each file
    results = []
    for input_file in input_files:
        result = process_fastq_file(
            input_path=input_file,
            output_dir=args.output_dir,
            threads=args.threads
        )
        if result:
            results.append(result)
    
    # Write manifest of processed files
    manifest_path = args.output_dir.parent / "trimmed_manifest.json"
    manifest = {
        "created_at": datetime.utcnow().isoformat(),
        "tool": "fastp",
        "tool_version": version,
        "mode": args.mode,
        "threads": args.threads,
        "processed_files": results
    }
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Processed {len(results)} files. Manifest written to {manifest_path}")
    
    # Record provenance
    if results:
        tracker = get_provenance_tracker()
        for result in results:
            record_provenance(
                tracker=tracker,
                artifact_type=ArtifactType.TRIMMED_FASTQ,
                artifact_id=result["accession_id"],
                source_ids=[result["input_file"]],
                output_path=result["output_file"],
                metadata=result
            )
    
    logger.info("Preprocessing complete")

if __name__ == "__main__":
    main()
