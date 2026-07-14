import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json
import os

from src.reports.generate_plots import (
    calculate_residuals,
    create_residual_plot,
    create_feature_importance_plot,
    create_predicted_vs_actual_plot,
    generate_diagnostic_report,
    load_model_results,
    load_processed_data
)

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame with required columns."""
    np.random.seed(42)
    n_games = 100
    df = pd.DataFrame({
        'game_id': range(n_games),
        'elo_expected_prob': np.random.uniform(0.3, 0.8, n_games),
        'outcome_deviation': np.random.uniform(-0.5, 0.5, n_games),
        'eco_code': np.random.choice(['B00', 'B10', 'C00', 'D00'], n_games)
    })
    return df

@pytest.fixture
def sample_model_results():
    """Create sample model results dictionary."""
    return {
        'ridge': {
            'coefficients': {
                'eco_B00': 0.15,
                'eco_B10': -0.08,
                'eco_C00': 0.22,
                'eco_D00': -0.03,
                'feature_x': 0.45,
                'feature_y': -0.12
            },
            'p_values': {
                'eco_B00': 0.03,
                'eco_B10': 0.15,
                'eco_C00': 0.01,
                'eco_D00': 0.45,
                'feature_x': 0.002,
                'feature_y': 0.08
            },
            'r_squared': 0.35,
            'aic': 1250.5
        },
        'glm': {
            'coefficients': {
                'eco_B00': 0.18,
                'eco_B10': -0.10,
                'eco_C00': 0.25,
                'eco_D00': -0.05,
                'feature_x': 0.42,
                'feature_y': -0.15
            },
            'p_values': {
                'eco_B00': 0.02,
                'eco_B10': 0.12,
                'eco_C00': 0.008,
                'eco_D00': 0.38,
                'feature_x': 0.001,
                'feature_y': 0.06
            },
            'r_squared': 0.38,
            'aic': 1245.2
        }
    }

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_calculate_residuals(sample_dataframe):
    """Test that residuals are calculated correctly."""
    result = calculate_residuals(sample_dataframe)
    
    assert 'residual' in result.columns
    assert 'outcome_deviation' in result.columns
    assert len(result) == len(sample_dataframe)
    
    # Check that residual equals outcome_deviation
    pd.testing.assert_series_equal(
        result['residual'], 
        result['outcome_deviation'],
        check_names=False
    )

def test_calculate_residuals_missing_column(sample_dataframe):
    """Test error handling when outcome_deviation is missing."""
    df = sample_dataframe.drop(columns=['outcome_deviation'])
    
    with pytest.raises(ValueError, match="DataFrame missing 'outcome_deviation' column"):
        calculate_residuals(df)

def test_load_model_results(temp_dir, sample_model_results):
    """Test loading model results from JSON file."""
    results_file = temp_dir / 'model_metrics.json'
    with open(results_file, 'w') as f:
        json.dump(sample_model_results, f)
    
    loaded = load_model_results(results_file)
    
    assert 'ridge' in loaded
    assert 'glm' in loaded
    assert loaded['ridge']['r_squared'] == sample_model_results['ridge']['r_squared']

def test_load_model_results_file_not_found(temp_dir):
    """Test error when model results file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        load_model_results(temp_dir / 'nonexistent.json')

def test_load_processed_data_parquet(temp_dir, sample_dataframe):
    """Test loading parquet file."""
    data_file = temp_dir / 'games.parquet'
    sample_dataframe.to_parquet(data_file)
    
    loaded = load_processed_data(data_file)
    
    assert len(loaded) == len(sample_dataframe)
    assert list(loaded.columns) == list(sample_dataframe.columns)

def test_load_processed_data_csv(temp_dir, sample_dataframe):
    """Test loading CSV file."""
    data_file = temp_dir / 'games.csv'
    sample_dataframe.to_csv(data_file, index=False)
    
    loaded = load_processed_data(data_file)
    
    assert len(loaded) == len(sample_dataframe)

def test_load_processed_data_unsupported_format(temp_dir):
    """Test error for unsupported file format."""
    data_file = temp_dir / 'games.txt'
    data_file.touch()
    
    with pytest.raises(ValueError, match="Unsupported file format"):
        load_processed_data(data_file)

def test_generate_diagnostic_report(temp_dir, sample_dataframe, sample_model_results):
    """Test diagnostic report generation."""
    report_path = temp_dir / 'diagnostics.json'
    
    report = generate_diagnostic_report(sample_dataframe, sample_model_results, report_path)
    
    assert report_path.exists()
    assert 'total_games' in report
    assert 'residual_statistics' in report
    assert 'model_metrics' in report
    assert 'plots_generated' in report
    
    assert report['total_games'] == len(sample_dataframe)
    assert 'mean' in report['residual_statistics']
    assert 'std' in report['residual_statistics']

def test_create_residual_plot_creates_file(temp_dir, sample_dataframe):
    """Test that residual plot file is created."""
    output_path = temp_dir / 'residual_test.png'
    
    # This should not raise an error and should create the file
    create_residual_plot(sample_dataframe, output_path, 'ridge')
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_create_predicted_vs_actual_plot_creates_file(temp_dir, sample_dataframe):
    """Test that predicted vs actual plot file is created."""
    output_path = temp_dir / 'predicted_vs_actual_test.png'
    
    create_predicted_vs_actual_plot(sample_dataframe, output_path, 'ridge')
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_create_feature_importance_plot_creates_file(temp_dir, sample_dataframe, sample_model_results):
    """Test that feature importance plot file is created."""
    output_path = temp_dir / 'feature_importance_test.png'
    
    create_feature_importance_plot(sample_dataframe, sample_model_results, output_path, 'ridge')
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0