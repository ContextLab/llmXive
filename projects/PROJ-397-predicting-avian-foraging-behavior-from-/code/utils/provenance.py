"""
Provenance module for metadata logging and hash generation.

This module provides utilities to:
- Compute SHA-256 hashes for files and data structures
- Generate and save provenance records with timestamps and metadata
- Log pipeline steps with their inputs and outputs
- Verify data integrity using stored hashes
"""
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .config import get_project_root, get_data_dir


def compute_file_hash(file_path: Union[str, Path], algorithm: str = 'sha256') -> str:
    """
    Compute the cryptographic hash of a file.
    
    Args:
        file_path: Path to the file to hash
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Hexadecimal string of the hash
        
    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the algorithm is not supported
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hasher = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    
    return hasher.hexdigest()


def compute_data_hash(data: Any, algorithm: str = 'sha256') -> str:
    """
    Compute the hash of a Python data structure.
    
    Args:
        data: Any JSON-serializable Python object
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Hexadecimal string of the hash
        
    Raises:
        TypeError: If the data is not JSON-serializable
    """
    json_str = json.dumps(data, sort_keys=True, default=str)
    hasher = hashlib.new(algorithm)
    hasher.update(json_str.encode('utf-8'))
    return hasher.hexdigest()


def generate_provenance_record(
    step_name: str,
    inputs: Optional[Dict[str, Any]] = None,
    outputs: Optional[Dict[str, Any]] = None,
    parameters: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate a provenance record for a pipeline step.
    
    Args:
        step_name: Name of the pipeline step
        inputs: Dictionary mapping input names to their metadata (e.g., file paths, hashes)
        outputs: Dictionary mapping output names to their metadata
        parameters: Dictionary of parameters used in the step
        metadata: Additional arbitrary metadata
        
    Returns:
        Dictionary containing the provenance record
    """
    record = {
        'step_name': step_name,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'inputs': inputs or {},
        'outputs': outputs or {},
        'parameters': parameters or {},
        'metadata': metadata or {}
    }
    
    # Generate a unique ID for this record
    record['record_id'] = compute_data_hash(record)[:16]
    
    return record


def save_provenance_record(
    record: Dict[str, Any],
    output_dir: Optional[Union[str, Path]] = None,
    filename: Optional[str] = None
) -> Path:
    """
    Save a provenance record to a JSON file.
    
    Args:
        record: The provenance record dictionary
        output_dir: Directory to save the record (default: data/provenance)
        filename: Optional filename (default: auto-generated based on timestamp and step)
        
    Returns:
        Path to the saved file
    """
    if output_dir is None:
        data_dir = get_data_dir()
        output_dir = Path(data_dir) / 'provenance'
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if filename is None:
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        step_name = record.get('step_name', 'unknown').replace(' ', '_')
        filename = f"{timestamp}_{step_name}_{record.get('record_id', 'unknown')}.json"
    
    file_path = output_dir / filename
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(record, f, indent=2, default=str)
    
    return file_path


def log_step(
    step_name: str,
    status: str = 'completed',
    inputs: Optional[Dict[str, Any]] = None,
    outputs: Optional[Dict[str, Any]] = None,
    parameters: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None
) -> Dict[str, Any]:
    """
    Log a pipeline step with its status and metadata.
    
    Args:
        step_name: Name of the pipeline step
        status: Status of the step ('completed', 'failed', 'skipped')
        inputs: Input metadata
        outputs: Output metadata
        parameters: Parameters used
        metadata: Additional metadata
        error: Error message if status is 'failed'
        
    Returns:
        The generated provenance record
    """
    record = generate_provenance_record(
        step_name=step_name,
        inputs=inputs,
        outputs=outputs,
        parameters=parameters,
        metadata=metadata or {}
    )
    
    record['status'] = status
    if error:
        record['error'] = error
    
    # Save the record
    save_provenance_record(record)
    
    return record


def verify_data_integrity(
    file_path: Union[str, Path],
    expected_hash: str,
    algorithm: str = 'sha256'
) -> bool:
    """
    Verify the integrity of a file by comparing its hash to an expected value.
    
    Args:
        file_path: Path to the file to verify
        expected_hash: Expected hash value
        algorithm: Hash algorithm to use
        
    Returns:
        True if the hash matches, False otherwise
        
    Raises:
        FileNotFoundError: If the file does not exist
    """
    actual_hash = compute_file_hash(file_path, algorithm)
    return actual_hash == expected_hash


def load_provenance_records(
    directory: Optional[Union[str, Path]] = None,
    step_name: Optional[str] = None
) -> list:
    """
    Load all provenance records from a directory.
    
    Args:
        directory: Directory containing provenance records (default: data/provenance)
        step_name: Optional filter to only return records for a specific step
        
    Returns:
        List of provenance record dictionaries
    """
    if directory is None:
        data_dir = get_data_dir()
        directory = Path(data_dir) / 'provenance'
    else:
        directory = Path(directory)
    
    if not directory.exists():
        return []
    
    records = []
    for file_path in directory.glob('*.json'):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                record = json.load(f)
                if step_name is None or record.get('step_name') == step_name:
                    records.append(record)
        except (json.JSONDecodeError, IOError):
            continue
    
    return records
