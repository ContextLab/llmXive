import hashlib
import os
from pathlib import Path
from typing import Optional, Tuple
from utils.logger import get_logger, log_error_context

logger = get_logger(__name__)

def calculate_md5(file_path: str) -> Optional[str]:
    """Calculate MD5 checksum of a file."""
    path = Path(file_path)
    if not path.exists():
        log_error_context(logger, f"File not found: {file_path}")
        return None
    
    hash_md5 = hashlib.md5()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        log_error_context(logger, f"Error calculating MD5 for {file_path}", e)
        return None

def calculate_sha256(file_path: str) -> Optional[str]:
    """Calculate SHA256 checksum of a file."""
    path = Path(file_path)
    if not path.exists():
        log_error_context(logger, f"File not found: {file_path}")
        return None
    
    hash_sha256 = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception as e:
        log_error_context(logger, f"Error calculating SHA256 for {file_path}", e)
        return None

def verify_checksum(file_path: str, expected_checksum: str, algorithm: str = "md5") -> bool:
    """Verify file checksum against an expected value."""
    if algorithm.lower() == "md5":
        actual = calculate_md5(file_path)
    elif algorithm.lower() == "sha256":
        actual = calculate_sha256(file_path)
    else:
        logger.error(f"Unsupported algorithm: {algorithm}")
        return False
    
    if actual is None:
        return False
    
    return actual.lower() == expected_checksum.lower()

def validate_input_file(file_path: str, required_checksum: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """Validate input file existence and optionally checksum."""
    path = Path(file_path)
    if not path.exists():
        return False, f"File not found: {file_path}"
    
    if required_checksum:
        # Infer algorithm from checksum length if not specified (simple heuristic)
        algo = "sha256" if len(required_checksum) == 64 else "md5"
        if not verify_checksum(file_path, required_checksum, algo):
            return False, f"Checksum mismatch for {file_path} (expected {required_checksum})"
    
    return True, None

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m utils.checksum <file_path> [expected_checksum]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    expected = sys.argv[2] if len(sys.argv) > 2 else None
    
    valid, error = validate_input_file(file_path, expected)
    if valid:
        print(f"Validation passed for {file_path}")
        if not expected:
            md5 = calculate_md5(file_path)
            sha = calculate_sha256(file_path)
            print(f"MD5: {md5}")
            print(f"SHA256: {sha}")
    else:
        print(f"Validation failed: {error}")
        sys.exit(1)

if __name__ == "__main__":
    main()
