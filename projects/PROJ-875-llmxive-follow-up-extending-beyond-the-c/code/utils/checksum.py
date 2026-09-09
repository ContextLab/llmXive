"""
utils/checksum.py - SHA-256 Checksum Generation for Data Artifacts

Generates SHA-256 checksums for all files in a specified directory
and outputs the results to a YAML manifest file.

Implements Constitution Principle III: Data Integrity Verification.
"""
import os
import hashlib
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any
import yaml
from datetime import datetime

# Configure logging to use the project's global logger if available,
# otherwise fallback to standard logging.
try:
    from logger import get_logger
    logger = get_logger("checksum")
except ImportError:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)


def calculate_sha256(file_path: Path) -> str:
    """
    Calculate the SHA-256 hash of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files efficiently
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except IOError as e:
        logger.error(f"IO Error reading {file_path}: {e}")
        raise


def generate_checksums(input_dir: Path) -> Dict[str, str]:
    """
    Generate checksums for all files in the input directory recursively.

    Args:
        input_dir: Path to the directory to scan.

    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes.

    Raises:
        NotADirectoryError: If input_dir is not a directory.
    """
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {input_dir}")

    checksums = {}
    logger.info(f"Scanning directory: {input_dir}")

    for file_path in input_dir.rglob("*"):
        if file_path.is_file():
            try:
                rel_path = str(file_path.relative_to(input_dir))
                checksum = calculate_sha256(file_path)
                checksums[rel_path] = checksum
                logger.debug(f"Checksummed: {rel_path} -> {checksum[:16]}...")
            except Exception as e:
                logger.error(f"Failed to checksum {file_path}: {e}")
                # Fail loudly as per constraints
                raise

    return checksums


def save_checksums(checksums: Dict[str, str], output_path: Path) -> None:
    """
    Save the checksums to a YAML file.

    Args:
        checksums: Dictionary of checksums.
        output_path: Path to the output YAML file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = {
        "generated_at": datetime.utcnow().isoformat(),
        "algorithm": "SHA-256",
        "file_count": len(checksums),
        "checksums": checksums
    }

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Checksums saved to: {output_path}")
    except IOError as e:
        logger.error(f"Failed to write output file {output_path}: {e}")
        raise


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate SHA-256 checksums for data artifacts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Example:
          python utils/checksum.py --input data/processed/ --output state/checksums.yaml
        """
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        required=True,
        help="Input directory to scan for files."
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        required=True,
        help="Output path for the YAML checksum manifest."
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging."
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        logger.error(f"Input directory does not exist: {input_path}")
        return 1

    try:
        checksums = generate_checksums(input_path)
        if not checksums:
            logger.warning(f"No files found in {input_path} to checksum.")
        save_checksums(checksums, output_path)
        return 0
    except Exception as e:
        logger.critical(f"Checksum generation failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
