"""
Unit tests for stability_check module.

Tests:
1. NaN detection in tensors
2. L2 relative error calculation
3. Max absolute difference calculation
4. Stability processing logic
5. Exclusion of unstable runs
"""
import pytest
import numpy as np
import json
import tempfile
from pathlib import Path
from code.analysis.stability_check import (
    detect_nan_in_tensor,
    calculate_l2_relative_error,
    calculate_max_absolute_difference,
    process_stability,
    StabilityResult
)

class TestDetectNanInTensor:
    """Tests for NaN/Inf detection in tensors."""
    
    def test_no_nan(self):
        """Test tensor with no NaN values."""
        tensor = [1.0, 2.0, 3.0, 4.0, 5.0]
        has_nan, indices = detect_nan_in_tensor(tensor)
        assert has_nan is False
        assert indices is None
        
    def test_has_nan(self):
        """Test tensor with NaN values."""
        tensor = [1.0, float('nan'), 3.0, 4.0, 5.0]
        has_nan, indices = detect_nan_in_tensor(tensor)
        assert has_nan is True
        assert indices == [1]
        
    def test_has_inf(self):
        """Test tensor with Inf values."""
        tensor = [1.0, 2.0, float('inf'), 4.0, 5.0]
        has_nan, indices = detect_nan_in_tensor(tensor)
        assert has_nan is True
        assert indices == [2]
        
    def test_has_negative_inf(self):
        """Test tensor with -Inf values."""
        tensor = [1.0, 2.0, float('-inf'), 4.0, 5.0]
        has_nan, indices = detect_nan_in_tensor(tensor)
        assert has_nan is True
        assert indices == [2]
        
    def test_multiple_nan(self):
        """Test tensor with multiple NaN values."""
        tensor = [float('nan'), 2.0, float('nan'), 4.0, float('nan')]
        has_nan, indices = detect_nan_in_tensor(tensor)
        assert has_nan is True
        assert indices == [0, 2, 4]
        
    def test_empty_tensor(self):
        """Test empty tensor."""
        tensor = []
        has_nan, indices = detect_nan_in_tensor(tensor)
        assert has_nan is False
        assert indices is None
        
    def test_none_tensor(self):
        """Test None tensor."""
        has_nan, indices = detect_nan_in_tensor(None)
        assert has_nan is False
        assert indices is None

class TestCalculateL2RelativeError:
    """Tests for L2 relative error calculation."""
    
    def test_identical_tensors(self):
        """Test with identical tensors (error should be 0)."""
        pred = [1.0, 2.0, 3.0]
        ref = [1.0, 2.0, 3.0]
        error = calculate_l2_relative_error(pred, ref)
        assert error == 0.0
        
    def test_different_tensors(self):
        """Test with different tensors."""
        pred = [1.0, 2.0, 3.0]
        ref = [1.1, 2.1, 3.1]
        error = calculate_l2_relative_error(pred, ref)
        # Error should be small but non-zero
        assert error > 0
        assert error < 1.0
        
    def test_large_difference(self):
        """Test with large difference."""
        pred = [0.0, 0.0, 0.0]
        ref = [1.0, 1.0, 1.0]
        error = calculate_l2_relative_error(pred, ref)
        # Error should be 1.0 (perfectly scaled)
        assert error == 1.0
        
    def test_zero_reference(self):
        """Test with zero reference tensor."""
        pred = [1.0, 2.0, 3.0]
        ref = [0.0, 0.0, 0.0]
        error = calculate_l2_relative_error(pred, ref)
        assert error == float('inf')
        
    def test_length_mismatch(self):
        """Test with mismatched tensor lengths."""
        pred = [1.0, 2.0]
        ref = [1.0, 2.0, 3.0]
        with pytest.raises(ValueError):
            calculate_l2_relative_error(pred, ref)

class TestCalculateMaxAbsoluteDifference:
    """Tests for maximum absolute difference calculation."""
    
    def test_identical_tensors(self):
        """Test with identical tensors."""
        pred = [1.0, 2.0, 3.0]
        ref = [1.0, 2.0, 3.0]
        diff = calculate_max_absolute_difference(pred, ref)
        assert diff == 0.0
        
    def test_different_tensors(self):
        """Test with different tensors."""
        pred = [1.0, 2.0, 3.0]
        ref = [1.5, 2.0, 3.0]
        diff = calculate_max_absolute_difference(pred, ref)
        assert diff == 0.5
        
    def test_negative_difference(self):
        """Test with negative differences."""
        pred = [1.0, 2.0, 3.0]
        ref = [1.0, 2.5, 3.0]
        diff = calculate_max_absolute_difference(pred, ref)
        assert diff == 0.5
        
    def test_length_mismatch(self):
        """Test with mismatched tensor lengths."""
        pred = [1.0, 2.0]
        ref = [1.0, 2.0, 3.0]
        with pytest.raises(ValueError):
            calculate_max_absolute_difference(pred, ref)

