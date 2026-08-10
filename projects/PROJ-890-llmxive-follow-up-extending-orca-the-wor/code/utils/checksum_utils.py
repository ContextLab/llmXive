import os
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        Hexadecimal checksum string.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_func = hashlib.new(algorithm)
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception as e:
        logger.error(f"Error computing checksum for {file_path}: {e}")
        raise

def generate_checksum_manifest(data_dir: Path, output_path: Optional[Path] = None) -> Path:
    """
    Generate a manifest of checksums for all files in the data directory.
    
    Args:
        data_dir: Root directory of the data structure.
        output_path: Optional path to write the manifest. Defaults to data_dir/checksum_manifest.json.
        
    Returns:
        Path to the generated manifest file.
    """
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
    
    manifest = {
        "algorithm": "sha256",
        "files": {}
    }
    
    for root, _, files in os.walk(data_dir):
        for file in files:
            if file == "checksum_manifest.json":
                continue
            
            file_path = Path(root) / file
            rel_path = file_path.relative_to(data_dir)
            
            try:
                checksum = compute_file_checksum(file_path)
                manifest["files"][str(rel_path)] = checksum
                logger.info(f"Checksum computed: {rel_path} -> {checksum[:16]}...")
            except Exception as e:
                logger.warning(f"Skipping file {rel_path} due to error: {e}")
    
    if output_path is None:
        output_path = data_dir / "checksum_manifest.json"
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Checksum manifest written to: {output_path}")
    return output_path

def verify_checksums(data_dir: Path, manifest_path: Optional[Path] = None) -> Tuple[bool, List[str], List[str]]:
    """
    Verify file checksums against a manifest.
    
    Args:
        data_dir: Root directory of the data structure.
        manifest_path: Optional path to the manifest. Defaults to data_dir/checksum_manifest.json.
        
    Returns:
        Tuple of (all_valid, passed_files, failed_files).
    """
    if manifest_path is None:
        manifest_path = data_dir / "checksum_manifest_manifest.json"
    
    if not manifest_path.exists():
        logger.error(f"Manifest file not found: {manifest_path}")
        return False, [], [f"Manifest missing: {manifest_path}"]
    
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in manifest: {e}")
        return False, [], [f"Invalid manifest JSON: {e}"]
    
    algorithm = manifest.get("algorithm", "sha256")
    expected_checksums = manifest.get("files", {})
    
    passed = []
    failed = []
    
    if not expected_checksums:
        logger.warning("Manifest contains no file entries.")
        return True, [], []
    
    for rel_path_str, expected_hash in expected_checksums.items():
        file_path = data_dir / rel_path_str
        
        if not file_path.exists():
            failed.append(f"Missing: {rel_path_str}")
            logger.warning(f"File missing: {rel_path_str}")
            continue
        
        try:
            actual_hash = compute_file_checksum(file_path, algorithm)
            if actual_hash == expected_hash:
                passed.append(rel_path_str)
                logger.info(f"Verified OK: {rel_path_str}")
            else:
                failed.append(f"Checksum mismatch: {rel_path_str}")
                logger.error(f"Checksum mismatch for {rel_path_str}: expected {expected_hash}, got {actual_hash}")
        except Exception as e:
            failed.append(f"Error reading {rel_path_str}: {e}")
            logger.error(f"Error reading {rel_path_str}: {e}")
    
    all_valid = len(failed) == 0
    return all_valid, passed, failed

def initialize_data_structure(root_dir: Path) -> None:
    """
    Initialize the data directory structure with raw, processed, and validation subdirectories.
    
    Args:
        root_dir: Root directory where data structure will be created.
    """
    subdirs = ["raw", "processed", "validation"]
    for subdir in subdirs:
        dir_path = root_dir / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {dir_path}")
    
    # Initialize .gitkeep files to ensure directories are tracked
    for subdir in subdirs:
        gitkeep_path = root_dir / subdir / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            logger.info(f"Created .gitkeep in: {root_dir / subdir}")

def main():
    """
    Main entry point for checksum utility scripts.
    Usage:
      python code/utils/checksum_utils.py init <data_dir>
      python code/utils/checksum_utils.py generate <data_dir>
      python code/utils/checksum_utils.py verify <data_dir>
    """
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python checksum_utils.py <command> <data_dir>")
        print("Commands: init, generate, verify")
        sys.exit(1)
    
    command = sys.argv[1]
    data_dir = Path(sys.argv[2])
    
    if command == "init":
        initialize_data_structure(data_dir)
        print(f"Data structure initialized at: {data_dir}")
    elif command == "generate":
        manifest_path = generate_checksum_manifest(data_dir)
        print(f"Checksum manifest generated at: {manifest_path}")
    elif command == "verify":
        all_valid, passed, failed = verify_checksums(data_dir)
        if all_valid:
            print("Verification PASSED. All files match their checksums.")
        else:
            print(f"Verification FAILED. {len(failed)} issues found.")
            for issue in failed:
                print(f"  - {issue}")
        sys.exit(0 if all_valid else 1)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
