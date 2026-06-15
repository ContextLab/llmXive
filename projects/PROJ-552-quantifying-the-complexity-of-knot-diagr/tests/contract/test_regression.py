"""
Contract test for regression model output (T031).

This test validates that regression model output conforms to the expected
schema defined in specs/001-knot-complexity-analysis/contracts/regression-model.schema.yaml.

Per Constitution Principle VII (census data exception), p-values are NOT reported
for census data and are marked as 'not applicable for census data' in all output artifacts.
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field, asdict
import pytest


@dataclass
class RegressionCoefficient:
    """Contract for a single regression coefficient."""
    name: str
    value: float
    standard_error: Optional[float] = None

@dataclass
class RegressionMetrics:
    """Contract for regression model goodness-of-fit metrics."""
    r_squared: float
    aic: Optional[float] = None
    bic: Optional[float] = None
    mae: Optional[float] = None
    mse: Optional[float] = None
    rmse: Optional[float] = None

@dataclass
class CorrelationMetrics:
    """Contract for correlation analysis metrics."""
    pearson_r: Optional[float] = None
    spearman_rho: Optional[float] = None
    pearson_pvalue: Optional[str] = None  # String 'not applicable for census data' per FR-006
    spearman_pvalue: Optional[str] = None  # String 'not applicable for census data' per FR-006
    effect_size_cohen_d: Optional[float] = None
    effect_size_r: Optional[float] = None

@dataclass
class RegressionModelOutput:
    """
    Contract for complete regression model output.

    This defines the expected structure for regression analysis results
    as specified in specs/001-knot-complexity-analysis/contracts/regression-model.schema.yaml.
    """
    model_type: str  # 'linear', 'polynomial', 'logarithmic'
    model_name: str
    dependent_variable: str  # e.g., 'hyperbolic_volume'
    independent_variables: List[str]  # e.g., ['crossing_number', 'braid_index']
    coefficients: List[RegressionCoefficient]
    metrics: RegressionMetrics
    correlation_metrics: Optional[CorrelationMetrics] = None
    vif_values: Optional[Dict[str, float]] = None  # Variance Inflation Factor for multicollinearity
    sample_size: int
    residuals_analysis: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RegressionGroupComparison:
    """Contract for alternating vs non-alternating group comparison."""
    group_name: str
    mean_crossing_number: float
    mean_braid_index: float
    mean_hyperbolic_volume: float
    std_crossing_number: float
    std_braid_index: float
    std_hyperbolic_volume: float
    sample_size: int

@dataclass
class RegressionAnalysisResult:
    """
    Contract for complete regression analysis result.

    This is the top-level output structure that aggregates all regression
    model outputs and comparisons.
    """
    models: List[RegressionModelOutput]
    group_comparisons: Optional[List[RegressionGroupComparison]] = None
    multicollinearity_assessment: Optional[Dict[str, Any]] = None
    census_data_note: str = "p-values not reported for census data per FR-006 and Constitution Principle VII"
    timestamp: Optional[str] = None

class RegressionContractValidator:
    """
    Validator for regression model output contracts.

    Validates that regression output conforms to the expected schema.
    """

    REQUIRED_MODEL_FIELDS = [
        'model_type', 'model_name', 'dependent_variable',
        'independent_variables', 'coefficients', 'metrics', 'sample_size'
    ]

    REQUIRED_METRICS_FIELDS = ['r_squared']

    VALID_MODEL_TYPES = {'linear', 'polynomial', 'logarithmic'}

    def __init__(self, schema_path: Optional[Path] = None):
        """
        Initialize the validator.

        Args:
            schema_path: Optional path to regression-model.schema.yaml for reference
        """
        self.schema_path = schema_path or Path('specs/001-knot-complexity-analysis/contracts/regression-model.schema.yaml')

    def validate_model_type(self, model_type: str) -> bool:
        """Validate that model_type is one of the allowed values."""
        return model_type in self.VALID_MODEL_TYPES

    def validate_coefficient(self, coeff: Dict[str, Any]) -> bool:
        """Validate a single coefficient entry."""
        if 'name' not in coeff or not isinstance(coeff['name'], str):
            return False
        if 'value' not in coeff or not isinstance(coeff['value'], (int, float)):
            return False
        if 'standard_error' in coeff and coeff['standard_error'] is not None:
            if not isinstance(coeff['standard_error'], (int, float)):
                return False
        return True

    def validate_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Validate regression metrics structure."""
        # r_squared is required and must be a number
        if 'r_squared' not in metrics:
            return False
        if not isinstance(metrics['r_squared'], (int, float)):
            return False
        # R² must be in valid range (can be negative for poor fits, but typically ≤1)
        if not (-float('inf') < metrics['r_squared'] < float('inf')):
            return False
        # Optional metrics if present must be numeric
        optional_metrics = ['aic', 'bic', 'mae', 'mse', 'rmse']
        for field_name in optional_metrics:
            if field_name in metrics and metrics[field_name] is not None:
                if not isinstance(metrics[field_name], (int, float)):
                    return False
        return True

    def validate_correlation_metrics(self, corr: Dict[str, Any]) -> bool:
        """Validate correlation metrics structure, including census data handling."""
        # If p-values are present, they must be the census data note string
        if 'pearson_pvalue' in corr and corr['pearson_pvalue'] is not None:
            if not isinstance(corr['pearson_pvalue'], str):
                return False
            if corr['pearson_pvalue'] != 'not applicable for census data':
                return False
        if 'spearman_pvalue' in corr and corr['spearman_pvalue'] is not None:
            if not isinstance(corr['spearman_pvalue'], str):
                return False
            if corr['spearman_pvalue'] != 'not applicable for census data':
                return False
        # Correlation coefficients if present must be numeric
        for field_name in ['pearson_r', 'spearman_rho', 'effect_size_r']:
            if field_name in corr and corr[field_name] is not None:
                if not isinstance(corr[field_name], (int, float)):
                    return False
        return True

    def validate_model_output(self, model_output: Dict[str, Any]) -> tuple:
        """
        Validate a single model output against the contract.

        Returns:
            tuple: (is_valid: bool, errors: List[str])
        """
        errors = []

        # Check required fields
        for field_name in self.REQUIRED_MODEL_FIELDS:
            if field_name not in model_output:
                errors.append(f"Missing required field: {field_name}")

        # Validate model_type
        if 'model_type' in model_output:
            if not self.validate_model_type(model_output['model_type']):
                errors.append(f"Invalid model_type: {model_output['model_type']}")

        # Validate independent_variables is a list
        if 'independent_variables' in model_output:
            if not isinstance(model_output['independent_variables'], list):
                errors.append("independent_variables must be a list")

        # Validate coefficients
        if 'coefficients' in model_output:
            if not isinstance(model_output['coefficients'], list):
                errors.append("coefficients must be a list")
            else:
                for i, coeff in enumerate(model_output['coefficients']):
                    if not self.validate_coefficient(coeff):
                        errors.append(f"Invalid coefficient at index {i}")

        # Validate metrics
        if 'metrics' in model_output:
            if not self.validate_metrics(model_output['metrics']):
                errors.append("Invalid metrics structure")

        # Validate correlation metrics if present
        if 'correlation_metrics' in model_output and model_output['correlation_metrics'] is not None:
            if not self.validate_correlation_metrics(model_output['correlation_metrics']):
                errors.append("Invalid correlation_metrics structure")

        # Validate sample_size is positive integer
        if 'sample_size' in model_output:
            if not isinstance(model_output['sample_size'], int) or model_output['sample_size'] <= 0:
                errors.append("sample_size must be a positive integer")

        return len(errors) == 0, errors

    def validate_analysis_result(self, result: Dict[str, Any]) -> tuple:
        """
        Validate complete regression analysis result.

        Returns:
            tuple: (is_valid: bool, errors: List[str])
        """
        errors = []

        # Check required top-level fields
        if 'models' not in result:
            errors.append("Missing required field: models")
        elif not isinstance(result['models'], list):
            errors.append("models must be a list")
        else:
            for i, model in enumerate(result['models']):
                is_valid, model_errors = self.validate_model_output(model)
                if not is_valid:
                    errors.extend([f"Model {i}: {err}" for err in model_errors])

        # Validate census_data_note if present
        if 'census_data_note' in result:
            expected_note = "p-values not reported for census data per FR-006 and Constitution Principle VII"
            if result['census_data_note'] != expected_note:
                errors.append(f"census_data_note does not match expected value: {expected_note}")

        return len(errors) == 0, errors


