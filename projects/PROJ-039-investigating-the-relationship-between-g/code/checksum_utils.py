import hashlib
import os
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, List
import json

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def compute_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Compute the SHA256 checksum of a file.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm (default: sha256).

    Returns:
        Hexadecimal digest string.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_func = hashlib.new(algorithm)
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except IOError as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise

def generate_checksums(data_dir: Path, output_path: Path) -> Dict[str, str]:
    """
    Generate SHA256 checksums for all files in the data directory.

    Args:
        data_dir: Root directory containing data files.
        output_path: Path to write the checksums.txt file.

    Returns:
        Dictionary mapping relative file paths to their checksums.

    Raises:
        FileNotFoundError: If data_dir does not exist.
    """
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    checksums = {}
    files_processed = 0

    logger.info(f"Scanning directory: {data_dir}")
    for file_path in data_dir.rglob('*'):
        if file_path.is_file():
            try:
                rel_path = file_path.relative_to(data_dir)
                checksum = compute_checksum(file_path)
                checksums[str(rel_path)] = checksum
                files_processed += 1
                logger.debug(f"Computed checksum for {rel_path}: {checksum[:16]}...")
            except Exception as e:
                logger.error(f"Failed to compute checksum for {file_path}: {e}")

    if files_processed == 0:
        logger.warning(f"No files found in {data_dir} to checksum.")
        # Create an empty file to indicate completion but no data
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("")
        return checksums

    # Write to output file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        for rel_path, checksum in sorted(checksums.items()):
            f.write(f"{checksum}  {rel_path}\n")

    logger.info(f"Generated checksums for {files_processed} files. Output: {output_path}")
    return checksums

def verify_checksums(data_dir: Path, checksums_path: Path) -> Tuple[bool, List[str]]:
    """
    Verify checksums of files in data_dir against a checksums file.

    Args:
        data_dir: Root directory containing data files.
        checksums_path: Path to the checksums.txt file.

    Returns:
        Tuple of (all_valid, list_of_failed_files).
    """
    if not checksums_path.exists():
        raise FileNotFoundError(f"Checksums file not found: {checksums_path}")

    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    failed_files = []
    all_valid = True

    with open(checksums_path, 'r') as f:
        lines = f.readlines()

    if not lines:
        logger.warning("Checksums file is empty.")
        return True, []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        parts = line.split('  ', 1)
        if len(parts) != 2:
            logger.warning(f"Skipping malformed checksum line: {line}")
            continue

        expected_checksum, rel_path = parts
        file_path = data_dir / rel_path

        if not file_path.exists():
            logger.error(f"File missing during verification: {rel_path}")
            failed_files.append(rel_path)
            all_valid = False
            continue

        try:
            actual_checksum = compute_checksum(file_path)
            if actual_checksum != expected_checksum:
                logger.error(f"Checksum mismatch for {rel_path}: expected {expected_checksum}, got {actual_checksum}")
                failed_files.append(rel_path)
                all_valid = False
            else:
                logger.debug(f"Checksum verified for {rel_path}")
        except Exception as e:
            logger.error(f"Error verifying checksum for {rel_path}: {e}")
            failed_files.append(rel_path)
            all_valid = False

    if all_valid:
        logger.info("All checksums verified successfully.")
    else:
        logger.error(f"Verification failed for {len(failed_files)} files.")

    return all_valid, failed_files

def update_checksum_for_file(file_path: Path, checksums_path: Path) -> Dict[str, str]:
    """
    Update the checksum for a specific file in the checksums file.
    If the file is not in the list, it is added.

    Args:
        file_path: Path to the file to update.
        checksums_path: Path to the checksums.txt file.

    Returns:
        Updated dictionary of checksums.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    checksums = {}
    if checksums_path.exists():
        with open(checksums_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and '  ' in line:
                    parts = line.split('  ', 1)
                    checksums[parts[1]] = parts[0]

    new_checksum = compute_checksum(file_path)
    rel_path = str(file_path.relative_to(checksums_path.parent.parent)) # Assuming data/ is sibling to artifacts/
    # Actually, we need to be careful with relative paths. Let's assume the input file_path is absolute or relative to root.
    # For safety, we'll just store the path as provided relative to the project root if possible, or just the filename if it's in data/.
    # A robust way: pass the relative path explicitly or derive it from the checksums file context.
    # For this utility, we assume file_path is inside the data directory managed by this script.
    
    # Let's assume the file_path is passed as relative to the project root or absolute.
    # We will try to make it relative to the data directory if it starts with 'data/'.
    # If the checksums file exists, we use its format.
    
    # Re-deriving relative path based on the assumption that checksums are stored relative to data/
    # This function is usually called after a file is written to data/.
    # We need to know the base directory. Let's assume it's 'data'.
    base_dir = Path('data')
    try:
        rel_path = file_path.relative_to(base_dir)
    except ValueError:
        # If not under data/, use the filename or full path
        rel_path = file_path.name if file_path.is_file() else str(file_path)

    checksums[str(rel_path)] = new_checksum

    with open(checksums_path, 'w') as f:
        for r_p, chk in sorted(checksums.items()):
            f.write(f"{chk}  {r_p}\n")

    logger.info(f"Updated checksum for {rel_path}: {new_checksum[:16]}...")
    return checksums

def main():
    """
    CLI entry point for checksum generation.
    Usage: python code/checksum_utils.py generate [data_dir] [output_path]
           python code/checksum_utils.py verify [data_dir] [checksums_path]
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage: python checksum_utils.py <generate|verify> [args...]")
        sys.exit(1)

    command = sys.argv[1]
    project_root = Path(__file__).parent.parent

    if command == 'generate':
        data_dir = project_root / 'data'
        output_path = project_root / 'artifacts' / 'checksums.txt'
        
        if len(sys.argv) > 2:
            data_dir = Path(sys.argv[2])
        if len(sys.argv) > 3:
            output_path = Path(sys.argv[3])

        try:
            generate_checksums(data_dir, output_path)
        except Exception as e:
            logger.error(f"Checksum generation failed: {e}")
            sys.exit(1)

    elif command == 'verify':
        data_dir = project_root / 'data'
        checksums_path = project_root / 'artifacts' / 'checksums.txt'

        if len(sys.argv) > 2:
            data_dir = Path(sys.argv[2])
        if len(sys.argv) > 3:
            checksums_path = Path(sys.argv[3])

        try:
            valid, failed = verify_checksums(data_dir, checksums_path)
            if not valid:
                logger.error(f"Verification failed for: {failed}")
                sys.exit(1)
            else:
                logger.info("Verification successful.")
                sys.exit(0)
        except Exception as e:
            logger.error(f"Checksum verification failed: {e}")
            sys.exit(1)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == '__main__':
    main()
