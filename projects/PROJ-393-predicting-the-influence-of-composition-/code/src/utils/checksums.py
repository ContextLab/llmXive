"""
Checksum utility for calculating SHA256 hashes for data files.

This module provides functionality to calculate SHA256 hashes for files
in the data/raw/ directory, ensuring data integrity and reproducibility.
"""
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

from .logging_config import calculate_checksum as log_calculate_checksum, setup_logging

# Initialize logger
logger = setup_logging(__name__)


def calculate_file_sha256(file_path: Union[str, Path], chunk_size: int = 8192) -> str:
    """
    Calculate the SHA256 hash of a file.
    
    Args:
        file_path: Path to the file to hash
        chunk_size: Size of chunks to read (default 8KB for memory efficiency)
        
    Returns:
        Hexadecimal string of the SHA256 hash
        
    Raises:
        FileNotFoundError: If the file does not exist
        PermissionError: If the file cannot be read
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")
    
    sha256_hash = hashlib.sha256()
    
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                sha256_hash.update(chunk)
    except PermissionError:
        raise PermissionError(f"Permission denied reading file: {file_path}")
    except Exception as e:
        raise IOError(f"Error reading file {file_path}: {e}")
    
    return sha256_hash.hexdigest()


def calculate_directory_checksums(
    directory: Union[str, Path], 
    extensions: Optional[List[str]] = None,
    recursive: bool = True
) -> Dict[str, str]:
    """
    Calculate SHA256 hashes for all files in a directory.
    
    Args:
        directory: Path to the directory to scan
        extensions: Optional list of file extensions to include (e.g., ['.csv', '.json'])
                   If None, all files are included
        recursive: If True, scan subdirectories as well
        
    Returns:
        Dictionary mapping relative file paths to their SHA256 hashes
        
    Raises:
        NotADirectoryError: If the path is not a directory
    """
    directory = Path(directory)
    
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    if not directory.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {directory}")
    
    checksums = {}
    
    # Determine file iterator based on recursive flag
    if recursive:
        file_iterator = directory.rglob("*")
    else:
        file_iterator = directory.glob("*")
    
    for file_path in file_iterator:
        if not file_path.is_file():
            continue
        
        # Filter by extension if specified
        if extensions:
            if file_path.suffix.lower() not in [ext.lower() for ext in extensions]:
                continue
        
        try:
            file_hash = calculate_file_sha256(file_path)
            # Store relative path from the target directory
            relative_path = str(file_path.relative_to(directory))
            checksums[relative_path] = file_hash
            logger.info(f"Calculated checksum for {relative_path}: {file_hash[:16]}...")
        except Exception as e:
            logger.error(f"Failed to calculate checksum for {file_path}: {e}")
    
    return checksums


def save_checksums_to_json(
    checksums: Dict[str, str], 
    output_path: Union[str, Path]
) -> None:
    """
    Save checksums dictionary to a JSON file.
    
    Args:
        checksums: Dictionary of file paths to hashes
        output_path: Path where the JSON file will be saved
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(checksums, f, indent=2)
        logger.info(f"Checksums saved to {output_path}")
        
        # Log the checksum of the checksum file itself
        checksum_of_checksums = calculate_file_sha256(output_path)
        logger.info(f"Checksum file integrity: {checksum_of_checksums[:16]}...")
        
    except Exception as e:
        logger.error(f"Failed to save checksums to {output_path}: {e}")
        raise


