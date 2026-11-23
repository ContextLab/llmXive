"""
Unit tests for edge cases across the pipeline modules.
Covers: memory limits, empty inputs, singular matrices, missing files,
time limits, and malformed JSON.
"""
import os
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import numpy as np
import pandas as pd

# Import from project modules
from config import get_memory_limit_gb, get_runtime_limit_hours
from memory_monitor import is_limit_exceeded, check_and_warn, enforce_limit
from logging_config import log_memory_warning, get_logger, MemoryCheckingFilter
from time_monitor import ensure_runtime_limit, check_runtime_status
from collinearity import calculate_vif, run_pca_on_metrics, generate_descriptive_vif_report
from graph_metrics import calculate_global_efficiency, calculate_local_efficiency, calculate_modularity
from analysis_report import load_json_safely, parse_log_for_memory, parse_log_for_runtime
from synthetic_data import generate_connectivity_matrix
from bootstrapping import calculate_correlation


class TestMemoryEdgeCases:
    """Tests for memory monitoring edge cases."""

    def test_is_limit_exceeded_at_exact_limit(self):
        """Test behavior when RAM usage is exactly at the limit (6GB)."""
        # Mock resource usage to be exactly at limit
        with patch('memory_monitor.get_current_ram_gb', return_value=get_memory_limit_gb()):
            # Should NOT exceed (limit is strict inequality: > 6.0)
            assert is_limit_exceeded() is False

    def test_is_limit_exceeded_just_above_limit(self):
        """Test behavior when RAM usage is just above the limit."""
        limit = get_memory_limit_gb()
        with patch('memory_monitor.get_current_ram_gb', return_value=limit + 0.1):
            assert is_limit_exceeded() is True

    def test_check_and_warn_no_warning_below_threshold(self):
        """Test that no warning is logged when RAM is well below threshold."""
        logger = get_logger("test_memory_warn")
        with patch('memory_monitor.get_current_ram_gb', return_value=2.0):
            with patch.object(logger, 'warning') as mock_warn:
                check_and_warn(logger)
                mock_warn.assert_not_called()

    def test_enforce_limit_raises_on_exceed(self):
        """Test that enforce_limit raises MemoryError when limit exceeded."""
        limit = get_memory_limit_gb()
        with patch('memory_monitor.get_current_ram_gb', return_value=limit + 1.0):
            with pytest.raises(MemoryError, match="Memory limit exceeded"):
                enforce_limit()


class TestCollinearityEdgeCases:
    """Tests for collinearity and PCA edge cases."""

    def test_vif_infinite_for_perfectly_collinear(self):
        """Test VIF returns infinity for perfectly collinear predictors."""
        # Create perfectly collinear data (X2 = 2 * X1)
        data = pd.DataFrame({
            'X1': [1, 2, 3, 4, 5],
            'X2': [2, 4, 6, 8, 10],  # Perfectly collinear
            'Y': [1, 2, 3, 4, 5]
        })
        vifs = calculate_vif(data[['X1', 'X2']])
        # At least one VIF should be infinite
        assert any(np.isinf(vifs.values))

    def test_vif_zero_variance_predictor(self):
        """Test VIF handles zero variance predictor."""
        data = pd.DataFrame({
            'X1': [1, 2, 3, 4, 5],
            'X2': [1, 1, 1, 1, 1],  # Zero variance
            'Y': [1, 2, 3, 4, 5]
        })
        vifs = calculate_vif(data[['X1', 'X2']])
        # Should handle without crashing (may return inf or large value)
        assert isinstance(vifs, pd.Series)

    def test_pca_singular_matrix(self):
        """Test PCA fallback when matrix is singular."""
        # Create singular matrix (all same values)
        data = pd.DataFrame({
            'X1': [1, 1, 1, 1, 1],
            'X2': [1, 1, 1, 1, 1],
            'X3': [1, 1, 1, 1, 1]
        })
        # Should raise LinAlgError or return empty components
        with pytest.raises((np.linalg.LinAlgError, ValueError)):
            run_pca_on_metrics(data)

    def test_descriptive_vif_report_empty_input(self):
        """Test VIF report generation with empty dataframe."""
        empty_df = pd.DataFrame()
        report = generate_descriptive_vif_report(empty_df)
        assert 'correlation_matrix' in report
        assert 'variance_decomposition' in report


