"""
Unit test for the dataset size binning sensitivity analysis (T030).

The test creates a temporary ``baseline_metrics.json`` file with three
synthetic datasets covering the three size bins and verifies that the
script produces a non‑empty JSON output containing the expected bin keys.
"""
import json
import os
import tempfile
from pathlib import Path

import pytest

# Import the functions directly from the module under test
from t030_dataset_size_sensitivity import (
    extract_dataset_info,
    bin_dataset_size,
    analyze_size_bin,
    run_sensitivity_analysis,
    write_output,
)

@pytest.fixture
def baseline_file(tmp_path: Path) -> Path:
    """Create a minimal baseline_metrics.json for testing."""
    data = {
        "small_dataset": {"size": 30, "p_value": 0.12, "ci": [0.1, 0.3]},
        "medium_dataset": {"size": 150, "p_value": 0.04, "ci": [0.02, 0.06]},
        "large_dataset": {"size": 350, "p_value": 0.20, "ci": [0.15, 0.25]},
    }
    baseline_path = tmp_path / "baseline_metrics.json"
    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    with baseline_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return baseline_path

def test_extract_dataset_info(baseline_file: Path):
    info = extract_dataset_info(baseline_file)
    assert len(info) == 3
    names = {d["name"] for d in info}
    assert names == {"small_dataset", "medium_dataset", "large_dataset"}

def test_bin_dataset_size(baseline_file: Path):
    info = extract_dataset_info(baseline_file)
    bins = bin_dataset_size(info)
    assert len(bins["small"]) == 1
    assert len(bins["medium"]) == 1
    assert len(bins["large"]) == 1

def test_analyze_size_bin():
    # Small bin with a single entry
    ds = [{"name": "a", "size": 10, "metrics": {"p_value": 0.5, "ci": [0.2, 0.6]}}]
    summary = analyze_size_bin("small", ds)
    assert summary["dataset_count"] == 1
    assert summary["mean_p_value"] == 0.5
    assert summary["mean_ci_width"] == 0.4

def test_full_workflow(tmp_path: Path, baseline_file: Path):
    # Patch the expected baseline location
    original_path = Path("data/processed/baseline_metrics.json")
    backup = None
    if original_path.is_file():
        backup = original_path.read_text()
    # Ensure the directory exists and copy the fixture there
    original_path.parent.mkdir(parents=True, exist_ok=True)
    original_path.write_text(baseline_file.read_text())

    try:
        results = run_sensitivity_analysis()
        assert isinstance(results, list) and len(results) == 3
        # Write to a temporary output file and verify JSON content
        out_path = tmp_path / "size_sensitivity.json"
        write_output(results, out_path)
        assert out_path.is_file()
        with out_path.open() as f:
            loaded = json.load(f)
        assert isinstance(loaded, list) and len(loaded) == 3
    finally:
        # Restore original baseline file if it existed
        if backup is not None:
            original_path.write_text(backup)
        else:
            original_path.unlink(missing_ok=True)