"""
Contract test for the model output metrics file.

The test loads ``data/results/model_metrics.json`` and validates that
the JSON structure conforms to the ``ModelOutput`` Pydantic model defined
in ``tests/contract/validators.py``.

If the file is not yet generated (e.g., the training step has not run),
the test is skipped so that the contract suite can still be executed
without causing a failure.
"""
import json
import pytest
from pathlib import Path

# Import the Pydantic model that defines the expected schema.
from .validators import ModelOutput


def _get_metrics_path() -> Path:
    """Return the absolute path to the model metrics JSON file."""
    return (
        Path(__file__).resolve().parents[2]
        / "data"
        / "results"
        / "model_metrics.json"
    )


def test_model_output_schema():
    """
    Verify that the model metrics file exists and matches the
    ``ModelOutput`` schema.
    """
    metrics_path = _get_metrics_path()
    if not metrics_path.exists():
        pytest.skip(f"Model metrics not found at {metrics_path}")

    with open(metrics_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Validation via Pydantic – will raise if fields are missing or out of range.
    model_output = ModelOutput(**data)

    assert isinstance(model_output, ModelOutput)
    # Ensure the numeric fields are indeed numbers (Pydantic already coerces).
    assert model_output.r2_score >= 0.0
    assert model_output.rmse >= 0.0
    assert model_output.baseline_r2 >= 0.0
