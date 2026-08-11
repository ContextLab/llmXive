"""
Unit tests for T022c: generate_ground_truth.py
"""
import os
import sys
import tempfile
import numpy as np
import pytest
from pathlib import Path
import yaml

# Add project root to path if running from tests/
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.validation.generate_ground_truth import (
    load_real_adapter_weights,
    interpolate_adapters,
    validate_weights,
    generate_composite_task_desc
)

class TestInterpolateAdapters:
    def test_interpolation_shapes_match(self):
        """Test that interpolated matrices have correct shapes."""
        A_a = np.random.rand(4, 2)
        B_a = np.random.rand(2, 4)
        A_b = np.random.rand(4, 2)
        B_b = np.random.rand(2, 4)
        
        adapter_a = {'A': A_a, 'B': B_a}
        adapter_b = {'A': A_b, 'B': B_b}
        
        comp_A, comp_B = interpolate_adapters(adapter_a, adapter_b, alpha=0.5)
        
        assert comp_A.shape == (4, 2)
        assert comp_B.shape == (2, 4)

    def test_interpolation_values(self):
        """Test that interpolation values are mathematically correct."""
        A_a = np.ones((2, 2)) * 0.0
        B_a = np.ones((2, 2)) * 0.0
        A_b = np.ones((2, 2)) * 2.0
        B_b = np.ones((2, 2)) * 2.0
        
        adapter_a = {'A': A_a, 'B': B_a}
        adapter_b = {'A': A_b, 'B': B_b}
        
        # alpha = 0.5 -> result should be 1.0
        comp_A, comp_B = interpolate_adapters(adapter_a, adapter_b, alpha=0.5)
        
        assert np.allclose(comp_A, 1.0)
        assert np.allclose(comp_B, 1.0)

    def test_shape_mismatch_raises_error(self):
        """Test that shape mismatch raises ValueError."""
        A_a = np.random.rand(4, 2)
        B_a = np.random.rand(2, 4)
        A_b = np.random.rand(3, 2) # Mismatch
        B_b = np.random.rand(2, 4)
        
        adapter_a = {'A': A_a, 'B': B_a}
        adapter_b = {'A': A_b, 'B': B_b}
        
        with pytest.raises(ValueError):
            interpolate_adapters(adapter_a, adapter_b)

class TestValidateWeights:
    def test_valid_weights(self):
        """Test that valid weights pass validation."""
        A = np.random.rand(4, 4)
        B = np.random.rand(4, 4)
        assert validate_weights(A, B) is True

    def test_nan_weights_fail(self):
        """Test that NaN weights fail validation."""
        A = np.random.rand(4, 4)
        B = np.random.rand(4, 4)
        B[0, 0] = np.nan
        assert validate_weights(A, B) is False

    def test_zero_weights_fail(self):
        """Test that zero weights fail validation."""
        A = np.zeros((4, 4))
        B = np.random.rand(4, 4)
        assert validate_weights(A, B) is False

class TestGenerateCompositeDesc:
    def test_desc_generation(self):
        """Test description generation."""
        desc_a = "Task A"
        desc_b = "Task B"
        result = generate_composite_task_desc(desc_a, desc_b)
        assert "Task A" in result
        assert "Task B" in result
        assert "Composite" in result

class TestLoadRealAdapterWeights:
    def test_no_files_raises_error(self):
        """Test that missing files raise FileNotFoundError."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            with pytest.raises(FileNotFoundError):
                load_real_adapter_weights(Path(tmp_dir))

    def test_load_valid_adapter(self):
        """Test loading a valid adapter file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            # Create a dummy npz file
            A = np.random.rand(4, 2)
            B = np.random.rand(2, 4)
            np.savez(tmp_path / "test_task_weights.npz", A=A, B=B)
            
            adapters = load_real_adapter_weights(tmp_path)
            
            assert "test_task" in adapters
            assert adapters["test_task"]["A"].shape == (4, 2)
            assert adapters["test_task"]["B"].shape == (2, 4)
            assert "desc" in adapters["test_task"]
