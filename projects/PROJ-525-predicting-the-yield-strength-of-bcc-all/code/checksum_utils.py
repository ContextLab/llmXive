"""
Utility script for generating and verifying checksums for data directories.
This script helps ensure data integrity throughout the research pipeline.
"""
import sys
import argparse
from pathlib import Path
from config import (
    DATA_RAW_DIR,
    DATA_PROCESSED_DIR,
    DATA_LOGS_DIR,
    compute_directory_checksum,
    save_checksums,
    verify_checksums
)

def main():
    parser = argparse.ArgumentParser(description="Data directory checksum utility")
    parser.add_argument(
        "action",
        choices=["generate", "verify"],
        help="Action to perform: generate or verify checksums"
    )
    parser.add_argument(
        "--dir",
        type=str,
        choices=["raw", "processed", "logs"],
        default="raw",
        help="Which data directory to operate on (default: raw)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Custom output path for checksums (optional)"
    )

    args = parser.parse_args()

    # Map directory argument to actual path
    dir_map = {
        "raw": DATA_RAW_DIR,
        "processed": DATA_PROCESSED_DIR,
        "logs": DATA_LOGS_DIR
    }
    target_dir = dir_map[args.dir]

    if not target_dir.exists():
        print(f"Error: Directory {target_dir} does not exist.")
        sys.exit(1)

    if args.action == "generate":
        print(f"Generating checksums for {target_dir}...")
        checksums = compute_directory_checksum(target_dir)
        
        if not checksums:
            print("No files found to checksum.")
            sys.exit(0)

        # Determine output path
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = target_dir.parent / f"{args.dir}_checksums.json"

        save_checksums(checksums, output_path)
        print(f"Checksums saved to {output_path}")
        print(f"Total files checksummed: {len(checksums)}")

    elif args.action == "verify":
        if args.output:
            checksum_file = Path(args.output)
        else:
            checksum_file = target_dir.parent / f"{args.dir}_checksums.json"

        if not checksum_file.exists():
            print(f"Error: Checksum file {checksum_file} does not exist.")
            print("Run 'generate' first to create checksums.")
            sys.exit(1)

        print(f"Verifying checksums for {target_dir} against {checksum_file}...")
        is_valid = verify_checksums(target_dir, checksum_file)
        
        if not is_valid:
            print("Verification failed!")
            sys.exit(1)
        else:
            print("Verification successful!")

if __name__ == "__main__":
    main()
