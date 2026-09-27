"""
Unit tests for schema validation logic.
"""
import pytest
import pandas as pd
import yaml
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from validate_schemas import (
    load_schema, 
    validate_column_types, 
    validate_rsa_metrics, 
    validate_merged_dataset, 
    validate_model_results,
    validate_vif_compliance,
    validate_proxy_detection
)

@pytest.fixture
def sample_rsa_metrics():
    return pd.DataFrame({
        'species_id': ['A', 'B', 'C'],
        'depth': [10.5, 15.2, 8.0],
        'branching_density': [2.1, 3.5, 1.8],
        'surface_area': [100.0, 150.0, 80.0]
    })

@pytest.fixture
def sample_merged_data():
    return pd.DataFrame({
        'species_id': ['A', 'B', 'C'],
        'depth': [10.5, 15.2, 8.0],
        'branching_density': [2.1, 3.5, 1.8],
        'surface_area': [100.0, 150.0, 80.0],
        'stomatal_conductance': [0.1, 0.2, 0.15],
        'photosynthesis': [5.0, 6.0, 4.5],
        'pca_depth': [0.1, 0.2, 0.15],
        'pca_branching': [0.3, 0.4, 0.35],
        'pca_surface': [0.2, 0.3, 0.25],
        'pvr_lambda': [0.5, 0.6, 0.55],
        'pvr_sigma': [1.0, 1.1, 1.05]
    })

@pytest.fixture
def sample_model_results():
    return pd.DataFrame({
        'model_type': ['OLS', 'Ridge', 'Lasso'],
        'predictor': ['depth', 'depth', 'depth'],
        'coefficient': [0.5, 0.4, 0.45],
        'p_value': [0.01, 0.02, 0.015],
        'r2': [0.6, 0.65, 0.62],
        'adj_p_value': [0.03, 0.04, 0.035],
        'vif': [1.2, 1.3, 1.25]
    })

@pytest.fixture
def contracts_dir():
    return Path(__file__).parent.parent.parent / 'contracts'

def test_load_schema(contracts_dir):
    schema_path = contracts_dir / 'rsametrics.schema.yaml'
    schema = load_schema(schema_path)
    assert schema is not None
    assert '$schema' in schema
    assert 'properties' in schema

def test_validate_rsa_metrics_valid(sample_rsa_metrics, contracts_dir):
    schema_path = contracts_dir / 'rsametrics.schema.yaml'
    passed, errors = validate_rsa_metrics(sample_rsa_metrics, schema_path)
    assert passed is True
    assert len(errors) == 0

def test_validate_rsa_metrics_invalid_depth(sample_rsa_metrics, contracts_dir):
    sample_rsa_metrics.loc[0, 'depth'] = -5.0
    schema_path = contracts_dir / 'rsametrics.schema.yaml'
    passed, errors = validate_rsa_metrics(sample_rsa_metrics, schema_path)
    assert passed is False
    assert any("depth must be > 0" in e for e in errors)

def test_validate_merged_data_valid(sample_merged_data, contracts_dir):
    schema_path = contracts_dir / 'merged_data.schema.yaml'
    passed, errors = validate_merged_dataset(sample_merged_data, schema_path)
    assert passed is True
    assert len(errors) == 0

def test_validate_model_results_valid(sample_model_results, contracts_dir):
    schema_path = contracts_dir / 'model_results.schema.yaml'
    passed, errors = validate_model_results(sample_model_results, schema_path)
    assert passed is True
    assert len(errors) == 0

def test_validate_model_results_invalid_pvalue(sample_model_results, contracts_dir):
    sample_model_results.loc[0, 'p_value'] = 1.5
    schema_path = contracts_dir / 'model_results.schema.yaml'
    passed, errors = validate_model_results(sample_model_results, schema_path)
    assert passed is False
    assert any("p_value must be between 0 and 1" in e for e in errors)

def test_validate_vif_compliance_valid(tmp_path):
    data = {
        'vif_status': 'PASS',
        'suppression_applied': False
    }
    yaml_path = tmp_path / 'test.yaml'
    with open(yaml_path, 'w') as f:
        yaml.dump(data, f)
    
    passed, errors = validate_vif_compliance(yaml_path)
    assert passed is True
    assert len(errors) == 0

def test_validate_vif_compliance_invalid(tmp_path):
    data = {
        'vif_status': 'PASS'
        # missing suppression_applied
    }
    yaml_path = tmp_path / 'test.yaml'
    with open(yaml_path, 'w') as f:
        yaml.dump(data, f)
    
    passed, errors = validate_vif_compliance(yaml_path)
    assert passed is False
    assert any("Missing required field: suppression_applied" in e for e in errors)

def test_validate_proxy_detection_valid(tmp_path):
    data = {
        'has_proxy': True
    }
    yaml_path = tmp_path / 'test.yaml'
    with open(yaml_path, 'w') as f:
        yaml.dump(data, f)
    
    passed, errors = validate_proxy_detection(yaml_path)
    assert passed is True
    assert len(errors) == 0

def test_validate_proxy_detection_invalid(tmp_path):
    data = {}
    yaml_path = tmp_path / 'test.yaml'
    with open(yaml_path, 'w') as f:
        yaml.dump(data, f)
    
    passed, errors = validate_proxy_detection(yaml_path)
    assert passed is False
    assert any("Missing required field: has_proxy" in e for e in errors)
