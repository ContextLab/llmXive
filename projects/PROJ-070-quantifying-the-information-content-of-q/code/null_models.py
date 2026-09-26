"""
Null model generators for quantum state analysis.
Implements random product states and Haar-random pure state ensembles.
"""
import os
import numpy as np
import h5py
from typing import List, Tuple, Optional, Dict, Any
from scipy.special import factorial
from config import Config

class NullModelError(Exception):
    """Custom exception for null model generation errors."""
    pass

def generate_random_product_state(
    n_spins: int,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Generate a random product state (unentangled state).
    
    A product state is of the form |ψ⟩ = ⊗ᵢ |ψᵢ⟩ where each |ψᵢ⟩ is a 
    single-qubit state with random phases.
    
    Args:
        n_spins: Number of spins in the system.
        seed: Random seed for reproducibility.
        
    Returns:
        Complex numpy array of shape (2**n_spins,) representing the state vector.
        
    Raises:
        NullModelError: If n_spins is invalid.
    """
    if n_spins <= 0:
        raise NullModelError(f"n_spins must be positive, got {n_spins}")
        
    if seed is not None:
        np.random.seed(seed)
        
    # Generate random phases for each spin
    # Each spin state: (1/√2) * (|0⟩ + e^(iφ) |1⟩)
    phases = np.random.uniform(0, 2 * np.pi, n_spins)
    
    # Build the product state by tensoring single-qubit states
    state = np.array([1.0 + 0j])
    
    for phi in phases:
        # Single qubit state: (|0⟩ + e^(iφ)|1⟩) / √2
        single_qubit = np.array([1.0, np.exp(1j * phi)]) / np.sqrt(2.0)
        state = np.kron(state, single_qubit)
        
    return state

def generate_random_product_states_batch(
    n_spins: int,
    n_states: int,
    seed: Optional[int] = None
) -> List[np.ndarray]:
    """
    Generate a batch of random product states.
    
    Args:
        n_spins: Number of spins in the system.
        n_states: Number of states to generate.
        seed: Random seed for reproducibility.
        
    Returns:
        List of complex numpy arrays, each of shape (2**n_spins,).
    """
    states = []
    for i in range(n_states):
        state_seed = None if seed is None else seed + i
        states.append(generate_random_product_state(n_spins, state_seed))
    return states

def generate_haar_random_state(
    n_spins: int,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Generate a Haar-random pure state.
    
    A Haar-random state is sampled uniformly from the unit sphere in 
    the 2^n-dimensional Hilbert space. This approximates a maximally 
    mixed state when considering reduced density matrices.
    
    Args:
        n_spins: Number of spins in the system.
        seed: Random seed for reproducibility.
        
    Returns:
        Complex numpy array of shape (2**n_spins,) representing the state vector.
        
    Raises:
        NullModelError: If n_spins is invalid or dimension too large.
    """
    if n_spins <= 0:
        raise NullModelError(f"n_spins must be positive, got {n_spins}")
        
    dim = 2 ** n_spins
    
    # Limit to prevent excessive memory usage
    if dim > 2**20:  # ~1 million dimensions
        raise NullModelError(
            f"Dimension {dim} (n_spins={n_spins}) is too large for "
            "Haar random state generation. Use n_spins <= 20."
        )
        
    if seed is not None:
        np.random.seed(seed)
        
    # Generate complex Gaussian random vector
    # Real and imaginary parts are independent N(0, 1)
    real_part = np.random.randn(dim)
    imag_part = np.random.randn(dim)
    state = real_part + 1j * imag_part
    
    # Normalize to unit length (project onto unit sphere)
    norm = np.linalg.norm(state)
    if norm == 0:
        raise NullModelError("Generated state has zero norm; retry with different seed")
        
    state = state / norm
    
    return state

def generate_haar_random_states_batch(
    n_spins: int,
    n_states: int,
    seed: Optional[int] = None
) -> List[np.ndarray]:
    """
    Generate a batch of Haar-random pure states.
    
    Args:
        n_spins: Number of spins in the system.
        n_states: Number of states to generate.
        seed: Random seed for reproducibility.
        
    Returns:
        List of complex numpy arrays, each of shape (2**n_spins,).
        
    Raises:
        NullModelError: If generation fails.
    """
    states = []
    for i in range(n_states):
        state_seed = None if seed is None else seed + i
        try:
            state = generate_haar_random_state(n_spins, state_seed)
            states.append(state)
        except NullModelError as e:
            raise NullModelError(f"Failed to generate Haar state {i}: {e}")
    return states

def save_product_states_to_hdf5(
    states: List[np.ndarray],
    n_spins: int,
    output_path: str,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Save product states to an HDF5 file.
    
    Args:
        states: List of state vectors.
        n_spins: Number of spins.
        output_path: Path to output HDF5 file.
        metadata: Optional metadata dictionary.
        
    Raises:
        NullModelError: If save fails.
    """
    try:
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        
        with h5py.File(output_path, 'w') as f:
            f.attrs['n_spins'] = n_spins
            f.attrs['n_states'] = len(states)
            f.attrs['state_type'] = 'product'
            f.attrs['dim'] = 2 ** n_spins
            
            if metadata:
                for key, value in metadata.items():
                    f.attrs[key] = str(value)
            
            # Create dataset for state vectors
            dtype = h5py.special_dtype(complex=np.complex128)
            ds = f.create_dataset('states', (len(states), 2 ** n_spins), dtype=dtype)
            
            for i, state in enumerate(states):
                ds[i, :] = state
                
    except Exception as e:
        raise NullModelError(f"Failed to save product states to {output_path}: {e}")

def save_haar_states_to_hdf5(
    states: List[np.ndarray],
    n_spins: int,
    output_path: str,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Save Haar-random states to an HDF5 file.
    
    Args:
        states: List of state vectors.
        n_spins: Number of spins.
        output_path: Path to output HDF5 file.
        metadata: Optional metadata dictionary.
        
    Raises:
        NullModelError: If save fails.
    """
    try:
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        
        with h5py.File(output_path, 'w') as f:
            f.attrs['n_spins'] = n_spins
            f.attrs['n_states'] = len(states)
            f.attrs['state_type'] = 'haar_random'
            f.attrs['dim'] = 2 ** n_spins
            
            if metadata:
                for key, value in metadata.items():
                    f.attrs[key] = str(value)
            
            # Create dataset for state vectors
            dtype = h5py.special_dtype(complex=np.complex128)
            ds = f.create_dataset('states', (len(states), 2 ** n_spins), dtype=dtype)
            
            for i, state in enumerate(states):
                ds[i, :] = state
                
    except Exception as e:
        raise NullModelError(f"Failed to save Haar states to {output_path}: {e}")

def main() -> None:
    """
    Main entry point for generating null model datasets.
    
    Generates:
    1. Product states for N=10, 12, 14, 16, 18, 20 (10 states each)
    2. Haar-random states for N=10, 12, 14, 16, 18, 20 (10 states each)
    
    Outputs are saved to data/null_models/ directory.
    """
    import argparse
    from logging_config import setup_logging, logger
    
    setup_logging()
    
    parser = argparse.ArgumentParser(description='Generate null model datasets')
    parser.add_argument('--n-spins', type=int, nargs='+', 
                      default=[10, 12, 14, 16, 18, 20],
                      help='System sizes to generate (default: 10, 12, 14, 16, 18, 20)')
    parser.add_argument('--n-states', type=int, default=10,
                      help='Number of states per system size (default: 10)')
    parser.add_argument('--seed', type=int, default=42,
                      help='Random seed (default: 42)')
    parser.add_argument('--output-dir', type=str, default='data/null_models',
                      help='Output directory (default: data/null_models)')
    
    args = parser.parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    logger.info(f"Generating null models: N={args.n_spins}, n_states={args.n_states}")
    
    # Generate and save product states
    for n in args.n_spins:
        logger.info(f"Generating {args.n_states} product states for N={n}")
        try:
            states = generate_random_product_states_batch(n, args.n_states, args.seed)
            output_path = os.path.join(args.output_dir, f'product_states_N{n}.h5')
            save_product_states_to_hdf5(states, n, output_path, {
                'generator': 'random_product',
                'seed': args.seed
            })
            logger.info(f"Saved product states to {output_path}")
        except NullModelError as e:
            logger.error(f"Failed to generate product states for N={n}: {e}")
    
    # Generate and save Haar-random states
    for n in args.n_spins:
        logger.info(f"Generating {args.n_states} Haar-random states for N={n}")
        try:
            states = generate_haar_random_states_batch(n, args.n_states, args.seed + 1000)
            output_path = os.path.join(args.output_dir, f'haar_states_N{n}.h5')
            save_haar_states_to_hdf5(states, n, output_path, {
                'generator': 'haar_random',
                'seed': args.seed + 1000
            })
            logger.info(f"Saved Haar states to {output_path}")
        except NullModelError as e:
            logger.error(f"Failed to generate Haar states for N={n}: {e}")
    
    logger.info("Null model generation complete")

if __name__ == '__main__':
    main()