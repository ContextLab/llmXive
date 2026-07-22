import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from models.collinearity_analysis import (
    load_final_dataset,
    get_predictor_columns,
    calculate_vif,
    interpret_vif,
    generate_collinearity_report,
    save_report
)

@pytest.fixture
def sample_dataset():
    """Create a sample dataset for testing."""
    data = {
        'composition_id': ['comp1', 'comp2', 'comp3', 'comp4', 'comp5'],
        'chemical_family': ['oxide', 'sulfide', 'oxide', 'organic', 'sulfide'],
        'Tg': [500.0, 520.0, 480.0, 450.0, 510.0],
        'Tx': [600.0, 620.0, 580.0, 550.0, 610.0],
        'crystallization_label': [0, 0, 0, 1, 0],
        'truncated': [False, False, True, False, False],
        'SRO_Invariance_Assumed': [False] * 5,
        'cooling_rate': [1.0e10] * 5,
        'scaling_factor': [1.0] * 5,
        'rdf_peak_position': [2.5, 2.6, 2.4, 2.3, 2.7],
        'rdf_peak_width': [0.1, 0.12, 0.09, 0.11, 0.13],
        'bond_angle_variance': [15.0, 16.0, 14.0, 13.0, 17.0],
        'coordination_number': [4.0, 4.2, 3.8, 3.5, 4.3],
        'glass_transition_entropy': [1.2, 1.3, 1.1, 1.0, 1.4]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_parquet_file(sample_dataset, tmp_path):
    """Create a temporary Parquet file with sample data."""
    file_path = tmp_path / "final_dataset.parquet"
    sample_dataset.to_parquet(file_path)
    return file_path

def test_get_predictor_columns(sample_dataset):
    """Test that get_predictor_columns correctly identifies predictor columns."""
    predictor_cols = get_predictor_columns(sample_dataset)
    
    expected_predictors = [
        'rdf_peak_position', 'rdf_peak_width', 'bond_angle_variance',
        'coordination_number', 'glass_transition_entropy'
    ]
    
    assert set(predictor_cols) == set(expected_predictors)
    assert 'composition_id' not in predictor_cols
    assert 'chemical_family' not in predictor_cols
    assert 'Tg' not in predictor_cols
    assert 'Tx' not in predictor_cols
    assert 'crystallization_label' not in predictor_cols

def test_calculate_vif_basic(sample_dataset):
    """Test VIF calculation with basic data."""
    predictor_cols = get_predictor_columns(sample_dataset)
    vif_df = calculate_vif(sample_dataset, predictor_cols)
    
    assert len(vif_df) == len(predictor_cols)
    assert 'feature' in vif_df.columns
    assert 'VIF' in vif_df.columns
    assert 'reason' in vif_df.columns
    
    # Check that all features have a reason
    assert all(vif_df['reason'].isin(['calculated', 'constant', 'calculation_error']))

def test_calculate_vif_constant_column(sample_dataset):
    """Test VIF calculation with a constant column."""
    df = sample_dataset.copy()
    df['constant_feature'] = 5.0
    
    predictor_cols = get_predictor_columns(df)
    vif_df = calculate_vif(df, predictor_cols)
    
    constant_row = vif_df[vif_df['feature'] == 'constant_feature']
    assert len(constant_row) == 1
    assert constant_row.iloc[0]['reason'] == 'constant'
    assert np.isinf(constant_row.iloc[0]['VIF'])

def test_interpret_vif(sample_dataset):
    """Test VIF interpretation."""
    predictor_cols = get_predictor_columns(sample_dataset)
    vif_df = calculate_vif(sample_dataset, predictor_cols)
    interpretation = interpret_vif(vif_df)
    
    assert 'summary' in interpretation
    assert 'high_collinearity_features' in interpretation
    assert 'moderate_collinearity_features' in interpretation
    assert 'low_collinearity_features' in interpretation
    assert 'constant_features' in interpretation
    assert 'error_features' in interpretation
    
    # Check summary structure
    summary = interpretation['summary']
    assert 'mean_vif' in summary
    assert 'max_vif' in summary
    assert 'min_vif' in summary

def test_interpret_vif_high_collinearity():
    """Test VIF interpretation with high collinearity."""
    # Create data with high collinearity
    np.random.seed(42)
    n = 100
    x1 = np.random.normal(0, 1, n)
    x2 = x1 * 0.99 + np.random.normal(0, 0.1, n)  # Highly correlated
    
    df = pd.DataFrame({
        'x1': x1,
        'x2': x2,
        'x3': np.random.normal(0, 1, n)  # Independent
    })
    
    predictor_cols = ['x1', 'x2', 'x3']
    vif_df = calculate_vif(df, predictor_cols)
    interpretation = interpret_vif(vif_df)
    
    # At least one feature should have high collinearity
    assert len(interpretation['high_collinearity_features']) > 0 or \
           len(interpretation['moderate_collinearity_features']) > 0

def test_save_report(tmp_path):
    """Test saving the report to a JSON file."""
    report = {
        "status": "success",
        "test_data": {"key": "value", "number": 42},
        "vif_results": [
            {"feature": "x1", "VIF": 1.5, "reason": "calculated"},
            {"feature": "x2", "VIF": 2.0, "reason": "calculated"}
        ]
    }
    
    output_path = tmp_path / "test_report.json"
    save_report(report, output_path)
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        loaded_report = json.load(f)
    
    assert loaded_report["status"] == "success"
    assert loaded_report["test_data"]["key"] == "value"
    assert len(loaded_report["vif_results"]) == 2

@patch('models.collinearity_analysis.get_paths')
@patch('models.collinearity_analysis.load_final_dataset')
@patch('models.collinearity_analysis.get_predictor_columns')
@patch('models.collinearity_analysis.calculate_vif')
@patch('models.collinearity_analysis.interpret_vif')
@patch('models.collinearity_analysis.save_report')
def test_generate_collinearity_report_mock(
    mock_save_report, mock_interpret_vif, mock_calculate_vif,
    mock_get_predictor_columns, mock_load_final_dataset, mock_get_paths,
    tmp_path
):
    """Test the full report generation with mocked dependencies."""
    # Setup mocks
    mock_paths = {
        "data_processed": tmp_path,
        "reports": tmp_path
    }
    mock_get_paths.return_value = mock_paths
    
    mock_df = pd.DataFrame({
        'rdf_peak_position': [1.0, 2.0],
        'rdf_peak_width': [0.1, 0.2]
    })
    mock_load_final_dataset.return_value = mock_df
    
    mock_get_predictor_columns.return_value = ['rdf_peak_position', 'rdf_peak_width']
    
    mock_vif_df = pd.DataFrame({
        'feature': ['rdf_peak_position', 'rdf_peak_width'],
        'VIF': [1.5, 2.0],
        'reason': ['calculated', 'calculated']
    })
    mock_calculate_vif.return_value = mock_vif_df
    
    mock_interpret_vif.return_value = {
        'summary': {'mean_vif': 1.75},
        'high_collinearity_features': [],
        'moderate_collinearity_features': [],
        'low_collinearity_features': ['rdf_peak_position', 'rdf_peak_width']
    }
    
    # Call the function
    report = generate_collinearity_report()
    
    # Verify
    assert report['status'] == 'success'
    assert 'vif_results' in report
    assert 'interpretation' in report
    mock_save_report.assert_called_once()

def test_no_predictors_case(tmp_path):
    """Test handling of dataset with no predictors."""
    df = pd.DataFrame({
        'composition_id': ['comp1', 'comp2'],
        'Tg': [500.0, 520.0],
        'Tx': [600.0, 620.0]
    })
    
    predictor_cols = get_predictor_columns(df)
    assert len(predictor_cols) == 0
    
    # Test interpret_vif with empty VIF DataFrame
    vif_df = pd.DataFrame(columns=['feature', 'VIF', 'reason'])
    interpretation = interpret_vif(vif_df)
    
    assert interpretation['summary'] == "No valid VIF values to interpret."
    assert len(interpretation['high_collinearity_features']) == 0
    assert len(interpretation['low_collinearity_features']) == 0