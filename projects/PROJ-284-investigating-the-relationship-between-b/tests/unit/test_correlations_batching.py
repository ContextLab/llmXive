import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from code.analysis.correlations import run_correlations_with_fd_covariate
from code.utils.memory_monitor import calculate_batch_size, get_available_memory

class TestBatchingLogic:
    
    def test_calculate_batch_size_respects_memory(self):
        """Test that batch size is calculated based on available memory."""
        total_rows = 10000
        
        # Mock available memory to be very low (100MB)
        with patch('code.utils.memory_monitor.get_available_memory', return_value=100 * 1024 * 1024):
            batch = calculate_batch_size(total_rows)
            
        # Batch should be smaller than total
        assert batch < total_rows
        assert batch > 0
        
    def test_calculate_batch_size_with_high_memory(self):
        """Test that batch size can be large when memory is abundant."""
        total_rows = 1000
        
        # Mock high memory (100GB)
        with patch('code.utils.memory_monitor.get_available_memory', return_value=100 * 1024 * 1024 * 1024):
            batch = calculate_batch_size(total_rows)
            
        # Batch should equal total rows when memory is sufficient
        assert batch == total_rows

    def test_run_correlations_with_batching(self):
        """Test that correlation function processes data in batches."""
        # Create synthetic data
        n_subjects = 100
        df = pd.DataFrame({
            "modularity": np.random.rand(n_subjects),
            "global_efficiency": np.random.rand(n_subjects),
            "motor_score": np.random.rand(n_subjects),
            "fd": np.random.rand(n_subjects)
        })
        
        # Mock memory to force small batch size
        with patch('code.utils.memory_monitor.get_available_memory', return_value=10 * 1024 * 1024):
            with patch('code.analysis.correlations.get_logger') as mock_logger:
                results = run_correlations_with_fd_covariate(
                    df, 
                    metric_cols=["modularity", "global_efficiency"]
                )
        
        # Verify results are computed
        assert len(results) == 2  # Two metrics
        assert all("r" in r for r in results)
        assert all("p" in r for r in results)
        
        # Verify logging occurred for batching
        calls = [call for call in mock_logger.return_value.log.call_args_list 
                if "batch" in str(call)]
        assert len(calls) > 0, "Batching should be logged"

    def test_empty_dataframe_handling(self):
        """Test that empty dataframe is handled gracefully."""
        df = pd.DataFrame(columns=["modularity", "motor_score", "fd"])
        
        results = run_correlations_with_fd_covariate(df, ["modularity"])
        assert results == []

    def test_nan_handling_in_batches(self):
        """Test that NaN values are properly handled within batches."""
        df = pd.DataFrame({
            "modularity": [1.0, np.nan, 3.0, 4.0],
            "motor_score": [1.0, 2.0, 3.0, 4.0],
            "fd": [0.1, 0.2, 0.3, 0.4]
        })
        
        results = run_correlations_with_fd_covariate(df, ["modularity"])
        
        # Should only compute on valid rows (3 rows)
        assert len(results) == 1
        assert results[0]["n"] == 3  # 3 valid rows used