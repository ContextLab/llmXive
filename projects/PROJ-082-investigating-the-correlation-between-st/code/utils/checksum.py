import hashlib
import os
from pathlib import Path
from typing import Optional, Tuple, Union
from utils.logger import get_logger, log_error_context

def calculate_md5(file_path: Union[str, Path]) -> str:
    """
    Calculate MD5 checksum for a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        MD5 hex digest string
    """
    hash_md5 = hashlib.md5()
    path_obj = Path(file_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    with open(path_obj, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def calculate_sha256(file_path: Union[str, Path]) -> str:
    """
    Calculate SHA256 checksum for a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        SHA256 hex digest string
    """
    hash_sha256 = hashlib.sha256()
    path_obj = Path(file_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    with open(path_obj, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def verify_checksum(file_path: Union[str, Path], expected_checksum: str, algorithm: str = "md5") -> bool:
    """
    Verify file checksum against expected value.
    
    Args:
        file_path: Path to file
        expected_checksum: Expected checksum value
        algorithm: Checksum algorithm ('md5' or 'sha256')
        
    Returns:
        True if checksum matches, False otherwise
    """
    if algorithm == "md5":
        actual_checksum = calculate_md5(file_path)
    elif algorithm == "sha256":
        actual_checksum = calculate_sha256(file_path)
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    return actual_checksum.lower() == expected_checksum.lower()

def validate_input_file(file_path: Union[str, Path], required_checksum: Optional[str] = None, algorithm: str = "md5") -> Tuple[bool, Optional[str]]:
    """
    Validate an input file exists and optionally verify its checksum.
    
    Args:
        file_path: Path to file
        required_checksum: Optional expected checksum
        algorithm: Checksum algorithm to use
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    logger = get_logger(__name__)
    path_obj = Path(file_path)
    
    if not path_obj.exists():
        error_msg = f"File not found: {file_path}"
        logger.error(error_msg)
        return False, error_msg
    
    if not path_obj.is_file():
        error_msg = f"Not a file: {file_path}"
        logger.error(error_msg)
        return False, error_msg
    
    if required_checksum:
        try:
            is_valid = verify_checksum(file_path, required_checksum, algorithm)
            if not is_valid:
                actual = calculate_md5(file_path) if algorithm == "md5" else calculate_sha256(file_path)
                error_msg = f"Checksum mismatch for {file_path}. Expected: {required_checksum}, Got: {actual}"
                logger.error(error_msg)
                return False, error_msg
        except FileNotFoundError as e:
            return False, str(e)
    
    return True, None

def main():
    """
    Entry point for checksum utility testing.
    Demonstrates usage on a real file if provided as argument.
    """
    logger = get_logger(__name__)
    logger.info("Checksum utility module loaded successfully.")
    
    import sys
    if len(sys.argv) > 1:
        target_file = sys.argv[1]
        if os.path.exists(target_file):
            try:
                md5_val = calculate_md5(target_file)
                sha256_val = calculate_sha256(target_file)
                logger.info(f"MD5: {md5_val}")
                logger.info(f"SHA256: {sha256_val}")
                
                valid, err = validate_input_file(target_file)
                if valid:
                    logger.info(f"Validation passed for {target_file}")
                else:
                    logger.error(f"Validation failed: {err}")
            except Exception as e:
                logger.error(f"Error processing file: {e}")
        else:
            logger.error(f"File not found: {target_file}")

if __name__ == "__main__":
    main()
