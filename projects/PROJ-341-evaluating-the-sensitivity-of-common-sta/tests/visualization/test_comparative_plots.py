"""
Unit tests for comparative plots generation in low sample size analysis.
"""

import os
import json
import csv
import tempfile
import shutil
from pathlib import Path
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from code.visualization.comparative_plots import (
    load_low_sample_data,
    plot_test_divergence,
    plot_test_pairwise_divergence,
    generate_comparative_plots
)


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_error_rates_data(temp_data_dir):
    """Create sample error rates CSV data for testing."""
    csv_path = os.path.join(temp_data_dir, 'error_rates_summary.csv')
    
    # Create sample data with low sample sizes (n < 30)
    data = [
        ['sample_size', 'test_type', 'error_rate', 'lower_ci', 'upper_ci', 'hypothesis', 'effect_size'],
        [5, 't-test', 0.062, 0.055, 0.069, 'null', '0.0'],
        [10, 't-test', 0.058, 0.051, 0.065, 'null', '0.0'],
        [15, 't-test', 0.053, 0.047, 0.059, 'null', '0.0'],
        [20, 't-test', 0.051, 0.045, 0.057, 'null', '0.0'],
        [25, 't-test', 0.050, 0.044, 0.056, 'null', '0.0'],
        [5, 'anova', 0.068, 0.060, 0.076, 'null', '0.0'],
        [10, 'anova', 0.063, 0.056, 0.070, 'null', '0.0'],
        [15, 'anova', 0.057, 0.051, 0.063, 'null', '0.0'],
        [20, 'anova', 0.054, 0.048, 0.060, 'null', '0.0'],
        [25, 'anova', 0.052, 0.046, 0.058, 'null', '0.0'],
        [5, 'chi-squared', 0.075, 0.067, 0.083, 'null', '0.0'],
        [10, 'chi-squared', 0.069, 0.062, 0.076, 'null', '0.0'],
        [15, 'chi-squared', 0.061, 0.055, 0.067, 'null', '0.0'],
        [20, 'chi-squared', 0.056, 0.050, 0.062, 'null', '0.0'],
        [25, 'chi-squared', 0.053, 0.047, 0.059, 'null', '0.0'],
        # High sample size (should be filtered out)
        [50, 't-test', 0.050, 0.045, 0.055, 'null', '0.0'],
        [100, 't-test', 0.049, 0.044, 0.054, 'null', '0.0'],
    ]
    
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(data)
    
    return csv_path


def test_load_low_sample_data(sample_error_rates_data, temp_data_dir):
    """Test loading and filtering of low sample size data."""
    data_by_test = load_low_sample_data(sample_error_rates_data, min_n=5, max_n=30)
    
    # Check that we have data for all test types
    assert 't-test' in data_by_test
    assert 'anova' in data_by_test
    assert 'chi-squared' in data_by_test
    
    # Check that high sample sizes are filtered out
    for test_type, data in data_by_test.items():
        for entry in data:
            assert 5 <= entry['sample_size'] < 30
    
    # Check data counts
    assert len(data_by_test['t-test']) == 5  # n=5, 10, 15, 20, 25
    assert len(data_by_test['anova']) == 5
    assert len(data_by_test['chi-squared']) == 5
    
    # Check data structure
    first_entry = data_by_test['t-test'][0]
    assert 'sample_size' in first_entry
    assert 'error_rate' in first_entry
    assert 'lower_ci' in first_entry
    assert 'upper_ci' in first_entry
    assert 'hypothesis' in first_entry
    assert 'effect_size' in first_entry


def test_load_low_sample_data_file_not_found(temp_data_dir):
    """Test that FileNotFoundError is raised when file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        load_low_sample_data('/nonexistent/path.csv')


def test_load_low_sample_data_empty_file(temp_data_dir):
    """Test handling of empty CSV file."""
    csv_path = os.path.join(temp_data_dir, 'empty.csv')
    with open(csv_path, 'w') as f:
        f.write('sample_size,test_type,error_rate\n')
    
    data_by_test = load_low_sample_data(csv_path)
    assert len(data_by_test) == 0


def test_plot_test_divergence(sample_error_rates_data, temp_data_dir):
    """Test generation of divergence plot."""
    output_path = os.path.join(temp_data_dir, 'divergence_plot.png')
    data_by_test = load_low_sample_data(sample_error_rates_data)
    
    # This should not raise an exception
    plot_test_divergence(data_by_test, output_path)
    
    # Check that file was created
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0


def test_plot_test_pairwise_divergence(sample_error_rates_data, temp_data_dir):
    """Test generation of pairwise divergence plot."""
    output_path = os.path.join(temp_data_dir, 'pairwise_plot.png')
    data_by_test = load_low_sample_data(sample_error_rates_data)
    
    # This should not raise an exception
    plot_test_pairwise_divergence(data_by_test, output_path)
    
    # Check that file was created
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0


def test_generate_comparative_plots(sample_error_rates_data, temp_data_dir):
    """Test generation of all comparative plots."""
    output_dir = os.path.join(temp_data_dir, 'plots')
    
    plots = generate_comparative_plots(
        error_rates_file=sample_error_rates_data,
        output_dir=output_dir
    )
    
    # Check that plots were generated
    assert len(plots) == 2
    assert os.path.exists(plots[0])
    assert os.path.exists(plots[1])
    
    # Check filenames
    assert 'comparative_test_divergence' in plots[0]
    assert 'pairwise_test_divergence' in plots[1]


def test_generate_comparative_plots_creates_output_dir(sample_error_rates_data, temp_data_dir):
    """Test that output directory is created if it doesn't exist."""
    output_dir = os.path.join(temp_data_dir, 'new_plots_dir')
    assert not os.path.exists(output_dir)
    
    plots = generate_comparative_plots(
        error_rates_file=sample_error_rates_data,
        output_dir=output_dir
    )
    
    assert os.path.exists(output_dir)
    assert len(plots) == 2


def test_generate_comparative_plots_file_not_found(temp_data_dir):
    """Test error handling when error rates file doesn't exist."""
    output_dir = os.path.join(temp_data_dir, 'plots')
    
    with pytest.raises(FileNotFoundError):
        generate_comparative_plots(
            error_rates_file='/nonexistent/error_rates.csv',
            output_dir=output_dir
        )


def test_plot_divergence_with_missing_ci(sample_error_rates_data, temp_data_dir):
    """Test handling of data with missing confidence intervals."""
    # Create modified data with missing CI values
    csv_path = os.path.join(temp_data_dir, 'error_rates_no_ci.csv')
    data = [
        ['sample_size', 'test_type', 'error_rate', 'lower_ci', 'upper_ci', 'hypothesis', 'effect_size'],
        [5, 't-test', 0.062, None, None, 'null', '0.0'],
        [10, 't-test', 0.058, None, None, 'null', '0.0'],
    ]
    
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(data)
    
    data_by_test = load_low_sample_data(csv_path)
    output_path = os.path.join(temp_data_dir, 'divergence_no_ci.png')
    
    # Should not raise an exception even with missing CI
    plot_test_divergence(data_by_test, output_path)
    assert os.path.exists(output_path)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])