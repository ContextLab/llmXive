"""
Contract tests for data schemas and results schemas.
Validates that data files and analysis outputs conform to defined contracts.
"""

import os
import sys
import yaml
import pandas as pd
import pytest
from pathlib import Path

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from config import get_config


class SchemaValidator:
    """Base class for schema validation tests."""

    def __init__(self, schema_path: str):
        self.schema_path = schema_path
        with open(schema_path, 'r') as f:
            self.schema = yaml.safe_load(f)

    def validate_schema(self, data: dict) -> bool:
        """Validate data against schema."""
        # Simple validation: check required fields exist
        if 'required_fields' in self.schema:
            for field in self.schema['required_fields']:
                if field not in data:
                    return False
        return True


class TestDatasetSchema:
    """Tests for dataset schema contracts."""

    @pytest.fixture
    def config(self):
        return get_config()

    def test_dataset_schema_contract(self, config):
        """Test that dataset schema contract is valid."""
        schema_path = config['schema_paths']['dataset']
        assert os.path.exists(schema_path), f"Dataset schema not found at {schema_path}"

        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)

        # Validate schema structure
        assert 'fields' in schema, "Schema must have 'fields' key"
        assert isinstance(schema['fields'], dict), "Schema fields must be a dictionary"

    def test_cleaned_data_conforms_to_schema(self, config):
        """Test that cleaned_data.csv conforms to dataset schema."""
        data_path = config['paths']['cleaned_data']
        schema_path = config['schema_paths']['dataset']

        assert os.path.exists(data_path), f"Cleaned data not found at {data_path}"
        assert os.path.exists(schema_path), f"Dataset schema not found at {schema_path}"

        # Load data
        df = pd.read_csv(data_path)

        # Load schema
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)

        # Check required fields
        required_fields = schema.get('required_fields', [])
        for field in required_fields:
            assert field in df.columns, f"Required field '{field}' missing from cleaned data"

    def test_engineered_data_conforms_to_schema(self, config):
        """Test that engineered_data.csv conforms to dataset schema with new features."""
        data_path = config['paths']['engineered_data']
        schema_path = config['schema_paths']['dataset']

        # Skip if engineered data doesn't exist yet
        if not os.path.exists(data_path):
            pytest.skip("Engineered data not yet generated")

        assert os.path.exists(data_path), f"Engineered data not found at {data_path}"
        assert os.path.exists(schema_path), f"Dataset schema not found at {schema_path}"

        # Load data
        df = pd.read_csv(data_path)

        # Load schema
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)

        # Check required fields including new engineered features
        required_fields = schema.get('required_fields', [])
        engineered_fields = ['engagement_score', 'adoption_binary']
        all_required = required_fields + engineered_fields

        for field in all_required:
            assert field in df.columns, f"Required field '{field}' missing from engineered data"


