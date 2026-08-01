"""
CLI script to run metadata verification.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.data.verify_metadata import main

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Verify metadata for downloaded FASTQ files")
    parser.add_argument("--mode", choices=["real", "synthetic"], default="real", help="Mode of operation")
    parser.add_argument("--fastq-dir", help="Directory containing FASTQ files")
    parser.add_argument("--manifest-path", help="Path to the manifest file")
    parser.add_argument("--synthetic-manifest-path", help="Path to the synthetic manifest")

    args = parser.parse_args()

    exit_code = main(
        mode=args.mode,
        fastq_dir=args.fastq_dir,
        manifest_path=args.manifest_path,
        synthetic_manifest_path=args.synthetic_manifest_path
    )
    sys.exit(exit_code)