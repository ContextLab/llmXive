"""
Checksum generation and validation utilities.
"""
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, Optional

def generate_checksum(filepath: Path, algorithm: str = "sha256") -> str:
    """
    Generate a checksum for a file.
    
    Args:
        filepath: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        str: Hexadecimal checksum string.
    """
    hash_obj = hashlib.new(algorithm)
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()

def generate_checksums_for_directory(
    directory: Path,
    output_file: Optional[Path] = None,
    algorithm: str = "sha256"
) -> Dict[str, str]:
    """
    Generate checksums for all files in a directory.
    
    Args:
        directory: Directory to scan.
        output_file: Optional path to write checksums in standard format.
        algorithm: Hash algorithm to use.
        
    Returns:
        Dict mapping relative file paths to checksums.
    """
    checksums = {}
    
    if not directory.exists():
        return checksums
    
    for filepath in sorted(directory.rglob("*")):
        if filepath.is_file():
            try:
                checksum = generate_checksum(filepath, algorithm)
                relative_path = filepath.relative_to(directory.parent)
                checksums[str(relative_path)] = checksum
            except Exception as e:
                logging.warning(f"Could not checksum {filepath}: {e}")
    
    if output_file:
        write_checksums_file(checksums, output_file)
    
    return checksums

def write_checksums_file(checksums: Dict[str, str], output_path: Path) -> None:
    """
    Write checksums to file in standard format:
    <hash>  <relative_path>
    
    Args:
        checksums: Mapping of relative_path -> checksum.
        output_path: Path to write the checksums file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        for path, checksum in sorted(checksums.items()):
            f.write(f"{checksum}  {path}\n")
    
    logging.info(f"Wrote checksums to {output_path}")

def verify_checksums(checksums_file: Path, base_directory: Path) -> bool:
    """
    Verify files against a checksums file.
    
    Args:
        checksums_file: Path to the checksums file.
        base_directory: Base directory for relative paths.
        
    Returns:
        bool: True if all checksums match.
    """
    if not checksums_file.exists():
        return False
    
    with open(checksums_file, 'r') as f:
        lines = f.readlines()
    
    all_valid = True
    for line in lines:
        parts = line.strip().split()
        if len(parts) < 2:
            continue
        
        expected_checksum = parts[0]
        relative_path = ' '.join(parts[1:])
        filepath = base_directory / relative_path
        
        if not filepath.exists():
            logging.warning(f"File not found: {filepath}")
            all_valid = False
            continue
        
        actual_checksum = generate_checksum(filepath)
        if actual_checksum != expected_checksum:
            logging.warning(f"Checksum mismatch for {filepath}")
            all_valid = False
    
    return all_valid