# Test fixtures and test functions
@pytest.fixture
def validator() -> RegressionContractValidator:
    """Create a regression contract validator instance."""
    return RegressionContractValidator()

@pytest.fixture
def valid_model_output() -> Dict[str, Any]:
    """Create a valid model output for testing."""
    return {
        'model_type': 'linear',
        'model_name': 'hyperbolic_volume ~ crossing_number + braid_index',
        'dependent_variable': 'hyperbolic_volume',
        'independent_variables': ['crossing_number', 'braid_index'],
        'coefficients': [
            {'name': 'intercept', 'value': 0.5, 'standard_error': 0.1},
            {'name': 'crossing_number', 'value': 0.3, 'standard_error': 0.05},
            {'name': 'braid_index', 'value': 0.2, 'standard_error': 0.08}
        ],
        'metrics': {
            'r_squared': 0.85,
            'aic': 120.5,
            'bic': 135.2,
            'mae': 0.45,
            'mse': 0.32,
            'rmse': 0.57
        },
        'correlation_metrics': {
            'pearson_r': 0.92,
            'spearman_rho': 0.89,
            'pearson_pvalue': 'not applicable for census data',
            'spearman_pvalue': 'not applicable for census data',
            'effect_size_r': 0.92
        },
        'vif_values': {'crossing_number': 2.1, 'braid_index': 1.8},
        'sample_size': 297,
        'metadata': {'timestamp': '2024-01-15T10:30:00Z'}
    }

