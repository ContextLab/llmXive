"""
Unit test for the a‑priori power analysis script (src.stats.power_pre).
The test runs the script with a small subject count to ensure that:
- The JSON file is created at the expected location.
- The JSON content can be parsed.
- The ``underpowered`` flag correctly reflects the computed power.
"""
import json
from pathlib import Path

import pytest

from llmxive_toolkit import paths
from src.stats.power_pre import compute_power, write_results, POWER_THRESHOLD


@pytest.fixture
def output_path(tmp_path: Path) -> Path:
    """Temporary path for the JSON output."""
    return tmp_path / "power_analysis_pre.json"


def test_compute_power_default():
    """Power with the default 200 subjects should be >= 0.80."""
    power = compute_power(n_subjects=200)
    assert isinstance(power, float)
    assert power >= POWER_THRESHOLD


def test_write_and_load_results(output_path: Path):
    """Verify that ``write_results`` creates a valid JSON file."""
    # Use a deliberately low subject count to trigger an underpowered flag
    low_n = 30
    power = compute_power(n_subjects=low_n)

    write_results(
        power=power,
        n_subjects=low_n,
        output_path=output_path,
    )

    # File must exist
    assert output_path.is_file()

    # Load and validate JSON structure
    with output_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    expected_keys = {"power", "effect_size_f2", "n_subjects", "alpha", "underpowered"}
    assert set(data.keys()) == expected_keys
    assert data["n_subjects"] == low_n
    assert data["underpowered"] is (power < POWER_THRESHOLD)
    # Power should be a float and within [0,1]
    assert 0.0 <= data["power"] <= 1.0
    # Effect size should match the constant defined in the module
    assert data["effect_size_f2"] == pytest.approx(0.05)