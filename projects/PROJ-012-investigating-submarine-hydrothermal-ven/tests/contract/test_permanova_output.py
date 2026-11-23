"""
Contract test for PERMANOVA output schema (T027, T007).

Validates that PERMANOVA results conform to analysis_results_schema.schema.yaml.
"""
import pytest
import yaml
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
CONTRACTS_DIR = BASE_DIR / "contracts"


@pytest.fixture
def analysis_schema():
    with open(CONTRACTS_DIR / "analysis_results_schema.schema.yaml", 'r') as f:
        return yaml.safe_load(f)


def test_permanova_required_fields(analysis_schema):
    """Verify PERMANOVA results have required fields."""
    props = analysis_schema['properties']['model_stats']['items']['properties']
    required = {'sample_id', 'predictor', 'estimate'}
    actual = set(props.keys())
    assert required.issubset(actual), f"Missing required fields: {required - actual}"


def test_permanova_specific_fields(analysis_schema):
    """Verify PERMANOVA results have specific fields."""
    props = analysis_schema['properties']['model_stats']['items']['properties']
    expected = {'r_squared', 'f_statistic', 'dispersion_confounded'}
    actual = set(props.keys())
    assert expected.issubset(actual), f"Missing PERMANOVA fields: {expected - actual}"


def test_dispersion_confounded_flag(analysis_schema):
    """Verify dispersion_confounded flag exists."""
    props = analysis_schema['properties']['model_stats']['items']['properties']
    assert 'dispersion_confounded' in props, "Missing dispersion_confounded"
    assert props['dispersion_confounded']['type'] == 'boolean', \
        "dispersion_confounded must be boolean"


def test_permanova_model_type(analysis_schema):
    """Verify PERMANOVA model type is in enum."""
    props = analysis_schema['properties']['model_stats']['items']['properties']
    model_type = props.get('model_type', {})
    enum = model_type.get('enum', [])
    assert 'permanova' in enum, "Missing 'permanova' in model_type"


def test_analysis_type_permanova(analysis_schema):
    """Verify analysis_type includes PERMANOVA variants."""
    analysis_type = analysis_schema['properties']['analysis_type']
    enum = analysis_type.get('enum', [])
    assert 'permanova' in enum, "Missing 'permanova' in analysis_type"
    assert 'permanova_dispersion_confounded' in enum, \
        "Missing 'permanova_dispersion_confounded' for flagged results"
