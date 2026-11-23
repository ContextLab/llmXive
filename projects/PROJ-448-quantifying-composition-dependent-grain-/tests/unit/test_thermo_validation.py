"""
Unit tests for thermodynamic validation service.
"""
import pytest
import json
from pathlib import Path
import tempfile
import numpy as np
from code.services.thermo_validation import (
    validate_binary_parameters,
    perform_linear_extrapolation,
    validate_and_extrapolate
)
from code.errors import ThermodynamicError

def test_validate_binary_parameters_present():
    """Test validation when binary parameters are present."""
    thermo_data = {
        "binary_parameters": {
            "Fe-Cr": {"L0": 15000.0, "L1": -2000.0}
        }
    }
    is_valid, warnings = validate_binary_parameters(thermo_data, "Fe-Cr")
    assert is_valid is True
    assert len(warnings) == 0

def test_validate_binary_parameters_missing():
    """Test validation when binary parameters are missing."""
    thermo_data = {
        "binary_parameters": {
            "Fe-Cr": {"L0": 15000.0}
            # Fe-Mo missing
        }
    }
    is_valid, warnings = validate_binary_parameters(thermo_data, "Fe-Mo")
    assert is_valid is False
    assert len(warnings) == 1
    assert "missing" in warnings[0].lower()

def test_perform_linear_extrapolation_success():
    """Test successful linear extrapolation."""
    known_params = {
        1000.0: 12000.0,
        1200.0: 10000.0,
        1400.0: 8000.0
    }
    target_temp = 1100.0
    temp_range = (900.0, 1500.0)

    result = perform_linear_extrapolation(known_params, target_temp, temp_range)
    assert "extrapolated_value" in result
    assert result["method"] == "linear"
    # Expected: slope = -10, intercept = 22000, value at 1100 = 11000
    assert abs(result["extrapolated_value"] - 11000.0) < 0.01

def test_perform_linear_extrapolation_insufficient_data():
    """Test extrapolation fails with insufficient data points."""
    known_params = {1000.0: 12000.0}  # Only one point
    target_temp = 1100.0
    temp_range = (900.0, 1500.0)

    with pytest.raises(ThermodynamicError):
        perform_linear_extrapolation(known_params, target_temp, temp_range)

def test_validate_and_extrapolate_with_missing_params():
    """Test full validation workflow with missing parameters."""
    thermo_data = {
        "binary_parameters": {},
        "temperature_dependent": {
            "Fe-Mo": {
                1000.0: 12000.0,
                1200.0: 10000.0,
                1400.0: 8000.0
            }
        }
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = Path(tmpdir) / "manifest.json"
        result = validate_and_extrapolate(
            thermo_data,
            "Fe-Mo",
            1100.0,
            (900.0, 1500.0),
            output_manifest_path=manifest_path
        )

        assert result["is_valid"] is False
        assert result["has_binary_params"] is False
        assert result["extrapolated"] is True
        assert result["gap_flagged"] is True
        assert result["parameters"]["extrapolated_value"] == 11000.0

        # Check manifest was updated
        assert manifest_path.exists()
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        assert manifest["systems"]["Fe-Mo"]["status"] == "extrapolated"
        assert manifest["systems"]["Fe-Mo"]["gap_flagged"] is True

def test_validate_and_extrapolate_no_extrapolation_possible():
    """Test validation when extrapolation is not possible."""
    thermo_data = {
        "binary_parameters": {},
        "temperature_dependent": {}
    }

    result = validate_and_extrapolate(
        thermo_data,
        "Fe-Mo",
        1100.0,
        (900.0, 1500.0),
        output_manifest_path=None
    )

    assert result["is_valid"] is False
    assert result["extrapolated"] is False
    assert result["gap_flagged"] is True
    assert len(result["warnings"]) > 0
    assert any("extrapolation" in w.lower() for w in result["warnings"])
