"""Contract test for the statistical analysis JSON output.

Validates that ``results/statistics.json`` exists and contains the
required top‑level keys with appropriate types.
"""
from __future__ import annotations

import json
from pathlib import Path

from llmxive_toolkit import paths

def test_statistics_json_schema():
    json_path = paths.results("statistics.json")
    assert json_path.exists(), f"{json_path} does not exist"

    data = json.loads(json_path.read_text(encoding="utf-8"))
    # Required top‑level keys
    for key in ["p_values", "significant", "effect_sizes", "exploratory"]:
        assert key in data, f"Missing key '{key}' in statistics.json"

    # Types
    assert isinstance(data["p_values"], dict), "'p_values' must be a dict"
    assert isinstance(data["significant"], dict), "'significant' must be a dict"
    assert isinstance(data["effect_sizes"], dict), "'effect_sizes' must be a dict"
    assert isinstance(data["exploratory"], bool), "'exploratory' must be a bool"