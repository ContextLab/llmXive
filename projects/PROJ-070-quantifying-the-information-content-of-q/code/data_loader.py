"""
Data loading and generation module for quantum many-body systems.

Handles external dataset validation, internal data generation (ED/DMRG),
and HDF5 persistence of wavefunction coefficients.
"""
import os
import numpy as np
import h5py
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh
from typing import Optional, Dict, Any, List, Tuple
from logging_config import logger

# Error codes
E_DATASET_MISSING = "E_DATASET_MISSING"
E_DATA_INSUFFICIENT = "E_DATA_INSUFFICIENT"

def validate_external_datasets() -> None:
    """
    Check for external datasets (Zenodo/HuggingFace) at startup.
    
    Per FR-009: If absent or malformed, raise E_DATASET_MISSING and exit immediately.
    NO internal generation fallback is permitted here.
    """
    # Check for configured external data paths
    external_paths = [
        os.getenv("EXTERNAL_DATASET_PATH"),
        os.getenv("ZENODO_DATASET_ID"),
        os.getenv("HF_DATASET_ID")
    ]
    
    # Filter out None values
    valid_paths = [p for p in external_paths if p is not None]
    
    if not valid_paths:
        # No external datasets configured - this is acceptable if internal generation is used
        logger.info("No external datasets configured. Internal generation will be used.")
        return
    
    # Validate each configured path
    for path in valid_paths:
        if not os.path.exists(path):
            logger.error(f"External dataset not found: {path}")
            raise RuntimeError(f"{E_DATASET_MISSING}: Dataset not found at {path}")
        
        # Basic validation of file integrity
        if path.endswith('.h5') or path.endswith('.hdf5'):
            try:
                with h5py.File(path, 'r') as f:
                    # Check for required keys
                    required_keys = ['wavefunction', 'system_size', 'model_type']
                    missing_keys = [k for k in required_keys if k not in f]
                    if missing_keys:
                        raise RuntimeError(f"{E_DATASET_MISSING}: Missing keys {missing_keys} in {path}")
            except Exception as e:
                logger.error(f"Malformed HDF5 dataset: {path} - {str(e)}")
                raise RuntimeError(f"{E_DATASET_MISSING}: Malformed dataset at {path}")
    
    logger.info("External datasets validated successfully")

