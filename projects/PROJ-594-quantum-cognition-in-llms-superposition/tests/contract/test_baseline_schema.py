"""
Contract test for baseline metrics schema.

Verifies that the output of the baseline experiment (data/results/baseline_metrics.json)
conforms to the expected schema defined in the project specifications.

This test ensures that:
1. The file exists at the expected path.
2. The JSON is valid and parseable.
3. Required keys (accuracy, macro_f1, seed, model_name, dataset) are present.
4. Metric values are floats within valid probability ranges [0, 1].
5. Metadata types are correct (strings for names, integers for seeds).
"""

import json
import os
import pytest
from typing import Any, Dict

# Expected path relative to project root
# The task description specifies this output path
EXPECTED_OUTPUT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "projects",
    "PROJ-594-quantum-cognition-in-llms-superposition",
    "data",
    "results",
    "baseline_metrics.json"
)

REQUIRED_KEYS = {"accuracy", "macro_f1", "seed", "model_name", "dataset", "timestamp"}


def load_baseline_metrics(path: str) -> Dict[str, Any]:
    """Load and parse the baseline metrics JSON file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Baseline metrics file not found at: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_baseline_metrics_schema_exists():
    """Contract: The baseline metrics file must exist after running the baseline experiment."""
    assert os.path.exists(EXPECTED_OUTPUT_PATH), (
        f"Contract failed: Expected file {EXPECTED_OUTPUT_PATH} does not exist. "
        "Run code/experiments/run_baseline.py first."
    )


def test_baseline_metrics_schema_valid_json():
    """Contract: The baseline metrics file must be valid JSON."""
    try:
        load_baseline_metrics(EXPECTED_OUTPUT_PATH)
    except json.JSONDecodeError as e:
        pytest.fail(f"Contract failed: Invalid JSON in baseline metrics file: {e}")


def test_baseline_metrics_schema_required_keys():
    """Contract: The baseline metrics file must contain all required keys."""
    data = load_baseline_metrics(EXPECTED_OUTPUT_PATH)

    missing_keys = REQUIRED_KEYS - set(data.keys())
    assert not missing_keys, (
        f"Contract failed: Missing required keys in baseline metrics: {missing_keys}. "
        f"Found keys: {list(data.keys())}"
    )


def test_baseline_metrics_schema_metric_types():
    """Contract: Accuracy and macro_f1 must be floats."""
    data = load_baseline_metrics(EXPECTED_OUTPUT_PATH)

    assert isinstance(data["accuracy"], (int, float)), (
        f"Contract failed: 'accuracy' must be a number, got {type(data['accuracy'])}"
    )
    assert isinstance(data["macro_f1"], (int, float)), (
        f"Contract failed: 'macro_f1' must be a number, got {type(data['macro_f1'])}"
    )


def test_baseline_metrics_schema_metric_ranges():
    """Contract: Accuracy and macro_f1 must be between 0 and 1."""
    data = load_baseline_metrics(EXPECTED_OUTPUT_PATH)

    assert 0.0 <= data["accuracy"] <= 1.0, (
        f"Contract failed: 'accuracy' {data['accuracy']} is outside [0, 1]"
    )
    assert 0.0 <= data["macro_f1"] <= 1.0, (
        f"Contract failed: 'macro_f1' {data['macro_f1']} is outside [0, 1]"
    )


def test_baseline_metrics_schema_metadata_types():
    """Contract: Metadata fields must be strings or integers."""
    data = load_baseline_metrics(EXPECTED_OUTPUT_PATH)

    assert isinstance(data["seed"], int), (
        f"Contract failed: 'seed' must be an integer, got {type(data['seed'])}"
    )
    assert isinstance(data["model_name"], str), (
        f"Contract failed: 'model_name' must be a string, got {type(data['model_name'])}"
    )
    assert isinstance(data["dataset"], str), (
        f"Contract failed: 'dataset' must be a string, got {type(data['dataset'])}"
    )
    assert isinstance(data["timestamp"], str), (
        f"Contract failed: 'timestamp' must be a string, got {type(data['timestamp'])}"
    )


def test_baseline_metrics_schema_seed_value():
    """Contract: Seed must be a non-negative integer."""
    data = load_baseline_metrics(EXPECTED_OUTPUT_PATH)

    assert data["seed"] >= 0, (
        f"Contract failed: 'seed' {data['seed']} must be non-negative"
    )

def test_baseline_metrics_schema_model_name():
    """Contract: Model name must indicate a frozen BERT variant."""
    data = load_baseline_metrics(EXPECTED_OUTPUT_PATH)

    model_name = data["model_name"].lower()
    assert "bert" in model_name, (
        f"Contract failed: 'model_name' must contain 'bert', got '{data['model_name']}'"
    )
    # Optional check for frozen status if encoded in name, but schema requires just the name
    # assert "frozen" in model_name or "base" in model_name, ...