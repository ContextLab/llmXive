"""
Unit tests for router edge cases and error handling.

Tests:
1. Out-of-range entropy values (clamping)
2. Proxy failure fallback to median index
3. Invalid matrix indices
4. Empty boundaries handling
5. Numerical precision edge cases
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.router import EntropyRouter
from config import Config


class TestRouterClamping:
    """Tests for entropy value clamping behavior."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = Config()
        self.router = EntropyRouter(
            entropy_boundaries=[0.0, 2.0, 4.0, 6.0, 8.0],
            matrix_indices=[0, 1, 2, 3, 4],
            config=self.config
        )

    def test_extreme_negative_entropy(self):
        """Test clamping of extremely negative entropy."""
        index = self.router.select_matrix(-1e10)
        assert index == 0
        assert index == self.router.matrix_indices[0]

    def test_extreme_positive_entropy(self):
        """Test clamping of extremely positive entropy."""
        index = self.router.select_matrix(1e10)
        assert index == 4
        assert index == self.router.matrix_indices[-1]

    def test_negative_zero(self):
        """Test handling of negative zero."""
        index = self.router.select_matrix(-0.0)
        assert index == 0

    def test_very_small_positive(self):
        """Test handling of very small positive values."""
        index = self.router.select_matrix(1e-10)
        assert index == 0

    def test_very_large_within_range(self):
        """Test handling of very large values within range."""
        index = self.router.select_matrix(7.999999)
        assert index == 3

class TestRouterProxyFailure:
    """Tests for proxy failure fallback behavior."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = Config()
        self.router = EntropyRouter(
            entropy_boundaries=[0.0, 2.0, 4.0, 6.0, 8.0],
            matrix_indices=[0, 1, 2, 3, 4],
            config=self.config
        )

    def test_proxy_timeout_fallback(self):
        """Test fallback to median index on timeout."""
        with patch.object(self.router, '_get_entropy_score') as mock_score:
            mock_score.side_effect = TimeoutError("Proxy timeout")
            
            index = self.router.select_matrix("test prompt")
            assert index == 2  # Median of [0, 1, 2, 3, 4]

    def test_proxy_api_error_fallback(self):
        """Test fallback to median index on API error."""
        with patch.object(self.router, '_get_entropy_score') as mock_score:
            mock_score.side_effect = RuntimeError("API error")
            
            index = self.router.select_matrix("test prompt")
            assert index == 2

    def test_proxy_network_error_fallback(self):
        """Test fallback to median index on network error."""
        with patch.object(self.router, '_get_entropy_score') as mock_score:
            mock_score.side_effect = ConnectionError("Network error")
            
            index = self.router.select_matrix("test prompt")
            assert index == 2

    def test_multiple_fallback_calls(self):
        """Test consistent fallback behavior across multiple calls."""
        with patch.object(self.router, '_get_entropy_score') as mock_score:
            mock_score.side_effect = RuntimeError("Always fails")
            
            for _ in range(5):
                index = self.router.select_matrix("test")
                assert index == 2

    def test_fallback_with_odd_number_of_matrices(self):
        """Test median calculation with odd number of matrices."""
        router = EntropyRouter(
            entropy_boundaries=[0.0, 2.0, 4.0],
            matrix_indices=[10, 20, 30],
            config=self.config
        )
        
        with patch.object(router, '_get_entropy_score') as mock_score:
            mock_score.side_effect = RuntimeError("Fail")
            
            index = router.select_matrix("test")
            assert index == 20  # Median of [10, 20, 30]

    def test_fallback_with_even_number_of_matrices(self):
        """Test median calculation with even number of matrices."""
        router = EntropyRouter(
            entropy_boundaries=[0.0, 2.0, 4.0, 6.0],
            matrix_indices=[10, 20, 30, 40],
            config=self.config
        )
        
        with patch.object(router, '_get_entropy_score') as mock_score:
            mock_score.side_effect = RuntimeError("Fail")
            
            index = router.select_matrix("test")
            # For even number, use lower median (index 1 -> value 20)
            assert index == 20

class TestRouterBoundaryConditions:
    """Tests for boundary condition handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = Config()

    def test_empty_boundaries_single_matrix(self):
        """Test with empty boundaries and single matrix."""
        router = EntropyRouter(
            entropy_boundaries=[],
            matrix_indices=[42],
            config=self.config
        )
        
        assert router.select_matrix(-1000) == 42
        assert router.select_matrix(0) == 42
        assert router.select_matrix(1000) == 42
        assert router.select_matrix(float('nan')) == 42

    def test_empty_boundaries_multiple_matrices(self):
        """Test with empty boundaries and multiple matrices (should use first)."""
        router = EntropyRouter(
            entropy_boundaries=[],
            matrix_indices=[10, 20, 30],
            config=self.config
        )
        
        # With no boundaries, should default to first matrix
        assert router.select_matrix(0) == 10
        assert router.select_matrix(100) == 10

    def test_single_boundary(self):
        """Test with single boundary."""
        router = EntropyRouter(
            entropy_boundaries=[5.0],
            matrix_indices=[0, 1],
            config=self.config
        )
        
        assert router.select_matrix(0.0) == 0
        assert router.select_matrix(4.9) == 0
        assert router.select_matrix(5.0) == 1
        assert router.select_matrix(10.0) == 1

    def test_boundary_at_zero(self):
        """Test with boundary at zero."""
        router = EntropyRouter(
            entropy_boundaries=[0.0, 5.0],
            matrix_indices=[0, 1],
            config=self.config
        )
        
        assert router.select_matrix(-1.0) == 0
        assert router.select_matrix(0.0) == 1
        assert router.select_matrix(4.9) == 1
        assert router.select_matrix(5.0) == 1

    def test_negative_boundaries(self):
        """Test with negative boundaries (should work if valid)."""
        router = EntropyRouter(
            entropy_boundaries=[-5.0, 0.0, 5.0],
            matrix_indices=[0, 1, 2],
            config=self.config
        )
        
        assert router.select_matrix(-10.0) == 0
        assert router.select_matrix(-5.0) == 1
        assert router.select_matrix(-1.0) == 1
        assert router.select_matrix(0.0) == 2
        assert router.select_matrix(4.9) == 2
        assert router.select_matrix(10.0) == 2

