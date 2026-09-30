"""
Data validation schema checks for generated wavefunctions.

Implements FR-009: Validation of wavefunction structure, normalization, and type.
This module ensures that generated wavefunctions adhere to strict physical and
mathematical constraints before being used in downstream metrics calculations.
"""
import numpy as np
from typing import Dict, Any, Tuple, List
from models.quantum_state import QuantumState, QuantumStateError
from logging_config import logger, E_NUMERICAL_INSTABILITY

class SchemaValidationError(Exception):
    """Raised when wavefunction data fails schema validation."""
    def __init__(self, message: str, details: List[str] = None):
        super().__init__(message)
        self.message = message
        self.details = details or []

def validate_wavefunction_schema(wavefunction: np.ndarray, system_size: int) -> Tuple[bool, List[str]]:
    """
    Validate the schema of a generated wavefunction.
    
    Checks:
    1. Type is numpy.ndarray
    2. Shape matches expected Hilbert space dimension (2^N for spin-1/2)
    3. No NaN or Inf values (numerical stability)
    4. Normalization check (L2 norm close to 1.0)
    5. Complex dtype requirement
    
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
    
    # Check dtype (must be complex for quantum states)
    if not np.iscomplexobj(wavefunction):
        errors.append(f"Wavefunction must be complex dtype, got {wavefunction.dtype}")
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
    
    # Check for NaN/Inf (Critical for numerical stability)
    has_nan = np.any(np.isnan(wavefunction))
    has_inf = np.any(np.isinf(wavefunction))
    
    if has_nan:
        errors.append("Wavefunction contains NaN values")
        logger.warning(E_NUMERICAL_INSTABILITY, "NaN detected in wavefunction for N=%d", system_size)
    if has_inf:
        errors.append("Wavefunction contains Inf values")
        logger.warning(E_NUMERICAL_INSTABILITY, "Inf detected in wavefunction for N=%d", system_size)
        
    if has_nan or has_inf:
        return False, errors
    
    # Check normalization
    # Use a slightly relaxed tolerance for initial check, strict for final validation
    norm = np.linalg.norm(wavefunction)
    if not np.isclose(norm, 1.0, atol=1e-6):
        errors.append(
            f"Wavefunction not normalized: norm={norm:.10f}, expected ~1.0 "
            f"(tolerance 1e-6)"
        )
        # If it's way off (> 1e-3), it's a fatal error
        if not np.isclose(norm, 1.0, atol=1e-3):
            return False, errors
        # If it's close but not exact, we warn but allow it to proceed
        logger.warning(
            "Wavefunction normalization is slightly off (norm=%.6f) for N=%d. "
            "Proceeding with caution.", norm, system_size
        )
    
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
        
        # Check metadata constraints
        if state.system_size <= 0:
            errors.append(f"Invalid system_size: {state.system_size} (must be > 0)")
            
        if state.model_type not in ["heisenberg", "ising", "random"]:
            errors.append(f"Unknown model_type: {state.model_type}. Must be one of ['heisenberg', 'ising', 'random']")
            
        # Check if the state is sparse (if applicable) and validate sparsity ratio
        if state.is_sparse:
            sparsity = state.get_sparsity_ratio()
            if sparsity < 0.0 or sparsity > 1.0:
                errors.append(f"Invalid sparsity ratio: {sparsity}")
                
    except QuantumStateError as e:
        errors.append(f"QuantumState validation error: {str(e)}")
    except Exception as e:
        errors.append(f"Unexpected error during state validation: {str(e)}")
        
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

def validate_hdf5_wavefunction_structure(file_path: str) -> Tuple[bool, List[str]]:
    """
    Validate the structure of an HDF5 file containing wavefunctions.
    
    Checks:
    1. File exists and is readable
    2. Required groups/keys are present
    3. Dataset shapes match expected dimensions
    
    Args:
        file_path: Path to the HDF5 file
        
    Returns:
        Tuple of (is_valid, list_of_error_messages)
    """
    import os
    import h5py
    
    errors = []
    
    if not os.path.exists(file_path):
        errors.append(f"HDF5 file not found: {file_path}")
        return False, errors
    
    try:
        with h5py.File(file_path, 'r') as f:
            # Check for required metadata
            if 'metadata' not in f:
                errors.append("Missing 'metadata' group in HDF5 file")
            else:
                metadata = f['metadata']
                required_keys = ['system_size', 'model_type', 'generation_date']
                for key in required_keys:
                    if key not in metadata:
                        errors.append(f"Missing metadata key: {key}")
            
            # Check for wavefunction data
            if 'wavefunctions' not in f:
                errors.append("Missing 'wavefunctions' group in HDF5 file")
            else:
                wf_group = f['wavefunctions']
                # Validate that datasets exist and have correct shape
                for key in wf_group.keys():
                    dataset = wf_group[key]
                    if len(dataset.shape) != 1:
                        errors.append(f"Wavefunction '{key}' is not 1D (shape: {dataset.shape})")
                    
                    # Check if it's complex
                    if dataset.dtype != 'complex128' and dataset.dtype != 'complex64':
                        errors.append(f"Wavefunction '{key}' has incorrect dtype: {dataset.dtype}")
                        
    except Exception as e:
        errors.append(f"Error reading HDF5 file: {str(e)}")
        
    return len(errors) == 0, errors

def run_validation_on_generated_data(data_path: str) -> bool:
    """
    Run full validation pipeline on generated data.
    
    This function orchestrates validation of both the HDF5 structure and
    the individual wavefunction schemas contained within.
    
    Args:
        data_path: Path to the generated HDF5 file
        
    Returns:
        True if all validations pass, False otherwise
    """
    # Validate HDF5 structure
    valid, errors = validate_hdf5_wavefunction_structure(data_path)
    if not valid:
        logger.error("HDF5 structure validation failed: %s", "; ".join(errors))
        return False
    
    # Load and validate individual wavefunctions
    import h5py
    with h5py.File(data_path, 'r') as f:
        wf_group = f['wavefunctions']
        metadata = f['metadata']
        system_size = int(metadata['system_size'][()])
        
        for key in wf_group.keys():
            wf_data = wf_group[key][:]
            valid, wf_errors = validate_wavefunction_schema(wf_data, system_size)
            if not valid:
                logger.error("Wavefunction '%s' validation failed: %s", key, "; ".join(wf_errors))
                return False
    
    logger.info("All validations passed for %s", data_path)
    return True