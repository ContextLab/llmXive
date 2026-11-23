import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from logging_config import get_logger, info, error, warning

logger = get_logger(__name__)

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum for a single file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        error(f"File not found: {file_path}")
        raise
    except PermissionError:
        error(f"Permission denied: {file_path}")
        raise

def generate_checksum_for_file(file_path: Path) -> Tuple[Path, str]:
    """Generate checksum for a single file and return (path, hash)."""
    if not file_path.exists():
        raise FileNotFoundError(f"File does not exist: {file_path}")
    checksum = compute_sha256(file_path)
    logger.info(f"Generated checksum for {file_path}: {checksum}")
    return file_path, checksum

def compute_checksums_for_directory(directory: Path, extensions: Optional[List[str]] = None) -> Dict[str, str]:
    """Compute checksums for all files in a directory (optionally filtered by extension)."""
    if not directory.exists():
        raise FileNotFoundError(f"Directory does not exist: {directory}")
    
    checksums = {}
    files_processed = 0
    
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            if extensions is None or any(file_path.suffix == ext for ext in extensions):
                try:
                    rel_path = file_path.relative_to(directory)
                    checksum = compute_sha256(file_path)
                    checksums[str(rel_path)] = checksum
                    files_processed += 1
                except Exception as e:
                    error(f"Failed to compute checksum for {file_path}: {e}")
    
    logger.info(f"Processed {files_processed} files in {directory}")
    return checksums

def save_checksums(checksums: Dict[str, str], output_path: Path) -> None:
    """Save checksums to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"Saved checksums to {output_path}")

def load_checksums(input_path: Path) -> Dict[str, str]:
    """Load checksums from a JSON file."""
    if not input_path.exists():
        raise FileNotFoundError(f"Checksum file not found: {input_path}")
    
    with open(input_path, "r") as f:
        checksums = json.load(f)
    
    logger.info(f"Loaded {len(checksums)} checksums from {input_path}")
    return checksums

def verify_checksums(directory: Path, checksums: Dict[str, str]) -> Tuple[bool, Dict[str, str]]:
    """
    Verify files in directory against provided checksums.
    Returns (all_valid, failures_dict) where failures_dict maps relative_path -> expected_hash.
    """
    all_valid = True
    failures = {}
    
    for rel_path_str, expected_hash in checksums.items():
        file_path = directory / rel_path_str
        
        if not file_path.exists():
            error(f"Missing file during verification: {file_path}")
            all_valid = False
            failures[rel_path_str] = expected_hash
            continue
        
        try:
            actual_hash = compute_sha256(file_path)
            if actual_hash != expected_hash:
                error(f"Checksum mismatch for {file_path}")
                error(f"  Expected: {expected_hash}")
                error(f"  Actual:   {actual_hash}")
                all_valid = False
                failures[rel_path_str] = expected_hash
            else:
                logger.debug(f"Verified: {file_path}")
        except Exception as e:
            error(f"Error verifying {file_path}: {e}")
            all_valid = False
            failures[rel_path_str] = expected_hash
    
    if all_valid:
        logger.info("All checksums verified successfully")
    else:
        logger.warning(f"Verification failed for {len(failures)} files")
    
    return all_valid, failures

def main():
    """Main entry point for checksum utility."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Checksum utility for data integrity")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate checksums for a directory")
    gen_parser.add_argument("directory", type=str, help="Directory to scan")
    gen_parser.add_argument("-o", "--output", type=str, required=True, help="Output JSON file path")
    gen_parser.add_argument("-e", "--extensions", nargs="+", help="File extensions to include (e.g., .csv .parquet)")
    
    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify files against checksums")
    verify_parser.add_argument("directory", type=str, help="Directory containing files to verify")
    verify_parser.add_argument("-c", "--checksums", type=str, required=True, help="Path to checksum JSON file")
    
    args = parser.parse_args()
    
    if args.command == "generate":
        directory = Path(args.directory)
        output_path = Path(args.output)
        extensions = [ext if ext.startswith(".") else f".{ext}" for ext in args.extensions] if args.extensions else None
        
        checksums = compute_checksums_for_directory(directory, extensions)
        save_checksums(checksums, output_path)
        logger.info(f"Successfully generated {len(checksums)} checksums")
        
    elif args.command == "verify":
        directory = Path(args.directory)
        checksums_path = Path(args.checksums)
        checksums = load_checksums(checksums_path)
        
        valid, failures = verify_checksums(directory, checksums)
        if valid:
            logger.info("Verification PASSED: All files match")
        else:
            logger.error(f"Verification FAILED: {len(failures)} mismatches")
            exit(1)
    else:
        parser.print_help()
        exit(1)

if __name__ == "__main__":
    main()