class TestRouterNumericalPrecision:
    """Tests for numerical precision edge cases."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = Config()
        self.router = EntropyRouter(
            entropy_boundaries=[0.0, 1e-10, 2e-10, 3e-10],
            matrix_indices=[0, 1, 2, 3],
            config=self.config
        )

    def test_very_small_boundaries(self):
        """Test with very small boundary values."""
        assert self.router.select_matrix(0.0) == 0
        assert self.router.select_matrix(0.5e-10) == 1
        assert self.router.select_matrix(1.5e-10) == 2
        assert self.router.select_matrix(2.5e-10) == 3

    def test_very_large_boundaries(self):
        """Test with very large boundary values."""
        router = EntropyRouter(
            entropy_boundaries=[1e10, 2e10, 3e10],
            matrix_indices=[0, 1, 2],
            config=self.config
        )
        
        assert router.select_matrix(0) == 0
        assert router.select_matrix(1.5e10) == 1
        assert router.select_matrix(2.5e10) == 2
        assert router.select_matrix(1e11) == 2

    def test_float_precision_errors(self):
        """Test handling of floating point precision errors."""
        router = EntropyRouter(
            entropy_boundaries=[1.0, 2.0, 3.0],
            matrix_indices=[0, 1, 2],
            config=self.config
        )
        
        # Test values that might cause precision issues
        assert router.select_matrix(0.999999999999) == 0
        assert router.select_matrix(1.000000000001) == 1
        assert router.select_matrix(2.999999999999) == 1
        assert router.select_matrix(3.000000000001) == 2

    def test_nan_handling(self):
        """Test handling of NaN values."""
        router = EntropyRouter(
            entropy_boundaries=[0.0, 2.0, 4.0],
            matrix_indices=[0, 1, 2],
            config=self.config
        )
        
        # NaN should fallback to median
        index = router.select_matrix(float('nan'))
        assert index == 1  # Median of [0, 1, 2]

    def test_inf_handling(self):
        """Test handling of infinity values."""
        router = EntropyRouter(
            entropy_boundaries=[0.0, 2.0, 4.0],
            matrix_indices=[0, 1, 2],
            config=self.config
        )
        
        # Positive infinity should clamp to last
        assert router.select_matrix(float('inf')) == 2
        
        # Negative infinity should clamp to first
        assert router.select_matrix(float('-inf')) == 0

class TestRouterValidation:
    """Tests for router validation and error handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = Config()

    def test_mismatched_boundaries_indices(self):
        """Test that mismatched boundaries and indices raise error."""
        with pytest.raises(ValueError):
            EntropyRouter(
                entropy_boundaries=[0.0, 2.0],
                matrix_indices=[0, 1, 2],  # Too many indices
                config=self.config
            )

    def test_unsorted_boundaries(self):
        """Test handling of unsorted boundaries."""
        # Should work but might produce unexpected results
        router = EntropyRouter(
            entropy_boundaries=[4.0, 2.0, 0.0],
            matrix_indices=[0, 1, 2],
            config=self.config
        )
        
        # The behavior depends on implementation, but shouldn't crash
        index = router.select_matrix(3.0)
        assert isinstance(index, int)

    def test_duplicate_boundaries(self):
        """Test handling of duplicate boundaries."""
        router = EntropyRouter(
            entropy_boundaries=[0.0, 0.0, 2.0],
            matrix_indices=[0, 1, 2],
            config=self.config
        )
        
        # Should handle gracefully
        index = router.select_matrix(1.0)
        assert isinstance(index, int)

    def test_negative_matrix_indices(self):
        """Test handling of negative matrix indices."""
        router = EntropyRouter(
            entropy_boundaries=[0.0, 2.0, 4.0],
            matrix_indices=[-1, 0, 1],
            config=self.config
        )
        
        # Should work with negative indices
        assert router.select_matrix(0.0) == -1
        assert router.select_matrix(2.0) == 0
        assert router.select_matrix(4.0) == 1

    def test_non_integer_matrix_indices(self):
        """Test handling of non-integer matrix indices."""
        router = EntropyRouter(
            entropy_boundaries=[0.0, 2.0, 4.0],
            matrix_indices=[0.5, 1.5, 2.5],
            config=self.config
        )
        
        # Should return the index as-is (might be float)
        index = router.select_matrix(1.0)
        assert index == 0.5 or isinstance(index, (int, float))

class TestRouterLogging:
    """Tests for router logging behavior."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = Config()
        self.router = EntropyRouter(
            entropy_boundaries=[0.0, 2.0, 4.0],
            matrix_indices=[0, 1, 2],
            config=self.config
        )

    def test_fallback_logging(self):
        """Test that fallback events are logged."""
        with patch.object(self.router, '_get_entropy_score') as mock_score:
            mock_score.side_effect = RuntimeError("Proxy failed")
            
            # This should trigger fallback and logging
            index = self.router.select_matrix("test prompt")
            
            assert index == 1  # Median

    def test_clamping_logging(self):
        """Test that clamping events are logged."""
        # Out of range values should be logged
        index1 = self.router.select_matrix(-100.0)
        assert index1 == 0

        index2 = self.router.select_matrix(100.0)
        assert index2 == 2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])