def generate_internal_wavefunction(
    model_type: str,
    system_size: int,
    seed: Optional[int] = None,
    method: str = "ED"
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Generate internal wavefunction for testing and development.
    
    Args:
        model_type: Type of model ('heisenberg_1d', 'ising_1d')
        system_size: Number of spins N (10-40)
        seed: Random seed for reproducibility
        method: Generation method ('ED' or 'DMRG')
    
    Returns:
        Tuple of (wavefunction_coeffs, metadata_dict)
    
    Raises:
        ValueError: If parameters are out of range
        RuntimeError: If generation fails
    """
    if system_size < 4 or system_size > 40:
        raise ValueError(f"System size must be between 4 and 40, got {system_size}")
    
    if method not in ["ED", "DMRG"]:
        raise ValueError(f"Method must be 'ED' or 'DMRG', got {method}")
    
    if seed is not None:
        np.random.seed(seed)
    
    # Hilbert space dimension
    dim = 2 ** system_size
    
    if method == "ED" and system_size > 20:
        logger.warning(f"ED requested for N={system_size}, may exceed memory. Consider DMRG.")
        # Fall back to DMRG for large systems
        method = "DMRG"
    
    if method == "ED":
        return _generate_ed_wavefunction(model_type, system_size, seed)
    else:
        return _generate_dmrg_wavefunction(model_type, system_size, seed)

def _generate_ed_wavefunction(
    model_type: str,
    system_size: int,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Generate wavefunction using Exact Diagonalization.
    
    Uses scipy.sparse.linalg.eigsh to find the ground state.
    
    Args:
        model_type: 'heisenberg_1d' or 'ising_1d'
        system_size: Number of spins N
        seed: Random seed (for Jahn-Teller degeneracy handling if needed)
    
    Returns:
        Tuple of (ground_state_coeffs, metadata)
    """
    if seed is not None:
        np.random.seed(seed)
    
    dim = 2 ** system_size
    
    # Build Hamiltonian
    H = _build_heisenberg_hamiltonian(system_size) if model_type == "heisenberg_1d" else \
        _build_ising_hamiltonian(system_size)
    
    # Find ground state using sparse eigsh
    # k=1 for ground state, which='SA' for smallest algebraic eigenvalue
    try:
        eigenvalues, eigenvectors = eigsh(H, k=1, which='SA', maxiter=10000)
    except Exception as e:
        logger.error(f"ED eigsh failed: {str(e)}")
        raise RuntimeError(f"E_DATA_INSUFFICIENT: ED ground state calculation failed - {str(e)}")
    
    ground_state = eigenvectors[:, 0]
    
    # Normalize
    norm = np.linalg.norm(ground_state)
    if norm < 1e-10:
        raise RuntimeError(f"E_DATA_INSUFFICIENT: Ground state norm too small: {norm}")
    ground_state = ground_state / norm
    
    metadata = {
        'model_type': model_type,
        'system_size': system_size,
        'method': 'ED',
        'ground_energy': float(eigenvalues[0]),
        'hilbert_dim': dim,
        'seed': seed
    }
    
    return ground_state, metadata

def _build_heisenberg_hamiltonian(N: int) -> sp.csr_matrix:
    """
    Build Heisenberg XXX Hamiltonian for 1D chain with periodic boundary conditions.
    
    H = J * sum_{i} (S_i^x S_{i+1}^x + S_i^y S_{i+1}^y + S_i^z S_{i+1}^z)
    
    Uses spin-1/2 operators: S^x = 0.5 * X, S^y = 0.5 * Y, S^z = 0.5 * Z
    """
    dim = 2 ** N
    
    # Pauli matrices
    I = sp.eye(2, format='csr')
    X = sp.csr_matrix([[0, 1], [1, 0]])
    Y = sp.csr_matrix([[0, -1j], [1j, 0]])
    Z = sp.csr_matrix([[1, 0], [0, -1]])
    
    H = sp.csr_matrix((dim, dim), dtype=np.complex128)
    
    # Build tensor products for each bond
    for i in range(N):
        j = (i + 1) % N  # Periodic boundary
        
        # Construct operator for bond (i, j)
        op_list = [I] * N
        
        # S_i^x S_j^x term
        op_x = op_list.copy()
        op_x[i] = X
        op_x[j] = X
        H_xx = op_x[0]
        for k in range(1, N):
            H_xx = sp.kron(H_xx, op_x[k])
        H += 0.25 * H_xx  # 0.5 * 0.5 from spin operators
        
        # S_i^y S_j^y term
        op_y = op_list.copy()
        op_y[i] = Y
        op_y[j] = Y
        H_yy = op_y[0]
        for k in range(1, N):
            H_yy = sp.kron(H_yy, op_y[k])
        H += 0.25 * H_yy
        
        # S_i^z S_j^z term
        op_z = op_list.copy()
        op_z[i] = Z
        op_z[j] = Z
        H_zz = op_z[0]
        for k in range(1, N):
            H_zz = sp.kron(H_zz, op_z[k])
        H += 0.25 * H_zz
    
    return H.tocsr()

def _build_ising_hamiltonian(N: int, h: float = 1.0) -> sp.csr_matrix:
    """
    Build Transverse Field Ising Hamiltonian.
    
    H = -J * sum_{i} Z_i Z_{i+1} - h * sum_{i} X_i
    
    """
    dim = 2 ** N
    
    I = sp.eye(2, format='csr')
    X = sp.csr_matrix([[0, 1], [1, 0]])
    Z = sp.csr_matrix([[1, 0], [0, -1]])
    
    H = sp.csr_matrix((dim, dim), dtype=np.complex128)
    
    # ZZ interaction term
    for i in range(N):
        j = (i + 1) % N
        
        op_list = [I] * N
        op_list[i] = Z
        op_list[j] = Z
        
        H_zz = op_list[0]
        for k in range(1, N):
            H_zz = sp.kron(H_zz, op_list[k])
        
        H -= H_zz  # -J term (J=1)
    
    # Transverse field term
    for i in range(N):
        op_list = [I] * N
        op_list[i] = X
        
        H_x = op_list[0]
        for k in range(1, N):
            H_x = sp.kron(H_x, op_list[k])
        
        H -= h * H_x  # -h term
    
    return H.tocsr()

def _generate_dmrg_wavefunction(
    model_type: str,
    system_size: int,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Generate wavefunction using DMRG via tenpy.
    
    For N > 20 where ED is infeasible.
    
    Args:
        model_type: 'heisenberg_1d' or 'ising_1d'
        system_size: Number of spins N
        seed: Random seed
    
    Returns:
        Tuple of (ground_state_coeffs, metadata)
    """
    try:
        from tenpy.models.spins import SpinChain
        from tenpy.algorithms import dmrg
        from tenpy.networks.mps import MPS
    except ImportError:
        raise RuntimeError("tenpy not installed. Install with: pip install tenpy")
    
    if seed is not None:
        np.random.seed(seed)
    
    # Configure model
    L = system_size
    J = 1.0
    h = 1.0 if model_type == "ising_1d" else 0.0
    
    model_params = {
        'L': L,
        'J': J,
        'h_x': h,
        'bc_MPS': 'finite',
        'conserve': None,  # No symmetry for general case
        'spin': 0.5
    }
    
    if model_type == "heisenberg_1d":
        model_params.update({
            'bc_x': 'periodic',  # Approximate with open for tenpy
            'Jz': J,
            'Jxy': J
        })
        model = SpinChain(model_params)
    else:  # ising_1d
        model_params.update({
            'hz': 0.0,
            'hx': h,
            'Jz': 1.0
        })
        model = SpinChain(model_params)
    
    # Initialize MPS with random product state
    psi = MPS.from_product_state(model.lat.mps_sites(), ["up"] * L, bc='finite')
    
    # DMRG parameters
    dmrg_params = {
        'mixer': True,
        'trunc_params': {
            'svd_min': 1e-10,
            'chi_max': 200
        },
        'max_E_err': 1e-10,
        'verbose': 0
    }
    
    # Run DMRG
    try:
        info = dmrg.run(psi, model, dmrg_params)
    except Exception as e:
        logger.error(f"DMRG failed: {str(e)}")
        raise RuntimeError(f"E_DATA_INSUFFICIENT: DMRG calculation failed - {str(e)}")
    
    # Convert MPS to full wavefunction (only feasible for moderate N)
    # For very large N, this may be memory-intensive
    if system_size > 24:
        logger.warning(f"Converting MPS to full wavefunction for N={system_size} may be memory intensive")
    
    # Get full wavefunction from MPS
    # Note: This is the full state vector in computational basis
    try:
        wavefunction = psi.to_full_state()
    except Exception as e:
        logger.error(f"Failed to convert MPS to full state: {str(e)}")
        raise RuntimeError(f"E_DATA_INSUFFICIENT: MPS to full state conversion failed - {str(e)}")
    
    # Normalize
    norm = np.linalg.norm(wavefunction)
    if norm < 1e-10:
        raise RuntimeError(f"E_DATA_INSUFFICIENT: Wavefunction norm too small: {norm}")
    wavefunction = wavefunction / norm
    
    metadata = {
        'model_type': model_type,
        'system_size': system_size,
        'method': 'DMRG',
        'ground_energy': float(info['E']),
        'hilbert_dim': 2 ** system_size,
        'bond_dimension_max': int(max(psi.chi)),
        'seed': seed
    }
    
    return wavefunction, metadata

def save_wavefunction_hdf5(
    wavefunction: np.ndarray,
    metadata: Dict[str, Any],
    output_path: str
) -> None:
    """
    Save wavefunction coefficients and metadata to HDF5 file.
    
    Args:
        wavefunction: Complex wavefunction coefficients
        metadata: Dictionary of metadata
        output_path: Path to output HDF5 file
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with h5py.File(output_path, 'w') as f:
        # Save wavefunction (real and imaginary parts)
        f.create_dataset('wavefunction_real', data=wavefunction.real)
        f.create_dataset('wavefunction_imag', data=wavefunction.imag)
        
        # Save metadata
        for key, value in metadata.items():
            if isinstance(value, (int, float, str, bool)):
                f.attrs[key] = value
            elif isinstance(value, (list, tuple)):
                f.attrs[key] = str(value)
            else:
                f.attrs[key] = str(value)
        
        # Add generation timestamp
        import datetime
        f.attrs['generated_at'] = datetime.datetime.now().isoformat()
    
    logger.info(f"Saved wavefunction to {output_path}")

def generate_internal_dataset(
    model_type: str,
    system_sizes: List[int],
    output_dir: str,
    seed_base: int = 42
) -> List[str]:
    """
    Generate a dataset of wavefunctions for multiple system sizes.
    
    Args:
        model_type: Type of model ('heisenberg_1d', 'ising_1d')
        system_sizes: List of system sizes to generate
        output_dir: Directory to save output files
        seed_base: Base seed for reproducibility
    
    Returns:
        List of paths to generated files
    """
    os.makedirs(output_dir, exist_ok=True)
    generated_files = []
    
    for i, N in enumerate(system_sizes):
        seed = seed_base + i
        method = "ED" if N <= 20 else "DMRG"
        
        logger.info(f"Generating {model_type} for N={N} using {method}")
        
        try:
            wavefunction, metadata = generate_internal_wavefunction(
                model_type, N, seed=seed, method=method
            )
            
            output_path = os.path.join(
                output_dir,
                f"{model_type}_N{N}_seed{seed}.h5"
            )
            
            save_wavefunction_hdf5(wavefunction, metadata, output_path)
            generated_files.append(output_path)
            
        except Exception as e:
            logger.error(f"Failed to generate for N={N}: {str(e)}")
            # Continue with other system sizes
            continue
    
    logger.info(f"Generated {len(generated_files)} wavefunctions")
    return generated_files

# Export public API
__all__ = [
    'E_DATASET_MISSING',
    'E_DATA_INSUFFICIENT',
    'validate_external_datasets',
    'generate_internal_wavefunction',
    'save_wavefunction_hdf5',
    'generate_internal_dataset'
]
