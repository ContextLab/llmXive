"""
Checksum utilities for data integrity verification.
Implements SHA-256 checksumming for files and directories.
"""
import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from config import DATA_DIR, RAW_DIR, PROCESSED_DIR, RESULTS_DIR
from utils.logging import get_logger

logger = get_logger(__name__)


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def compute_directory_checksums(dir_path: Path, extensions: Optional[List[str]] = None) -> Dict[str, str]:
    """Compute checksums for all files in a directory."""
    checksums = {}
    dir_path = Path(dir_path)
    
    if not dir_path.exists():
        logger.warning(f"Directory does not exist: {dir_path}")
        return checksums

    for file_path in dir_path.rglob("*"):
        if file_path.is_file():
            if extensions is None or any(file_path.suffix == ext for ext in extensions):
                rel_path = file_path.relative_to(dir_path)
                checksums[str(rel_path)] = compute_sha256(file_path)
    
    return checksums


def save_checksums(checksums: Dict[str, str], output_path: Path) -> None:
    """Save checksums to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"Checksums saved to {output_path}")


def load_checksums(checksum_path: Path) -> Dict[str, str]:
    """Load checksums from a JSON file."""
    if not checksum_path.exists():
        logger.warning(f"Checksum file not found: {checksum_path}")
        return {}
    
    with open(checksum_path, "r") as f:
        return json.load(f)


def verify_checksums(checksum_path: Path, base_dir: Path) -> Tuple[bool, List[str]]:
    """Verify file checksums against stored values."""
    stored = load_checksums(checksum_path)
    if not stored:
        return False, ["No checksums found"]

    failures = []
    for rel_path, expected_hash in stored.items():
        file_path = base_dir / rel_path
        if not file_path.exists():
            failures.append(f"Missing: {rel_path}")
            continue
        
        actual_hash = compute_sha256(file_path)
        if actual_hash != expected_hash:
            failures.append(f"Checksum mismatch: {rel_path}")
    
    if failures:
        logger.error(f"Checksum verification failed for {len(failures)} files")
        return False, failures
    
    logger.info("Checksum verification passed")
    return True, []


def ensure_data_directories() -> None:
    """Ensure all required data directories exist."""
    dirs = [RAW_DIR, PROCESSED_DIR, RESULTS_DIR]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory: {d}")


def generate_and_save_checksums(dir_path: Path, output_name: str = "checksums.json") -> None:
    """Generate and save checksums for a directory."""
    ensure_data_directories()
    checksums = compute_directory_checksums(dir_path)
    output_path = dir_path / output_name
    save_checksums(checksums, output_path)


def main():
    """Main entry point for checksum operations."""
    import argparse

    parser = argparse.ArgumentParser(description="Checksum utilities")
    parser.add_argument("command", choices=["compute", "verify"], help="Command to run")
    parser.add_argument("--path", type=str, required=True, help="Path to directory or file")
    parser.add_argument("--output", type=str, help="Output path for checksums (for compute)")
    
    args = parser.parse_args()
    path = Path(args.path)

    if args.command == "compute":
        if not path.exists():
            logger.error(f"Path does not exist: {path}")
            return 1
        
        if path.is_file():
            hash_val = compute_sha256(path)
            print(f"{hash_val}  {path.name}")
        else:
            checksums = compute_directory_checksums(path)
            if args.output:
                save_checksums(checksums, Path(args.output))
            else:
                print(json.dumps(checksums, indent=2))
    
    elif args.command == "verify":
        if not path.exists():
            logger.error(f"Path does not exist: {path}")
            return 1
        
        checksum_file = path / "checksums.json"
        if not checksum_file.exists():
            logger.error(f"Checksum file not found: {checksum_file}")
            return 1
        
        success, failures = verify_checksums(checksum_file, path)
        if not success:
            for f in failures:
                print(f"FAIL: {f}")
            return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
