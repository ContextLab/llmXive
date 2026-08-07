"""
Test verification for the pipeline runtime report.

This test ensures that the JSON file ``output/pipeline_runtime.json`` exists,
conforms to the expected schema, and reports a ``status`` of ``"pass"`` with
a total runtime not exceeding the 7200‑second limit.

The test is deliberately simple and raises AssertionError if any condition
is not met, which aligns with the project's verification conventions.
"""

import json
from pathlib import Path

import pytest

# Path to the runtime JSON artifact produced by the full pipeline (T117)
RUNTIME_JSON_PATH = Path("output/pipeline_runtime.json")

@pytest.fixture(scope="module")
def runtime_data():
    """Load and return the runtime JSON content."""
    assert RUNTIME_JSON_PATH.is_file(), (
        f"Runtime report not found at {RUNTIME_JSON_PATH!s}. "
        "Ensure that the full pipeline (T117) has been executed."
    )
    with RUNTIME_JSON_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def test_runtime_schema(runtime_data):
    """Check that required keys exist and have appropriate types."""
    required_keys = {
        "total_runtime_seconds": (int, float),
        "limit_seconds": (int, float),
        "status": str,
    }
    for key, expected_type in required_keys.items():
        assert key in runtime_data, f"Missing key '{key}' in runtime JSON."
        assert isinstance(runtime_data[key], expected_type), (
            f"Key '{key}' should be of type {expected_type}, "
            f"got {type(runtime_data[key])}."
        )

def test_runtime_within_limit(runtime_data):
    """Assert that the total runtime does not exceed the allowed limit."""
    total = runtime_data["total_runtime_seconds"]
    limit = runtime_data["limit_seconds"]
    assert total <= limit, (
        f"Pipeline runtime exceeds limit: {total}s > {limit}s."
    )
    assert total <= 7200, (
        f"Pipeline runtime exceeds the 2‑hour threshold: {total}s > 7200s."
    )

def test_status_is_pass(runtime_data):
    """The status field must be exactly 'pass'."""
    assert runtime_data["status"] == "pass", (
        f"Pipeline runtime status is '{runtime_data['status']}', expected 'pass'."
    )