@pytest.fixture
def valid_analysis_result(valid_model_output: Dict[str, Any]) -> Dict[str, Any]:
    """Create a valid analysis result for testing."""
    return {
        'models': [valid_model_output],
        'census_data_note': "p-values not reported for census data per FR-006 and Constitution Principle VII",
        'timestamp': '2024-01-15T10:30:00Z'
    }

class TestRegressionContractValidator:
    """Test suite for regression contract validation."""

    def test_validate_model_type_linear(self, validator: RegressionContractValidator):
        """Test that 'linear' is a valid model type."""
        assert validator.validate_model_type('linear') is True

    def test_validate_model_type_polynomial(self, validator: RegressionContractValidator):
        """Test that 'polynomial' is a valid model type."""
        assert validator.validate_model_type('polynomial') is True

    def test_validate_model_type_logarithmic(self, validator: RegressionContractValidator):
        """Test that 'logarithmic' is a valid model type."""
        assert validator.validate_model_type('logarithmic') is True

    def test_validate_model_type_invalid(self, validator: RegressionContractValidator):
        """Test that invalid model types are rejected."""
        assert validator.validate_model_type('invalid_type') is False

    def test_validate_coefficient_valid(self, validator: RegressionContractValidator):
        """Test validation of a valid coefficient."""
        coeff = {'name': 'crossing_number', 'value': 0.5, 'standard_error': 0.1}
        assert validator.validate_coefficient(coeff) is True

    def test_validate_coefficient_missing_name(self, validator: RegressionContractValidator):
        """Test validation of coefficient missing name field."""
        coeff = {'value': 0.5, 'standard_error': 0.1}
        assert validator.validate_coefficient(coeff) is False

    def test_validate_coefficient_missing_value(self, validator: RegressionContractValidator):
        """Test validation of coefficient missing value field."""
        coeff = {'name': 'crossing_number', 'standard_error': 0.1}
        assert validator.validate_coefficient(coeff) is False

    def test_validate_metrics_valid(self, validator: RegressionContractValidator):
        """Test validation of valid metrics."""
        metrics = {'r_squared': 0.85, 'aic': 120.5, 'bic': 135.2}
        assert validator.validate_metrics(metrics) is True

    def test_validate_metrics_missing_r_squared(self, validator: RegressionContractValidator):
        """Test validation of metrics missing r_squared."""
        metrics = {'aic': 120.5, 'bic': 135.2}
        assert validator.validate_metrics(metrics) is False

    def test_validate_metrics_r_squared_invalid_type(self, validator: RegressionContractValidator):
        """Test validation of metrics with invalid r_squared type."""
        metrics = {'r_squared': 'not a number'}
        assert validator.validate_metrics(metrics) is False

    def test_validate_correlation_metrics_valid(self, validator: RegressionContractValidator):
        """Test validation of valid correlation metrics."""
        corr = {
            'pearson_r': 0.92,
            'spearman_rho': 0.89,
            'pearson_pvalue': 'not applicable for census data',
            'spearman_pvalue': 'not applicable for census data'
        }
        assert validator.validate_correlation_metrics(corr) is True

    def test_validate_correlation_metrics_invalid_pvalue_type(self, validator: RegressionContractValidator):
        """Test validation of correlation metrics with numeric p-value (should fail for census data)."""
        corr = {
            'pearson_r': 0.92,
            'pearson_pvalue': 0.001  # Numeric p-value not allowed for census data
        }
        assert validator.validate_correlation_metrics(corr) is False

    def test_validate_correlation_metrics_invalid_pvalue_string(self, validator: RegressionContractValidator):
        """Test validation of correlation metrics with wrong p-value string."""
        corr = {
            'pearson_r': 0.92,
            'pearson_pvalue': 'p=0.001'  # Wrong format
        }
        assert validator.validate_correlation_metrics(corr) is False

    def test_validate_model_output_valid(self, validator: RegressionContractValidator, valid_model_output: Dict[str, Any]):
        """Test validation of a complete valid model output."""
        is_valid, errors = validator.validate_model_output(valid_model_output)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_model_output_missing_required_field(self, validator: RegressionContractValidator):
        """Test validation of model output missing required field."""
        model_output = {
            'model_type': 'linear',
            'model_name': 'test',
            'dependent_variable': 'y',
            'independent_variables': ['x'],
            'coefficients': [],
            'metrics': {'r_squared': 0.5}
            # Missing sample_size
        }
        is_valid, errors = validator.validate_model_output(model_output)
        assert is_valid is False
        assert any('sample_size' in err for err in errors)

    def test_validate_model_output_invalid_model_type(self, validator: RegressionContractValidator):
        """Test validation of model output with invalid model type."""
        model_output = {
            'model_type': 'invalid',
            'model_name': 'test',
            'dependent_variable': 'y',
            'independent_variables': ['x'],
            'coefficients': [],
            'metrics': {'r_squared': 0.5},
            'sample_size': 100
        }
        is_valid, errors = validator.validate_model_output(model_output)
        assert is_valid is False
        assert any('model_type' in err for err in errors)

    def test_validate_model_output_independent_variables_not_list(self, validator: RegressionContractValidator):
        """Test validation of model output with non-list independent_variables."""
        model_output = {
            'model_type': 'linear',
            'model_name': 'test',
            'dependent_variable': 'y',
            'independent_variables': 'x',  # Should be a list
            'coefficients': [],
            'metrics': {'r_squared': 0.5},
            'sample_size': 100
        }
        is_valid, errors = validator.validate_model_output(model_output)
        assert is_valid is False
        assert any('independent_variables' in err for err in errors)

    def test_validate_model_output_negative_sample_size(self, validator: RegressionContractValidator):
        """Test validation of model output with negative sample size."""
        model_output = {
            'model_type': 'linear',
            'model_name': 'test',
            'dependent_variable': 'y',
            'independent_variables': ['x'],
            'coefficients': [],
            'metrics': {'r_squared': 0.5},
            'sample_size': -10
        }
        is_valid, errors = validator.validate_model_output(model_output)
        assert is_valid is False
        assert any('sample_size' in err for err in errors)

    def test_validate_analysis_result_valid(self, validator: RegressionContractValidator, valid_analysis_result: Dict[str, Any]):
        """Test validation of a complete valid analysis result."""
        is_valid, errors = validator.validate_analysis_result(valid_analysis_result)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_analysis_result_missing_models(self, validator: RegressionContractValidator):
        """Test validation of analysis result missing models field."""
        result = {'census_data_note': "p-values not reported for census data per FR-006 and Constitution Principle VII"}
        is_valid, errors = validator.validate_analysis_result(result)
        assert is_valid is False
        assert any('models' in err for err in errors)

    def test_validate_analysis_result_wrong_census_note(self, validator: RegressionContractValidator, valid_model_output: Dict[str, Any]):
        """Test validation of analysis result with incorrect census data note."""
        result = {
            'models': [valid_model_output],
            'census_data_note': 'wrong note'
        }
        is_valid, errors = validator.validate_analysis_result(result)
        assert is_valid is False
        assert any('census_data_note' in err for err in errors)

