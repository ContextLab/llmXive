"""
Unit tests for partial correlation analysis (T032).
"""
import os
import sys
import tempfile
import json
import pytest
import pandas as pd
import numpy as np

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.analysis.partial_corr import (
    calculate_partial_correlation,
    run_partial_correlation_analysis,
    load_simulation_data
)

class TestPartialCorrelation:
    """Tests for partial correlation calculation."""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        np.random.seed(42)
        n = 100
        data = {
            'diversity': np.random.randn(n),
            'memory_depth': np.random.randn(n),
            'coherence_score': np.random.randn(n),
            'step_latency': np.random.randn(n),
            'param_id': np.random.choice(['A', 'B', 'C'], n)
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def sample_data_path(self, sample_data):
        """Create a temporary CSV file with sample data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_data.to_csv(f, index=False)
            path = f.name
        yield path
        os.unlink(path)

    def test_partial_correlation_calculation(self, sample_data):
        """Test that partial correlation is calculated correctly."""
        target = 'diversity'
        control = 'memory_depth'
        controls = ['coherence_score', 'step_latency']
        threshold = 0.05

        coeff, is_indep, stats = calculate_partial_correlation(
            sample_data, target, control, controls, threshold
        )

        # Check return types
        assert isinstance(coeff, float)
        assert isinstance(is_indep, bool)
        assert isinstance(stats, dict)

        # Check stats keys
        assert 'partial_correlation' in stats
        assert 'is_independent' in stats
        assert stats['partial_correlation'] == coeff
        assert stats['is_independent'] == is_indep

    def test_partial_correlation_independence_assertion(self, sample_data):
        """Test that independence assertion works correctly."""
        target = 'diversity'
        control = 'memory_depth'
        controls = ['coherence_score', 'step_latency']
        threshold = 0.05

        coeff, is_indep, _ = calculate_partial_correlation(
            sample_data, target, control, controls, threshold
        )

        # The assertion should match the threshold check
        assert is_indep == (abs(coeff) < threshold)

    def test_missing_columns_error(self):
        """Test that missing columns raise an error."""
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [1, 2, 3]})
        
        with pytest.raises(ValueError) as excinfo:
            calculate_partial_correlation(
                df, 'target', 'control', ['missing_col']
            )
        assert "Missing required columns" in str(excinfo.value)

    def test_insufficient_data_error(self):
        """Test that insufficient data raises an error."""
        # Need at least len(controls) + 2 rows
        df = pd.DataFrame({
            'target': [1, 2, 3],
            'control': [1, 2, 3],
            'ctrl1': [1, 2, 3],
            'ctrl2': [1, 2, 3]
        })
        
        with pytest.raises(ValueError) as excinfo:
            calculate_partial_correlation(
                df, 'target', 'control', ['ctrl1', 'ctrl2']
            )
        assert "Insufficient data points" in str(excinfo.value)

    def test_run_analysis_saves_file(self, sample_data_path):
        """Test that run_analysis saves results to a file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name
        
        try:
            result = run_partial_correlation_analysis(
                input_path=sample_data_path,
                output_path=output_path
            )
            
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                saved_data = json.load(f)
            
            assert 'partial_correlation' in saved_data
            assert 'is_independent' in saved_data
            assert saved_data['partial_correlation'] == result['partial_correlation']
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_load_simulation_data(self, sample_data_path):
        """Test loading simulation data from CSV."""
        df = load_simulation_data(sample_data_path)
        
        assert isinstance(df, pd.DataFrame)
        assert 'diversity' in df.columns
        assert 'memory_depth' in df.columns

    def test_load_simulation_data_missing_file(self):
        """Test that loading missing file raises error."""
        with pytest.raises(FileNotFoundError):
            load_simulation_data("nonexistent_file.csv")

    def test_partial_correlation_with_nan_handling(self):
        """Test that NaN values are handled correctly."""
        df = pd.DataFrame({
            'diversity': [1.0, 2.0, np.nan, 4.0, 5.0],
            'memory_depth': [1.0, 2.0, 3.0, np.nan, 5.0],
            'coherence_score': [1.0, 2.0, 3.0, 4.0, 5.0],
            'step_latency': [1.0, 2.0, 3.0, 4.0, 5.0]
        })
        
        # Should drop NaN rows and calculate
        coeff, is_indep, stats = calculate_partial_correlation(
            df, 'diversity', 'memory_depth', ['coherence_score', 'step_latency']
        )
        
        # Should have fewer observations than original
        assert stats['n_observations'] < len(df)
        assert isinstance(coeff, float)
        assert isinstance(is_indep, bool)
