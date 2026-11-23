"""
Script to calculate checksums for all downloaded datasets and update the project state.
This script is designed to run after data ingestion tasks (T011, T012) are complete.
"""
import sys
import os
from pathlib import Path
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.checksum_manager import calculate_batch_checksums
from src.utils.logging import setup_logger, log_info, log_error

def main():
    parser = argparse.ArgumentParser(description="Calculate checksums for dataset artifacts.")
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default="data/processed",
        help="Directory containing processed dataset files."
    )
    parser.add_argument(
        "--checksum-file", 
        type=str, 
        default="data/checksums.json",
        help="Path to store the checksums."
    )
    parser.add_argument(
        "--state-file", 
        type=str, 
        default="state/projects/PROJ-088-predicting-reaction-mechanisms-from-spec.yaml",
        help="Path to the project state YAML file."
    )
    args = parser.parse_args()

    setup_logger(level="INFO")
    log_info(f"Starting checksum calculation for project PROJ-088")

    # Define expected output files from T011, T012, T013b
    # Based on task descriptions:
    # T011 (NIST) -> likely data/raw/nist_*.json or similar, but T013b merges to fingerprints.parquet
    # T013b explicitly outputs: data/processed/fingerprints.parquet
    # We assume T011/T012 might have intermediate raw files if they exist, 
    # but the primary artifact for checksumming as per T017 is the processed output.
    # To be robust, we check for common output patterns.
    
    output_dir = Path(args.output_dir)
    if not output_dir.exists():
        log_error(f"Output directory {output_dir} does not exist. Has T013b run?")
        sys.exit(1)

    # Collect files to checksum
    files_to_check = []
    
    # Look for the primary fingerprint file
    fingerprint_file = output_dir / "fingerprints.parquet"
    if fingerprint_file.exists():
        files_to_check.append(str(fingerprint_file))
    
    # Check for intermediate raw data files if they exist in data/raw
    raw_dir = Path("data/raw")
    if raw_dir.exists():
        for f in raw_dir.glob("*"):
            if f.is_file():
                files_to_check.append(str(f))

    # Also check data/reference if T033a/b might have created files (though T017 is US1, 
    # we might want to checksum any existing reference data if present)
    ref_dir = Path("data/reference")
    if ref_dir.exists():
        for f in ref_dir.glob("*.json"):
            files_to_check.append(str(f))

    if not files_to_check:
        log_error("No dataset files found to checksum. Please ensure data ingestion tasks have completed.")
        sys.exit(1)

    log_info(f"Found {len(files_to_check)} files to checksum.")
    
    results = calculate_batch_checksums(
        file_paths=files_to_check,
        checksums_file=args.checksum_file,
        state_file=args.state_file
    )

    if results:
        log_info(f"Successfully calculated checksums for {len(results)} files.")
        log_info(f"Checksums saved to {args.checksum_file}")
        log_info(f"Project state updated at {args.state_file}")
    else:
        log_error("No checksums were calculated successfully.")
        sys.exit(1)

if __name__ == "__main__":
    main()
