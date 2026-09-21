"""
Data validation schema checks for generated wavefunctions.

Implements FR-009: Validation of wavefunction structure, normalization, and type.
"""
import numpy as np
from typing import Dict, Any, Tuple, List
from models.quantum_state import QuantumState, QuantumStateError
from logging_config import logger, E_NUMERICAL_INSTABILITY

class SchemaValidationError(Exception):
    """Raised when wavefunction data fails schema validation."""
    pass

def validate_wavefunction_schema(wavefunction: np.ndarray, system_size: int) -> Tuple[bool, List[str]]:
    """
    Validate the schema of a generated wavefunction.
    
    Checks:
    1. Type is numpy.ndarray
    2. Shape matches expected Hilbert space dimension (2^N for spin-1/2)
    3. No NaN or Inf values
    4. Normalization check (L2 norm close to 1.0)
    
    Args:
        wavefunction: 1D array of complex coefficients
        system_size: N (number of spins)
        
    Returns:
        Tuple of (is_valid, list_of_error_messages)
    """
    errors = []
    
    # Check type
    if not isinstance(wavefunction, np.ndarray):
        errors.append(f"Wavefunction must be numpy.ndarray, got {type(wavefunction)}")
        return False, errors
    
    # Check dimensionality
    if wavefunction.ndim != 1:
        errors.append(f"Wavefunction must be 1D, got {wavefunction.ndim}D")
        return False, errors
    
    # Check Hilbert space dimension
    expected_dim = 2 ** system_size
    if wavefunction.shape[0] != expected_dim:
        errors.append(
            f"Wavefunction dimension {wavefunction.shape[0]} does not match "
            f"expected Hilbert space {expected_dim} for N={system_size}"
        )
        return False, errors
    
    # Check for NaN/Inf
    if np.any(np.isnan(wavefunction)):
        errors.append("Wavefunction contains NaN values")
        logger.warning(E_NUMERICAL_INSTABILITY, "NaN detected in wavefunction")
    if np.any(np.isinf(wavefunction)):
        errors.append("Wavefunction contains Inf values")
        logger.warning(E_NUMERICAL_INSTABILITY, "Inf detected in wavefunction")
        
    if np.any(np.isnan(wavefunction)) or np.any(np.isinf(wavefunction)):
        return False, errors
    
    # Check normalization
    norm = np.linalg.norm(wavefunction)
    if not np.isclose(norm, 1.0, atol=1e-6):
        errors.append(
            f"Wavefunction not normalized: norm={norm:.6f}, expected ~1.0 "
            f"(tolerance 1e-6)"
        )
        # Log but don't fail if close enough for numerical reasons
        if not np.isclose(norm, 1.0, atol=1e-3):
            return False, errors
    
    return True, errors

def validate_quantum_state(state: QuantumState) -> Tuple[bool, List[str]]:
    """
    Validate a QuantumState object schema.
    
    Args:
        state: QuantumState instance
        
    Returns:
        Tuple of (is_valid, list_of_error_messages)
    """
    errors = []
    
    try:
        # Validate underlying wavefunction
        valid, wf_errors = validate_wavefunction_schema(
            state.get_wavefunction(), 
            state.system_size
        )
        errors.extend(wf_errors)
        
        # Check metadata
        if state.system_size <= 0:
            errors.append(f"Invalid system_size: {state.system_size}")
            
        if state.model_type not in ["heisenberg", "ising", "random"]:
            errors.append(f"Unknown model_type: {state.model_type}")
            
    except QuantumStateError as e:
        errors.append(f"QuantumState validation error: {str(e)}")
        
    return len(errors) == 0, errors

def validate_wavefunction_batch(wavefunctions: List[np.ndarray], system_sizes: List[int]) -> Dict[int, Tuple[bool, List[str]]]:
    """
    Validate a batch of wavefunctions against their respective system sizes.
    
    Args:
        wavefunctions: List of 1D numpy arrays
        system_sizes: List of corresponding N values
        
    Returns:
        Dictionary mapping index to (is_valid, errors) tuple
    """
    if len(wavefunctions) != len(system_sizes):
        raise ValueError("wavefunctions and system_sizes must have the same length")
    
    results = {}
    for i, (wf, size) in enumerate(zip(wavefunctions, system_sizes)):
        results[i] = validate_wavefunction_schema(wf, size)
        
    return results