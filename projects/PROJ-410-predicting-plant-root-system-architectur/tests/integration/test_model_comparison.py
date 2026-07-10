import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from compare_models import (
    load_null_metrics,
    load_trained_metrics,
    compare_models,
    save_comparison_results
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_null_metrics(temp_data_dir):
    """Create sample null model metrics file."""
    data = {
        'nutrient_condition': ['N', 'P', 'K'],
        'model_type': ['null', 'null', 'null'],
        'r2': [0.02, 0.01, 0.03],
        'mae': [10.5, 12.3, 9.8],
        'rmse': [14.2, 15.1, 13.5]
    }
    df = pd.DataFrame(data)
    file_path = temp_data_dir / "null_model_metrics.csv"
    df.to_csv(file_path, index=False)
    return file_path, df

@pytest.fixture
def sample_trained_metrics(temp_data_dir):
    """Create sample trained model metrics file."""
    data = {
        'nutrient_condition': ['N', 'N', 'P', 'P', 'K', 'K'],
        'model_type': ['lasso', 'rf', 'lasso', 'rf', 'lasso', 'rf'],
        'r2': [0.45, 0.52, 0.38, 0.41, 0.49, 0.55],
        'mae': [6.2, 5.8, 7.1, 6.9, 5.5, 5.1],
        'rmse': [8.5, 7.9, 9.2, 8.8, 7.8, 7.2]
    }
    df = pd.DataFrame(data)
    file_path = temp_data_dir / "model_metrics.csv"
    df.to_csv(file_path, index=False)
    return file_path, df

def test_load_null_metrics_valid_file(sample_null_metrics):
    """Test loading valid null metrics file."""
    file_path, expected_df = sample_null_metrics
    result_df = load_null_metrics(file_path)
    
    assert len(result_df) == 3
    assert list(result_df.columns) == ['nutrient_condition', 'model_type', 'r2', 'mae', 'rmse']
    assert all(result_df['nutrient_condition'] == expected_df['nutrient_condition'])

def test_load_null_metrics_missing_file(temp_data_dir):
    """Test error handling for missing file."""
    non_existent_path = temp_data_dir / "nonexistent.csv"
    
    with pytest.raises(FileNotFoundError):
        load_null_metrics(non_existent_path)

def test_load_null_metrics_empty_file(temp_data_dir):
    """Test error handling for empty file."""
    file_path = temp_data_dir / "empty.csv"
    file_path.touch()
    
    with pytest.raises(ValueError):
        load_null_metrics(file_path)

def test_load_trained_metrics_valid_file(sample_trained_metrics):
    """Test loading valid trained metrics file."""
    file_path, expected_df = sample_trained_metrics
    result_df = load_trained_metrics(file_path)
    
    assert len(result_df) == 6
    assert list(result_df.columns) == ['nutrient_condition', 'model_type', 'r2', 'mae', 'rmse']

def test_compare_models_basic(sample_null_metrics, sample_trained_metrics):
    """Test basic model comparison logic."""
    _, null_df = sample_null_metrics
    _, trained_df = sample_trained_metrics
    
    result_df = compare_models(null_df, trained_df)
    
    assert len(result_df) == 6  # 2 models per condition * 3 conditions
    assert 'delta_r2' in result_df.columns
    assert 'overall_improved' in result_df.columns
    
    # Check that all trained models show improvement over null
    assert all(result_df['delta_r2'] > 0)
    assert all(result_df['overall_improved'])

def test_compare_models_no_improvement(sample_null_metrics, sample_trained_metrics):
    """Test comparison when models don't improve over null."""
    _, null_df = sample_null_metrics
    _, trained_df = sample_trained_metrics
    
    # Modify trained data to be worse than null
    trained_df['r2'] = 0.01
    trained_df['mae'] = 15.0
    trained_df['rmse'] = 18.0
    
    result_df = compare_models(null_df, trained_df)
    
    assert len(result_df) == 6
    assert all(~result_df['overall_improved'])
    assert all(result_df['delta_r2'] < 0)

def test_compare_models_partial_data(sample_null_metrics, sample_trained_metrics):
    """Test comparison with missing conditions."""
    _, null_df = sample_null_metrics
    _, trained_df = sample_trained_metrics
    
    # Remove one condition from trained data
    trained_df = trained_df[trained_df['nutrient_condition'] != 'K']
    
    result_df = compare_models(null_df, trained_df)
    
    assert len(result_df) == 4  # Only N and P conditions
    assert 'K' not in result_df['nutrient_condition'].values

def test_save_comparison_results(sample_null_metrics, sample_trained_metrics, temp_data_dir):
    """Test saving comparison results."""
    _, null_df = sample_null_metrics
    _, trained_df = sample_trained_metrics
    
    comparison_df = compare_models(null_df, trained_df)
    output_path = temp_data_dir / "comparison_results.csv"
    
    save_comparison_results(comparison_df, output_path)
    
    assert output_path.exists()
    assert output_path.parent.exists()
    
    # Check saved file content
    saved_df = pd.read_csv(output_path)
    assert len(saved_df) == len(comparison_df)
    assert list(saved_df.columns) == list(comparison_df.columns)
    
    # Check summary file was created
    summary_path = output_path.parent / "comparison_summary.txt"
    assert summary_path.exists()

def test_integration_full_workflow(sample_null_metrics, sample_trained_metrics, temp_data_dir):
    """Test complete workflow from loading to saving."""
    _, null_df = sample_null_metrics
    _, trained_df = sample_trained_metrics
    
    # Compare models
    result_df = compare_models(null_df, trained_df)
    
    # Save results
    output_path = temp_data_dir / "full_workflow_results.csv"
    save_comparison_results(result_df, output_path)
    
    # Verify outputs
    assert output_path.exists()
    assert (temp_data_dir / "comparison_summary.txt").exists()
    
    # Load and verify content
    loaded_df = pd.read_csv(output_path)
    assert len(loaded_df) == 6
    assert all(loaded_df['overall_improved'])