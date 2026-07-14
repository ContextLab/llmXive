import hashlib
import os
from pathlib import Path
from typing import Optional, Tuple
from utils.logger import get_logger, log_error_context

logger = get_logger(__name__)

def calculate_md5(file_path: Union[str, Path]) -> str:
    """
    Calculate the MD5 checksum of a file.
    
    Args:
        file_path: Path to the file.
    
    Returns:
        Hexadecimal MD5 hash string.
    """
    hash_md5 = hashlib.md5()
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    
    return hash_md5.hexdigest()

def calculate_sha256(file_path: Union[str, Path]) -> str:
    """
    Calculate the SHA256 checksum of a file.
    
    Args:
        file_path: Path to the file.
    
    Returns:
        Hexadecimal SHA256 hash string.
    """
    hash_sha256 = hashlib.sha256()
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    
    return hash_sha256.hexdigest()

def verify_checksum(file_path: Union[str, Path], expected_checksum: str, algorithm: str = "md5") -> bool:
    """
    Verify a file's checksum against an expected value.
    
    Args:
        file_path: Path to the file.
        expected_checksum: Expected checksum string.
        algorithm: Hash algorithm ('md5' or 'sha256').
    
    Returns:
        True if checksum matches, False otherwise.
    """
    if algorithm == "md5":
        actual = calculate_md5(file_path)
    elif algorithm == "sha256":
        actual = calculate_sha256(file_path)
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    return actual.lower() == expected_checksum.lower()

def validate_input_file(file_path: Union[str, Path], expected_checksum: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate an input file exists and optionally matches a checksum.
    
    Args:
        file_path: Path to the file.
        expected_checksum: Optional expected checksum.
    
    Returns:
        Tuple of (is_valid, error_message).
    """
    path = Path(file_path)
    
    if not path.exists():
        return False, f"File not found: {path}"
    
    if not path.is_file():
        return False, f"Path is not a file: {path}"
    
    if expected_checksum:
        # Try to detect algorithm from length or default to md5
        if len(expected_checksum) == 64:
            if not verify_checksum(path, expected_checksum, "sha256"):
                return False, "SHA256 checksum mismatch"
        elif len(expected_checksum) == 32:
            if not verify_checksum(path, expected_checksum, "md5"):
                return False, "MD5 checksum mismatch"
        else:
            # Assume MD5 for 32 chars, but if length is ambiguous, try MD5 first
            if not verify_checksum(path, expected_checksum, "md5"):
                return False, "Checksum mismatch"
    
    return True, None

def main():
    """CLI entry point for checksum utilities."""
    import argparse
    parser = argparse.ArgumentParser(description="File checksum utilities")
    parser.add_argument("file", help="Path to the file")
    parser.add_argument("--algorithm", choices=["md5", "sha256"], default="md5", help="Hash algorithm")
    parser.add_argument("--verify", help="Verify against expected checksum")
    
    args = parser.parse_args()
    
    path = Path(args.file)
    if not path.exists():
        print(f"Error: File not found: {path}")
        return 1
    
    if args.verify:
        is_valid, error = validate_input_file(path, args.verify)
        if is_valid:
            print("Checksum verified successfully.")
            return 0
        else:
            print(f"Verification failed: {error}")
            return 1
    else:
        if args.algorithm == "md5":
            checksum = calculate_md5(path)
        else:
            checksum = calculate_sha256(path)
        print(f"{args.algorithm.upper()}: {checksum}")
        return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
