"""
Checksum generation and management for project artifacts.

This module provides functionality to:
- Compute SHA256 checksums for files in the data directory
- Generate and manage a checksum registry file
- Update the project state YAML with artifact hashes
- Verify existing checksums against current file contents
"""
import hashlib
import os
import json
import yaml
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def compute_file_checksum(file_path: Path) -> str:
    """
    Compute SHA256 checksum of a file.

    Args:
        file_path: Path to the file

    Returns:
        Hexadecimal string of the SHA256 hash
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error computing checksum for {file_path}: {e}")
        raise


def generate_checksum_file(data_dir: Path, output_path: Path) -> Dict[str, str]:
    """
    Generate checksums for all files in the data directory.

    Args:
        data_dir: Root directory containing data files
        output_path: Path to write the checksum JSON file

    Returns:
        Dictionary mapping relative file paths to their checksums
    """
    checksums = {}

    for root, _, files in os.walk(data_dir):
        for file in files:
            file_path = Path(root) / file
            relative_path = file_path.relative_to(data_dir)
            checksum = compute_file_checksum(file_path)
            checksums[str(relative_path)] = checksum
            logger.info(f"Computed checksum for {relative_path}: {checksum[:16]}...")

    # Write checksums to file
    with open(output_path, 'w') as f:
        json.dump(checksums, f, indent=2)

    logger.info(f"Checksum file written to {output_path}")
    return checksums


def verify_checksums(checksum_file: Path, data_dir: Path) -> Tuple[bool, List[str]]:
    """
    Verify that files match their recorded checksums.

    Args:
        checksum_file: Path to the JSON file containing checksums
        data_dir: Root directory containing data files

    Returns:
        Tuple of (all_valid, list_of_mismatched_files)
    """
    with open(checksum_file, 'r') as f:
        recorded_checksums = json.load(f)

    mismatches = []
    all_valid = True

    for relative_path, expected_checksum in recorded_checksums.items():
        file_path = data_dir / relative_path
        if not file_path.exists():
            logger.warning(f"File not found: {relative_path}")
            mismatches.append(relative_path)
            all_valid = False
            continue

        actual_checksum = compute_file_checksum(file_path)
        if actual_checksum != expected_checksum:
            logger.warning(f"Checksum mismatch for {relative_path}")
            mismatches.append(relative_path)
            all_valid = False

    return all_valid, mismatches


def verify_single_file(file_path: Path, expected_checksum: str) -> bool:
    """
    Verify a single file against an expected checksum.

    Args:
        file_path: Path to the file
        expected_checksum: Expected SHA256 hash

    Returns:
        True if checksum matches, False otherwise
    """
    actual_checksum = compute_file_checksum(file_path)
    return actual_checksum == expected_checksum


def setup_data_directories(project_root: Path) -> None:
    """
    Ensure all required data directories exist.

    Args:
        project_root: Root directory of the project
    """
    data_dirs = [
        project_root / "data",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "analysis"
    ]

    for directory in data_dirs:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory exists: {directory}")


def register_artifacts(project_root: Path, state_file: Path) -> Dict[str, str]:
    """
    Update the project state YAML file with current artifact checksums.

    Args:
        project_root: Root directory of the project
        state_file: Path to the project state YAML file

    Returns:
        Dictionary of updated artifact hashes
    """
    data_dir = project_root / "data"
    checksums = generate_checksum_file(data_dir, project_root / "data" / "checksums.json")

    # Load or create state file
    if state_file.exists():
        with open(state_file, 'r') as f:
            state = yaml.safe_load(f) or {}
    else:
        state = {}

    # Ensure artifact_hashes key exists
    if 'artifact_hashes' not in state:
        state['artifact_hashes'] = {}

    # Update with new checksums
    state['artifact_hashes'].update(checksums)

    # Write updated state
    with open(state_file, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Updated artifact hashes in {state_file}")
    return state['artifact_hashes']


def main():
    """Main entry point for the checksum utility."""
    parser = argparse.ArgumentParser(
        description='Generate and manage checksums for project artifacts'
    )
    parser.add_argument(
        '--update',
        action='store_true',
        help='Update the project state file with new checksums'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify existing checksums against current files'
    )
    parser.add_argument(
        '--project-root',
        type=Path,
        default=Path.cwd(),
        help='Root directory of the project (default: current directory)'
    )

    args = parser.parse_args()

    # Ensure data directories exist
    setup_data_directories(args.project_root)

    if args.update:
        state_file = args.project_root / "state" / "projects" / "PROJ-440-investigating-the-impact-of-network-stru.yaml"
        if not state_file.parent.exists():
            state_file.parent.mkdir(parents=True, exist_ok=True)

        if not state_file.exists():
            logger.info(f"Creating new state file at {state_file}")
            # Create initial state structure
            state = {
                'project_id': 'PROJ-440-investigating-the-impact-of-network-stru',
                'artifact_hashes': {}
            }
            with open(state_file, 'w') as f:
                yaml.dump(state, f, default_flow_style=False)

        artifacts = register_artifacts(args.project_root, state_file)
        logger.info(f"Registered {len(artifacts)} artifacts")

    elif args.verify:
        checksum_file = args.project_root / "data" / "checksums.json"
        data_dir = args.project_root / "data"

        if not checksum_file.exists():
            logger.error(f"Checksum file not found: {checksum_file}")
            logger.info("Run with --update first to generate checksums")
            return

        all_valid, mismatches = verify_checksums(checksum_file, data_dir)

        if all_valid:
            logger.info("All checksums verified successfully")
        else:
            logger.error(f"Checksum verification failed for {len(mismatches)} files:")
            for mismatch in mismatches:
                logger.error(f"  - {mismatch}")

    else:
        # Default: generate checksums without updating state
        data_dir = args.project_root / "data"
        output_path = data_dir / "checksums.json"
        checksums = generate_checksum_file(data_dir, output_path)
        logger.info(f"Generated {len(checksums)} checksums")


if __name__ == "__main__":
    main()