import hashlib
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import h5py
import numpy as np

from code.config import get_config

def _compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def log_provenance_entry(entry: Dict[str, Any]):
    """Log a provenance entry to data/metadata/provenance.json as JSONL.
    
    MUST log `realization_index`, `seed`, `W`, `L` for every generated instance.
    """
    config = get_config()
    output_path = Path(config['PROJECT_ROOT']) / 'data' / 'metadata' / 'provenance.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    entry['timestamp'] = datetime.now().isoformat()
    
    # Ensure required fields are present
    required_fields = ['realization_index', 'seed', 'W', 'L']
    for field in required_fields:
        if field not in entry:
            raise ValueError(f"Provenance entry missing required field: {field}")
    
    # Append as JSONL line
    with open(output_path, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def save_hamiltonian_to_hdf5(H: np.ndarray, W: float, L: int, realization_index: int, seed: int) -> str:
    """Save Hamiltonian to HDF5 with metadata and return checksum.
    
    Args:
        H: Hamiltonian matrix (L x L)
        W: Disorder strength
        L: System size
        realization_index: Index of this realization
        seed: Random seed used
        
    Returns:
        Path to the saved HDF5 file
    """
    config = get_config()
    output_dir = Path(config['PROJECT_ROOT']) / 'data' / 'raw' / 'hamiltonians'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"H_W{W:.1f}_L{L}_idx{realization_index}.h5"
    file_path = output_dir / filename
    
    with h5py.File(file_path, 'w') as f:
        f.create_dataset('hamiltonian', data=H)
        f.attrs['W'] = W
        f.attrs['L'] = L
        f.attrs['realization_index'] = realization_index
        f.attrs['seed'] = seed
        f.attrs['timestamp'] = datetime.now().isoformat()
    
    # Compute and log checksum
    checksum = _compute_sha256(file_path)
    
    # Log provenance
    log_provenance_entry({
        'task_id': 'T007',
        'action': 'stored',
        'input_files': [],
        'output_files': [str(file_path.relative_to(config['PROJECT_ROOT']))],
        'parameters': {'W': W, 'L': L, 'realization_index': realization_index, 'seed': seed},
        'checksums': {str(filename): checksum},
        'status': 'success'
    })
    
    return str(file_path)

def load_hamiltonian_from_hdf5(file_path: str) -> Dict[str, Any]:
    """Load Hamiltonian from HDF5.
    
    Args:
        file_path: Path to HDF5 file
        
    Returns:
        Dict with 'hamiltonian' (np.ndarray) and metadata
    """
    with h5py.File(file_path, 'r') as f:
        H = np.array(f['hamiltonian'])
        metadata = {
            'W': f.attrs['W'],
            'L': f.attrs['L'],
            'realization_index': f.attrs['realization_index'],
            'seed': f.attrs['seed']
        }
    return {'hamiltonian': H, **metadata}

def save_eigenstates_to_hdf5(eigenvalues: np.ndarray, eigenvectors: np.ndarray, 
                             W: float, L: int, realization_index: int, seed: int,
                             residual_norm: float, converged: bool) -> str:
    """Save eigenstates to HDF5 with metadata and return checksum.
    
    Args:
        eigenvalues: Array of eigenvalues
        eigenvectors: Matrix of eigenvectors (columns)
        W: Disorder strength
        L: System size
        realization_index: Index of this realization
        seed: Random seed used
        residual_norm: Numerical residual from eigenvalue solver
        converged: Whether solver converged
        
    Returns:
        Path to the saved HDF5 file
    """
    config = get_config()
    output_dir = Path(config['PROJECT_ROOT']) / 'data' / 'raw' / 'eigenstates'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"eigenstates_W{W:.1f}_L{L}_idx{realization_index}.h5"
    file_path = output_dir / filename
    
    with h5py.File(file_path, 'w') as f:
        f.create_dataset('eigenvalues', data=eigenvalues)
        f.create_dataset('eigenvectors', data=eigenvectors)
        f.attrs['W'] = W
        f.attrs['L'] = L
        f.attrs['realization_index'] = realization_index
        f.attrs['seed'] = seed
        f.attrs['residual_norm'] = residual_norm
        f.attrs['converged'] = converged
        f.attrs['timestamp'] = datetime.now().isoformat()
    
    # Compute and log checksum
    checksum = _compute_sha256(file_path)
    
    # Log provenance
    log_provenance_entry({
        'task_id': 'T007',
        'action': 'stored',
        'input_files': [],
        'output_files': [str(file_path.relative_to(config['PROJECT_ROOT']))],
        'parameters': {'W': W, 'L': L, 'realization_index': realization_index, 'seed': seed, 
                     'residual_norm': residual_norm, 'converged': converged},
        'checksums': {str(filename): checksum},
        'status': 'success' if converged else 'partial'
    })
    
    return str(file_path)

def save_localization_length(xi: float, W: float, L: int, realization_index: int, 
                             seed: int, fit_params: Dict[str, Any]) -> str:
    """Save localization length result to HDF5 and log provenance.
    
    Args:
        xi: Localization length
        W: Disorder strength
        L: System size
        realization_index: Index of this realization
        seed: Random seed used
        fit_params: Dictionary of fit parameters
        
    Returns:
        Path to the saved HDF5 file
    """
    config = get_config()
    output_dir = Path(config['PROJECT_ROOT']) / 'data' / 'processed' / 'localization_lengths'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"xi_W{W:.1f}_L{L}_idx{realization_index}.h5"
    file_path = output_dir / filename
    
    with h5py.File(file_path, 'w') as f:
        f.attrs['xi'] = xi
        f.attrs['W'] = W
        f.attrs['L'] = L
        f.attrs['realization_index'] = realization_index
        f.attrs['seed'] = seed
        f.attrs['timestamp'] = datetime.now().isoformat()
        
        # Store fit parameters
        fit_group = f.create_group('fit_params')
        for key, value in fit_params.items():
            if isinstance(value, (int, float)):
                fit_group.attrs[key] = value
            elif isinstance(value, str):
                fit_group.attrs[key] = value
    
    # Compute and log checksum
    checksum = _compute_sha256(file_path)
    
    # Log provenance
    log_provenance_entry({
        'task_id': 'T007',
        'action': 'processed',
        'input_files': [],
        'output_files': [str(file_path.relative_to(config['PROJECT_ROOT']))],
        'parameters': {'W': W, 'L': L, 'realization_index': realization_index, 'seed': seed, 'xi': xi},
        'checksums': {str(filename): checksum},
        'status': 'success'
    })
    
    return str(file_path)
