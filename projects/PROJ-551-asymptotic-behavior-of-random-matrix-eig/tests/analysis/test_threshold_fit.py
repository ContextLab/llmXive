"""
Test that the threshold fitting script produces a non‑empty JSON file with the
expected top‑level keys.
"""
import json
from pathlib import Path

from llmxive_toolkit import paths as llm_paths

def test_threshold_statistical_json_exists():
    json_path = llm_paths.processed("threshold_statistical.json")
    assert json_path.is_file(), f"Expected {json_path} to exist"

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Basic sanity checks
    assert "generated_at" in data, "Missing 'generated_at' timestamp"
    assert "threshold_estimates" in data, "Missing 'threshold_estimates' list"
    assert isinstance(data["threshold_estimates"], list), "'threshold_estimates' should be a list"
    # Ensure at least one group was processed (the real sweep contains 36 groups)
    assert len(data["threshold_estimates"]) >= 1, "No threshold estimates were written"