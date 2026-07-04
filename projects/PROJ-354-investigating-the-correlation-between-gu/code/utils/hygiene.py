"""
Data hygiene utilities for the Gut Microbiome-Cognitive Correlation Study.

Provides checksumming for data integrity verification and PII masking helpers
to ensure participant privacy compliance.
"""

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import numpy as np


# Constants for PII patterns
EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
PHONE_PATTERN = re.compile(r'\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b')
SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
IP_PATTERN = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')

# UK Biobank specific PII fields to mask
UKB_PII_FIELDS = [
    'eid',  # Event ID - unique participant identifier
    'participant_id',
    'email',
    'phone',
    'address',
    'postcode',
    'date_of_birth',
]


def compute_file_checksum(
    file_path: Union[str, Path], 
    algorithm: str = 'sha256'
) -> str:
    """
    Compute a cryptographic checksum for a file to verify data integrity.
    
    Args:
        file_path: Path to the file to checksum
        algorithm: Hash algorithm to use (sha256, md5, sha1)
        
    Returns:
        Hexadecimal string of the computed checksum
        
    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the algorithm is not supported
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_func = hashlib.new(algorithm)
    
    with open(path, 'rb') as f:
        # Read in chunks to handle large files (>14GB) without loading entirely into memory
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def compute_directory_checksum(
    dir_path: Union[str, Path], 
    algorithm: str = 'sha256'
) -> Dict[str, str]:
    """
    Compute checksums for all files in a directory.
    
    Args:
        dir_path: Path to the directory
        algorithm: Hash algorithm to use
        
    Returns:
        Dictionary mapping relative file paths to their checksums
    """
    path = Path(dir_path)
    if not path.is_dir():
        raise NotADirectoryError(f"Not a directory: {dir_path}")
    
    checksums = {}
    for file_path in sorted(path.rglob('*')):
        if file_path.is_file():
            rel_path = file_path.relative_to(path)
            checksums[str(rel_path)] = compute_file_checksum(file_path, algorithm)
    
    return checksums


def mask_pii_value(
    value: Any, 
    field_name: Optional[str] = None,
    mask_char: str = '*'
) -> Any:
    """
    Mask PII in a single value based on detected patterns or field name.
    
    Args:
        value: The value to mask
        field_name: Optional field name hint for masking strategy
        mask_char: Character to use for masking
        
    Returns:
        Masked value (string or original type if no PII detected)
    """
    if pd.isna(value) or value is None:
        return value
    
    str_value = str(value)
    
    # Check for specific field names
    if field_name:
        field_lower = field_name.lower()
        if 'email' in field_lower:
            return EMAIL_PATTERN.sub(mask_char * 5 + '@' + mask_char * 5, str_value)
        elif 'phone' in field_lower or 'tel' in field_lower:
            return PHONE_PATTERN.sub(mask_char * 10, str_value)
        elif 'ssn' in field_lower or 'national_id' in field_lower:
            return SSN_PATTERN.sub(mask_char * 9, str_value)
        elif 'ip' in field_lower:
            return IP_PATTERN.sub(mask_char * 7, str_value)
    
    # Generic pattern detection
    if EMAIL_PATTERN.search(str_value):
        return EMAIL_PATTERN.sub(mask_char * 5 + '@' + mask_char * 5, str_value)
    if PHONE_PATTERN.search(str_value):
        return PHONE_PATTERN.sub(mask_char * 10, str_value)
    if SSN_PATTERN.search(str_value):
        return SSN_PATTERN.sub(mask_char * 9, str_value)
    if IP_PATTERN.search(str_value):
        return IP_PATTERN.sub(mask_char * 7, str_value)
    
    return value


def mask_dataframe_pii(
    df: pd.DataFrame,
    pii_columns: Optional[List[str]] = None,
    mask_char: str = '*'
) -> pd.DataFrame:
    """
    Mask PII in a DataFrame based on column names or explicit column list.
    
    Args:
        df: Input DataFrame
        pii_columns: Optional list of column names to mask. If None, auto-detect.
        mask_char: Character to use for masking
        
    Returns:
        DataFrame with PII masked
    """
    masked_df = df.copy()
    
    if pii_columns is None:
        # Auto-detect PII columns
        pii_columns = [
            col for col in masked_df.columns 
            if any(keyword in col.lower() for keyword in UKB_PII_FIELDS + ['email', 'phone', 'ssn', 'ip'])
        ]
    
    for col in pii_columns:
        if col in masked_df.columns:
            masked_df[col] = masked_df[col].apply(
                lambda x: mask_pii_value(x, field_name=col, mask_char=mask_char)
            )
    
    return masked_df


def validate_data_integrity(
    expected_checksums: Dict[str, str],
    data_dir: Union[str, Path]
) -> Dict[str, bool]:
    """
    Validate data integrity by comparing computed checksums against expected values.
    
    Args:
        expected_checksums: Dictionary of expected file checksums
        data_dir: Directory containing the data files
        
    Returns:
        Dictionary mapping file paths to validation status (True = valid)
    """
    validation_results = {}
    data_path = Path(data_dir)
    
    for rel_path, expected_checksum in expected_checksums.items():
        file_path = data_path / rel_path
        if not file_path.exists():
            validation_results[rel_path] = False
            continue
        
        try:
            actual_checksum = compute_file_checksum(file_path)
            validation_results[rel_path] = (actual_checksum == expected_checksum)
        except Exception:
            validation_results[rel_path] = False
    
    return validation_results


def generate_data_manifest(
    data_dir: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    algorithm: str = 'sha256'
) -> Dict[str, Any]:
    """
    Generate a manifest file containing checksums and metadata for a data directory.
    
    Args:
        data_dir: Directory to scan
        output_path: Optional path to write the manifest JSON
        algorithm: Hash algorithm to use
        
    Returns:
        Manifest dictionary
    """
    data_path = Path(data_dir)
    if not data_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {data_dir}")
    
    checksums = compute_directory_checksum(data_path, algorithm)
    
    manifest = {
        'algorithm': algorithm,
        'data_directory': str(data_path),
        'file_count': len(checksums),
        'checksums': checksums,
    }
    
    if output_path:
        with open(output_path, 'w') as f:
            json.dump(manifest, f, indent=2)
    
    return manifest