class TestResultsSchema:
    """Tests for results schema contracts (US3)."""

    @pytest.fixture
    def config(self):
        return get_config()

    def test_results_schema_contract(self, config):
        """Test that results schema contract is valid."""
        schema_path = config['schema_paths']['results']
        assert os.path.exists(schema_path), f"Results schema not found at {schema_path}"

        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)

        # Validate schema structure
        assert 'sections' in schema, "Results schema must have 'sections' key"
        expected_sections = ['regression_summary', 'mediation_analysis', 'model_diagnostics', 'validity_metrics']
        for section in expected_sections:
            assert section in schema['sections'], f"Results schema missing section: {section}"

    def test_regression_table_conforms_to_schema(self, config):
        """Test that regression results conform to results schema."""
        results_path = config['paths']['results_dir']
        schema_path = config['schema_paths']['results']

        # Skip if results don't exist yet
        if not os.path.exists(results_path):
            pytest.skip("Results directory not yet generated")

        regression_file = os.path.join(results_path, 'regression_results.yaml')
        if not os.path.exists(regression_file):
            pytest.skip("Regression results not yet generated")

        with open(regression_file, 'r') as f:
            results = yaml.safe_load(f)

        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)

        # Validate regression table structure
        assert 'coefficients' in results, "Regression results must have 'coefficients' key"
        assert 'standard_errors' in results, "Regression results must have 'standard_errors' key"
        assert 'p_values' in results, "Regression results must have 'p_values' key"
        assert 'odds_ratios' in results, "Regression results must have 'odds_ratios' key"

        # Check that coefficient names match
        coef_names = results['coefficients'].keys()
        se_names = results['standard_errors'].keys()
        p_names = results['p_values'].keys()
        or_names = results['odds_ratios'].keys()

        assert coef_names == se_names == p_names == or_names, \
            "Coefficient names must match across all result types"

    def test_mediation_results_conform_to_schema(self, config):
        """Test that mediation analysis results conform to results schema."""
        results_path = config['paths']['results_dir']
        schema_path = config['schema_paths']['results']

        # Skip if results don't exist yet
        if not os.path.exists(results_path):
            pytest.skip("Results directory not yet generated")

        mediation_file = os.path.join(results_path, 'mediation_results.yaml')
        if not os.path.exists(mediation_file):
            pytest.skip("Mediation results not yet generated")

        with open(mediation_file, 'r') as f:
            results = yaml.safe_load(f)

        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)

        # Validate mediation analysis structure
        required_keys = ['direct_effect', 'indirect_effect', 'total_effect', 'confidence_intervals']
        for key in required_keys:
            assert key in results, f"Mediation results must have '{key}' key"

        # Check confidence interval structure
        assert 'lower' in results['confidence_intervals'], "CI must have 'lower' bound"
        assert 'upper' in results['confidence_intervals'], "CI must have 'upper' bound"

    def test_auc_value_conforms_to_schema(self, config):
        """Test that AUC value is present and valid."""
        results_path = config['paths']['results_dir']
        schema_path = config['schema_paths']['results']

        # Skip if results don't exist yet
        if not os.path.exists(results_path):
            pytest.skip("Results directory not yet generated")

        model_diagnostics_file = os.path.join(results_path, 'model_diagnostics.yaml')
        if not os.path.exists(model_diagnostics_file):
            pytest.skip("Model diagnostics not yet generated")

        with open(model_diagnostics_file, 'r') as f:
            diagnostics = yaml.safe_load(f)

        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)

        # Validate AUC presence and range
        assert 'auc' in diagnostics, "Model diagnostics must have 'auc' key"
        auc_value = diagnostics['auc']
        assert 0.5 <= auc_value <= 1.0, f"AUC must be between 0.5 and 1.0, got {auc_value}"

    def test_vif_diagnostics_conform_to_schema(self, config):
        """Test that VIF diagnostics conform to results schema."""
        results_path = config['paths']['results_dir']
        schema_path = config['schema_paths']['results']

        # Skip if results don't exist yet
        if not os.path.exists(results_path):
            pytest.skip("Results directory not yet generated")

        model_diagnostics_file = os.path.join(results_path, 'model_diagnostics.yaml')
        if not os.path.exists(model_diagnostics_file):
            pytest.skip("Model diagnostics not yet generated")

        with open(model_diagnostics_file, 'r') as f:
            diagnostics = yaml.safe_load(f)

        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)

        # Validate VIF structure
        assert 'vif' in diagnostics, "Model diagnostics must have 'vif' key"
        vif_values = diagnostics['vif']

        # Check that VIF is a dictionary with numeric values
        assert isinstance(vif_values, dict), "VIF must be a dictionary"
        for var, value in vif_values.items():
            assert isinstance(value, (int, float)), f"VIF value for {var} must be numeric"
            assert value >= 1.0, f"VIF value for {var} must be >= 1.0, got {value}"

    def test_fdr_adjusted_pvalues_conform_to_schema(self, config):
        """Test that FDR-adjusted p-values conform to results schema."""
        results_path = config['paths']['results_dir']
        schema_path = config['schema_paths']['results']

        # Skip if results don't exist yet
        if not os.path.exists(results_path):
            pytest.skip("Results directory not yet generated")

        regression_file = os.path.join(results_path, 'regression_results.yaml')
        if not os.path.exists(regression_file):
            pytest.skip("Regression results not yet generated")

        with open(regression_file, 'r') as f:
            results = yaml.safe_load(f)

        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)

        # Validate FDR-adjusted p-values
        assert 'p_values_fdr' in results, "Regression results must have 'p_values_fdr' key"
        fdr_pvalues = results['p_values_fdr']

        # Check that FDR p-values are in valid range
        for var, pval in fdr_pvalues.items():
            assert 0 <= pval <= 1, f"FDR p-value for {var} must be between 0 and 1, got {pval}"

    def test_sensitivity_analysis_conforms_to_schema(self, config):
        """Test that sensitivity analysis results conform to results schema."""
        results_path = config['paths']['results_dir']
        schema_path = config['schema_paths']['results']

        # Skip if results don't exist yet
        if not os.path.exists(results_path):
            pytest.skip("Results directory not yet generated")

        mediation_file = os.path.join(results_path, 'mediation_results.yaml')
        if not os.path.exists(mediation_file):
            pytest.skip("Mediation results not yet generated")

        with open(mediation_file, 'r') as f:
            results = yaml.safe_load(f)

        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)

        # Validate sensitivity analysis structure
        assert 'sensitivity_analysis' in results, "Mediation results must have 'sensitivity_analysis' key"
        sensitivity = results['sensitivity_analysis']

        # Check for E-values
        assert 'e_values' in sensitivity, "Sensitivity analysis must have 'e_values' key"
        e_values = sensitivity['e_values']

        # Check for Rosenbaum bounds
        assert 'rosenbaum_bounds' in sensitivity, "Sensitivity analysis must have 'rosenbaum_bounds' key"
        rosenbaum = sensitivity['rosenbaum_bounds']

        # Validate E-values structure
        assert 'point_estimate' in e_values, "E-values must have 'point_estimate'"
        assert 'ci_lower' in e_values, "E-values must have 'ci_lower'"
        assert 'ci_upper' in e_values, "E-values must have 'ci_upper'"

        # Validate Rosenbaum bounds structure
        assert 'gamma_range' in rosenbaum, "Rosenbaum bounds must have 'gamma_range'"
        assert 'significant_gamma' in rosenbaum, "Rosenbaum bounds must have 'significant_gamma'"

    def test_full_results_workflow(self, config):
        """Test that all required results files exist and conform to schema."""
        results_path = config['paths']['results_dir']
        schema_path = config['schema_paths']['results']

        # Skip if results don't exist yet
        if not os.path.exists(results_path):
            pytest.skip("Results directory not yet generated")

        # Check all required files exist
        required_files = [
            'regression_results.yaml',
            'mediation_results.yaml',
            'model_diagnostics.yaml'
        ]

        for filename in required_files:
            filepath = os.path.join(results_path, filename)
            assert os.path.exists(filepath), f"Required results file missing: {filename}"

        # Validate each file against schema
        self.test_regression_table_conforms_to_schema(config)
        self.test_mediation_results_conform_to_schema(config)
        self.test_auc_value_conforms_to_schema(config)
        self.test_vif_diagnostics_conform_to_schema(config)
        self.test_fdr_adjusted_pvalues_conform_to_schema(config)
        self.test_sensitivity_analysis_conforms_to_schema(config)