class TestGraphMetricsEdgeCases:
    """Tests for graph metric edge cases."""

    def test_global_efficiency_empty_graph(self):
        """Test global efficiency on empty graph."""
        empty_matrix = np.zeros((5, 5))
        result = calculate_global_efficiency(empty_matrix)
        # Should return 0 or handle gracefully
        assert result == 0.0 or np.isnan(result)

    def test_global_efficiency_single_node(self):
        """Test global efficiency on single node."""
        single_node = np.array([[0]])
        result = calculate_global_efficiency(single_node)
        assert result == 0.0 or np.isnan(result)

    def test_local_efficiency_disconnected_graph(self):
        """Test local efficiency on disconnected graph."""
        # Two disconnected components
        matrix = np.array([
            [0, 1, 0, 0],
            [1, 0, 0, 0],
            [0, 0, 0, 1],
            [0, 0, 1, 0]
        ])
        result = calculate_local_efficiency(matrix)
        assert isinstance(result, np.ndarray)
        assert len(result) == 4

    def test_modularity_self_loops(self):
        """Test modularity calculation with self-loops."""
        # Matrix with self-loops (should be ignored)
        matrix = np.array([
            [1, 1, 0],
            [1, 1, 1],
            [0, 1, 1]
        ])
        result = calculate_modularity(matrix)
        # Modularity should be in [0, 1]
        assert 0 <= result <= 1


class TestSyntheticDataEdgeCases:
    """Tests for synthetic data generator edge cases."""

    def test_generate_connectivity_matrix_zero_size(self):
        """Test connectivity matrix generation with zero size."""
        with pytest.raises(ValueError):
            generate_connectivity_matrix(n_nodes=0)

    def test_generate_connectivity_matrix_negative_size(self):
        """Test connectivity matrix generation with negative size."""
        with pytest.raises(ValueError):
            generate_connectivity_matrix(n_nodes=-5)

    def test_generate_connectivity_matrix_very_large(self):
        """Test connectivity matrix generation with very large size."""
        # Should not crash, but may be slow
        matrix = generate_connectivity_matrix(n_nodes=100)
        assert matrix.shape == (100, 100)
        assert np.allclose(matrix, matrix.T)  # Symmetric


class TestAnalysisReportEdgeCases:
    """Tests for analysis report utility edge cases."""

    def test_load_json_safely_empty_file(self):
        """Test loading empty JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('')
            temp_path = f.name
        
        result = load_json_safely(temp_path)
        assert result is None
        os.unlink(temp_path)

    def test_load_json_safely_malformed_json(self):
        """Test loading malformed JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{invalid json}')
            temp_path = f.name
        
        result = load_json_safely(temp_path)
        assert result is None
        os.unlink(temp_path)

    def test_load_json_safely_nonexistent_file(self):
        """Test loading non-existent file."""
        result = load_json_safely('/nonexistent/path/file.json')
        assert result is None

    def test_parse_log_for_memory_no_memory_logs(self):
        """Test parsing log with no memory entries."""
        log_content = "2024-01-01 INFO: Starting process\n2024-01-01 INFO: Done"
        result = parse_log_for_memory(log_content)
        assert result is None

    def test_parse_log_for_runtime_no_runtime_logs(self):
        """Test parsing log with no runtime entries."""
        log_content = "2024-01-01 INFO: Starting process\n2024-01-01 INFO: Done"
        result = parse_log_for_runtime(log_content)
        assert result is None


class TestTimeMonitorEdgeCases:
    """Tests for time monitoring edge cases."""

    def test_ensure_runtime_limit_zero_limit(self):
        """Test runtime limit with zero hours."""
        with patch('time_monitor.get_elapsed_time_hours', return_value=0.1):
            with pytest.raises(RuntimeError, match="Time limit exceeded"):
                ensure_runtime_limit(limit_hours=0)

    def test_check_runtime_status_near_limit(self):
        """Test runtime status when near limit."""
        limit = 1.0
        with patch('time_monitor.get_elapsed_time_hours', return_value=0.99):
            status = check_runtime_status(limit_hours=limit)
            assert status['status'] == 'warning'
            assert status['remaining_hours'] < 0.02


class TestCorrelationEdgeCases:
    """Tests for correlation calculation edge cases."""

    def test_correlation_constant_variable(self):
        """Test correlation when one variable is constant."""
        x = [1, 1, 1, 1, 1]
        y = [1, 2, 3, 4, 5]
        result = calculate_correlation(x, y)
        # Correlation with constant should be 0 or NaN
        assert result == 0.0 or np.isnan(result)

    def test_correlation_single_point(self):
        """Test correlation with single data point."""
        x = [1]
        y = [2]
        result = calculate_correlation(x, y)
        # Single point correlation is undefined
        assert np.isnan(result)

    def test_correlation_all_nan(self):
        """Test correlation with all NaN values."""
        x = [np.nan, np.nan, np.nan]
        y = [np.nan, np.nan, np.nan]
        result = calculate_correlation(x, y)
        assert np.isnan(result)