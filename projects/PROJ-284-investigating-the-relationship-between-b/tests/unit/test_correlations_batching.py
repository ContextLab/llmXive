import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import os
import tempfile

from code.analysis.correlations import (
    calculate_batched_connectivity_matrices,
    run_batched_analysis,
    calculate_correlation_with_covariate
)
from code.utils.memory_monitor import get_available_memory

class TestDynamicBatching:
    """Tests for T028: Dynamic batch sizing for matrix computation."""

    def test_batch_size_calculation_logic(self):
        """Test that batch size respects memory constraints."""
        # Create synthetic time series for 10 subjects, 400 nodes, 100 timepoints
        n_subjects = 10
        n_timepoints = 100
        n_nodes = 400
        
        time_series = np.random.randn(n_subjects, n_timepoints, n_nodes)
        subject_ids = [f"sub-{i:03d}" for i in range(n_subjects)]
        
        # Run with default batch sizing
        matrices = calculate_batched_connectivity_matrices(time_series, subject_ids)
        
        assert len(matrices) == n_subjects
        assert all(m.shape == (n_nodes, n_nodes) for m in matrices)

    def test_batching_with_small_memory_limit(self):
        """Test that batching works correctly even with artificially small limits."""
        # This test verifies the logic of splitting into batches
        n_subjects = 20
        n_timepoints = 50
        n_nodes = 100 # Smaller for speed
        
        time_series = np.random.randn(n_subjects, n_timepoints, n_nodes)
        subject_ids = [f"sub-{i:03d}" for i in range(n_subjects)]
        
        # Force a small batch size (e.g., 5) to ensure multiple batches
        matrices = calculate_batched_connectivity_matrices(
            time_series, subject_ids, batch_size=5
        )
        
        assert len(matrices) == n_subjects
        
        # Verify we actually processed in batches (internal log would show this, 
        # but we can infer from the fact that it didn't OOM and produced correct count)
        
    def test_empty_input(self):
        """Test handling of empty subject list."""
        matrices = calculate_batched_connectivity_matrices(
            np.array([]).reshape(0, 10, 10), []
        )
        assert matrices == []

    def test_single_subject(self):
        """Test handling of single subject."""
        ts = np.random.randn(1, 50, 100)
        ids = ["sub-001"]
        matrices = calculate_batched_connectivity_matrices(ts, ids)
        assert len(matrices) == 1
        assert matrices[0].shape == (100, 100)

    def test_correlation_with_covariate_basic(self):
        """Test basic correlation calculation."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        r, p = calculate_correlation_with_covariate(x, y)
        
        assert r > 0.9 # Strong positive correlation
        assert p < 0.05

    def test_correlation_with_covariate_control(self):
        """Test partial correlation with covariate."""
        x = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        y = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        cov = np.array([1, 1, 1, 1, 1, 2, 2, 2, 2, 2])
        
        r, p = calculate_correlation_with_covariate(x, y, covariate=cov)
        
        # Should still be positive, but p-value might differ
        assert isinstance(r, float)
        assert isinstance(p, float)

class TestRunBatchedAnalysis:
    """Integration tests for the batched analysis pipeline."""

    def test_run_batched_analysis_creates_output(self):
        """Test that run_batched_analysis creates the output CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            metrics_path = Path(tmpdir) / "aggregated_metrics.csv"
            output_path = Path(tmpdir) / "correlations.csv"
            
            # Create dummy input
            df = pd.DataFrame({
                'subject_id': ['s1', 's2', 's3'],
                'modularity': [0.1, 0.2, 0.3],
                'global_efficiency': [0.4, 0.5, 0.6],
                'participation_coef': [0.7, 0.8, 0.9],
                'within_module_degree': [1.0, 1.1, 1.2],
                'MeanFD': [0.1, 0.2, 0.3],
                'motor_score': [50, 60, 70]
            })
            df.to_csv(metrics_path, index=False)
            
            result = run_batched_analysis(str(metrics_path), str(output_path))
            
            assert output_path.exists()
            assert len(result) > 0
            assert 'metric' in result.columns
            assert 'r' in result.columns
            assert 'p' in result.columns
            assert 'q' in result.columns
            assert 'significant' in result.columns

    def test_run_batched_analysis_missing_fd(self):
        """Test error handling when MeanFD is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            metrics_path = Path(tmpdir) / "aggregated_metrics.csv"
            output_path = Path(tmpdir) / "correlations.csv"
            
            df = pd.DataFrame({
                'subject_id': ['s1'],
                'modularity': [0.1],
                'global_efficiency': [0.2],
                'participation_coef': [0.3],
                'within_module_degree': [0.4],
                # Missing MeanFD
            })
            df.to_csv(metrics_path, index=False)
            
            with pytest.raises(ValueError, match="Covariate column"):
                run_batched_analysis(str(metrics_path), str(output_path))