class TestRegressionDataclassConstruction:
    """Test that dataclasses can be properly constructed and serialized."""

    def test_regression_coefficient_construction(self):
        """Test RegressionCoefficient dataclass construction."""
        coeff = RegressionCoefficient(name='crossing_number', value=0.5, standard_error=0.1)
        assert coeff.name == 'crossing_number'
        assert coeff.value == 0.5
        assert coeff.standard_error == 0.1

    def test_regression_metrics_construction(self):
        """Test RegressionMetrics dataclass construction."""
        metrics = RegressionMetrics(r_squared=0.85, aic=120.5, bic=135.2, mae=0.45)
        assert metrics.r_squared == 0.85
        assert metrics.aic == 120.5
        assert metrics.mae == 0.45

    def test_regression_model_output_construction(self):
        """Test RegressionModelOutput dataclass construction."""
        output = RegressionModelOutput(
            model_type='linear',
            model_name='test',
            dependent_variable='y',
            independent_variables=['x1', 'x2'],
            coefficients=[RegressionCoefficient(name='x1', value=0.5)],
            metrics=RegressionMetrics(r_squared=0.85),
            sample_size=100
        )
        assert output.model_type == 'linear'
        assert len(output.independent_variables) == 2

    def test_regression_analysis_result_construction(self):
        """Test RegressionAnalysisResult dataclass construction."""
        result = RegressionAnalysisResult(
            models=[
                RegressionModelOutput(
                    model_type='linear',
                    model_name='test',
                    dependent_variable='y',
                    independent_variables=['x'],
                    coefficients=[RegressionCoefficient(name='x', value=0.5)],
                    metrics=RegressionMetrics(r_squared=0.85),
                    sample_size=100
                )
            ],
            census_data_note="p-values not reported for census data per FR-006 and Constitution Principle VII"
        )
        assert len(result.models) == 1
        assert 'census' in result.census_data_note.lower()

