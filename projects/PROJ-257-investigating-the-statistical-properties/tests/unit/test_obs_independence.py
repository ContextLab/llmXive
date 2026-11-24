"""Unit test for the observational independence validation script.

The test checks that:
1. The script runs without error on a real ``obs_point_estimates.csv`` file.
2. The generated ``obs_independence.json`` conforms to the expected schema
   (a simple contract defined inline for the purpose of the test).
3. The lag‑1 autocorrelation values are numeric.
4. The ``independence_flag`` is ``True`` when both autocorrelations are
   below the 0.1 magnitude threshold.
"""

import json
from pathlib import Path

import pytest
from jsonschema import validate as jsonschema_validate, ValidationError

# Import the function under test.
from src.validation.validate_observations import validate_observations

# Minimal inline schema for the output JSON.
OBS_INDEP_SCHEMA = {
    "type": "object",
    "properties": {
        "lag1_mass_ratio": {"type": "number"},
        "lag1_effective_spin": {"type": "number"},
        "independence_flag": {"type": "boolean"},
    },
    "required": ["lag1_mass_ratio", "lag1_effective_spin", "independence_flag"],
    "additionalProperties": False,
}


def test_validate_observations_produces_json(tmp_path, monkeypatch):
    """
    Run ``validate_observations`` and verify the output JSON.
    The test uses the actual data produced by earlier pipeline steps;
    it therefore requires that ``obs_point_estimates.csv`` exists.
    """
    # Ensure the function writes to the canonical location under the project root.
    out_path = validate_observations()
    assert out_path.is_file(), "Output JSON file was not created."

    # Load and validate the JSON content.
    with out_path.open("r", encoding="utf-8") as f:
        result = json.load(f)

    # Schema validation.
    try:
        jsonschema_validate(instance=result, schema=OBS_INDEP_SCHEMA)
    except ValidationError as exc:
        pytest.fail(f"Output JSON does not match schema: {exc.message}")

    # Autocorrelation values must be real numbers.
    assert isinstance(result["lag1_mass_ratio"], float)
    assert isinstance(result["lag1_effective_spin"], float)

    # The independence flag should be true only when both |ρ₁| < 0.1.
    flag_expected = (
        abs(result["lag1_mass_ratio"]) < 0.1 and abs(result["lag1_effective_spin"]) < 0.1
    )
    assert result["independence_flag"] == flag_expected