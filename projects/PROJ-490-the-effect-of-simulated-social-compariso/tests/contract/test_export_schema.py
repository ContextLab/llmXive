"""
Contract test for T021: Export regression results schema.

Verifies that the exported CSV and JSON files adhere to the expected schema.
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd

from utils.validators import validate_dataframe_schema, validate_json_against_schema
from code.analysis.export_results import run_export


# Define expected schemas
COEFFICIENTS_SCHEMA = {
    "type": "dataframe",
    "required_columns": [
        "term", "estimate", "std_error", "t_statistic", "p_value"
    ],
    "optional_columns": [
        "conf_interval_lower", "conf_interval_upper"
    ],
    "column_types": {
        "term": "object",
        "estimate": "float64",
        "std_error": "float64",
        "t_statistic": "float64",
        "p_value": "float64",
        "conf_interval_lower": "float64",
        "conf_interval_upper": "float64"
    }
}

DIAGNOSTICS_SCHEMA = {
    "type": "object",
    "required_keys": [
        "assumptions", "vif", "bootstrap_ci"
    ],
    "optional_keys": [
        "interpretation", "data_source_type", "model_info"
    ],
    "nested_schemas": {
        "assumptions": {
            "type": "object",
            "required_keys": ["normality", "homoscedasticity"]
        },
        "vif": {
            "type": "object",
            "additional_properties": "number"
        },
        "bootstrap_ci": {
            "type": "object"
        }
    }
}


def test_export_coefficients_csv_schema(tmp_path):
    """Test that exported CSV matches the coefficients schema."""
    # Prepare mock results
    mock_coefficients = {
        'term': ['Intercept', 'avatar_condition', 'pre_self_esteem'],
        'estimate': [2.5, 0.8, 0.6],
        'std_error': [0.15, 0.12, 0.08],
        't_statistic': [16.67, 6.67, 7.50],
        'p_value': [1e-10, 1e-8, 1e-9],
        'conf_interval_lower': [2.20, 0.56, 0.44],
        'conf_interval_upper': [2.80, 1.04, 0.76]
    }
    
    mock_diagnostics = {
        'assumptions': {'normality': {}, 'homoscedasticity': {}},
        'vif': {'avatar_condition': 1.2},
        'bootstrap_ci': {}
    }
    
    results = {
        'coefficients': mock_coefficients,
        'diagnostics': mock_diagnostics,
        'interpretation_label': 'Test',
        'data_source_type': 'synthetic'
    }
    
    # Run export
    output_paths = run_export(results, output_dir=tmp_path)
    csv_path = output_paths['coefficients_csv']
    
    # Validate CSV
    assert csv_path.exists(), "CSV file was not created"
    
    df = pd.read_csv(csv_path)
    
    # Check required columns
    required_cols = COEFFICIENTS_SCHEMA['required_columns']
    for col in required_cols:
        assert col in df.columns, f"Missing required column: {col}"
    
    # Check column types
    for col, expected_type in COEFFICIENTS_SCHEMA['column_types'].items():
        if col in df.columns:
            # Pandas might infer float64 as float32 in some cases, so we check for numeric
            if 'float' in expected_type:
                assert pd.api.types.is_numeric_dtype(df[col]), \
                    f"Column {col} should be numeric, got {df[col].dtype}"
            elif expected_type == 'object':
                assert df[col].dtype == 'object', \
                    f"Column {col} should be object, got {df[col].dtype}"


def test_export_diagnostics_json_schema(tmp_path):
    """Test that exported JSON matches the diagnostics schema."""
    # Prepare mock results
    mock_coefficients = {
        'term': ['Intercept'],
        'estimate': [2.5],
        'std_error': [0.15],
        't_statistic': [16.67],
        'p_value': [1e-10]
    }
    
    mock_diagnostics = {
        'assumptions': {
            'normality': {'test': 'Shapiro', 'p_value': 0.15, 'passed': True},
            'homoscedasticity': {'test': 'BP', 'p_value': 0.27, 'passed': True}
        },
        'vif': {
            'avatar_condition': 1.2,
            'pre_self_esteem': 1.5
        },
        'bootstrap_ci': {
            'interaction': {'estimate': 0.2, 'ci_lower': 0.01, 'ci_upper': 0.39}
        },
        'interpretation': 'Simulated Causal Effect',
        'data_source_type': 'synthetic'
    }
    
    results = {
        'coefficients': mock_coefficients,
        'diagnostics': mock_diagnostics
    }
    
    # Run export
    output_paths = run_export(results, output_dir=tmp_path)
    json_path = output_paths['diagnostics_json']
    
    # Validate JSON
    assert json_path.exists(), "JSON file was not created"
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Check required keys
    required_keys = DIAGNOSTICS_SCHEMA['required_keys']
    for key in required_keys:
        assert key in data, f"Missing required key: {key}"
    
    # Check nested structure
    assert 'normality' in data['assumptions'], "Missing 'normality' in assumptions"
    assert 'homoscedasticity' in data['assumptions'], "Missing 'homoscedasticity' in assumptions"
    
    # Check VIF values are numeric
    for var, vif_val in data['vif'].items():
        assert isinstance(vif_val, (int, float)), f"VIF for {var} should be numeric"
        
        # Check for VIF >= 5 flagging (T022 requirement, but we check presence here)
        if vif_val >= 5:
            # In a full implementation, this would trigger a specific flag
            # For now, we just ensure the value is present
            pass


def test_export_integration(tmp_path):
    """Integration test: Run export and verify both files are created and valid."""
    # Full mock data
    mock_coefficients = {
        'term': ['Intercept', 'avatar_condition', 'pre_self_esteem', 
                 'comparison_tendency', 'interaction'],
        'estimate': [2.5, 0.8, 0.6, 0.3, 0.2],
        'std_error': [0.15, 0.12, 0.08, 0.10, 0.09],
        't_statistic': [16.67, 6.67, 7.50, 3.00, 2.22],
        'p_value': [1e-10, 1e-8, 1e-9, 0.003, 0.027],
        'conf_interval_lower': [2.20, 0.56, 0.44, 0.10, 0.02],
        'conf_interval_upper': [2.80, 1.04, 0.76, 0.50, 0.38]
    }
    
    mock_diagnostics = {
        'assumptions': {
            'normality': {'test': 'Shapiro-Wilk', 'statistic': 0.98, 'p_value': 0.15, 'passed': True},
            'homoscedasticity': {'test': 'Breusch-Pagan', 'statistic': 1.2, 'p_value': 0.27, 'passed': True}
        },
        'vif': {
            'avatar_condition': 1.2,
            'pre_self_esteem': 1.5,
            'comparison_tendency': 1.3,
            'interaction': 1.8
        },
        'bootstrap_ci': {
            'interaction_effect': {
                'estimate': 0.2,
                'ci_lower': 0.02,
                'ci_upper': 0.38,
                'ci_width': 0.36,
                'iterations': 1000
            }
        },
        'model_info': {
            'r_squared': 0.45,
            'adj_r_squared': 0.43,
            'f_statistic': 25.6,
            'f_p_value': 1e-15
        }
    }
    
    results = {
        'coefficients': mock_coefficients,
        'diagnostics': mock_diagnostics,
        'interpretation_label': 'Empirical Association',
        'data_source_type': 'real'
    }
    
    # Run export
    output_paths = run_export(results, output_dir=tmp_path)
    
    # Verify files exist
    assert output_paths['coefficients_csv'].exists()
    assert output_paths['diagnostics_json'].exists()
    
    # Verify CSV content
    df = pd.read_csv(output_paths['coefficients_csv'])
    assert len(df) == 5  # 5 terms
    assert list(df['term']) == ['Intercept', 'avatar_condition', 'pre_self_esteem', 
                                'comparison_tendency', 'interaction']
    
    # Verify JSON content
    with open(output_paths['diagnostics_json'], 'r') as f:
        data = json.load(f)
    
    assert data['interpretation'] == 'Empirical Association'
    assert data['data_source_type'] == 'real'
    assert 'interaction_effect' in data['bootstrap_ci']