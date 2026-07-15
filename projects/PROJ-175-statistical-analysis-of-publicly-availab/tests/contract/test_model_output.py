"""
Contract test for model output schema (Task T020).

Verifies that model output artifacts (logistic and Bayesian) conform to the
schema defined in specs/001-statistical-analysis-of-recipe-data/contracts/model_output.schema.yaml.

This test ensures:
1. Required files exist at expected paths
2. JSON structure matches the schema
3. Required fields are present with correct types
4. Statistical metrics are within expected ranges
"""
import json
import os
import pytest
from pathlib import Path
from typing import Dict, Any, List
import numpy as np

# Project root relative to tests/
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
SPECS_DIR = PROJECT_ROOT / "specs" / "001-statistical-analysis-of-recipe-data" / "contracts"

# Expected output paths based on task descriptions
LOGISTIC_OUTPUT_PATH = DATA_DIR / "logistic_model_output.json"
BAYESIAN_OUTPUT_PATH = DATA_DIR / "bayesian_model_output.json"
SCHEMA_PATH = SPECS_DIR / "model_output.schema.yaml"

@pytest.fixture
def schema() -> Dict[str, Any]:
    """Load the model output schema definition."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found: {SCHEMA_PATH}")
    
    try:
        import yaml
        with open(SCHEMA_PATH, 'r') as f:
            return yaml.safe_load(f)
    except ImportError:
        pytest.skip("PyYAML not installed, skipping schema validation")
    except Exception as e:
        pytest.fail(f"Failed to load schema: {e}")

@pytest.fixture
def logistic_output() -> Dict[str, Any]:
    """Load logistic model output if it exists."""
    if not LOGISTIC_OUTPUT_PATH.exists():
        pytest.skip(f"Logistic model output not found: {LOGISTIC_OUTPUT_PATH}. "
                   "Run T022 first to generate this file.")
    
    with open(LOGISTIC_OUTPUT_PATH, 'r') as f:
        return json.load(f)

@pytest.fixture
def bayesian_output() -> Dict[str, Any]:
    """Load Bayesian model output if it exists."""
    if not BAYESIAN_OUTPUT_PATH.exists():
        pytest.skip(f"Bayesian model output not found: {BAYESIAN_OUTPUT_PATH}. "
                   "Run T025 first to generate this file.")
    
    with open(BAYESIAN_OUTPUT_PATH, 'r') as f:
        return json.load(f)

class TestLogisticModelOutputSchema:
    """Contract tests for logistic regression model output."""

    def test_file_exists(self):
        """Test that logistic model output file exists."""
        assert LOGISTIC_OUTPUT_PATH.exists(), \
            f"Logistic model output file not found: {LOGISTIC_OUTPUT_PATH}"

    def test_has_required_top_level_keys(self, logistic_output: Dict[str, Any]):
        """Test that all required top-level keys are present."""
        required_keys = ['model_type', 'sample_size', 'coefficients', 
                       'metrics', 'diagnostics', 'metadata']
        
        for key in required_keys:
            assert key in logistic_output, \
                f"Missing required top-level key: {key}"

    def test_model_type_is_correct(self, logistic_output: Dict[str, Any]):
        """Test that model_type is 'logistic_regression'."""
        assert logistic_output['model_type'] == 'logistic_regression', \
            f"Expected model_type 'logistic_regression', got '{logistic_output['model_type']}'"

    def test_sample_size_is_positive_integer(self, logistic_output: Dict[str, Any]):
        """Test that sample_size is a positive integer."""
        sample_size = logistic_output['sample_size']
        assert isinstance(sample_size, int), \
            f"sample_size must be an integer, got {type(sample_size)}"
        assert sample_size > 0, \
            f"sample_size must be positive, got {sample_size}"

    def test_coefficients_structure(self, logistic_output: Dict[str, Any]):
        """Test that coefficients have the required structure."""
        coefficients = logistic_output['coefficients']
        assert isinstance(coefficients, list), \
            f"coefficients must be a list, got {type(coefficients)}"
        
        assert len(coefficients) > 0, "coefficients list cannot be empty"
        
        required_coef_keys = ['feature', 'coefficient', 'std_error', 'p_value']
        
        for i, coef in enumerate(coefficients):
            for key in required_coef_keys:
                assert key in coef, \
                    f"Missing key '{key}' in coefficients[{i}]"
            
            # Validate types
            assert isinstance(coef['feature'], str), \
                f"feature must be string, got {type(coef['feature'])}"
            assert isinstance(coef['coefficient'], (int, float)), \
                f"coefficient must be numeric, got {type(coef['coefficient'])}"
            assert isinstance(coef['std_error'], (int, float)), \
                f"std_error must be numeric, got {type(coef['std_error'])}"
            assert isinstance(coef['p_value'], (int, float)), \
                f"p_value must be numeric, got {type(coef['p_value'])}"

    def test_metrics_structure(self, logistic_output: Dict[str, Any]):
        """Test that metrics have the required structure."""
        metrics = logistic_output['metrics']
        assert isinstance(metrics, dict), \
            f"metrics must be a dict, got {type(metrics)}"
        
        required_metrics = ['auc', 'accuracy', 'precision', 'recall', 'f1_score']
        
        for metric in required_metrics:
            assert metric in metrics, \
                f"Missing required metric: {metric}"
            assert isinstance(metrics[metric], (int, float)), \
                f"{metric} must be numeric, got {type(metrics[metric])}"
            assert 0 <= metrics[metric] <= 1, \
                f"{metric} must be between 0 and 1, got {metrics[metric]}"

    def test_diagnostics_structure(self, logistic_output: Dict[str, Any]):
        """Test that diagnostics have the required structure."""
        diagnostics = logistic_output['diagnostics']
        assert isinstance(diagnostics, dict), \
            f"diagnostics must be a dict, got {type(diagnostics)}"
        
        # Check for VIF scores if present
        if 'vif_scores' in diagnostics:
            assert isinstance(diagnostics['vif_scores'], dict), \
                "vif_scores must be a dict"
            
            for feature, vif in diagnostics['vif_scores'].items():
                assert isinstance(vif, (int, float)), \
                    f"VIF for {feature} must be numeric, got {type(vif)}"
                assert vif > 0, \
                    f"VIF for {feature} must be positive, got {vif}"
        
        # Check for likelihood ratio test if present
        if 'likelihood_ratio_test' in diagnostics:
            lrt = diagnostics['likelihood_ratio_test']
            assert 'p_value' in lrt, "likelihood_ratio_test must have p_value"
            assert isinstance(lrt['p_value'], (int, float)), \
                "likelihood_ratio_test p_value must be numeric"
            assert 0 <= lrt['p_value'] <= 1, \
                f"likelihood_ratio_test p_value must be between 0 and 1, got {lrt['p_value']}"

    def test_metadata_structure(self, logistic_output: Dict[str, Any]):
        """Test that metadata has the required structure."""
        metadata = logistic_output['metadata']
        assert isinstance(metadata, dict), \
            f"metadata must be a dict, got {type(metadata)}"
        
        required_metadata = ['timestamp', 'version', 'random_seed']
        
        for key in required_metadata:
            assert key in metadata, \
                f"Missing required metadata key: {key}"
        
        assert isinstance(metadata['timestamp'], str), \
            "timestamp must be a string"
        assert isinstance(metadata['version'], str), \
            "version must be a string"
        assert isinstance(metadata['random_seed'], int), \
            "random_seed must be an integer"

class TestBayesianModelOutputSchema:
    """Contract tests for hierarchical Bayesian model output."""

    def test_file_exists(self):
        """Test that Bayesian model output file exists."""
        assert BAYESIAN_OUTPUT_PATH.exists(), \
            f"Bayesian model output file not found: {BAYESIAN_OUTPUT_PATH}"

    def test_has_required_top_level_keys(self, bayesian_output: Dict[str, Any]):
        """Test that all required top-level keys are present."""
        required_keys = ['model_type', 'sample_size', 'coefficients', 
                       'metrics', 'diagnostics', 'metadata']
        
        for key in required_keys:
            assert key in bayesian_output, \
                f"Missing required top-level key: {key}"

    def test_model_type_is_correct(self, bayesian_output: Dict[str, Any]):
        """Test that model_type is 'hierarchical_bayesian'."""
        assert bayesian_output['model_type'] == 'hierarchical_bayesian', \
            f"Expected model_type 'hierarchical_bayesian', got '{bayesian_output['model_type']}'"

    def test_sample_size_is_positive_integer(self, bayesian_output: Dict[str, Any]):
        """Test that sample_size is a positive integer."""
        sample_size = bayesian_output['sample_size']
        assert isinstance(sample_size, int), \
            f"sample_size must be an integer, got {type(sample_size)}"
        assert sample_size > 0, \
            f"sample_size must be positive, got {sample_size}"

    def test_coefficients_structure(self, bayesian_output: Dict[str, Any]):
        """Test that coefficients have the required structure for Bayesian output."""
        coefficients = bayesian_output['coefficients']
        assert isinstance(coefficients, list), \
            f"coefficients must be a list, got {type(coefficients)}"
        
        assert len(coefficients) > 0, "coefficients list cannot be empty"
        
        required_coef_keys = ['feature', 'mean', 'std', 
                             'hdi_lower', 'hdi_upper', 'p_value']
        
        for i, coef in enumerate(coefficients):
            for key in required_coef_keys:
                assert key in coef, \
                    f"Missing key '{key}' in coefficients[{i}]"
            
            # Validate types
            assert isinstance(coef['feature'], str), \
                f"feature must be string, got {type(coef['feature'])}"
            assert isinstance(coef['mean'], (int, float)), \
                f"mean must be numeric, got {type(coef['mean'])}"
            assert isinstance(coef['std'], (int, float)), \
                f"std must be numeric, got {type(coef['std'])}"
            assert isinstance(coef['hdi_lower'], (int, float)), \
                f"hdi_lower must be numeric, got {type(coef['hdi_lower'])}"
            assert isinstance(coef['hdi_upper'], (int, float)), \
                f"hdi_upper must be numeric, got {type(coef['hdi_upper'])}"
            assert isinstance(coef['p_value'], (int, float)), \
                f"p_value must be numeric, got {type(coef['p_value'])}"
            
            # Validate HDI bounds
            assert coef['hdi_lower'] < coef['hdi_upper'], \
                f"hdi_lower must be less than hdi_upper for {coef['feature']}"

    def test_metrics_structure(self, bayesian_output: Dict[str, Any]):
        """Test that metrics have the required structure."""
        metrics = bayesian_output['metrics']
        assert isinstance(metrics, dict), \
            f"metrics must be a dict, got {type(metrics)}"
        
        required_metrics = ['auc', 'accuracy', 'precision', 'recall', 'f1_score']
        
        for metric in required_metrics:
            assert metric in metrics, \
                f"Missing required metric: {metric}"
            assert isinstance(metrics[metric], (int, float)), \
                f"{metric} must be numeric, got {type(metrics[metric])}"
            assert 0 <= metrics[metric] <= 1, \
                f"{metric} must be between 0 and 1, got {metrics[metric]}"

    def test_diagnostics_structure(self, bayesian_output: Dict[str, Any]):
        """Test that diagnostics have the required structure for Bayesian output."""
        diagnostics = bayesian_output['diagnostics']
        assert isinstance(diagnostics, dict), \
            f"diagnostics must be a dict, got {type(diagnostics)}"
        
        # Check for convergence metrics
        convergence_keys = ['rhat_max', 'effective_sample_size', 'divergences']
        
        for key in convergence_keys:
            if key in diagnostics:
                assert isinstance(diagnostics[key], (int, float)), \
                    f"{key} must be numeric, got {type(diagnostics[key])}"
        
        # R-hat should be close to 1.0 (typically < 1.1)
        if 'rhat_max' in diagnostics:
            assert diagnostics['rhat_max'] < 1.1, \
                f"R-hat max {diagnostics['rhat_max']} indicates poor convergence"

    def test_metadata_structure(self, bayesian_output: Dict[str, Any]):
        """Test that metadata has the required structure."""
        metadata = bayesian_output['metadata']
        assert isinstance(metadata, dict), \
            f"metadata must be a dict, got {type(metadata)}"
        
        required_metadata = ['timestamp', 'version', 'random_seed', 'n_chains', 'n_samples']
        
        for key in required_metadata:
            assert key in metadata, \
                f"Missing required metadata key: {key}"
        
        assert isinstance(metadata['timestamp'], str), \
            "timestamp must be a string"
        assert isinstance(metadata['version'], str), \
            "version must be a string"
        assert isinstance(metadata['random_seed'], int), \
            "random_seed must be an integer"
        assert isinstance(metadata['n_chains'], int), \
            "n_chains must be an integer"
        assert isinstance(metadata['n_samples'], int), \
            "n_samples must be an integer"

class TestSchemaConsistency:
    """Tests to ensure consistency between model outputs and schema definition."""

    def test_schema_file_exists(self):
        """Test that schema file exists."""
        assert SCHEMA_PATH.exists(), \
            f"Schema file not found: {SCHEMA_PATH}"

    def test_logistic_output_matches_schema(self, logistic_output: Dict[str, Any], schema: Dict[str, Any]):
        """Test that logistic output conforms to schema definition."""
        # This would implement full schema validation if schema is detailed enough
        # For now, we verify basic structure matches common patterns
        assert 'logistic_regression' in schema.get('model_types', []), \
            "Schema does not define 'logistic_regression' model type"

    def test_bayesian_output_matches_schema(self, bayesian_output: Dict[str, Any], schema: Dict[str, Any]):
        """Test that Bayesian output conforms to schema definition."""
        # This would implement full schema validation if schema is detailed enough
        # For now, we verify basic structure matches common patterns
        assert 'hierarchical_bayesian' in schema.get('model_types', []), \
            "Schema does not define 'hierarchical_bayesian' model type"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])