"""
Contract test for model output schema compliance.

This test suite validates that the model evaluation pipeline produces outputs
that strictly adhere to the defined schema in contracts/model_output.schema.yaml.
It ensures that metrics, feature importances, and statistical corrections are
correctly structured and contain expected fields.
"""
import pytest
import json
import pandas as pd
import numpy as np
from pathlib import Path
from code.models.evaluate import calculate_metrics, benjamini_hochberg_fdr
from code.models.entities import IsothermParameter
import yaml

# Path to the schema definition
SCHEMA_PATH = Path("contracts/model_output.schema.yaml")

@pytest.fixture
def sample_predictions():
    """Create sample predictions and true values from a realistic distribution."""
    # Simulating Henry constant predictions (cm3(STP)/g)
    np.random.seed(42)
    true_values = np.random.uniform(10.0, 100.0, size=100)
    # Add some noise to create realistic predictions
    noise = np.random.normal(0, 5.0, size=100)
    predicted_values = true_values + noise
    return {
        'true_values': true_values.tolist(),
        'predicted_values': predicted_values.tolist()
    }

@pytest.fixture
def sample_feature_importance():
    """Create sample feature importance data matching expected descriptors."""
    return {
        'polarizability': 0.35,
        'kinetic_diameter': 0.25,
        'molecular_weight': 0.15,
        'polar_surface_area': 0.10,
        'h_bond_donors': 0.08,
        'h_bond_acceptors': 0.05,
        'v_vdW': 0.02
    }

@pytest.fixture
def sample_p_values():
    """Sample p-values for FDR correction testing."""
    return [0.001, 0.01, 0.02, 0.04, 0.05, 0.10, 0.20, 0.50]

