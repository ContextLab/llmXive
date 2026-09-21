import numpy as np
from scipy.sparse.linalg import svds
from scipy.sparse import csr_matrix
import gzip
import lzma
import bz2
import os
import sys
from typing import List, Dict, Tuple, Optional, Union
import logging
import struct

# Import project-specific utilities and logging
from logging_config import (
    setup_logging,
    logger,
    E_NUMERICAL_INSTABILITY,
    log_data_exclusion,
    get_instability_events,
    clear_event_logs,
    check_numerical_stability
)
from utils.sparse_helpers import convert_to_csr, ensure_sparse_format
from validators.data_schema import validate_wavefunction_schema, SchemaValidationError
from config import Config, ConfigError

# Custom exception for data insufficiency
class E_DATA_INSUFFICIENT(Exception):
    """Raised when the dataset is insufficient for analysis (e.g., all data excluded due to numerical instability)."""
    pass

def load_wavefunction_from_hdf5(filepath: str) -> np.ndarray:
    """
    Load a wavefunction vector from an HDF5 file.
    
    Args:
        filepath: Path to the HDF5 file containing the wavefunction.
        
    Returns:
        Complex numpy array representing the wavefunction.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the data cannot be loaded or is malformed.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Wavefunction file not found: {filepath}")
    
    import h5py
    with h5py.File(filepath, 'r') as f:
        if 'wavefunction' not in f:
            raise ValueError(f"File {filepath} does not contain a 'wavefunction' dataset.")
        wf = f['wavefunction'][:]
        
    # Validate schema
    try:
        validate_wavefunction_schema(wf)
    except SchemaValidationError as e:
        logger.error(f"Schema validation failed for {filepath}: {e}")
        raise
        
    return wf

def calculate_entanglement_entropy(wavefunction: np.ndarray, subsystem_size: int) -> float:
    """
    Calculate bipartite entanglement entropy using sparse SVD.
    
    Args:
        wavefunction: 1D complex array of wavefunction coefficients.
        subsystem_size: Size of subsystem A (number of spins).
        
    Returns:
        Entanglement entropy value.
        
    Raises:
        E_DATA_INSUFFICIENT: If numerical instability prevents calculation.
    """
    N = int(np.log2(len(wavefunction)))
    dim_A = 2 ** subsystem_size
    dim_B = 2 ** (N - subsystem_size)
    
    # Reshape to matrix
    psi_matrix = wavefunction.reshape(dim_A, dim_B)
    
    # Convert to sparse format for efficiency
    psi_sparse = ensure_sparse_format(psi_matrix)
    
    # Compute reduced density matrix rho_A = psi * psi^H
    # We use sparse operations: rho_A = psi_sparse @ psi_sparse.conj().T
    # However, for SVD approach: singular values of psi_matrix are sqrt(eigenvalues of rho_A)
    # We need enough singular values to capture the spectrum.
    # For entanglement entropy, we need all non-zero singular values if possible, 
    # but for large systems we might truncate. Here we try to get all if possible.
    
    k = min(dim_A, dim_B, 1000) # Limit k for svds if dimensions are huge
    if k == 0:
        logger.warning("Matrix dimensions too small for svds, using dense SVD")
        u, s, vt = np.linalg.svd(psi_matrix, full_matrices=False)
        singular_values = s
    else:
        try:
            u, s, vt = svds(psi_sparse, k=k)
            # svds returns singular values in ascending order usually, but let's sort
            singular_values = np.sort(s)[::-1]
        except Exception as e:
            logger.error(f"Sparse SVD failed: {e}. Falling back to dense SVD.")
            u, s, vt = np.linalg.svd(psi_matrix, full_matrices=False)
            singular_values = s
    
    # Check for numerical instability in singular values
    if not check_numerical_stability(singular_values, context="singular_values"):
        raise E_DATA_INSUFFICIENT("Numerical instability detected in singular values during entanglement calculation.")
        
    # Calculate entropy: S = - sum(lambda_i * log(lambda_i)) where lambda_i = s_i^2 / sum(s_j^2)
    # Normalize singular values squared to get probabilities
    probs = singular_values ** 2
    total_prob = np.sum(probs)
    if total_prob == 0:
        raise E_DATA_INSUFFICIENT("Total probability is zero; wavefunction is null.")
        
    probs = probs / total_prob
    
    # Filter out zero probabilities to avoid log(0)
    probs = probs[probs > 1e-15]
    
    if len(probs) == 0:
        logger.warning("No valid probabilities found for entropy calculation.")
        return 0.0
        
    entropy = -np.sum(probs * np.log(probs))
    
    # Final check
    if not np.isfinite(entropy):
        raise E_DATA_INSUFFICIENT(f"Calculated entropy is not finite: {entropy}")
        
    return entropy

def quantize_wavefunction(wavefunction: np.ndarray, bits: int = 16) -> bytes:
    """
    Quantize complex wavefunction coefficients to fixed-point signed integers.
    
    Args:
        wavefunction: 1D complex numpy array.
        bits: Number of bits for quantization (default 16).
        
    Returns:
        Bytes representation of the quantized wavefunction.
        
    Raises:
        E_DATA_INSUFFICIENT: If quantization fails due to numerical issues.
    """
    if not check_numerical_stability(wavefunction, context="wavefunction_input"):
        raise E_DATA_INSUFFICIENT("Input wavefunction contains NaN or Inf.")
        
    # Separate real and imaginary parts
    real_part = np.real(wavefunction)
    imag_part = np.imag(wavefunction)
    
    # Find max absolute value for scaling
    max_val = max(np.max(np.abs(real_part)), np.max(np.abs(imag_part)))
    
    if max_val == 0:
        raise E_DATA_INSUFFICIENT("Wavefunction is zero; cannot quantize.")
        
    # Scale to [-1, 1] range then to integer range
    # For signed integers of 'bits', range is [-2^(bits-1), 2^(bits-1)-1]
    max_int = 2 ** (bits - 1) - 1
    min_int = -2 ** (bits - 1)
    
    scale_factor = max_int / max_val
    
    quantized_real = np.round(real_part * scale_factor).astype(np.int16)
    quantized_imag = np.round(imag_part * scale_factor).astype(np.int16)
    
    # Check for overflow/underflow
    if np.any(quantized_real > max_int) or np.any(quantized_real < min_int) or \
       np.any(quantized_imag > max_int) or np.any(quantized_imag < min_int):
        logger.warning("Quantization overflow detected. Re-scaling.")
        # Re-scale conservatively
        scale_factor = (max_int - 1) / max_val
        quantized_real = np.round(real_part * scale_factor).astype(np.int16)
        quantized_imag = np.round(imag_part * scale_factor).astype(np.int16)
        
    # Pack into bytes
    # Using struct to ensure consistent binary representation
    byte_data = bytearray()
    for r, i in zip(quantized_real, quantized_imag):
        byte_data.extend(struct.pack('<h', r)) # little-endian short
        byte_data.extend(struct.pack('<h', i))
        
    return bytes(byte_data)

def generate_internal_baseline(wavefunction: np.ndarray) -> bytes:
    """
    Generate an internal size-matched random baseline (random phases on product basis).
    
    Args:
        wavefunction: Original wavefunction to match size against.
        
    Returns:
        Bytes representation of the baseline.
    """
    N = len(wavefunction)
    # Generate random phases
    phases = np.random.uniform(0, 2 * np.pi, N)
    # Product basis state: all |0> or similar, but we just need random phases on a basis
    # A simple product state in computational basis is usually |00...0> which has 1 at index 0.
    # But the spec says "random phases on product basis". 
    # We'll create a vector with random phases but magnitude 1 (or normalized)
    # To be a valid state, we should normalize, but for NCD compression, the content matters.
    # Let's create a state where each component has a random phase but is otherwise a basis state?
    # The spec says "random product states" in T023, here it's "internal baseline".
    # Interpretation: A state with random phases relative to a fixed product basis.
    # We'll generate a vector of random complex numbers with unit magnitude and random phases.
    baseline_complex = np.exp(1j * phases)
    # Normalize to be a valid state vector (optional for NCD but good practice)
    baseline_complex = baseline_complex / np.linalg.norm(baseline_complex)
    
    return quantize_wavefunction(baseline_complex)

def calculate_ncd(original: bytes, baseline: bytes, compressor: str = 'gzip') -> float:
    """
    Calculate Normalized Compression Distance (NCD).
    
    NCD(x, y) = (C(xy) - min(C(x), C(y))) / max(C(x), C(y))
    
    Args:
        original: Bytes of the original quantized wavefunction.
        baseline: Bytes of the baseline quantized wavefunction.
        compressor: Compressor to use ('gzip', 'lzma', 'bzip2').
        
    Returns:
        NCD value between 0 and 1.
        
    Raises:
        E_DATA_INSUFFICIENT: If compression fails or results are invalid.
    """
    def compress(data: bytes) -> int:
        if compressor == 'gzip':
            return len(gzip.compress(data))
        elif compressor == 'lzma':
            return len(lzma.compress(data))
        elif compressor == 'bzip2':
            return len(bz2.compress(data))
        else:
            raise ValueError(f"Unknown compressor: {compressor}")
    
    try:
        c_x = compress(original)
        c_y = compress(baseline)
        c_xy = compress(original + baseline)
        
        min_c = min(c_x, c_y)
        max_c = max(c_x, c_y)
        
        if max_c == 0:
            raise E_DATA_INSUFFICIENT("Compressed size is zero.")
            
        ncd = (c_xy - min_c) / max_c
        
        if not np.isfinite(ncd):
            raise E_DATA_INSUFFICIENT(f"NCD calculation resulted in non-finite value: {ncd}")
            
        return float(ncd)
        
    except Exception as e:
        logger.error(f"Compression failed: {e}")
        raise E_DATA_INSUFFICIENT(f"Compression failed: {e}")

def process_dataset_for_complexity(
    dataset_path: str, 
    output_path: str, 
    subsystem_size: int,
    compressor: str = 'gzip'
) -> List[Dict[str, Union[str, float]]]:
    """
    Process a dataset of wavefunctions to calculate entanglement entropy and complexity (NCD).
    
    Args:
        dataset_path: Path to the directory containing HDF5 wavefunction files.
        output_path: Path to the output CSV file.
        subsystem_size: Size of subsystem A.
        compressor: Compressor for NCD.
        
    Returns:
        List of dictionaries containing results.
        
    Raises:
        E_DATA_INSUFFICIENT: If no valid data remains after stability checks.
    """
    results = []
    files = [f for f in os.listdir(dataset_path) if f.endswith('.h5') or f.endswith('.hdf5')]
    
    if not files:
        raise E_DATA_INSUFFICIENT(f"No wavefunction files found in {dataset_path}")
        
    logger.info(f"Processing {len(files)} wavefunction files...")
    
    valid_count = 0
    excluded_count = 0
    
    for filename in files:
        filepath = os.path.join(dataset_path, filename)
        try:
            wf = load_wavefunction_from_hdf5(filepath)
            
            # Check numerical stability immediately
            if not check_numerical_stability(wf, context=f"File {filename}"):
                log_data_exclusion(filename, "Numerical instability (NaN/Inf) in wavefunction")
                excluded_count += 1
                continue
                
            # Calculate Entanglement
            try:
                entropy = calculate_entanglement_entropy(wf, subsystem_size)
            except E_DATA_INSUFFICIENT as e:
                log_data_exclusion(filename, f"Entanglement calculation failed: {e}")
                excluded_count += 1
                continue
                
            # Calculate Complexity (NCD)
            try:
                quantized_wf = quantize_wavefunction(wf)
                baseline = generate_internal_baseline(wf)
                ncd = calculate_ncd(quantized_wf, baseline, compressor)
            except E_DATA_INSUFFICIENT as e:
                log_data_exclusion(filename, f"NCD calculation failed: {e}")
                excluded_count += 1
                continue
                
            # Determine system size N
            N = int(np.log2(len(wf)))
            
            results.append({
                'file': filename,
                'N': N,
                'subsystem_size': subsystem_size,
                'entanglement_entropy': entropy,
                'entropy_per_spin': entropy / subsystem_size,
                'complexity_ncd': ncd
            })
            valid_count += 1
            
        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")
            log_data_exclusion(filename, f"Processing error: {e}")
            excluded_count += 1
            
    logger.info(f"Processing complete. Valid: {valid_count}, Excluded: {excluded_count}")
    
    if valid_count == 0:
        raise E_DATA_INSUFFICIENT("E_DATA_INSUFFICIENT: No valid data points remained after numerical stability checks and exclusions.")
        
    # Write results to CSV
    import csv
    with open(output_path, 'w', newline='') as csvfile:
        fieldnames = ['file', 'N', 'subsystem_size', 'entanglement_entropy', 'entropy_per_spin', 'complexity_ncd']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
        
    logger.info(f"Results written to {output_path}")
    return results

def main():
    """
    Main entry point for running the metrics calculation pipeline.
    Expects environment variables or arguments to define paths.
    """
    setup_logging()
    logger.info("Starting metrics calculation pipeline with numerical stability checks.")
    
    # Default paths - can be overridden by config or args
    dataset_path = os.getenv('DATASET_PATH', 'data/raw/generated')
    output_path = os.getenv('OUTPUT_PATH', 'data/processed/entanglement_metrics.csv')
    subsystem_size = int(os.getenv('SUBSYSTEM_SIZE', '10'))
    compressor = os.getenv('COMPRESSOR', 'gzip')
    
    try:
        results = process_dataset_for_complexity(
            dataset_path=dataset_path,
            output_path=output_path,
            subsystem_size=subsystem_size,
            compressor=compressor
        )
        logger.info(f"Pipeline completed successfully. Processed {len(results)} items.")
    except E_DATA_INSUFFICIENT as e:
        logger.critical(f"Pipeline failed due to insufficient data: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Pipeline failed with unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()