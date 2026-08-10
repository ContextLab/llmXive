"""
Tests for T022c: generate_ground_truth.py
"""
import os
import sys
import tempfile
import numpy as np
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.validation.generate_ground_truth import (
    load_real_weights,
    interpolate_adapters,
    validate_weights
)

class TestGenerateGroundTruth:
    
    def test_interpolate_adapters_shapes(self):
        """Test that interpolation preserves shapes."""
        A1 = np.ones((10, 10))
        B1 = np.ones((10, 10))
        A2 = np.zeros((10, 10))
        B2 = np.zeros((10, 10))
        
        A_comp, B_comp = interpolate_adapters(A1, B1, A2, B2, alpha=0.5)
        
        assert A_comp.shape == (10, 10)
        assert B_comp.shape == (10, 10)
        # At alpha=0.5, result should be 0.5
        assert np.allclose(A_comp, 0.5)
        assert np.allclose(B_comp, 0.5)

    def test_interpolate_adapters_mismatch_shapes(self):
        """Test that shape mismatch raises ValueError."""
        A1 = np.ones((10, 10))
        B1 = np.ones((10, 10))
        A2 = np.zeros((5, 5)) # Mismatch
        B2 = np.zeros((5, 5))
        
        with pytest.raises(ValueError, match="Shape mismatch"):
            interpolate_adapters(A1, B1, A2, B2)

    def test_validate_weights_nan(self):
        """Test that NaN validation fails."""
        A = np.ones((10, 10))
        A[0, 0] = np.nan
        B = np.ones((10, 10))
        
        with pytest.raises(ValueError, match="NaN values detected"):
            validate_weights(A, B, "test_task")

    def test_validate_weights_zero(self):
        """Test that zero validation fails."""
        A = np.zeros((10, 10))
        B = np.zeros((10, 10))
        
        with pytest.raises(ValueError, match="Zero weights detected"):
            validate_weights(A, B, "test_task")

    def test_validate_weights_success(self):
        """Test that valid weights pass."""
        A = np.ones((10, 10))
        B = np.ones((10, 10))
        
        # Should not raise
        validate_weights(A, B, "test_task")

    def test_load_real_weights_missing_file(self):
        """Test that missing file raises FileNotFoundError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_path = Path(tmpdir) / "nonexistent.npz"
            with pytest.raises(FileNotFoundError):
                load_real_weights(fake_path)

    def test_load_real_weights_invalid_keys(self):
        """Test that invalid keys raise ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_path = Path(tmpdir) / "bad.npz"
            np.savez(fake_path, X=np.ones((10, 10)), Y=np.ones((10, 10)))
            
            with pytest.raises(ValueError, match="Expected keys 'A' and 'B'"):
                load_real_weights(fake_path)

    def test_load_real_weights_success(self):
        """Test successful loading of valid file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_path = Path(tmpdir) / "good.npz"
            A_val = np.ones((5, 5))
            B_val = np.zeros((5, 5))
            np.savez(fake_path, A=A_val, B=B_val)
            
            A_loaded, B_loaded = load_real_weights(fake_path)
            
            assert np.array_equal(A_loaded, A_val)
            assert np.array_equal(B_loaded, B_val)