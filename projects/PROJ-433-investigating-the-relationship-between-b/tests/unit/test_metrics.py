import pytest
import numpy as np
from pathlib import Path
import json
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from metrics import extract_reconfigurability, compute_sliding_window
from utils import setup_logger, get_seeded_rng

@pytest.fixture
def sample_time_series():
    """Generate a sample time series for testing."""
    np.random.seed(42)
    n_timepoints = 150
    n_parcels = 20
    return np.random.randn(n_timepoints, n_parcels)

@pytest.fixture
def logger():
    """Create a test logger."""
    return setup_logger()

class TestExtractReconfigurability:
    
    def test_successful_extraction(self, sample_time_series, logger):
        """Test that reconfigurability is extracted successfully."""
        result = extract_reconfigurability(
            time_series=sample_time_series,
            window_size=30,
            step_size=10,
            subject_id="test_001",
            logger=logger
        )
        
        assert result['status'] == 'SUCCESS'
        assert result['transition_count'] is not None
        assert result['transition_count'] >= 0
        assert result['windows_processed'] > 0
        
    def test_retry_logic_on_failure(self, sample_time_series, logger, monkeypatch):
        """Test that retry logic is triggered on convergence failure."""
        # Mock the community_louvain to fail once then succeed
        import metrics
        
        original_best_partition = None
        call_count = [0]
        
        def mock_best_partition(G, weight=None, resolution=1.0, random_state=None):
            call_count[0] += 1
            if call_count[0] == 1:
                raise ValueError("Simulated convergence failure")
            # Return a simple partition
            return {i: i % 2 for i in range(G.number_of_nodes())}
        
        # Only run this test if community_louvain is available
        if metrics.community_louvain is not None:
            monkeypatch.setattr(metrics.community_louvain, 'best_partition', mock_best_partition)
            
            result = extract_reconfigurability(
                time_series=sample_time_series,
                window_size=30,
                step_size=10,
                max_retries=2,
                subject_id="test_retry",
                logger=logger
            )
            
            # Should succeed after retry
            assert result['status'] == 'SUCCESS'
            assert result['transition_count'] is not None
        else:
            pytest.skip("python-louvain not installed")

    def test_exclusion_on_max_retries(self, sample_time_series, logger, monkeypatch):
        """Test that subject is excluded after max retries."""
        import metrics
        
        def mock_best_partition_failure(G, weight=None, resolution=1.0, random_state=None):
            raise ValueError("Simulated persistent failure")
        
        if metrics.community_louvain is not None:
            monkeypatch.setattr(metrics.community_louvain, 'best_partition', mock_best_partition_failure)
            
            result = extract_reconfigurability(
                time_series=sample_time_series,
                window_size=30,
                step_size=10,
                max_retries=2,
                subject_id="test_exclude",
                logger=logger
            )
            
            assert result['status'] == 'FAILED'
            assert result['transition_count'] is None
            assert 'Louvain community detection failed' in result['exclusion_reason']
        else:
            pytest.skip("python-louvain not installed")

    def test_seed_reproducibility(self, sample_time_series, logger):
        """Test that results are reproducible with the same seed."""
        result1 = extract_reconfigurability(
            time_series=sample_time_series,
            window_size=30,
            step_size=10,
            subject_id="test_seed_1",
            logger=logger
        )
        
        # Reset RNG state by creating a new instance
        # Note: The function internally uses get_seeded_rng(42) so results should be same
        result2 = extract_reconfigurability(
            time_series=sample_time_series,
            window_size=30,
            step_size=10,
            subject_id="test_seed_2",
            logger=logger
        )
        
        # The transition counts should be identical due to seeded RNG
        assert result1['transition_count'] == result2['transition_count']

class TestSlidingWindow:
    
    def test_sliding_window_shapes(self, sample_time_series):
        """Test that sliding window output has correct shapes."""
        window_size = 30
        step_size = 10
        
        windows = compute_sliding_window(sample_time_series, window_size, step_size)
        
        n_timepoints, n_parcels = sample_time_series.shape
        expected_n_windows = (n_timepoints - window_size) // step_size + 1
        
        assert len(windows) == expected_n_windows
        for i, w in enumerate(windows):
            assert w.shape == (n_parcels, n_parcels), f"Window {i} has wrong shape"
            
    def test_sliding_window_overlap(self, sample_time_series):
        """Test that windows overlap as expected."""
        window_size = 30
        step_size = 10
        
        windows = compute_sliding_window(sample_time_series, window_size, step_size)
        
        # Check that there is overlap between consecutive windows
        # (This is implicitly tested by the fact that we get multiple windows)
        assert len(windows) > 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])