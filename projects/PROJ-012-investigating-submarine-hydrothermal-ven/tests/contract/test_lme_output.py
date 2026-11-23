"""
Contract test for LME output schema (T016, T007).

Validates that LME analysis outputs conform to analysis_results_schema.schema.yaml.
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


def test_lme_required_fields(analysis_schema):
    """Verify LME results have required fields."""
    props = analysis_schema['properties']['model_stats']['items']['properties']
    required = {'sample_id', 'predictor', 'estimate'}
    actual = set(props.keys())
    assert required.issubset(actual), f"Missing required fields: {required - actual}"


def test_lme_optional_fields(analysis_schema):
    """Verify LME results have expected optional fields."""
    props = analysis_schema['properties']['model_stats']['items']['properties']
    expected_optional = {'se', 'p_value', 'model_type'}
    actual = set(props.keys())
    assert expected_optional.issubset(actual), \
        f"Missing expected optional fields: {expected_optional - actual}"


def test_metadata_flag_requirement(analysis_schema):
    """Verify FR-003.1 metadata flag is required."""
    props = analysis_schema['properties']['model_stats']['items']['properties']
    assert 'metadata_flag' in props, "Missing metadata_flag (FR-003.1)"
    default = props['metadata_flag'].get('default', '')
    assert 'associational analysis' in default.lower(), \
        f"Metadata flag default incorrect: {default}"


def test_model_type_enum(analysis_schema):
    """Verify model_type enum includes LME."""
    props = analysis_schema['properties']['model_stats']['items']['properties']
    model_type = props.get('model_type', {})
    enum = model_type.get('enum', [])
    assert 'lme' in enum, "Missing 'lme' in model_type enum"


def test_analysis_type_enum(analysis_schema):
    """Verify analysis_type enum includes LME."""
    analysis_type = analysis_schema['properties']['analysis_type']
    enum = analysis_type.get('enum', [])
    assert 'lme' in enum, "Missing 'lme' in analysis_type enum"
    assert 'fixed_effects' in enum, "Missing 'fixed_effects' for fallback"
    assert 'spearman' in enum, "Missing 'spearman' for small N"
