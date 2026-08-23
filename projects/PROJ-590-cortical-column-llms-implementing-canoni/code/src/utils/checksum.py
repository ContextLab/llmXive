import os
import hashlib
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_sha256(file_path: Path) -> str:
    """
    Calculate the SHA256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA256 hash.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error hashing file {file_path}: {e}")
        raise

def find_files(root_dir: Path, extensions: Optional[List[str]] = None) -> List[Path]:
    """
    Find all files in a directory recursively.

    Args:
        root_dir: Root directory to search.
        extensions: Optional list of file extensions to filter by (e.g., ['.json', '.yaml']).
                   If None, includes all files.

    Returns:
        List of Path objects for matching files.
    """
    files = []
    if not root_dir.exists():
        logger.warning(f"Directory does not exist: {root_dir}")
        return files

    for path in root_dir.rglob('*'):
        if path.is_file():
            if extensions is None:
                files.append(path)
            else:
                if any(path.suffix == ext for ext in extensions):
                    files.append(path)
    return files

def generate_checksums(
    directories: List[Path],
    output_file: Path,
    extensions: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Generate SHA256 checksums for all files in specified directories and save to a JSON file.

    Args:
        directories: List of directory paths to scan.
        output_file: Path where the checksum JSON file will be written.
        extensions: Optional list of file extensions to include.

    Returns:
        Dictionary mapping relative file paths to their SHA256 hashes.
    """
    checksums = {}
    all_files = []

    for directory in directories:
        if not directory.exists():
            logger.warning(f"Skipping non-existent directory: {directory}")
            continue
        found_files = find_files(directory, extensions)
        all_files.extend(found_files)

    logger.info(f"Found {len(all_files)} files to hash.")

    for file_path in all_files:
        # Calculate relative path from project root (assuming project root is parent of 'code')
        # We store the path relative to the specific directory being hashed for clarity,
        # or relative to a common root if needed. Here we store absolute path converted to string
        # relative to the input directory structure for readability.
        rel_path = str(file_path)
        try:
            file_hash = calculate_sha256(file_path)
            checksums[rel_path] = file_hash
            logger.debug(f"Hashed: {rel_path}")
        except Exception as e:
            logger.error(f"Failed to hash {file_path}: {e}")
            continue

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(checksums, f, indent=2, sort_keys=True)

    logger.info(f"Checksums written to {output_file}")
    return checksums

def verify_checksums(
    checksum_file: Path,
    directories: List[Path],
    extensions: Optional[List[str]] = None
) -> bool:
    """
    Verify current file checksums against a stored checksum file.

    Args:
        checksum_file: Path to the JSON file containing stored checksums.
        directories: List of directory paths to scan for verification.
        extensions: Optional list of file extensions to include.

    Returns:
        True if all checksums match, False otherwise.
    """
    if not checksum_file.exists():
        logger.error(f"Checksum file not found: {checksum_file}")
        return False

    with open(checksum_file, 'r', encoding='utf-8') as f:
        stored_checksums = json.load(f)

    logger.info(f"Verifying {len(stored_checksums)} stored checksums.")

    all_match = True
    current_files = find_files(directories[0] if len(directories) == 1 else Path('.'), extensions)
    
    # Re-gather current state of the specific directories to check
    current_state = {}
    for directory in directories:
        if not directory.exists():
            continue
        for f_path in find_files(directory, extensions):
            current_state[str(f_path)] = f_path

    # Check stored files
    for rel_path, stored_hash in stored_checksums.items():
        file_path = Path(rel_path)
        if not file_path.exists():
            logger.warning(f"File missing during verification: {rel_path}")
            all_match = False
            continue

        try:
            current_hash = calculate_sha256(file_path)
            if current_hash != stored_hash:
                logger.error(f"Checksum mismatch for {rel_path}")
                logger.error(f"  Stored: {stored_hash}")
                logger.error(f"  Current: {current_hash}")
                all_match = False
            else:
                logger.debug(f"Verified: {rel_path}")
        except Exception as e:
            logger.error(f"Error reading file {rel_path} during verification: {e}")
            all_match = False

    # Check for new files not in the stored list (optional strictness)
    # For this implementation, we only verify files that were previously recorded.
    
    if all_match:
        logger.info("Verification successful: All checksums match.")
    else:
        logger.error("Verification failed: Some checksums do not match.")
    
    return all_match

def main():
    """
    Main entry point for the checksum utility.
    Usage:
      - Generate: python -m src.utils.checksum --generate
      - Verify: python -m src.utils.checksum --verify
    """
    import argparse

    parser = argparse.ArgumentParser(description="Generate and verify SHA256 checksums for project artifacts.")
    parser.add_argument(
        '--generate',
        action='store_true',
        help='Generate checksums for data/configs, data/results, data/logs, and state.'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify checksums against the stored manifest.'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/configs/checksums.json',
        help='Path for the checksum output file (default: data/configs/checksums.json)'
    )

    args = parser.parse_args()

    # Define root directories relative to project root
    # Assuming this script is run from the project root or code/ root
    # We use relative paths that work from the project root
    project_root = Path.cwd()
    
    target_dirs = [
        project_root / 'data' / 'configs',
        project_root / 'data' / 'results',
        project_root / 'data' / 'logs',
        project_root / 'state'
    ]

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = project_root / output_path

    if args.generate:
        logger.info("Generating checksums...")
        generate_checksums(target_dirs, output_path)
        logger.info("Done.")
    elif args.verify:
        logger.info("Verifying checksums...")
        success = verify_checksums(output_path, target_dirs)
        if success:
            logger.info("All checksums verified.")
            exit(0)
        else:
            logger.error("Checksum verification failed.")
            exit(1)
    else:
        parser.print_help()
        exit(1)

if __name__ == '__main__':
    main()
