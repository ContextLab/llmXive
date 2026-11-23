"""
Unit tests for the generation runner (T009).

The tests verify that:
* The runner creates the expected output directory.
* At least one batch file and a generation_log.json are written.
* The log file respects the required schema.
"""

import json
import os
from pathlib import Path

import pytest

from code.generation.runner import run_generation_pipeline, _resolve_model_path

# ----------------------------------------------------------------------
# Helper: a minimal in‑memory dummy model that mimics the llama_cpp API
# ----------------------------------------------------------------------
class DummyModel:
    def __call__(self, prompt, **kwargs):
        # Return a deterministic placeholder text – no external model needed.
        return {"choices": [{"text": f"Generated response for: {prompt[:30]}..."}]}

# ----------------------------------------------------------------------
# Fixture: temporary configuration pointing to the dummy model
# ----------------------------------------------------------------------
@pytest.fixture
def dummy_config(tmp_path):
    return {
        "output_dir": str(tmp_path / "raw"),
        "samples_per_prompt": 5,  # Small number for fast test execution
        "strategies": ["direct", "hypothetical", "comparative", "role-play"],
        "model_path": "dummy",  # Triggers the dummy‑model path handling
    }

# ----------------------------------------------------------------------
# Patch the model‑loading logic to return the DummyModel instead of
# attempting a real download. This keeps the test fast and deterministic.
# ----------------------------------------------------------------------
@pytest.fixture(autouse=True)
def mock_load_model(monkeypatch):
    def _mock_load_model(model_path, n_ctx=2048, n_threads=4):
        return DummyModel()

    monkeypatch.setattr(
        "code.generation.runner.load_model", _mock_load_model, raising=False
    )
    # Also bypass the HF download logic – it will never be called because we
    # provide ``model_path`` directly.
    yield

# ----------------------------------------------------------------------
# Test: runner creates batch files and a proper log
# ----------------------------------------------------------------------
def test_run_generation_pipeline_writes_outputs(dummy_config):
    out_dir = Path(dummy_config["output_dir"])
    run_generation_pipeline(dummy_config)

    # Verify the output directory exists
    assert out_dir.is_dir()

    # Verify at least one batch file exists
    batch_files = list(out_dir.glob("generation_batch_*.json"))
    assert batch_files, "No batch files were written"

    # Verify generation_log.json exists and follows the schema
    log_path = out_dir / "generation_log.json"
    assert log_path.is_file(), "generation_log.json missing"

    with log_path.open() as f:
        log_data = json.load(f)

    # Required keys
    for key in ("total", "success", "fail", "strategy_counts"):
        assert key in log_data

    # Basic sanity checks
    assert isinstance(log_data["total"], int) and log_data["total"] > 0
    assert isinstance(log_data["success"], int)
    assert isinstance(log_data["fail"], int)
    assert isinstance(log_data["strategy_counts"], dict)

# ----------------------------------------------------------------------
# Test: internal helper resolves explicit model_path correctly
# ----------------------------------------------------------------------
def test_resolve_model_path_explicit():
    cfg = {"model_path": "/tmp/fake.gguf"}
    resolved = _resolve_model_path(cfg)
    assert resolved == "/tmp/fake.gguf"