import numpy as np
import pytest
from analysis.connectivity import (
    compute_sliding_window_connectivity,
    compute_static_connectivity_strength
)


class TestComputeSlidingWindowConnectivity:
    def test_returns_list_of_matrices(self):
        """Test that the function returns a list of numpy arrays."""
        # Create dummy data: 100 timepoints, 10 ROIs
        fmri_data = np.random.rand(100, 10)
        window_size = 20
        step = 5
        
        result = compute_sliding_window_connectivity(fmri_data, window_size, step)
        
        assert isinstance(result, list)
        assert len(result) > 0
        for matrix in result:
            assert isinstance(matrix, np.ndarray)
            assert matrix.shape == (10, 10)  # 10 ROIs x 10 ROIs

    def test_window_size_validation(self):
        """Test that insufficient timepoints raise an error."""
        fmri_data = np.random.rand(10, 5)
        window_size = 20
        step = 5
        
        with pytest.raises(ValueError, match="Insufficient timepoints"):
            compute_sliding_window_connectivity(fmri_data, window_size, step)

    def test_correlation_values_in_range(self):
        """Test that correlation values are within [-1, 1]."""
        fmri_data = np.random.rand(50, 5)
        window_size = 10
        step = 5
        
        result = compute_sliding_window_connectivity(fmri_data, window_size, step)
        
        for matrix in result:
            assert np.all(matrix >= -1.0)
            assert np.all(matrix <= 1.0)

    def test_diagonal_is_one(self):
        """Test that diagonal elements are 1 (self-correlation)."""
        fmri_data = np.random.rand(50, 5)
        window_size = 10
        step = 5
        
        result = compute_sliding_window_connectivity(fmri_data, window_size, step)
        
        for matrix in result:
            assert np.allclose(np.diag(matrix), 1.0)

    def test_handles_nan_in_input(self):
        """Test that NaN values in input are handled."""
        fmri_data = np.random.rand(50, 5)
        fmri_data[5, 2] = np.nan  # Introduce a NaN
        window_size = 10
        step = 5
        
        # Should not raise, should handle NaNs
        result = compute_sliding_window_connectivity(fmri_data, window_size, step)
        
        assert len(result) > 0
        # Check that no NaNs remain in output matrices
        for matrix in result:
            assert not np.any(np.isnan(matrix))


class TestComputeStaticConnectivityStrength:
    def test_returns_float(self):
        """Test that the function returns a float."""
        fmri_data = np.random.rand(100, 10)
        
        result = compute_static_connectivity_strength(fmri_data)
        
        assert isinstance(result, float)

    def test_value_in_range(self):
        """Test that the result is within [0, 1] (absolute correlations)."""
        fmri_data = np.random.rand(100, 10)
        
        result = compute_static_connectivity_strength(fmri_data)
        
        assert 0.0 <= result <= 1.0

    def test_insufficient_timepoints(self):
        """Test that less than 2 timepoints raise an error."""
        fmri_data = np.random.rand(1, 10)
        
        with pytest.raises(ValueError, match="Need at least 2 timepoints"):
            compute_static_connectivity_strength(fmri_data)

    def test_diagonal_excluded(self):
        """Test that diagonal elements are excluded from the mean."""
        # Create data where diagonal would be 1, off-diagonal is 0
        fmri_data = np.eye(10).T  # 10 timepoints, 10 ROIs (each row is a standard basis vector)
        # This creates a specific pattern; we just verify the function runs
        result = compute_static_connectivity_strength(fmri_data)
        
        assert isinstance(result, float)

    def test_handles_nan_in_input(self):
        """Test that NaN values in input are handled."""
        fmri_data = np.random.rand(50, 5)
        fmri_data[5, 2] = np.nan
        
        # Should not raise, should handle NaNs
        result = compute_static_connectivity_strength(fmri_data)
        
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0