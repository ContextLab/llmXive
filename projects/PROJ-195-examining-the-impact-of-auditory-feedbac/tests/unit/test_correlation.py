import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json

# Add code directory to path
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from correlation_analysis import (
    load_roi_betas,
    load_learning_rate_slopes,
    calculate_pearson_correlation,
    generate_scatter_plot
)

class TestCorrelationAnalysis:
    
    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary directory for test data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_load_roi_betas_missing_file(self):
        """Test that FileNotFoundError is raised when ROI file is missing."""
        with pytest.raises(FileNotFoundError):
            load_roi_betas("nonexistent/path.csv")

    def test_load_learning_rate_missing_file(self):
        """Test that FileNotFoundError is raised when learning rate file is missing."""
        with pytest.raises(FileNotFoundError):
            load_learning_rate_slopes("nonexistent/path.csv")

    def test_load_roi_betas_valid(self, temp_data_dir):
        """Test loading a valid ROI betas CSV."""
        data = {
            'subject_id': ['sub-01', 'sub-02', 'sub-03'],
            'mean_beta': [0.5, 1.2, 0.8]
        }
        df = pd.DataFrame(data)
        filepath = temp_data_dir / "roi_betas.csv"
        df.to_csv(filepath, index=False)
        
        loaded = load_roi_betas(str(filepath))
        assert len(loaded) == 3
        assert 'subject_id' in loaded.columns
        assert 'mean_beta' in loaded.columns
        assert list(loaded['subject_id']) == ['sub-01', 'sub-02', 'sub-03']

    def test_load_learning_rate_valid(self, temp_data_dir):
        """Test loading a valid learning rates CSV."""
        data = {
            'subject_id': ['sub-01', 'sub-02', 'sub-03'],
            'slope': [-5.0, -12.0, -8.0]
        }
        df = pd.DataFrame(data)
        filepath = temp_data_dir / "learning_rates.csv"
        df.to_csv(filepath, index=False)
        
        loaded = load_learning_rate_slopes(str(filepath))
        assert len(loaded) == 3
        assert 'slope' in loaded.columns

    def test_calculate_pearson_correlation(self, temp_data_dir):
        """Test Pearson correlation calculation logic."""
        # Create data with a known negative correlation
        roi_data = {
            'subject_id': ['s1', 's2', 's3', 's4', 's5'],
            'mean_beta': [1.0, 2.0, 3.0, 4.0, 5.0]
        }
        slope_data = {
            'subject_id': ['s1', 's2', 's3', 's4', 's5'],
            'slope': [10.0, 8.0, 6.0, 4.0, 2.0]
        }
        
        roi_df = pd.DataFrame(roi_data)
        slope_df = pd.DataFrame(slope_data)
        
        r, p, merged = calculate_pearson_correlation(roi_df, slope_df)
        
        # Check that correlation is negative (as beta increases, slope decreases)
        assert r < 0
        # Check that we have perfect negative correlation for this linear data
        assert np.isclose(r, -1.0, atol=0.01)
        # Check that merged data has correct length
        assert len(merged) == 5

    def test_calculate_pearson_correlation_insufficient_data(self):
        """Test that ValueError is raised with insufficient data points."""
        roi_data = {
            'subject_id': ['s1'],
            'mean_beta': [1.0]
        }
        slope_data = {
            'subject_id': ['s1'],
            'slope': [5.0]
        }
        
        roi_df = pd.DataFrame(roi_data)
        slope_df = pd.DataFrame(slope_data)
        
        with pytest.raises(ValueError, match="Insufficient data points"):
            calculate_pearson_correlation(roi_df, slope_df)

    def test_generate_scatter_plot(self, temp_data_dir):
        """Test that scatter plot is generated successfully."""
        data = {
            'subject_id': ['s1', 's2', 's3'],
            'mean_beta': [1.0, 2.0, 3.0],
            'slope': [5.0, 4.0, 3.0]
        }
        df = pd.DataFrame(data)
        
        output_path = temp_data_dir / "test_plot.png"
        
        generate_scatter_plot(
            df, 
            roi_col='mean_beta', 
            slope_col='slope', 
            output_path=str(output_path),
            correlation_val=-0.5,
            p_value=0.01
        )
        
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_pearson_correlation_and_plot_generation(self, temp_data_dir):
        """
        Comprehensive test: Verify Pearson's r calculation and that a PNG/PDF plot is generated.
        This test simulates the full workflow of T033.
        """
        # Prepare synthetic but realistic data
        subjects = [f'sub-{i:02d}' for i in range(1, 11)]
        # Simulate a moderate negative correlation
        betas = np.random.normal(loc=1.5, scale=0.3, size=10)
        slopes = -2.0 * betas + np.random.normal(loc=0, scale=0.5, size=10)
        
        roi_df = pd.DataFrame({
            'subject_id': subjects,
            'mean_beta': betas
        })
        
        slope_df = pd.DataFrame({
            'subject_id': subjects,
            'slope': slopes
        })
        
        # Calculate correlation
        r, p, merged = calculate_pearson_correlation(roi_df, slope_df)
        
        # Assertions on correlation
        assert -1.0 <= r <= 1.0
        assert 0.0 <= p <= 1.0
        assert len(merged) == 10
        
        # Generate plot
        plot_path = temp_data_dir / "correlation_output.png"
        generate_scatter_plot(
            merged, 
            roi_col='mean_beta', 
            slope_col='slope', 
            output_path=str(plot_path),
            correlation_val=r,
            p_value=p
        )
        
        # Verify plot exists and is non-empty
        assert plot_path.exists()
        assert plot_path.stat().st_size > 1000 # Should be a reasonable image size

        # Verify merged data structure
        assert 'subject_id' in merged.columns
        assert 'mean_beta' in merged.columns
        assert 'slope' in merged.columns
        
        # Verify correlation sign (should be negative in this simulation)
        assert r < 0
        assert p < 0.10 # With 10 subjects and strong effect, should be significant