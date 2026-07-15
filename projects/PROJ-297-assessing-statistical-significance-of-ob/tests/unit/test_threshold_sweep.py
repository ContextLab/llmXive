import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import run_threshold_sweep, generate_sensitivity_report
import config

class TestThresholdSweep:
    """Test cases for threshold sweep functionality (T024)."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        np.random.seed(42)
        data = np.random.randn(100, 10)
        columns = [f'var_{i}' for i in range(10)]
        return pd.DataFrame(data, columns=columns)
    
    @pytest.fixture
    def mock_dataset_loader(self, sample_data):
        """Mock the dataset loader to return sample data."""
        with patch('main.load_and_hygiene_dataset') as mock_loader:
            mock_loader.return_value = sample_data
            yield mock_loader
    
    @pytest.fixture
    def mock_stats_engine(self):
        """Mock the stats engine functions."""
        with patch('main.stats_engine') as mock_engine:
            # Setup mock correlation matrix
            mock_corr = pd.DataFrame(
                np.random.rand(10, 10),
                columns=[f'var_{i}' for i in range(10)],
                index=[f'var_{i}' for i in range(10)]
            )
            mock_corr = (mock_corr + mock_corr.T) / 2  # Make symmetric
            np.fill_diagonal(mock_corr.values, 1.0)
            
            # Setup mock graph
            mock_graph = MagicMock()
            mock_graph.number_of_edges.return_value = 5
            mock_graph.edges.return_value = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]
            mock_graph.edges.return_value = [(f'var_{i}', f'var_{i+1}') for i in range(5)]
            mock_graph.edges.return_value = [(f'var_{i}', f'var_{i+1}', {'weight': 0.5}) for i in range(5)]
            
            # Setup mock statistics
            mock_stats = {
                'mean_abs_correlation': 0.5,
                'edge_density': 0.1,
                'max_abs_correlation': 0.8,
                'average_clustering_coefficient': 0.3
            }
            
            # Setup mock null distributions
            mock_null_dist = {
                'mean_abs_correlation': [0.4, 0.45, 0.5, 0.55, 0.6],
                'edge_density': [0.05, 0.08, 0.1, 0.12, 0.15],
                'max_abs_correlation': [0.7, 0.75, 0.8, 0.85, 0.9],
                'average_clustering_coefficient': [0.2, 0.25, 0.3, 0.35, 0.4]
            }
            
            mock_engine.compute_correlation.return_value = mock_corr
            mock_engine.construct_graph.return_value = mock_graph
            mock_engine.calculate_stats.return_value = mock_stats
            mock_engine.generate_null_distribution.return_value = mock_null_dist
            mock_engine.calculate_empirical_p_value.side_effect = lambda dist, obs: 0.3
            
            yield mock_engine
    
    def test_threshold_sweep_runs_for_all_thresholds(self, mock_dataset_loader, mock_stats_engine):
        """Test that threshold sweep runs for all specified thresholds."""
        thresholds = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        results = run_threshold_sweep('test_dataset', thresholds, n_permutations=100)
        
        assert len(results) == len(thresholds), f"Expected {len(thresholds)} results, got {len(results)}"
        
        # Check that each result has the correct threshold
        result_thresholds = [r['threshold'] for r in results]
        assert sorted(result_thresholds) == sorted(thresholds), "Not all thresholds were processed"
    
    def test_threshold_sweep_includes_01_baseline(self, mock_dataset_loader, mock_stats_engine):
        """Test that the 0.1 threshold baseline is included (FR-005 requirement)."""
        thresholds = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        results = run_threshold_sweep('test_dataset', thresholds, n_permutations=100)
        
        threshold_01_results = [r for r in results if r['threshold'] == 0.1]
        assert len(threshold_01_results) == 1, "Threshold 0.1 should be in results"
    
    def test_sensitivity_report_contains_all_thresholds(self, mock_dataset_loader, mock_stats_engine, tmp_path):
        """Test that sensitivity report contains rows for all thresholds."""
        thresholds = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        sweep_results = [run_threshold_sweep('test_dataset', thresholds, n_permutations=100)]
        
        output_path = tmp_path / "test_sensitivity.csv"
        generate_sensitivity_report(sweep_results, str(output_path))
        
        # Verify file was created
        assert output_path.exists(), "Sensitivity report file was not created"
        
        # Read and verify content
        df = pd.read_csv(output_path)
        
        # Check that all thresholds are present
        unique_thresholds = sorted(df['threshold'].unique())
        assert unique_thresholds == thresholds, f"Expected thresholds {thresholds}, got {unique_thresholds}"
    
    def test_sensitivity_report_includes_01_baseline(self, mock_dataset_loader, mock_stats_engine, tmp_path):
        """Test that sensitivity report explicitly includes the 0.1 threshold row."""
        thresholds = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        sweep_results = [run_threshold_sweep('test_dataset', thresholds, n_permutations=100)]
        
        output_path = tmp_path / "test_sensitivity.csv"
        generate_sensitivity_report(sweep_results, str(output_path))
        
        df = pd.read_csv(output_path)
        
        # Check that 0.1 threshold row exists
        threshold_01_rows = df[df['threshold'] == 0.1]
        assert len(threshold_01_rows) > 0, "Threshold 0.1 row should be present in sensitivity report"
    
    def test_sensitivity_report_structure(self, mock_dataset_loader, mock_stats_engine, tmp_path):
        """Test that sensitivity report has the expected structure."""
        thresholds = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        sweep_results = [run_threshold_sweep('test_dataset', thresholds, n_permutations=100)]
        
        output_path = tmp_path / "test_sensitivity.csv"
        generate_sensitivity_report(sweep_results, str(output_path))
        
        df = pd.read_csv(output_path)
        
        # Check required columns
        required_columns = ['dataset_id', 'threshold', 'statistic', 'observed_value', 'p_value', 'q_value', 'is_significant', 'significant_count']
        for col in required_columns:
            assert col in df.columns, f"Required column '{col}' missing from sensitivity report"