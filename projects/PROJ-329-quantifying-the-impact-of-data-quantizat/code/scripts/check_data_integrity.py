"""
CLI Script: Check Data Integrity

This script scans the data/raw and data/processed directories,
computes checksums, and verifies them against the recorded state.
It can also be used to record the current state.
"""
import argparse
import logging
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.data_hygiene import (
    get_data_directories,
    compute_checksums_for_directory,
    verify_data_integrity,
    record_directory_state,
    main as hygiene_main
)

logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(
        description="Data Integrity Checker for PROJ-329",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
          # Compute and print checksums
          python scripts/check_data_integrity.py --action compute
          
          # Verify data against stored state
          python scripts/check_data_integrity.py --action verify
          
          # Record current state as the new baseline
          python scripts/check_data_integrity.py --action record
        """
    )
    parser.add_argument(
        "--action",
        choices=["compute", "verify", "record"],
        default="compute",
        help="Action to perform"
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=None,
        help="Path to project root. Defaults to script's parent directory."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    project_root = Path(args.project_root) if args.project_root else Path(__file__).resolve().parent.parent
    
    logger.info(f"Project root: {project_root}")
    logger.info(f"Action: {args.action}")

    raw_dir, processed_dir = get_data_directories(project_root)
    
    logger.info(f"Scanning {raw_dir}...")
    raw_checksums = compute_checksums_for_directory(raw_dir)
    logger.info(f"Scanning {processed_dir}...")
    processed_checksums = compute_checksums_for_directory(processed_dir)

    if args.action == "compute":
        print(f"\n--- Checksums for {raw_dir} ---")
        if not raw_checksums:
            print("  (No files found)")
        for path, hash_val in raw_checksums.items():
            print(f"  {path}: {hash_val[:32]}...")
        
        print(f"\n--- Checksums for {processed_dir} ---")
        if not processed_checksums:
            print("  (No files found)")
        for path, hash_val in processed_checksums.items():
            print(f"  {path}: {hash_val[:32]}...")

    elif args.action == "verify":
        is_valid, errors = verify_data_integrity(raw_checksums, processed_checksums)
        if is_valid:
            print("\n✓ Data integrity verified successfully.")
            sys.exit(0)
        else:
            print("\n✗ Data integrity check FAILED.")
            for err in errors:
                print(f"  - {err}")
            sys.exit(1)

    elif args.action == "record":
        success = record_directory_state(raw_checksums, processed_checksums)
        if success:
            print("\n✓ Directory state recorded successfully.")
            sys.exit(0)
        else:
            print("\n✗ Failed to record directory state.")
            sys.exit(1)

if __name__ == "__main__":
    main()