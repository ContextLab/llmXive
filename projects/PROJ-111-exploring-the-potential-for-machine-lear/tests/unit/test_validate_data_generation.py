"""
Unit tests for the validation logic in T012.
Tests the shape, normalization, and temperature coverage checks.
"""
import unittest
import numpy as np
from pathlib import Path
import tempfile
import os

# Import the validation logic if we extract it, 
# but for T012 we are testing the script's behavior via integration or mocking.
# Since the script is a standalone runner, we will test the helper functions
# by replicating the logic or importing if refactored.
# For this task, we will simulate the validation checks on mock data.

def validate_data_content_logic(file_path):
    """Replicate the validation logic for testing."""
    errors = []
    try:
        data = np.load(file_path)
    except Exception as e:
        errors.append(f"Failed to load {file_path}: {e}")
        return errors

    if 'spins' not in data:
        errors.append(f"Missing 'spins' key in {file_path}")
        return errors
    
    if 'temperatures' not in data:
        errors.append(f"Missing 'temperatures' key in {file_path}")
    
    spins = data['spins']
    temps = data['temperatures'] if 'temperatures' in data else []
    
    if spins.ndim != 4:
        errors.append(f"Spins in {file_path} are not 4D (got {spins.ndim}D).")
        return errors

    N, dim, L_x, L_y = spins.shape
    if L_x != L_y:
        errors.append(f"Non-square lattice in {file_path}: {L_x}x{L_y}")
    
    L = L_x
    expected_model = "heisenberg" if dim == 3 else ("xy" if dim == 2 else "unknown")
    
    if expected_model not in ["heisenberg", "xy"]:
        errors.append(f"Unexpected spin dimension {dim} in {file_path}.")
    
    if L not in [16, 24]:
        errors.append(f"Lattice size {L} in {file_path} not in expected set [16, 24].")

    if len(temps) > 0:
        min_t, max_t = float(np.min(temps)), float(np.max(temps))
        if min_t < 0.1 - 0.01 or max_t > 3.0 + 0.01:
            errors.append(f"Temperature range [{min_t}, {max_t}] in {file_path} outside expected [0.1, 3.0].")
    
    norms = np.linalg.norm(spins, axis=1)
    if not np.allclose(norms, 1.0, atol=1e-5):
        off_count = np.sum(~np.isclose(norms, 1.0, atol=1e-5))
        errors.append(f"Unit norm violation in {file_path}: {off_count} vectors not normalized.")

    return errors

class TestDataValidation(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_valid_heisenberg(self):
        """Test a valid Heisenberg data file."""
        L = 16
        N = 100
        spins = np.random.randn(N, 3, L, L)
        norms = np.linalg.norm(spins, axis=1, keepdims=True)
        spins = spins / norms
        
        temps = np.linspace(0.1, 3.0, 30)
        
        path = Path(self.temp_dir) / "test_heisenberg.npz"
        np.savez(path, spins=spins, temperatures=temps)
        
        errors = validate_data_content_logic(path)
        self.assertEqual(len(errors), 0, f"Unexpected errors: {errors}")

    def test_invalid_norm(self):
        """Test detection of non-unit norms."""
        L = 24
        N = 50
        spins = np.random.randn(N, 3, L, L)
        # Do not normalize
        
        path = Path(self.temp_dir) / "test_bad_norm.npz"
        np.savez(path, spins=spins, temperatures=np.array([1.0]))
        
        errors = validate_data_content_logic(path)
        self.assertTrue(any("Unit norm violation" in e for e in errors))

    def test_wrong_lattice_size(self):
        """Test detection of invalid lattice size."""
        L = 32  # Invalid
        N = 10
        spins = np.random.randn(N, 3, L, L)
        norms = np.linalg.norm(spins, axis=1, keepdims=True)
        spins = spins / norms
        
        path = Path(self.temp_dir) / "test_bad_l.npz"
        np.savez(path, spins=spins, temperatures=np.array([1.0]))
        
        errors = validate_data_content_logic(path)
        self.assertTrue(any("Lattice size 32" in e for e in errors))

    def test_wrong_dimension(self):
        """Test detection of wrong spin dimension (e.g. 4D)."""
        L = 16
        N = 10
        spins = np.random.randn(N, 4, L, L) # Invalid
        
        path = Path(self.temp_dir) / "test_bad_dim.npz"
        np.savez(path, spins=spins, temperatures=np.array([1.0]))
        
        errors = validate_data_content_logic(path)
        self.assertTrue(any("Unexpected spin dimension 4" in e for e in errors))

    def test_temperature_range(self):
        """Test detection of out-of-range temperatures."""
        L = 16
        N = 10
        spins = np.random.randn(N, 3, L, L)
        norms = np.linalg.norm(spins, axis=1, keepdims=True)
        spins = spins / norms
        
        # Temp range 0.05 to 5.0
        temps = np.array([0.05, 5.0])
        
        path = Path(self.temp_dir) / "test_bad_temp.npz"
        np.savez(path, spins=spins, temperatures=temps)
        
        errors = validate_data_content_logic(path)
        self.assertTrue(any("Temperature range" in e for e in errors))

if __name__ == '__main__':
    unittest.main()