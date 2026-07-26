import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import os

# Import functions to test
from stats.sensitivity import (
    threshold_connectivity_matrix,
    calculate_stability,
    run_sensitivity_analysis,
    DENSITY_THRESHOLDS
)

@pytest.fixture
def sample_connectivity_matrix():
    """Create a sample connectivity matrix for testing."""
    np.random.seed(42)
    n_nodes = 10
    matrix = np.random.rand(n_nodes, n_nodes)
    # Make it symmetric
    matrix = (matrix + matrix.T) / 2.0
    # Set diagonal to 0
    np.fill_diagonal(matrix, 0)
    return matrix

@pytest.fixture
def sample_metrics_df():
    """Create a sample metrics DataFrame for testing."""
    data = {
        'subject_id': ['sub1', 'sub1', 'sub2', 'sub2'],
        'threshold': [0.1, 0.2, 0.1, 0.2],
        'global_efficiency': [0.5, 0.6, 0.55, 0.65],
        'local_efficiency': [0.3, 0.35, 0.32, 0.38],
        'clustering_coefficient': [0.4, 0.45, 0.42, 0.47]
    }
    return pd.DataFrame(data)

class TestThresholdConnectivityMatrix:
    def test_density_threshold(self, sample_connectivity_matrix):
        """Test that thresholding reduces the number of non-zero edges."""
        matrix = sample_connectivity_matrix
        n_nodes = matrix.shape[0]
        
        # Test with low density
        low_density_matrix = threshold_connectivity_matrix(matrix, 0.1)
        low_nonzero = np.count_nonzero(low_density_matrix)
        
        # Test with high density
        high_density_matrix = threshold_connectivity_matrix(matrix, 0.5)
        high_nonzero = np.count_nonzero(high_density_matrix)
        
        # High density should have more non-zero edges
        assert high_nonzero > low_nonzero
        
        # Test symmetry
        assert np.allclose(low_density_matrix, low_density_matrix.T)
        assert np.allclose(high_density_matrix, high_density_matrix.T)
    
    def test_invalid_density(self, sample_connectivity_matrix):
        """Test that invalid density values raise an error."""
        matrix = sample_connectivity_matrix
        
        with pytest.raises(ValueError):
            threshold_connectivity_matrix(matrix, -0.1)
        
        with pytest.raises(ValueError):
            threshold_connectivity_matrix(matrix, 1.5)

class TestCalculateStability:
    def test_stable_metric(self, sample_metrics_df):
        """Test stability calculation for a stable metric."""
        # Create data with low variation
        df = pd.DataFrame({
            'subject_id': ['s1', 's1', 's2', 's2'],
            'threshold': [0.1, 0.2, 0.1, 0.2],
            'metric': [0.5, 0.51, 0.5, 0.51]
        })
        
        std_dev, is_stable = calculate_stability(df, 'metric')
        
        assert is_stable == True
        assert std_dev < 0.05
    
    def test_unstable_metric(self, sample_metrics_df):
        """Test stability calculation for an unstable metric."""
        # Create data with high variation
        df = pd.DataFrame({
            'subject_id': ['s1', 's1', 's2', 's2'],
            'threshold': [0.1, 0.2, 0.1, 0.2],
            'metric': [0.1, 0.9, 0.2, 0.8]
        })
        
        std_dev, is_stable = calculate_stability(df, 'metric')
        
        assert is_stable == False
        assert std_dev >= 0.05

class TestRunSensitivityAnalysis:
    def test_run_sensitivity_analysis(self, sample_connectivity_matrix):
        """Test the full sensitivity analysis pipeline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create connectivity directory with sample matrix
            conn_dir = tmpdir / "connectivity_matrices"
            conn_dir.mkdir()
            
            # Save sample matrix
            np.save(conn_dir / "test_subject_connectivity.npy", sample_connectivity_matrix)
            
            # Create output directory
            output_dir = tmpdir / "results"
            output_dir.mkdir()
            
            # Run sensitivity analysis
            report_df = run_sensitivity_analysis(conn_dir, output_dir)
            
            # Check that report was generated
            assert report_df is not None
            assert isinstance(report_df, pd.DataFrame)
            
            # Check required columns
            required_columns = ['threshold', 'metric_name', 'std_dev', 'is_stable']
            for col in required_columns:
                assert col in report_df.columns
            
            # Check that we have entries for each threshold
            for threshold in DENSITY_THRESHOLDS:
                assert threshold in report_df['threshold'].values
            
            # Check that is_stable is boolean
            assert report_df['is_stable'].dtype == bool
            
            # Check that the output file was created
            output_file = output_dir / "sensitivity_density_report.csv"
            assert output_file.exists()
            
            # Load and verify the saved file
            saved_df = pd.read_csv(output_file)
            assert saved_df.shape == report_df.shape
