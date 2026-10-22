"""
Contract test: the real model output JSON conforms to the schema.

Validates ``data/results/model_metrics.json`` (produced by the training
step, T104) using the Pydantic ``ModelOutput`` validator.

If the real artifact has not been generated yet, the test is SKIPPED
with an explicit message — it never fabricates metrics.
"""

import json
import sys
from pathlib import Path

import pytest

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

from validators import ModelOutput  # noqa: E402

PROJECT_ROOT = THIS_DIR.parents[1]
METRICS_JSON = PROJECT_ROOT / "data" / "results" / "model_metrics.json"


def test_real_model_metrics_conform():
    if not METRICS_JSON.exists():
        pytest.skip(
            "data/results/model_metrics.json not yet generated (T104 pending)"
        )
    with open(METRICS_JSON, "r", encoding="utf-8") as f:
        payload = json.load(f)

    model_output = ModelOutput(**payload)
    assert model_output.r2_score >= 0.10, (
        f"validation R² {model_output.r2_score:.4f} below 0.10 threshold"
    )
    assert model_output.r2_score > model_output.baseline_r2, (
        "model must exceed the null (mean-only) baseline"
    )
    assert model_output.rmse >= 0.0


def test_model_output_rejects_bad_payloads():
    """The validator itself must fail loudly on malformed payloads."""
    with pytest.raises(Exception):
        ModelOutput(**{"r2_score": "high", "rmse": 1.0, "baseline_r2": 0.0})
    with pytest.raises(Exception):
        ModelOutput(**{"rmse": 1.0, "baseline_r2": 0.0})
    # A well-formed payload must pass.
    ok = ModelOutput(r2_score=0.5, rmse=0.7, baseline_r2=0.0)
    assert ok.r2_score == 0.5
