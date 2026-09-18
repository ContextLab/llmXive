"""
Checksum generation and management for synthetic artifacts.

This script provides utilities to generate SHA256 checksums for data artifacts
to ensure integrity and reproducibility of synthetic outputs.
"""
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

# Import existing checksum manager utilities
from data.checksum_manager import calculate_sha256, generate_checksums, save_checksums, load_checksums, verify_integrity


def generate_artifact_checksums(data_dir: Path, output_file: Optional[Path] = None) -> Dict:
    """
    Generate checksums for all artifacts in the data directory.

    Args:
        data_dir: Path to the data directory containing artifacts.
        output_file: Optional path to save the checksum manifest.

    Returns:
        Dictionary containing checksums and metadata.
    """
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory does not exist: {data_dir}")

    checksums = generate_checksums(data_dir)

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_directory": str(data_dir),
        "checksums": checksums,
        "total_files": len(checksums)
    }

    if output_file:
        save_checksums(manifest, output_file)

    return manifest


def verify_artifact_integrity(checksum_file: Path) -> bool:
    """
    Verify integrity of data artifacts against stored checksums.

    Args:
        checksum_file: Path to the checksum manifest file.

    Returns:
        True if all artifacts pass verification, False otherwise.
    """
    if not checksum_file.exists():
        raise FileNotFoundError(f"Checksum file does not exist: {checksum_file}")

    manifest = load_checksums(checksum_file)
    data_dir = Path(manifest["data_directory"])

    return verify_integrity(data_dir, manifest["checksums"])


def main():
    """Main entry point for checksum generation and verification."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate and verify checksums for data artifacts."
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data",
        help="Path to the data directory (default: data)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/checksum_manifest.json",
        help="Path to save checksum manifest (default: data/checksum_manifest.json)"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify existing checksums instead of generating new ones"
    )
    parser.add_argument(
        "--checksum-file",
        type=str,
        default="data/checksum_manifest.json",
        help="Path to checksum manifest for verification"
    )

    args = parser.parse_args()
    data_dir = Path(args.data_dir)
    output_file = Path(args.output)
    checksum_file = Path(args.checksum_file)

    try:
        if args.verify:
            if not checksum_file.exists():
                print(f"Error: Checksum file not found: {checksum_file}")
                sys.exit(1)

            print(f"Verifying integrity of artifacts in {data_dir}...")
            is_valid = verify_artifact_integrity(checksum_file)

            if is_valid:
                print("✓ All artifacts verified successfully.")
                sys.exit(0)
            else:
                print("✗ Verification failed: One or more artifacts are corrupted.")
                sys.exit(1)
        else:
            print(f"Generating checksums for artifacts in {data_dir}...")
            manifest = generate_artifact_checksums(data_dir, output_file)

            print(f"✓ Generated checksums for {manifest['total_files']} files.")
            print(f"  Manifest saved to: {output_file}")
            sys.exit(0)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()