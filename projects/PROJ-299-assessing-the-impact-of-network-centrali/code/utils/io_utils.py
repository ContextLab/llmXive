"""
Utility functions for CSV reading/writing and checksum validation (FR-001, Data Hygiene).

Provides robust, type-safe helpers for handling data files with integrity checks.
"""
import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, TextIO, BinaryIO


def calculate_file_checksum(file_path: Union[str, Path], algorithm: str = 'sha256') -> str:
    """
    Calculate the cryptographic checksum of a file.
    
    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        Hexadecimal string of the file's checksum.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found for checksum: {path}")
        
    try:
        hasher = hashlib.new(algorithm)
    except ValueError as e:
        raise ValueError(f"Unsupported hash algorithm '{algorithm}': {e}")
        
    with open(path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
            
    return hasher.hexdigest()


def verify_file_checksum(file_path: Union[str, Path], expected_checksum: str, 
                         algorithm: str = 'sha256') -> bool:
    """
    Verify a file's checksum against an expected value.
    
    Args:
        file_path: Path to the file to verify.
        expected_checksum: The expected checksum value.
        algorithm: Hash algorithm to use.
        
    Returns:
        True if the checksum matches, False otherwise.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    actual_checksum = calculate_file_checksum(file_path, algorithm)
    return actual_checksum.lower() == expected_checksum.lower()


def read_csv_as_dicts(file_path: Union[str, Path], 
                      delimiter: str = ',',
                      encoding: str = 'utf-8') -> List[Dict[str, Any]]:
    """
    Read a CSV file and return a list of dictionaries.
    
    Args:
        file_path: Path to the CSV file.
        delimiter: Field delimiter character.
        encoding: File encoding.
        
    Returns:
        List of dictionaries, one per row.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        csv.Error: If the CSV is malformed.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")
        
    rows = []
    with open(path, 'r', encoding=encoding, newline='') as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            rows.append(dict(row))
            
    return rows


def write_dicts_to_csv(data: List[Dict[str, Any]], 
                       file_path: Union[str, Path],
                       delimiter: str = ',',
                       encoding: str = 'utf-8',
                       overwrite: bool = True) -> None:
    """
    Write a list of dictionaries to a CSV file.
    
    Args:
        data: List of dictionaries to write.
        file_path: Output file path.
        delimiter: Field delimiter character.
        encoding: File encoding.
        overwrite: If True, overwrite existing file; if False, raise error.
        
    Raises:
        FileExistsError: If the file exists and overwrite is False.
    """
    path = Path(file_path)
    if path.exists() and not overwrite:
        raise FileExistsError(f"Output file already exists and overwrite=False: {path}")
        
    if not data:
        # Write empty file with no headers if no data
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding=encoding, newline='') as f:
            pass
        return
        
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = list(data[0].keys())
    with open(path, 'w', encoding=encoding, newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
        writer.writeheader()
        writer.writerows(data)


def read_json(file_path: Union[str, Path], encoding: str = 'utf-8') -> Any:
    """
    Read a JSON file and return its contents.
    
    Args:
        file_path: Path to the JSON file.
        encoding: File encoding.
        
    Returns:
        Parsed JSON data (dict, list, etc.).
        
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")
        
    with open(path, 'r', encoding=encoding) as f:
        return json.load(f)


def write_json(data: Any, file_path: Union[str, Path], encoding: str = 'utf-8',
               indent: Optional[int] = 2, overwrite: bool = True) -> None:
    """
    Write data to a JSON file.
    
    Args:
        data: Data to serialize to JSON.
        file_path: Output file path.
        encoding: File encoding.
        indent: Indentation level for pretty-printing (None for compact).
        overwrite: If True, overwrite existing file; if False, raise error.
        
    Raises:
        FileExistsError: If the file exists and overwrite is False.
    """
    path = Path(file_path)
    if path.exists() and not overwrite:
        raise FileExistsError(f"Output file already exists and overwrite=False: {path}")
        
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding=encoding) as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def generate_checksum_file(source_file: Union[str, Path], 
                           checksum_file: Union[str, Path],
                           algorithm: str = 'sha256') -> None:
    """
    Generate a checksum file for a given source file.
    
    Creates a text file containing the checksum and filename.
    Format: <checksum>  <filename>
    
    Args:
        source_file: Path to the source file to checksum.
        checksum_file: Path where the checksum file will be written.
        algorithm: Hash algorithm to use.
    """
    source_path = Path(source_file)
    checksum_path = Path(checksum_file)
    
    checksum_value = calculate_file_checksum(source_path, algorithm)
    filename = source_path.name
    
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(checksum_path, 'w', encoding='utf-8') as f:
        f.write(f"{checksum_value}  {filename}\n")


def verify_checksum_file(checksum_file: Union[str, Path], 
                         base_directory: Optional[Union[str, Path]] = None) -> Dict[str, bool]:
    """
    Verify files against a checksum file.
    
    Args:
        checksum_file: Path to the checksum file.
        base_directory: Directory where source files are located (defaults to checksum file dir).
        
    Returns:
        Dictionary mapping filename to verification result (True/False).
        
    Raises:
        FileNotFoundError: If the checksum file does not exist.
    """
    checksum_path = Path(checksum_file)
    if not checksum_path.exists():
        raise FileNotFoundError(f"Checksum file not found: {checksum_path}")
        
    if base_directory is None:
        base_directory = checksum_path.parent
    else:
        base_directory = Path(base_directory)
        
    results = {}
    
    with open(checksum_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            parts = line.split('  ', 1)
            if len(parts) != 2:
                continue
                
            expected_checksum, filename = parts
            file_path = base_directory / filename
            
            if file_path.exists():
                try:
                    actual_checksum = calculate_file_checksum(file_path)
                    results[filename] = actual_checksum.lower() == expected_checksum.lower()
                except Exception:
                    results[filename] = False
            else:
                results[filename] = False
                
    return results
