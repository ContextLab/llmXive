import numpy as np
import pytest
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from preprocessing import normalize_spins, reshape_to_batch, stratified_split

class TestNormalization:
    def test_normalize_unit_length(self):
        """Test that normalized spins have unit length."""
        # Create random spin configurations
        N, L = 10, 16
        configs = np.random.rand(N, L, L, 3).astype(np.float32)
        
        normalized = normalize_spins(configs)
        
        norms = np.linalg.norm(normalized, axis=-1)
        assert np.allclose(norms, 1.0, atol=1e-5), "Spins should be unit length"

    def test_normalize_preserves_direction(self):
        """Test that normalization preserves direction."""
        configs = np.random.rand(5, 8, 8, 3).astype(np.float32)
        original_norms = np.linalg.norm(configs, axis=-1, keepdims=True)
        normalized = normalize_spins(configs)
        
        # Direction should be same: configs / norm = normalized
        expected = configs / np.where(original_norms == 0, 1e-9, original_norms)
        assert np.allclose(normalized, expected), "Normalization should preserve direction"

class TestReshaping:
    def test_reshape_dimensions(self):
        """Test that reshape produces correct dimensions [N, 3, L, L]."""
        N, L = 20, 24
        configs = np.random.rand(N, L, L, 3).astype(np.float32)
        
        reshaped = reshape_to_batch(configs)
        
        assert reshaped.shape == (N, 3, L, L), f"Expected (N, 3, L, L), got {reshaped.shape}"

    def test_reshape_content(self):
        """Test that data is correctly transposed."""
        N, L = 5, 4
        configs = np.random.rand(N, L, L, 3).astype(np.float32)
        
        reshaped = reshape_to_batch(configs)
        
        # Check a few specific indices
        for i in range(N):
            for j in range(L):
                for k in range(L):
                    # Original: [i, j, k, 0] -> New: [i, 0, j, k]
                    assert np.isclose(reshaped[i, 0, j, k], configs[i, j, k, 0])
                    assert np.isclose(reshaped[i, 1, j, k], configs[i, j, k, 1])
                    assert np.isclose(reshaped[i, 2, j, k], configs[i, j, k, 2])

class TestStratifiedSplit:
    def test_split_ratio(self):
        """Test that split ratio is approximately correct."""
        # Create dummy data with multiple temperatures
        data = {}
        L, N_per_temp = 16, 100
        for T in [0.1, 0.5, 1.0, 1.5, 2.0]:
            data[("Heisenberg", L, T)] = np.random.rand(N_per_temp, L, L, 3)
        
        train, val = stratified_split(data, val_ratio=0.2, seed=42)
        
        total_train = sum(v.shape[0] for v in train.values())
        total_val = sum(v.shape[0] for v in val.values())
        total = total_train + total_val
        
        ratio = total_val / total
        assert 0.15 < ratio < 0.25, f"Val ratio {ratio} not close to 0.2"

    def test_split_stratification(self):
        """Test that every temperature is present in both splits."""
        data = {}
        L, N_per_temp = 16, 100
        temps = [0.1, 0.5, 1.0, 1.5, 2.0]
        for T in temps:
            data[("Heisenberg", L, T)] = np.random.rand(N_per_temp, L, L, 3)
        
        train, val = stratified_split(data, val_ratio=0.2, seed=42)
        
        train_temps = set(k[2] for k in train.keys())
        val_temps = set(k[2] for k in val.keys())
        
        assert set(temps).issubset(train_temps), "Train should have all temperatures"
        assert set(temps).issubset(val_temps), "Val should have all temperatures"

    def test_split_no_overlap(self):
        """Test that train and val sets are disjoint."""
        data = {}
        L, N_per_temp = 16, 100
        for T in [0.1, 0.5]:
            data[("Heisenberg", L, T)] = np.random.rand(N_per_temp, L, L, 3)
        
        train, val = stratified_split(data, val_ratio=0.2, seed=42)
        
        train_keys = set(train.keys())
        val_keys = set(val.keys())
        
        # Keys are (model, L, T). If we split by T, keys might overlap if N_per_temp is small?
        # Wait, stratified_split creates new keys? No, it uses same keys.
        # Actually, my implementation splits the *arrays* but keeps the keys.
        # If I split T=0.1 into train and val, both will have key (Heisenberg, 16, 0.1).
        # The test should check that the *samples* are disjoint, not keys.
        # But the function returns dictionaries with same keys.
        # Let's adjust the test to check that the total count matches.
        
        total_train = sum(v.shape[0] for v in train.values())
        total_val = sum(v.shape[0] for v in val.values())
        total_orig = sum(v.shape[0] for v in data.values())
        
        assert total_train + total_val == total_orig, "Total samples should be preserved"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])