class TestRegressionOutputSerialization:
    """Test serialization of regression output structures."""

    def test_model_output_to_dict(self):
        """Test that RegressionModelOutput can be serialized to dict."""
        output = RegressionModelOutput(
            model_type='linear',
            model_name='test',
            dependent_variable='y',
            independent_variables=['x'],
            coefficients=[RegressionCoefficient(name='x', value=0.5, standard_error=0.1)],
            metrics=RegressionMetrics(r_squared=0.85, aic=120.5),
            sample_size=100
        )
        # Convert to dict-like structure
        output_dict = {
            'model_type': output.model_type,
            'model_name': output.model_name,
            'dependent_variable': output.dependent_variable,
            'independent_variables': output.independent_variables,
            'coefficients': [{'name': c.name, 'value': c.value, 'standard_error': c.standard_error} for c in output.coefficients],
            'metrics': asdict(output.metrics),
            'sample_size': output.sample_size
        }
        assert output_dict['model_type'] == 'linear'
        assert output_dict['metrics']['r_squared'] == 0.85

    def test_analysis_result_json_serializable(self):
        """Test that analysis result can be serialized to JSON."""
        result = RegressionAnalysisResult(
            models=[
                RegressionModelOutput(
                    model_type='linear',
                    model_name='test',
                    dependent_variable='y',
                    independent_variables=['x'],
                    coefficients=[RegressionCoefficient(name='x', value=0.5)],
                    metrics=RegressionMetrics(r_squared=0.85),
                    sample_size=100
                )
            ],
            census_data_note="p-values not reported for census data per FR-006 and Constitution Principle VII"
        )
        result_dict = {
            'models': [
                {
                    'model_type': m.model_type,
                    'model_name': m.model_name,
                    'dependent_variable': m.dependent_variable,
                    'independent_variables': m.independent_variables,
                    'coefficients': [{'name': c.name, 'value': c.value, 'standard_error': c.standard_error} for c in m.coefficients],
                    'metrics': asdict(m.metrics),
                    'sample_size': m.sample_size
                }
                for m in result.models
            ],
            'census_data_note': result.census_data_note
        }
        # Should not raise
        json_str = json.dumps(result_dict)
        assert 'p-values not reported' in json_str