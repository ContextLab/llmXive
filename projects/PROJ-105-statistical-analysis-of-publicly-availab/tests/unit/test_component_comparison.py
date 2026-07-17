import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import json
import tempfile
import os

from models import compare_component_distributions

class TestComponentComparison:
    @pytest.fixture
    def sample_data(self):
        """Create sample flight delay data for testing."""
        np.random.seed(42)
        n = 1000
        
        # Simulate realistic delay distributions
        arr_delay = np.random.exponential(scale=15, size=n)
        dep_delay = np.random.exponential(scale=20, size=n)
        
        # Total delay is sum of arrival and departure delays
        total_delay = arr_delay + dep_delay
        
        # Add some noise and occasional large delays
        total_delay += np.random.normal(0, 5, size=n)
        total_delay = np.maximum(total_delay, 0) # Ensure non-negative
        
        # Create DataFrame
        df = pd.DataFrame({
            'total_delay': total_delay,
            'ArrDelay': arr_delay,
            'DepDelay': dep_delay,
            'other_col': np.random.randint(0, 100, size=n)
        })
        
        return df

    @pytest.fixture
    def temp_data_file(self, sample_data):
        """Create a temporary CSV file with sample data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_data.to_csv(f, index=False)
            return f.name

    @pytest.fixture
    def temp_output_file(self):
        """Create a temporary output file path."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name
        return output_path

    def test_compare_component_distributions_creates_output(self, temp_data_file, temp_output_file):
        """Test that the function creates the output JSON file."""
        compare_component_distributions(temp_data_file, temp_output_file)
        
        assert Path(temp_output_file).exists(), "Output file was not created"
        
        with open(temp_output_file, 'r') as f:
            results = json.load(f)
        
        assert 'ks_tests' in results
        assert 'histograms' in results
        assert 'sample_sizes' in results

    def test_compare_component_distributions_has_correct_ks_tests(self, temp_data_file, temp_output_file):
        """Test that KS tests are performed for all required pairs."""
        compare_component_distributions(temp_data_file, temp_output_file)
        
        with open(temp_output_file, 'r') as f:
            results = json.load(f)
        
        ks_tests = results['ks_tests']
        
        assert 'total_vs_arr' in ks_tests
        assert 'total_vs_dep' in ks_tests
        assert 'arr_vs_dep' in ks_tests
        
        # Check structure of each test result
        for test_name, test_result in ks_tests.items():
            assert 'statistic' in test_result
            assert 'p_value' in test_result
            assert 'interpretation' in test_result
            assert isinstance(test_result['statistic'], float)
            assert isinstance(test_result['p_value'], float)
            assert test_result['interpretation'] in ['different', 'similar']

    def test_compare_component_distributions_histograms(self, temp_data_file, temp_output_file):
        """Test that histogram data is generated correctly."""
        compare_component_distributions(temp_data_file, temp_output_file)
        
        with open(temp_output_file, 'r') as f:
            results = json.load(f)
        
        histograms = results['histograms']
        
        assert 'bins' in histograms
        assert 'total_delay' in histograms
        assert 'arrival_delay' in histograms
        assert 'departure_delay' in histograms
        
        # Check that bin counts match number of bins
        assert len(histograms['total_delay']) == len(histograms['bins']) - 1
        assert len(histograms['arrival_delay']) == len(histograms['bins']) - 1
        assert len(histograms['departure_delay']) == len(histograms['bins']) - 1

    def test_compare_component_distributions_sample_sizes(self, temp_data_file, temp_output_file):
        """Test that sample sizes are recorded correctly."""
        compare_component_distributions(temp_data_file, temp_output_file)
        
        with open(temp_output_file, 'r') as f:
            results = json.load(f)
        
        sample_sizes = results['sample_sizes']
        
        assert 'total' in sample_sizes
        assert 'arrival' in sample_sizes
        assert 'departure' in sample_sizes
        
        # All should be positive integers
        assert sample_sizes['total'] > 0
        assert sample_sizes['arrival'] > 0
        assert sample_sizes['departure'] > 0

    def test_compare_component_distributions_missing_columns(self, temp_output_file):
        """Test that the function raises an error for missing columns."""
        # Create a DataFrame with missing columns
        df = pd.DataFrame({
            'total_delay': [1, 2, 3],
            'ArrDelay': [1, 2, 3]
            # Missing 'DepDelay'
        })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f, index=False)
            temp_data_file = f.name
        
        try:
            with pytest.raises(ValueError, match="Missing required columns"):
                compare_component_distributions(temp_data_file, temp_output_file)
        finally:
            os.unlink(temp_data_file)

    def test_compare_component_distributions_empty_data(self, temp_output_file):
        """Test behavior with empty data."""
        df = pd.DataFrame({
            'total_delay': [],
            'ArrDelay': [],
            'DepDelay': []
        })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f, index=False)
            temp_data_file = f.name
        
        try:
            # Should handle empty data gracefully or raise appropriate error
            # For now, we expect it to run but produce empty results or raise
            compare_component_distributions(temp_data_file, temp_output_file)
            
            with open(temp_output_file, 'r') as f:
                results = json.load(f)
            
            # Check that sample sizes are 0
            assert results['sample_sizes']['total'] == 0
        except Exception as e:
            # If it raises, that's also acceptable for empty data
            assert "empty" in str(e).lower() or "zero" in str(e).lower()
        finally:
            os.unlink(temp_data_file)
