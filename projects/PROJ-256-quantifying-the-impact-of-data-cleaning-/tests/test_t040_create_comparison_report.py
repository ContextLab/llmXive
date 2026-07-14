"""
Unit test for the ``t040_create_comparison_report`` script.

The test creates temporary baseline and cleaned metric files, runs the
script's ``main`` function and then checks that the generated
``comparison_report.json`` contains the expected absolute and relative
differences.
"""
import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest

# Import the script after we have set up a temporary working directory
from t040_create_comparison_report import main as create_report

@pytest.fixture
def temp_workdir():
    """Create a temporary directory that mimics the repository layout."""
    original_cwd = Path.cwd()
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        # Recreate the expected processed data directory
        (tmp_dir / "data" / "processed").mkdir(parents=True, exist_ok=True)
        os.chdir(tmp_dir)
        yield tmp_dir
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(tmp_dir, ignore_errors=True)

def write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def test_comparison_report_generation(temp_workdir):
    # Arrange – create minimal baseline and cleaned metric files
    baseline = {
        "p_value": 0.123,
        "ci_width": 0.45,
        "effect_size": 0.8
    }
    cleaned = {
        "p_value": 0.200,
        "ci_width": 0.30,
        "effect_size": 0.85
    }
    write_json(Path("data/processed/baseline_metrics.json"), baseline)
    write_json(Path("data/processed/cleaned_metrics.json"), cleaned)

    # Act
    create_report()

    # Assert – the output file exists and contains the expected diffs
    out_path = Path("data/processed/comparison_report.json")
    assert out_path.is_file(), "Comparison report was not created"

    with open(out_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    # Absolute differences should be rounded to three decimals
    assert report["absolute_diff"]["p_value"] == round(abs(0.200 - 0.123), 3)
    assert report["absolute_diff"]["ci_width"] == round(abs(0.30 - 0.45), 3)
    assert report["absolute_diff"]["effect_size"] == round(abs(0.85 - 0.8), 3)

    # Relative differences should be rounded to two decimals
    expected_rel_p = round((0.200 - 0.123) / abs(0.123), 2)
    expected_rel_ci = round((0.30 - 0.45) / abs(0.45), 2)
    expected_rel_es = round((0.85 - 0.8) / abs(0.8), 2)

    assert report["relative_diff"]["p_value"] == expected_rel_p
    assert report["relative_diff"]["ci_width"] == expected_rel_ci
    assert report["relative_diff"]["effect_size"] == expected_rel_es

    # The original metric payloads should be embedded unchanged
    assert report["baseline_metrics"] == baseline
    assert report["cleaned_metrics"] == cleaned