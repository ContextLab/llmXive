"""
Unit test for the baseline overhead computation (T009).

The test simply verifies that the JSON artifact produced by
``code/baseline_overhead.py`` exists, contains the three expected keys,
and that each median latency is a positive number.
"""

import json
from pathlib import Path

from llmxive_toolkit import paths

def test_baseline_overhead_file_exists_and_valid():
    # Resolve the expected location of the baseline JSON file.
    baseline_path: Path = paths.data("processed", "baseline_overhead.json")
    assert baseline_path.is_file(), f"Baseline file missing: {baseline_path}"

    # Load and validate the JSON structure.
    with baseline_path.open("r", encoding="utf-8") as fp:
        data = json.load(fp)

    # Expected keys according to the specification.
    expected_keys = {"bm25", "sqlite", "rdflib"}
    assert set(data.keys()) == expected_keys, f"Unexpected keys: {data.keys()}"

    # Every median latency must be a positive number.
    for key, value in data.items():
        assert isinstance(value, (int, float)), f"Value for {key} is not numeric"
        assert value > 0, f"Median latency for {key} must be > 0, got {value}"