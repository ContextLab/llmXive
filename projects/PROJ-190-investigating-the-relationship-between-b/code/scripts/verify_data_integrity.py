import argparse
import sys
from pathlib import Path
import json

from utils.checksum import (
    compute_directory_checksums,
    save_checksums,
    load_checksums,
    verify_directory_against_checksums,
)
from utils.logging import setup_logging, get_logger, info, error, warning

logger = get_logger(__name__)

def main():
    parser = argparse.ArgumentParser(
        description="Verify data integrity using SHA-256 checksums."
    )
    parser.add_argument(
        "action",
        choices=["create", "verify"],
        help="Action to perform: create checksums or verify against existing.",
    )
    parser.add_argument(
        "--path",
        type=str,
        required=True,
        help="Path to the directory to process.",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Path for the checksum JSON file (required for 'create').",
    )
    parser.add_argument(
        "--input",
        type=str,
        help="Path to the checksum JSON file (required for 'verify').",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(level="INFO")

    dir_path = Path(args.path)
    if not dir_path.exists():
        error(f"Directory does not exist: {dir_path}")
        sys.exit(1)

    if args.action == "create":
        if not args.output:
            error("Output path (--output) is required for 'create' action.")
            sys.exit(1)

        info(f"Creating checksums for {dir_path}...")
        try:
            checksums = compute_directory_checksums(dir_path, recursive=True)
            save_checksums(checksums, args.output)
            info(f"Successfully created {len(checksums)} checksums.")
        except Exception as e:
            error(f"Failed to create checksums: {e}")
            sys.exit(1)

    elif args.action == "verify":
        if not args.input:
            error("Input path (--input) is required for 'verify' action.")
            sys.exit(1)

        input_path = Path(args.input)
        if not input_path.exists():
            error(f"Checksum file does not exist: {input_path}")
            sys.exit(1)

        info(f"Verifying {dir_path} against {input_path}...")
        try:
            success = verify_directory_against_checksums(dir_path, input_path)
            if success:
                info("Verification successful.")
                sys.exit(0)
            else:
                error("Verification failed. Data integrity compromised.")
                sys.exit(1)
        except Exception as e:
            error(f"Verification error: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
