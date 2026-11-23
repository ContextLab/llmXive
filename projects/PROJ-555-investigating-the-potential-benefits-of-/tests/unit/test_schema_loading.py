"""
Unit tests for schema loading functionality.
Verifies that output.schema.yaml definitions are correctly converted to Pydantic models.
"""
import pytest
import sys
from pathlib import Path
from typing import Any

# Add code to path if not already
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils.schema_loader import get_output_schema, load_schema_to_pydantic
from pydantic import ValidationError

def test_output_schema_exists():
    """Test that the output schema file exists and can be loaded."""
    schemas = get_output_schema()
    assert "FinalReport" in schemas
    assert "SensitivityArtifact" in schemas

def test_final_report_structure():
    """Test that FinalReport model has the required fields."""
    schemas = get_output_schema()
    FinalReport = schemas["FinalReport"]

    # Check that required fields exist
    fields = FinalReport.model_fields
    assert "regression_coefficients" in fields
    assert "sensitivity_analysis" in fields
    assert "data_quality_flags" in fields

def test_sensitivity_artifact_structure():
    """Test that SensitivityArtifact model has the required fields."""
    schemas = get_output_schema()
    SensitivityArtifact = schemas["SensitivityArtifact"]

    fields = SensitivityArtifact.model_fields
    assert "threshold" in fields
    assert "proxy_variable" in fields
    assert "model_params" in fields
    assert "metrics" in fields

def test_final_report_validation_valid():
    """Test that a valid FinalReport instance can be created."""
    schemas = get_output_schema()
    FinalReport = schemas["FinalReport"]

    valid_data = {
        "regression_coefficients": {
            "fixed_effects": {"ecotourism": 0.5},
            "random_effects": {"pair_var": 0.1},
            "variance_components": {"residual": 0.2}
        },
        "sensitivity_analysis": [
            {
                "threshold": 1000.0,
                "proxy_variable": "revenue_usd",
                "effect_size": 0.45,
                "p_value": 0.03,
                "corrected_p_value": 0.06
            }
        ],
        "data_quality_flags": ["All checks passed"]
    }

    instance = FinalReport(**valid_data)
    assert instance is not None
    assert len(instance.sensitivity_analysis) == 1

def test_final_report_validation_invalid():
    """Test that invalid data raises ValidationError."""
    schemas = get_output_schema()
    FinalReport = schemas["FinalReport"]

    invalid_data = {
        "regression_coefficients": "not_a_dict", # Should be dict
        "sensitivity_analysis": [],
        "data_quality_flags": []
    }

    with pytest.raises(ValidationError):
        FinalReport(**invalid_data)

def test_sensitivity_artifact_validation_valid():
    """Test that a valid SensitivityArtifact instance can be created."""
    schemas = get_output_schema()
    SensitivityArtifact = schemas["SensitivityArtifact"]

    valid_data = {
        "threshold": 5000.0,
        "proxy_variable": "visitor_count",
        "model_params": {"solver": "bfgs", "max_iter": 1000},
        "metrics": {"aic": 120.5, "bic": 130.2}
    }

    instance = SensitivityArtifact(**valid_data)
    assert instance is not None
    assert instance.threshold == 5000.0
    assert instance.proxy_variable == "visitor_count"