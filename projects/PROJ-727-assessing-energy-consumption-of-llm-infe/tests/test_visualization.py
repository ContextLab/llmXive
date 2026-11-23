import os
import sys
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from visualization import load_data, plot_energy_bar, plot_tradeoff_scatter
from scatter_slope import calculate_scatter_slope, main as slope_main
from config import DATA_PROCESSED_DIR

@pytest.fixture
def sample_data(tmp_path):
    """Create sample data for testing."""
    # Create sample CSV
    csv_path = os.path.join(DATA_PROCESSED_DIR, "energy_results_aggregated.csv")
    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
    
    data = {
        'model_id': ['gpt2-small', 'gpt2-small', 'codebert-base', 'codebert-base', 'starcoder-1b', 'starcoder-1b'],
        'problem_id': ['prob1', 'prob2', 'prob1', 'prob2', 'prob1', 'prob2'],
        'tokens_generated': [100, 150, 80, 120, 200, 250],
        'energy_kwh': [0.0001, 0.00015, 0.00008, 0.00012, 0.0002, 0.00025],
        'runtime_seconds': [10, 15, 8, 12, 20, 25],
        'pass_fail_status': [1, 0, 1, 1, 0, 1]
    }
    
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    return csv_path

def test_load_data(sample_data):
    """Test that load_data correctly reads the CSV file."""
    df = load_data()
    assert isinstance(df, pd.DataFrame)
    assert 'model_id' in df.columns
    assert 'energy_kwh' in df.columns
    assert len(df) > 0

def test_plot_energy_bar_creates_file(sample_data):
    """Test that plot_energy_bar creates the expected output file."""
    output_path = plot_energy_bar(load_data())
    assert os.path.exists(output_path)
    assert output_path.endswith('.png')
    # Check file size is non-zero
    assert os.path.getsize(output_path) > 0

def test_plot_tradeoff_scatter_creates_file(sample_data):
    """Test that plot_tradeoff_scatter creates the expected output file."""
    output_path = plot_tradeoff_scatter(load_data())
    assert os.path.exists(output_path)
    assert output_path.endswith('.png')
    # Check file size is non-zero
    assert os.path.getsize(output_path) > 0

def test_calculate_scatter_slope(sample_data):
    """Test that scatter slope calculation works."""
    slope, plot_data = calculate_scatter_slope()
    assert isinstance(slope, (int, float, np.floating))
    assert isinstance(plot_data, pd.DataFrame)
    assert 'model_id' in plot_data.columns
    assert 'accuracy' in plot_data.columns
    assert 'energy_per_correct' in plot_data.columns

def test_scatter_slope_main_creates_file(sample_data):
    """Test that scatter_slope main function creates the output file."""
    output_path = slope_main()
    assert os.path.exists(output_path)
    assert output_path.endswith('.txt')
    
    # Check file content
    with open(output_path, 'r') as f:
        content = f.read()
        assert 'Slope' in content
        assert 'Model Data Points' in content

def test_plot_labels_exist(sample_data):
    """Test that plots have proper labels (by checking the code generates them)."""
    # This is a structural test - we verify the functions exist and run
    # The actual label verification would require image inspection
    df = load_data()
    
    # Run both plotting functions
    bar_path = plot_energy_bar(df)
    scatter_path = plot_tradeoff_scatter(df)
    
    # Verify files exist
    assert os.path.exists(bar_path)
    assert os.path.exists(scatter_path)