def load_checksums_from_json(input_path: Union[str, Path]) -> Dict[str, str]:
    """
    Load checksums from a JSON file.
    
    Args:
        input_path: Path to the JSON file
        
    Returns:
        Dictionary of file paths to hashes
        
    Raises:
        FileNotFoundError: If the file does not exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    input_path = Path(input_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Checksum file not found: {input_path}")
    
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in checksum file {input_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to load checksums from {input_path}: {e}")
        raise


def verify_checksums(
    base_directory: Union[str, Path],
    checksums: Dict[str, str]
) -> Dict[str, bool]:
    """
    Verify file integrity against stored checksums.
    
    Args:
        base_directory: Base directory where files are located
        checksums: Dictionary of relative paths to expected hashes
        
    Returns:
        Dictionary mapping file paths to verification status (True/False)
    """
    base_directory = Path(base_directory)
    results = {}
    
    for relative_path, expected_hash in checksums.items():
        file_path = base_directory / relative_path
        
        if not file_path.exists():
            logger.warning(f"File missing during verification: {relative_path}")
            results[relative_path] = False
            continue
        
        try:
            actual_hash = calculate_file_sha256(file_path)
            is_valid = actual_hash == expected_hash
            results[relative_path] = is_valid
            
            if is_valid:
                logger.debug(f"Verification passed for {relative_path}")
            else:
                logger.error(f"Verification FAILED for {relative_path}: "
                             f"expected {expected_hash[:16]}..., got {actual_hash[:16]}...")
        except Exception as e:
            logger.error(f"Error verifying {relative_path}: {e}")
            results[relative_path] = False
    
    return results


def generate_raw_data_checksums(
    raw_data_dir: Optional[Union[str, Path]] = None,
    output_file: Optional[Union[str, Path]] = None
) -> Dict[str, str]:
    """
    Generate checksums for all files in the data/raw/ directory.
    
    This is a convenience function specifically for the project's raw data directory.
    
    Args:
        raw_data_dir: Path to the raw data directory. Defaults to 'data/raw/' relative to project root.
        output_file: Optional path to save the checksums. If None, checksums are not saved to disk.
                    
    Returns:
        Dictionary of relative file paths to SHA256 hashes
    """
    if raw_data_dir is None:
        # Default to data/raw/ relative to project root
        # We assume this is called from the project root or code/ directory
        raw_data_dir = Path("data/raw")
    else:
        raw_data_dir = Path(raw_data_dir)
    
    if not raw_data_dir.exists():
        logger.warning(f"Raw data directory does not exist: {raw_data_dir}. "
                       f"No checksums generated.")
        return {}
    
    logger.info(f"Generating checksums for {raw_data_dir}...")
    checksums = calculate_directory_checksums(raw_data_dir, extensions=[".csv", ".json", ".yaml", ".yml", ".txt"])
    
    if output_file:
        save_checksums_to_json(checksums, output_file)
    else:
        # Log summary
        logger.info(f"Generated {len(checksums)} checksums for raw data files.")
    
    return checksums


def main():
    """
    Command-line entry point for checksum generation.
    
    Usage:
        python -m src.utils.checksums
    """
    import sys
    
    # Setup logging for CLI
    logger = setup_logging(__name__, level=logging.INFO)
    
    try:
        raw_data_path = Path("data/raw")
        output_path = Path("data/raw/checksums.json")
        
        if not raw_data_path.exists():
            logger.error(f"Raw data directory not found: {raw_data_path}")
            logger.info("Please ensure data/raw/ directory exists and contains data files.")
            sys.exit(1)
        
        logger.info(f"Scanning {raw_data_path} for files...")
        checksums = generate_raw_data_checksums(raw_data_path, output_path)
        
        if not checksums:
            logger.warning("No files found to checksum in data/raw/.")
            sys.exit(0)
        
        # Verify the generated checksums immediately
        logger.info("Verifying generated checksums...")
        verification_results = verify_checksums(raw_data_path, checksums)
        all_passed = all(verification_results.values())
        
        if all_passed:
            logger.info(f"SUCCESS: All {len(checksums)} files verified successfully.")
        else:
            failed_count = sum(1 for v in verification_results.values() if not v)
            logger.warning(f"WARNING: {failed_count} out of {len(checksums)} files failed verification.")
            sys.exit(1)
            
    except Exception as e:
        logger.critical(f"Checksum generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
