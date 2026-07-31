import json
import os
import tempfile
from pathlib import Path
import pytest
import numpy as np
import h5py

from code.storage_utils import (
    log_provenance_entry,
    save_hamiltonian_to_hdf5,
    load_hamiltonian_from_hdf5,
    save_eigenstates_to_hdf5,
    save_localization_length,
    _compute_sha256
)
from code.config import get_config

@pytest.fixture
def temp_config():
    """Create a temporary config for testing."""
    original_config = get_config()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a minimal config dict
        test_config = {
            'PROJECT_ROOT': tmpdir,
            'W_LIST': [1.0],
            'L_LIST': [100],
            'NUM_REALIZATIONS': 1,
            'SEED': 42,
            'WEAK_DISORDER_CUTOFF': 1.0,
            'NUMERICAL_RESIDUAL_THRESHOLD': 1e-6,
            'MAX_TM_ITERATIONS': 1000
        }
        
        # Mock get_config to return our test config
        import code.config
        original_get_config = code.config.get_config
        code.config.get_config = lambda: test_config
        
        yield test_config
        
        # Restore original
        code.config.get_config = original_get_config

def test_log_provenance_entry(temp_config):
    """Test that provenance entries are logged correctly with required fields."""
    entry = {
        'task_id': 'T007',
        'action': 'stored',
        'input_files': [],
        'output_files': ['test.h5'],
        'parameters': {
            'W': 1.0,
            'L': 100,
            'realization_index': 0,
            'seed': 42
        },
        'checksums': {'test.h5': 'abc123'},
        'status': 'success'
    }
    
    log_provenance_entry(entry)
    
    # Verify file exists
    provenance_path = Path(temp_config['PROJECT_ROOT']) / 'data' / 'metadata' / 'provenance.json'
    assert provenance_path.exists()
    
    # Verify content
    with open(provenance_path, 'r') as f:
        line = f.readline()
        data = json.loads(line)
        
        assert 'timestamp' in data
        assert data['task_id'] == 'T007'
        assert data['action'] == 'stored'
        assert data['parameters']['W'] == 1.0
        assert data['parameters']['L'] == 100
        assert data['parameters']['realization_index'] == 0
        assert data['parameters']['seed'] == 42

def test_log_provenance_missing_fields(temp_config):
    """Test that missing required fields raise an error."""
    entry = {
        'task_id': 'T007',
        'action': 'stored',
        'input_files': [],
        'output_files': ['test.h5'],
        'checksums': {'test.h5': 'abc123'},
        'status': 'success'
    }
    
    with pytest.raises(ValueError, match="missing required field"):
        log_provenance_entry(entry)

def test_save_hamiltonian_to_hdf5(temp_config):
    """Test Hamiltonian saving and loading."""
    L = 10
    W = 1.0
    H = np.random.randn(L, L)
    H = (H + H.T) / 2  # Make symmetric
    
    file_path = save_hamiltonian_to_hdf5(H, W, L, 0, 42)
    
    assert os.path.exists(file_path)
    
    # Load and verify
    loaded = load_hamiltonian_from_hdf5(file_path)
    
    np.testing.assert_array_almost_equal(loaded['hamiltonian'], H)
    assert loaded['W'] == W
    assert loaded['L'] == L
    assert loaded['realization_index'] == 0
    assert loaded['seed'] == 42

def test_save_eigenstates_to_hdf5(temp_config):
    """Test eigenstate saving and provenance logging."""
    L = 10
    W = 1.0
    eigenvalues = np.random.randn(L)
    eigenvectors = np.random.randn(L, L)
    
    file_path = save_eigenstates_to_hdf5(
        eigenvalues, eigenvectors, W, L, 0, 42, 
        residual_norm=1e-8, converged=True
    )
    
    assert os.path.exists(file_path)
    
    # Verify HDF5 content
    with h5py.File(file_path, 'r') as f:
        np.testing.assert_array_almost_equal(np.array(f['eigenvalues']), eigenvalues)
        np.testing.assert_array_almost_equal(np.array(f['eigenvectors']), eigenvectors)
        assert f.attrs['W'] == W
        assert f.attrs['L'] == L
        assert f.attrs['realization_index'] == 0
        assert f.attrs['seed'] == 42
        assert f.attrs['residual_norm'] == 1e-8
        assert f.attrs['converged'] == True

def test_save_localization_length(temp_config):
    """Test localization length saving."""
    W = 1.0
    L = 100
    xi = 50.0
    fit_params = {'A': 1.0, 'xi_fit': 50.0, 'r_squared': 0.95}
    
    file_path = save_localization_length(xi, W, L, 0, 42, fit_params)
    
    assert os.path.exists(file_path)
    
    # Verify HDF5 content
    with h5py.File(file_path, 'r') as f:
        assert f.attrs['xi'] == xi
        assert f.attrs['W'] == W
        assert f.attrs['L'] == L
        assert f.attrs['realization_index'] == 0
        assert f.attrs['seed'] == 42
        assert f.attrs['fit_params/A'] == 1.0
        assert f.attrs['fit_params/r_squared'] == 0.95

def test_compute_sha256(temp_config):
    """Test SHA-256 checksum computation."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_file = f.name
    
    try:
        checksum = _compute_sha256(Path(temp_file))
        assert len(checksum) == 64  # SHA-256 hex length
        assert all(c in '0123456789abcdef' for c in checksum)
    finally:
        os.unlink(temp_file)
