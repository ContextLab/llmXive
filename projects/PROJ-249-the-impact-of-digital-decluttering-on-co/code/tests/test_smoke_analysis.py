"""
test_smoke_analysis.py

Verifies that the smoke‑analysis JSON produced by
``code/validation/produce_smoke_results.py`` conforms to the
``contracts/analysis.schema.yaml`` schema and that required numeric
fields are present and finite.
"""

import json
import math
from pathlib import Path

import pytest
from jsonschema import validate, ValidationError

from llmxive_toolkit import paths

# Path to the generated JSON (produced by the script under test)
SMOKE_JSON = paths.data("results", "smoke_results.json")
# Path to the JSON‑Schema for an analysis result
SCHEMA_PATH = Path(__file__).parents[3] / "contracts" / "analysis.schema.yaml"

@pytest.fixture(scope="module")
def schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def test_smoke_results_file_exists():
    assert SMOKE_JSON.is_file(), f"Expected smoke results at {SMOKE_JSON}"

def test_json_structure(schema):
    """The top‑level must contain a ``metrics`` list and a timestamp."""
    with open(SMOKE_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "generated_at" in data
    assert "metrics" in data
    assert isinstance(data["metrics"], list)

    # Validate each metric entry against the schema
    for metric_obj in data["metrics"]:
        try:
            validate(instance=metric_obj, schema=schema)
        except ValidationError as e:
            pytest.fail(f"Metric entry failed schema validation: {e}")

def test_numeric_fields_are_finite(schema):
    """All numeric fields must be real, finite numbers."""
    with open(SMOKE_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    for metric in data["metrics"]:
        for field in (
            "mean_change",
            "ci_lower",
            "ci_upper",
            "p_value_uncorrected",
            "p_value_corrected",
            "effect_size_cohen_d",
        ):
            value = metric.get(field)
            assert value is not None, f"{field} missing for metric {metric.get('metric')}"
            assert isinstance(value, (int, float)), f"{field} not numeric"
            assert math.isfinite(value), f"{field} is not finite for metric {metric.get('metric')}"

        # method_used must be one of the allowed strings
        assert metric["method_used"] in {"bootstrap", "wilcoxon"}, (
            f"Unexpected method_used: {metric['method_used']}"
        )