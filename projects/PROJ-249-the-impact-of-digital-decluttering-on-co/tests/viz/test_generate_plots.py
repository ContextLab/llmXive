"""
Tests for the visualization generator.

These tests verify that the plot generation functions work correctly
with mock data and produce valid output files.
"""

import os
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd

# Import the module to test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from viz.generate_plots import (
    load_change_scores_data,
    create_boxplot_metrics,
    create_change_score_distribution,
    create_change_score_boxplot,
    generate_all_plots,
    main
)
from config.env_config import ProjectConfig


@pytest.fixture
def temp_directory():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_config(temp_directory):
    """Create a mock configuration for testing."""
    config = ProjectConfig(
        project_root=str(temp_directory),
        data_dir=str(temp_directory / 'data'),
        figures_dir=str(temp_directory / 'figures'),
        results_dir=str(temp_directory / 'results'),
        raw_data_path=str(temp_directory / 'data' / 'raw' / 'synthetic_baseline.csv'),
        merged_data_path=str(temp_directory / 'data' / 'processed' / 'merged_data.csv'),
        seed=42
    )
    
    # Create necessary directories
    (temp_directory / 'data' / 'raw').mkdir(parents=True, exist_ok=True)
    (temp_directory / 'data' / 'processed').mkdir(parents=True, exist_ok=True)
    (temp_directory / 'figures').mkdir(parents=True, exist_ok=True)
    
    return config


@pytest.fixture
def sample_merged_data():
    """Create sample merged data for testing."""
    data = {
        'participant_id': ['P001', 'P001', 'P002', 'P002', 'P003', 'P003'],
        'metric_type': ['SART_errors', 'SART_errors', 'SART_errors', 
                       'SART_errors', 'Ospan_score', 'Ospan_score'],
        'time_point': ['baseline', 'post_intervention', 'baseline', 
                      'post_intervention', 'baseline', 'post_intervention'],
        'value': [12.0, 8.0, 15.0, 10.0, 45.0, 52.0]
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_change_data():
    """Create sample change score data for testing."""
    data = {
        'participant_id': ['P001', 'P002', 'P003'],
        'metric_type': ['SART_errors', 'SART_errors', 'Ospan_score'],
        'change_score': [-4.0, -5.0, 7.0]
    }
    return pd.DataFrame(data)


def test_create_boxplot_metrics(mock_config, sample_merged_data, temp_directory):
    """Test the boxplot metrics generation function."""
    output_path = temp_directory / 'test_boxplot.png'
    
    with patch('viz.generate_plots.get_config', return_value=mock_config):
        with patch('viz.generate_plots.load_merged_data', return_value=sample_merged_data):
            create_boxplot_metrics(sample_merged_data, output_path)
    
    assert output_path.exists(), "Boxplot file was not created"
    assert output_path.stat().st_size > 0, "Boxplot file is empty"


def test_create_change_score_distribution(mock_config, sample_change_data, temp_directory):
    """Test the change score distribution generation function."""
    output_path = temp_directory / 'test_distribution.png'
    
    with patch('viz.generate_plots.get_config', return_value=mock_config):
        create_change_score_distribution(sample_change_data, output_path)
    
    assert output_path.exists(), "Distribution plot file was not created"
    assert output_path.stat().st_size > 0, "Distribution plot file is empty"


def test_create_change_score_boxplot(mock_config, sample_change_data, temp_directory):
    """Test the change score boxplot generation function."""
    output_path = temp_directory / 'test_change_boxplot.png'
    
    with patch('viz.generate_plots.get_config', return_value=mock_config):
        create_change_score_boxplot(sample_change_data, output_path)
    
    assert output_path.exists(), "Change score boxplot file was not created"
    assert output_path.stat().st_size > 0, "Change score boxplot file is empty"


def test_generate_all_plots(mock_config, sample_merged_data, sample_change_data, temp_directory):
    """Test the full plot generation pipeline."""
    # Create a mock for load_change_scores_data
    def mock_load_change_scores():
        return sample_change_data
    
    with patch('viz.generate_plots.get_config', return_value=mock_config):
        with patch('viz.generate_plots.load_merged_data', return_value=sample_merged_data):
            with patch('viz.generate_plots.load_change_scores_data', side_effect=mock_load_change_scores):
                output_files = generate_all_plots()
    
    assert 'boxplot_metrics' in output_files, "Boxplot metrics not in output"
    assert 'change_score_distribution' in output_files, "Change score distribution not in output"
    assert 'change_score_boxplot' in output_files, "Change score boxplot not in output"
    
    # Verify files exist
    for name, path in output_files.items():
        assert os.path.exists(path), f"Output file {path} does not exist"
        assert os.path.getsize(path) > 0, f"Output file {path} is empty"
    
    # Verify metadata file
    metadata_path = Path(mock_config.figures_dir) / 'plot_metadata.json'
    assert metadata_path.exists(), "Metadata file was not created"
    
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    assert 'plots' in metadata, "Metadata missing 'plots' key"
    assert metadata['total_plots'] == 3, "Incorrect number of plots in metadata"


def test_main_function(mock_config, sample_merged_data, sample_change_data):
    """Test the main entry point."""
    def mock_load_change_scores():
        return sample_change_data
    
    with patch('viz.generate_plots.get_config', return_value=mock_config):
        with patch('viz.generate_plots.load_merged_data', return_value=sample_merged_data):
            with patch('viz.generate_plots.load_change_scores_data', side_effect=mock_load_change_scores):
                main()
    
    # Verify files were created
    figures_dir = Path(mock_config.figures_dir)
    assert (figures_dir / 'boxplot_metrics.png').exists()
    assert (figures_dir / 'change_score_distribution.png').exists()
    assert (figures_dir / 'change_score_boxplot.png').exists()
    assert (figures_dir / 'plot_metadata.json').exists()


def test_empty_data_handling(mock_config, temp_directory):
    """Test handling of empty data."""
    empty_df = pd.DataFrame(columns=['metric_type', 'time_point', 'value'])
    output_path = temp_directory / 'empty_test.png'
    
    with patch('viz.generate_plots.get_config', return_value=mock_config):
        # Should not raise an error, just log a warning
        create_boxplot_metrics(empty_df, output_path)
    
    # File might not be created if no data, which is acceptable
    # The important thing is no exception was raised


def test_invalid_path_handling(mock_config):
    """Test handling of invalid paths."""
    with patch('viz.generate_plots.get_config', return_value=mock_config):
        with pytest.raises(FileNotFoundError):
            load_change_scores_data()

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
