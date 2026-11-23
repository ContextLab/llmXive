"""
Utility functions for data processing, seeding, and validation.

This module centralizes common utilities used across the data pipeline,
including random seed management, logging setup, and data validation.
"""
import os
import random
import hashlib
import logging
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field

from data.logging_config import configure_logging, get_logger

# Seed management
_SEED = 42
_SEED_HASH = None

def set_seed(seed: int) -> None:
    """
    Set the global random seed for reproducibility.
    
    Args:
        seed: The integer seed value.
    """
    global _SEED, _SEED_HASH
    _SEED = seed
    _SEED_HASH = hashlib.sha256(str(seed).encode()).hexdigest()[:8]
    random.seed(seed)
    if 'numpy' in sys.modules:
        import numpy as np
        np.random.seed(seed)
    if 'torch' in sys.modules:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

def get_seed() -> int:
    """Return the current global seed."""
    return _SEED

def get_seed_hash() -> Optional[str]:
    """Return the hash of the current seed."""
    return _SEED_HASH

def ensure_seed_initialized() -> None:
    """Ensure the seed is set if not already initialized."""
    if _SEED_HASH is None:
        set_seed(_SEED)

def setup_logging(
    level: str = "INFO",
    log_to_file: bool = True,
    log_file: Optional[str] = None
) -> None:
    """
    Configure the logging system using the standardized configuration.
    
    Args:
        level: Logging level string (e.g., 'DEBUG', 'INFO', 'WARNING').
        log_to_file: Whether to log to a file.
        log_file: Optional path to the log file.
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    file_path = Path(log_file) if log_file else None
    configure_logging(level=numeric_level, log_to_file=log_to_file, log_file=file_path)

@dataclass
class ValidationResult:
    """Container for validation results."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

def validate_smiles(smiles: str) -> ValidationResult:
    """
    Validate a SMILES string.
    
    Args:
        smiles: The SMILES string to validate.
    
    Returns:
        ValidationResult indicating validity and any issues.
    """
    errors = []
    warnings = []
    
    if not smiles or not isinstance(smiles, str):
        errors.append("SMILES string is empty or invalid type.")
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
    
    # Basic structural checks
    if smiles.count('(') != smiles.count(')'):
        errors.append("Unbalanced parentheses in SMILES.")
    
    # Check for invalid characters (basic set)
    valid_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789[]()=-#/:@.$")
    if not all(c in valid_chars for c in smiles):
        warnings.append("SMILES contains non-standard characters.")
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )

def validate_mw(mw: float, min_mw: float = 1000.0) -> ValidationResult:
    """
    Validate molecular weight.
    
    Args:
        mw: The molecular weight to validate.
        min_mw: Minimum acceptable molecular weight.
    
    Returns:
        ValidationResult indicating validity and any issues.
    """
    errors = []
    warnings = []
    
    if mw is None or not isinstance(mw, (int, float)):
        errors.append("Molecular weight is not a number.")
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
    
    if mw < 0:
        errors.append("Molecular weight cannot be negative.")
    elif mw < min_mw:
        warnings.append(f"Molecular weight ({mw}) is below threshold ({min_mw}).")
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )

def validate_record(record: Dict[str, Any]) -> ValidationResult:
    """
    Validate a single data record.
    
    Args:
        record: Dictionary representing a data record.
    
    Returns:
        ValidationResult indicating validity and any issues.
    """
    errors = []
    warnings = []
    
    required_fields = ['smiles', 'permeability']
    for field_name in required_fields:
        if field_name not in record:
            errors.append(f"Missing required field: {field_name}")
    
    if 'smiles' in record:
        smiles_result = validate_smiles(record['smiles'])
        errors.extend(smiles_result.errors)
        warnings.extend(smiles_result.warnings)
    
    if 'permeability' in record:
        if record['permeability'] is None:
            errors.append("Permeability value is missing.")
        elif not isinstance(record['permeability'], (int, float)):
            errors.append("Permeability value is not numeric.")
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )

def validate_dataset(records: List[Dict[str, Any]]) -> ValidationResult:
    """
    Validate a list of data records.
    
    Args:
        records: List of dictionaries representing data records.
    
    Returns:
        ValidationResult indicating validity and summary statistics.
    """
    errors = []
    warnings = []
    valid_count = 0
    invalid_count = 0
    
    for i, record in enumerate(records):
        result = validate_record(record)
        if result.is_valid:
            valid_count += 1
        else:
            invalid_count += 1
            errors.extend([f"Record {i}: {e}" for e in result.errors])
            warnings.extend([f"Record {i}: {w}" for w in result.warnings])
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        # Note: ValidationResult dataclass doesn't support extra fields by default,
        # but we return the counts in the message or handle them separately if needed.
    )

# Import sys here to avoid circular imports if set_seed is called early
import sys
from pathlib import Path
