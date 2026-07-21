import hashlib
import os
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, List

from config import get_project_root

logger = logging.getLogger(__name__)

CHECKSUM_FILE = "artifacts/checksums.txt"

def compute_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file using the specified algorithm (MD5 or SHA256).
    
    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use ('md5' or 'sha256').
        
    Returns:
        Hexadecimal digest string of the file checksum.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If an unsupported algorithm is requested.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if algorithm.lower() == "md5":
        hasher = hashlib.md5()
    elif algorithm.lower() == "sha256":
        hasher = hashlib.sha256()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}. Use 'md5' or 'sha256'.")

    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files without loading entirely into memory
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except IOError as e:
        logger.error(f"Error reading file {file_path} for checksum: {e}")
        raise

def generate_checksums(files: List[Path], algorithm: str = "sha256") -> Dict[str, str]:
    """
    Generate checksums for a list of files.
    
    Args:
        files: List of Path objects to files.
        algorithm: Hash algorithm to use.
        
    Returns:
        Dictionary mapping relative file paths to their checksums.
    """
    checksums = {}
    for file_path in files:
        try:
            checksum = compute_checksum(file_path, algorithm)
            # Store relative path from project root for portability
            rel_path = file_path.relative_to(get_project_root())
            checksums[str(rel_path)] = checksum
            logger.info(f"Generated {algorithm.upper()} checksum for {rel_path}: {checksum[:16]}...")
        except (FileNotFoundError, IOError) as e:
            logger.warning(f"Skipping {file_path}: {e}")
    return checksums

def verify_checksums(files: List[Path], algorithm: str = "sha256") -> Tuple[bool, Dict[str, bool]]:
    """
    Verify checksums of files against stored values in artifacts/checksums.txt.
    
    Args:
        files: List of Path objects to files to verify.
        algorithm: Hash algorithm used to generate the stored checksums.
        
    Returns:
        Tuple of (all_valid: bool, results: Dict[rel_path: str, is_valid: bool])
    """
    checksums_path = get_project_root() / CHECKSUM_FILE
    if not checksums_path.exists():
        logger.error(f"Checksum file not found: {checksums_path}. Cannot verify.")
        return False, {str(f.relative_to(get_project_root())): False for f in files}

    # Load stored checksums
    stored_checksums = {}
    try:
        with open(checksums_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    # Format: <checksum>  <filepath> or <checksum> <filepath>
                    checksum = parts[0]
                    # Rejoin path parts in case of spaces, though unlikely in this project
                    filepath = " ".join(parts[1:])
                    stored_checksums[filepath] = checksum
    except IOError as e:
        logger.error(f"Failed to read checksum file: {e}")
        return False, {}

    all_valid = True
    results = {}

    for file_path in files:
        rel_path = str(file_path.relative_to(get_project_root()))
        if rel_path not in stored_checksums:
            logger.warning(f"No stored checksum found for {rel_path}")
            results[rel_path] = False
            all_valid = False
            continue

        try:
            current_checksum = compute_checksum(file_path, algorithm)
            is_valid = current_checksum == stored_checksums[rel_path]
            results[rel_path] = is_valid
            if not is_valid:
                logger.error(f"Checksum mismatch for {rel_path}")
                logger.error(f"  Expected: {stored_checksums[rel_path]}")
                logger.error(f"  Got:      {current_checksum}")
                all_valid = False
            else:
                logger.info(f"Checksum verified for {rel_path}")
        except (FileNotFoundError, IOError) as e:
            logger.error(f"Could not verify {rel_path}: {e}")
            results[rel_path] = False
            all_valid = False

    return all_valid, results

def update_checksum_for_file(file_path: Path, algorithm: str = "sha256") -> bool:
    """
    Compute the checksum for a single file and update the artifacts/checksums.txt file.
    If the file exists in the checksum file, it is updated; otherwise, it is appended.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use.
        
    Returns:
        True if successful, False otherwise.
    """
    checksums_path = get_project_root() / CHECKSUM_FILE
    try:
        new_checksum = compute_checksum(file_path, algorithm)
        rel_path = str(file_path.relative_to(get_project_root()))
        
        # Read existing checksums
        existing_checksums = {}
        if checksums_path.exists():
            with open(checksums_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split()
                    if len(parts) >= 2:
                        checksum = parts[0]
                        filepath = " ".join(parts[1:])
                        existing_checksums[filepath] = checksum

        # Update or add
        existing_checksums[rel_path] = new_checksum

        # Write back
        with open(checksums_path, "w") as f:
            f.write(f"# Checksums for project artifacts ({algorithm.upper()})\n")
            f.write(f"# Generated automatically. Do not edit manually.\n")
            for path, checksum in existing_checksums.items():
                f.write(f"{checksum}  {path}\n")
        
        logger.info(f"Updated checksum for {rel_path} in {CHECKSUM_FILE}")
        return True
    except Exception as e:
        logger.error(f"Failed to update checksum for {file_path}: {e}")
        return False

def main():
    """
    CLI entry point for checksum operations.
    Usage:
      python code/checksum_utils.py generate [file1 file2 ...]  -> Generate checksums for files
      python code/checksum_utils.py verify [file1 file2 ...]    -> Verify checksums
      python code/checksum_utils.py update <file>               -> Update checksum for a single file
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage: python code/checksum_utils.py <generate|verify|update> [args...]")
        sys.exit(1)

    command = sys.argv[1]
    root = get_project_root()

    if command == "generate":
        # If no files provided, default to known artifacts
        if len(sys.argv) < 3:
            files = [
                root / "data" / "processed" / "microbiome_features.csv",
                root / "data" / "processed" / "eeg_features.csv",
                root / "data" / "processed" / "matched_pairs.csv",
                root / "data" / "processed" / "distribution_groups.csv",
                root / "artifacts" / "analysis_results.json",
            ]
            # Filter to existing files
            files = [f for f in files if f.exists()]
        else:
            files = [root / arg for arg in sys.argv[2:]]
            files = [f for f in files if f.exists()]

        if not files:
            print("No valid files found to generate checksums for.")
            sys.exit(1)

        checksums = generate_checksums(files)
        if checksums:
            print(f"Generated checksums for {len(checksums)} files.")
            print(f"Saved to {CHECKSUM_FILE}")
        else:
            print("No checksums generated.")

    elif command == "verify":
        if len(sys.argv) < 3:
            # Default to known artifacts
            files = [
                root / "data" / "processed" / "microbiome_features.csv",
                root / "data" / "processed" / "eeg_features.csv",
                root / "data" / "processed" / "matched_pairs.csv",
                root / "data" / "processed" / "distribution_groups.csv",
                root / "artifacts" / "analysis_results.json",
            ]
            files = [f for f in files if f.exists()]
        else:
            files = [root / arg for arg in sys.argv[2:]]
            files = [f for f in files if f.exists()]

        if not files:
            print("No valid files found to verify.")
            sys.exit(1)

        valid, results = verify_checksums(files)
        if valid:
            print("All checksums verified successfully.")
        else:
            print("Checksum verification failed.")
            for path, is_ok in results.items():
                if not is_ok:
                    print(f"  FAILED: {path}")
            sys.exit(1)

    elif command == "update":
        if len(sys.argv) < 3:
            print("Usage: python code/checksum_utils.py update <file_path>")
            sys.exit(1)
        
        file_path = root / sys.argv[2]
        if not file_path.exists():
            print(f"File not found: {file_path}")
            sys.exit(1)
        
        if update_checksum_for_file(file_path):
            print(f"Updated checksum for {file_path.relative_to(root)}")
        else:
            print("Failed to update checksum.")
            sys.exit(1)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
