"""
Contract tests for the model output metrics.
Checks that the JSON file produced by the training step conforms
to the ModelOutput Pydantic schema.
"""

import json
from pathlib import Path

import pytest

from tests.contract.validators import ModelOutput

# Path to the model metrics JSON file as defined in the quickstart spec
METRICS_JSON = Path("data") / "results" / "model_metrics.json"


def test_model_metrics_file_exists():
    """The model_metrics.json file must exist."""
    assert METRICS_JSON.is_file(), f"{METRICS_JSON} does not exist"


def test_model_metrics_schema():
    """Validate that the JSON content matches the ModelOutput schema."""
    with open(METRICS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Pydantic will raise ValidationError if the schema does not match
    ModelOutput.parse_obj(data)