def load_model_output_schema():
    """Load the model output schema definition."""
    if not SCHEMA_PATH.exists():
        pytest.skip(f"Schema file not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

def test_calculate_metrics_structure(sample_predictions):
    """Test that metrics calculation returns expected structure."""
    metrics = calculate_metrics(
        sample_predictions['true_values'],
        sample_predictions['predicted_values']
    )
    
    assert isinstance(metrics, dict), "Metrics should be a dictionary"
    assert 'r2' in metrics, "Missing r2 metric"
    assert 'rmse' in metrics, "Missing rmse metric"
    assert 'mae' in metrics, "Missing mae metric"
    
    # Check that metrics are numeric
    assert isinstance(metrics['r2'], (int, float)), "r2 should be numeric"
    assert isinstance(metrics['rmse'], (int, float)), "rmse should be numeric"
    assert isinstance(metrics['mae'], (int, float)), "mae should be numeric"

def test_calculate_metrics_reasonable_values(sample_predictions):
    """Test that calculated metrics are within reasonable ranges."""
    metrics = calculate_metrics(
        sample_predictions['true_values'],
        sample_predictions['predicted_values']
    )
    
    # R2 should be between 0 and 1 for good predictions (or negative for very bad)
    assert metrics['r2'] <= 1.0, f"R2 should be <= 1, got {metrics['r2']}"
    
    # RMSE and MAE should be non-negative
    assert metrics['rmse'] >= 0, "RMSE should be non-negative"
    assert metrics['mae'] >= 0, "MAE should be non-negative"

def test_benjamini_hochberg_fdr_structure(sample_p_values):
    """Test that FDR correction returns expected structure."""
    result = benjamini_hochberg_fdr(sample_p_values, alpha=0.05)
    
    assert isinstance(result, dict), "Result should be a dictionary"
    assert 'corrected_p_values' in result, "Missing corrected_p_values"
    assert 'significant' in result, "Missing significant mask"
    assert 'fdr_threshold' in result, "Missing fdr_threshold"
    
    # Check lengths match
    assert len(result['corrected_p_values']) == len(sample_p_values), \
        "Corrected p-values length should match input"
    assert len(result['significant']) == len(sample_p_values), \
        "Significant mask length should match input"
    
    # Check types
    assert all(isinstance(p, float) for p in result['corrected_p_values']), \
        "All corrected p-values should be floats"
    assert all(isinstance(s, bool) for s in result['significant']), \
        "All significance flags should be booleans"

def test_benjamini_hochberg_fdr_monotonicity(sample_p_values):
    """Test that FDR correction maintains monotonicity."""
    # Sort p-values for the test
    sorted_p_values = sorted(sample_p_values)
    result = benjamini_hochberg_fdr(sorted_p_values, alpha=0.05)
    corrected = result['corrected_p_values']
    
    # Corrected p-values should be monotonically increasing
    for i in range(1, len(corrected)):
        assert corrected[i] >= corrected[i-1], \
            f"Corrected p-values should be monotonically increasing. Got {corrected[i]} < {corrected[i-1]}"

def test_model_output_json_serialization(sample_predictions):
    """Test that model output can be serialized to JSON."""
    metrics = calculate_metrics(
        sample_predictions['true_values'],
        sample_predictions['predicted_values']
    )
    
    # Should be able to serialize to JSON
    json_str = json.dumps(metrics)
    assert json_str is not None, "JSON serialization should succeed"
    
    # Should be able to deserialize back
    loaded = json.loads(json_str)
    assert loaded == metrics, "Deserialized JSON should match original"

def test_schema_compliance_metrics(sample_predictions):
    """Test that metrics output complies with the schema definition."""
    schema = load_model_output_schema()
    metrics = calculate_metrics(
        sample_predictions['true_values'],
        sample_predictions['predicted_values']
    )
    
    # Validate required fields based on schema
    required_fields = schema.get('required', [])
    for field in required_fields:
        assert field in metrics, f"Schema requires field '{field}'"
    
    # Validate types based on schema
    properties = schema.get('properties', {})
    for key, value in metrics.items():
        if key in properties:
            expected_type = properties[key].get('type')
            if expected_type == 'number':
                assert isinstance(value, (int, float)), \
                    f"Field '{key}' should be a number, got {type(value)}"

def test_schema_compliance_fdr_result(sample_p_values):
    """Test that FDR result complies with the schema definition."""
    schema = load_model_output_schema()
    fdr_schema = schema.get('properties', {}).get('fdr_correction', {})
    result = benjamini_hochberg_fdr(sample_p_values, alpha=0.05)
    
    # Check required fields in FDR result
    fdr_required = fdr_schema.get('required', [])
    for field in fdr_required:
        assert field in result, f"FDR schema requires field '{field}'"
    
    # Check types
    fdr_properties = fdr_schema.get('properties', {})
    if 'corrected_p_values' in fdr_properties:
        assert isinstance(result['corrected_p_values'], list), \
            "corrected_p_values should be a list"
        assert all(isinstance(p, (int, float)) for p in result['corrected_p_values']), \
            "All corrected p-values should be numbers"
    
    if 'significant' in fdr_properties:
        assert isinstance(result['significant'], list), \
            "significant should be a list"
        assert all(isinstance(s, bool) for s in result['significant']), \
            "All significance flags should be booleans"

def test_empty_input_handling():
    """Test that functions handle empty inputs gracefully or fail loudly."""
    # calculate_metrics should raise an error or return NaN for empty lists
    with pytest.raises((ValueError, IndexError)):
        calculate_metrics([], [])
    
    # FDR correction on empty list
    result = benjamini_hochberg_fdr([], alpha=0.05)
    assert result['corrected_p_values'] == []
    assert result['significant'] == []

def test_single_value_handling():
    """Test behavior with single data point."""
    single_true = [10.0]
    single_pred = [10.0]
    
    metrics = calculate_metrics(single_true, single_pred)
    # With a single perfect prediction, R2 is undefined (0/0), so it might be NaN or 1.0
    # The important thing is it doesn't crash
    assert isinstance(metrics['r2'], (int, float, type(np.nan)))
    assert metrics['rmse'] == 0.0
    assert metrics['mae'] == 0.0