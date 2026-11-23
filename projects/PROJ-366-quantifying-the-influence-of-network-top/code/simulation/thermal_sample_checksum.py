"""
Thermal Sample Checksum Generation and Verification Module.

This module implements checksum generation for serialized ThermalSample objects
to ensure data integrity throughout the pipeline. It provides functions to:
- Calculate SHA-256 checksums for files
- Find all thermal sample files in a directory
- Generate checksums for all thermal samples
- Save checksums to a manifest file (data/checksums.json)
- Load and verify checksums against the manifest
"""

import json
import hashlib
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


def calculate_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Calculate the checksum of a file.

    Args:
        file_path: Path to the file to checksum
        algorithm: Hash algorithm to use (default: sha256)

    Returns:
        Hexadecimal string of the file's checksum

    Raises:
        FileNotFoundError: If the file does not exist
        IOError: If the file cannot be read
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_obj = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hash_obj.update(chunk)

    return hash_obj.hexdigest()


def find_thermal_sample_files(directory: Path, extensions: List[str] = None) -> List[Path]:
    """
    Find all thermal sample files in a directory.

    Args:
        directory: Directory to search
        extensions: List of file extensions to look for (default: ['.pkl', '.pickle', '.parquet'])

    Returns:
        List of Path objects for matching files
    """
    if extensions is None:
        extensions = [".pkl", ".pickle", ".parquet"]

    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return []

    files = []
    for ext in extensions:
        files.extend(directory.glob(f"*{ext}"))

    # Also look for JSON files that might contain thermal samples
    files.extend(directory.glob("*.json"))

    return sorted(files)


def generate_checksums_for_thermal_samples(
    directory: Path,
    output_path: Optional[Path] = None
) -> Dict[str, str]:
    """
    Generate checksums for all thermal sample files in a directory.

    Args:
        directory: Directory containing thermal sample files
        output_path: Optional path to save the checksum manifest

    Returns:
        Dictionary mapping file names to their checksums
    """
    files = find_thermal_sample_files(directory)

    if not files:
        logger.warning(f"No thermal sample files found in {directory}")
        return {}

    checksums = {}
    for file_path in files:
        try:
            checksum = calculate_file_checksum(file_path)
            relative_path = str(file_path.relative_to(directory))
            checksums[relative_path] = checksum
            logger.debug(f"Generated checksum for {relative_path}: {checksum[:16]}...")
        except Exception as e:
            logger.error(f"Failed to generate checksum for {file_path}: {e}")

    if output_path:
        save_checksum_manifest(checksums, output_path)

    return checksums


def save_checksum_manifest(checksums: Dict[str, str], output_path: Path) -> None:
    """
    Save checksums to a JSON manifest file.

    Args:
        checksums: Dictionary mapping file names to checksums
        output_path: Path to save the manifest
    """
    manifest = {
        "checksums": checksums,
        "algorithm": "sha256",
        "generated_at": None  # Could add timestamp if needed
    }

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Saved checksum manifest to {output_path}")


def load_checksum_manifest(manifest_path: Path) -> Dict[str, str]:
    """
    Load checksums from a manifest file.

    Args:
        manifest_path: Path to the manifest file

    Returns:
        Dictionary mapping file names to checksums

    Raises:
        FileNotFoundError: If manifest does not exist
        json.JSONDecodeError: If manifest is invalid JSON
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Checksum manifest not found: {manifest_path}")

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    return manifest.get("checksums", {})


def verify_checksums_against_manifest(
    directory: Path,
    manifest_path: Path
) -> Dict[str, bool]:
    """
    Verify that file checksums match those in the manifest.

    Args:
        directory: Directory containing the files
        manifest_path: Path to the checksum manifest

    Returns:
        Dictionary mapping file names to verification status (True = valid)
    """
    try:
        expected_checksums = load_checksum_manifest(manifest_path)
    except Exception as e:
        logger.error(f"Failed to load manifest: {e}")
        return {}

    results = {}
    for relative_path, expected_checksum in expected_checksums.items():
        file_path = directory / relative_path

        if not file_path.exists():
            logger.warning(f"File not found for verification: {relative_path}")
            results[relative_path] = False
            continue

        try:
            actual_checksum = calculate_file_checksum(file_path)
            is_valid = actual_checksum == expected_checksum
            results[relative_path] = is_valid

            if not is_valid:
                logger.error(
                    f"Checksum mismatch for {relative_path}:\n"
                    f"  Expected: {expected_checksum}\n"
                    f"  Actual:   {actual_checksum}"
                )
            else:
                logger.debug(f"Checksum verified for {relative_path}")

        except Exception as e:
            logger.error(f"Failed to verify checksum for {relative_path}: {e}")
            results[relative_path] = False

    return results


def main():
    """
    Main entry point for checksum generation and verification.

    This function:
    1. Generates checksums for all thermal sample files in data/processed/conductivities/
    2. Saves the manifest to data/checksums.json
    3. Verifies the checksums against the manifest
    4. Prints a summary of the verification results
    """
    import sys
    from config import get_paths

    config = get_paths()
    conductivities_dir = config.get("conductivities_dir", "data/processed/conductivities")
    checksums_path = config.get("checksums_path", "data/checksums.json")

    conductivities_path = Path(conductivities_dir)
    checksums_file = Path(checksums_path)

    logger.info(f"Generating checksums for thermal samples in {conductivities_path}")

    if not conductivities_path.exists():
        logger.error(f"Directory not found: {conductivities_path}")
        sys.exit(1)

    # Generate checksums
    checksums = generate_checksums_for_thermal_samples(conductivities_path, checksums_file)

    if not checksums:
        logger.warning("No checksums generated. Exiting.")
        sys.exit(0)

    logger.info(f"Generated {len(checksums)} checksums")

    # Verify checksums
    logger.info("Verifying checksums...")
    results = verify_checksums_against_manifest(conductivities_path, checksums_file)

    if not results:
        logger.warning("No files to verify.")
        sys.exit(0)

    # Print summary
    valid_count = sum(1 for v in results.values() if v)
    invalid_count = len(results) - valid_count

    print(f"\nChecksum Verification Summary:")
    print(f"  Total files: {len(results)}")
    print(f"  Valid: {valid_count}")
    print(f"  Invalid: {invalid_count}")

    if invalid_count > 0:
        print("\nInvalid files:")
        for file_path, is_valid in results.items():
            if not is_valid:
                print(f"  - {file_path}")
        sys.exit(1)
    else:
        print("\nAll checksums verified successfully!")
        sys.exit(0)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    main()