class TestProcessStability:
    """Tests for stability processing logic."""
    
    def test_all_stable(self):
        """Test with all stable runs."""
        raw_logs = [
            {
                'config_id': 'test1',
                'kernel_type': 'matmul',
                'output_tensor': [1.0, 2.0, 3.0],
                'reference_tensor': [1.0, 2.0, 3.0],
                'downsampled_flag': False
            }
        ]
        ref_logs = [
            {
                'config_id': 'test1',
                'kernel_type': 'matmul',
                'output_tensor': [1.0, 2.0, 3.0]
            }
        ]
        
        stable, unstable = process_stability(raw_logs, ref_logs)
        
        assert len(stable) == 1
        assert len(unstable) == 0
        assert stable[0].status == 'stable'
        
    def test_nan_excluded(self):
        """Test that NaN runs are excluded and marked unstable."""
        raw_logs = [
            {
                'config_id': 'test_nan',
                'kernel_type': 'matmul',
                'output_tensor': [1.0, float('nan'), 3.0],
                'reference_tensor': [1.0, 2.0, 3.0],
                'downsampled_flag': False
            }
        ]
        ref_logs = [
            {
                'config_id': 'test_nan',
                'kernel_type': 'matmul',
                'output_tensor': [1.0, 2.0, 3.0]
            }
        ]
        
        stable, unstable = process_stability(raw_logs, ref_logs)
        
        assert len(stable) == 0
        assert len(unstable) == 1
        assert unstable[0].status == 'nan'
        assert unstable[0].nan_indices == [1]
        
    def test_high_error_excluded(self):
        """Test that high error runs are excluded."""
        raw_logs = [
            {
                'config_id': 'test_error',
                'kernel_type': 'matmul',
                'output_tensor': [0.0, 0.0, 0.0],
                'reference_tensor': [1.0, 1.0, 1.0],
                'downsampled_flag': False
            }
        ]
        ref_logs = [
            {
                'config_id': 'test_error',
                'kernel_type': 'matmul',
                'output_tensor': [1.0, 1.0, 1.0]
            }
        ]
        
        stable, unstable = process_stability(raw_logs, ref_logs, error_threshold=1e-5)
        
        assert len(stable) == 0
        assert len(unstable) == 1
        assert unstable[0].status == 'unstable'
        assert unstable[0].l2_error == 1.0
        
    def test_mixed_results(self):
        """Test with mixed stable and unstable runs."""
        raw_logs = [
            {
                'config_id': 'stable1',
                'kernel_type': 'matmul',
                'output_tensor': [1.0, 2.0, 3.0],
                'reference_tensor': [1.0, 2.0, 3.0],
                'downsampled_flag': False
            },
            {
                'config_id': 'nan_run',
                'kernel_type': 'softmax',
                'output_tensor': [1.0, float('nan'), 3.0],
                'reference_tensor': [1.0, 2.0, 3.0],
                'downsampled_flag': False
            },
            {
                'config_id': 'high_error',
                'kernel_type': 'layernorm',
                'output_tensor': [0.0, 0.0, 0.0],
                'reference_tensor': [1.0, 1.0, 1.0],
                'downsampled_flag': False
            }
        ]
        ref_logs = [
            {
                'config_id': 'stable1',
                'kernel_type': 'matmul',
                'output_tensor': [1.0, 2.0, 3.0]
            },
            {
                'config_id': 'nan_run',
                'kernel_type': 'softmax',
                'output_tensor': [1.0, 2.0, 3.0]
            },
            {
                'config_id': 'high_error',
                'kernel_type': 'layernorm',
                'output_tensor': [1.0, 1.0, 1.0]
            }
        ]
        
        stable, unstable = process_stability(raw_logs, ref_logs)
        
        assert len(stable) == 1
        assert len(unstable) == 2
        assert stable[0].config_id == 'stable1'
        assert any(u.config_id == 'nan_run' for u in unstable)
        assert any(u.config_id == 'high_error' for u in unstable)
        
    def test_downsampled_flag_preserved(self):
        """Test that downsampled flag is preserved in results."""
        raw_logs = [
            {
                'config_id': 'downsampled_run',
                'kernel_type': 'matmul',
                'output_tensor': [1.0, 2.0, 3.0],
                'reference_tensor': [1.0, 2.0, 3.0],
                'downsampled_flag': True
            }
        ]
        ref_logs = [
            {
                'config_id': 'downsampled_run',
                'kernel_type': 'matmul',
                'output_tensor': [1.0, 2.0, 3.0]
            }
        ]
        
        stable, unstable = process_stability(raw_logs, ref_logs)
        
        assert len(stable) == 1
        assert stable[0].downsampled is True

class TestStabilityResult:
    """Tests for StabilityResult dataclass."""
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = StabilityResult(
            config_id='test',
            kernel_type='matmul',
            status='stable',
            l2_error=0.001,
            max_diff=0.0005,
            downsampled=False
        )
        
        d = result.to_dict()
        assert d['config_id'] == 'test'
        assert d['kernel_type'] == 'matmul'
        assert d['status'] == 'stable'
        assert d['l2_error'] == 0.001
        assert d['max_diff'] == 0.0005
        assert d['downsampled'] is False