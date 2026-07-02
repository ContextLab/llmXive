import hashlib
import json
from pathlib import Path
from typing import Optional

from utils.logging import get_logger

logger = get_logger(__name__)


def compute_sha256(filepath: Path) -> str:
    """
    Compute the SHA-256 checksum of a file.
    
    Args:
        filepath: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file cannot be read.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
        
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            # Read in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except PermissionError as e:
        logger.error(f"Permission denied reading file: {filepath}")
        raise
    except Exception as e:
        logger.error(f"Error computing checksum for {filepath}: {e}")
        raise


def write_checksum_file(checksum: str, output_path: Path) -> None:
    """
    Write the checksum to a .sha256 file in the standard format.
    
    Format: <hash>  <filename>
    
    Args:
        checksum: The SHA-256 hash string.
        output_path: Path where the .sha256 file will be written.
    """
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Standard format: hash followed by two spaces and filename
    filename = output_path.stem  # e.g., "full_pool_final.csv"
    content = f"{checksum}  {filename}\n"
    
    with open(output_path, "w") as f:
        f.write(content)
        
    logger.info(f"Checksum written to {output_path}")


def generate_and_save_checksum(input_file: Path, output_dir: Optional[Path] = None) -> str:
    """
    Compute SHA-256 checksum for a file and save it to a .sha256 file.
    
    Args:
        input_file: Path to the source file.
        output_dir: Directory to save the checksum file. Defaults to input_file's directory.
        
    Returns:
        The computed checksum string.
        
    Raises:
        FileNotFoundError: If input_file does not exist.
    """
    if output_dir is None:
        output_dir = input_file.parent
        
    checksum = compute_sha256(input_file)
    
    checksum_file = output_dir / f"{input_file.name}.sha256"
    write_checksum_file(checksum, checksum_file)
    
    return checksum
