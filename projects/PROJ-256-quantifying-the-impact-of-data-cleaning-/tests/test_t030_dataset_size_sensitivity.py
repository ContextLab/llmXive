import json
import os
from pathlib import Path

import pytest

# Import the module under test
from t030_dataset_size_sensitivity import (
    extract_dataset_info,
    bin_dataset_size,
    analyze_size_bin,
    run_sensitivity_analysis,
    write_output,
)


@pytest.fixture
def baseline_json(tmp_path: Path):
    """Create a minimal baseline_metrics.json for testing."""
    data = {
        "ds_small": {"n_samples": 30, "t_test": {"p_value": 0.04, "ci": [0.1, 0.5], "cohen_d": 0.6}},
        "ds_medium": {"n_samples": 120, "t_test": {"p_value": 0.20, "ci": [0.2, 0.8], "cohen_d": 0.3}},
        "ds_large": {"n_samples": 350, "t_test": {"p_value": 0.01, "ci": [0.05, 0.4], "cohen_d": 0.9}},
    }
    path = tmp_path / "baseline_metrics.json"
    path.write_text(json.dumps(data))
    return path


def test_extract_dataset_info(baseline_json: Path):
    info = extract_dataset_info(baseline_json)
    assert len(info) == 3
    names = {i["dataset_name"] for i in info}
    assert names == {"ds_small", "ds_medium", "ds_large"}
    assert {i["n_samples"] for i in info} == {30, 120, 350}


def test_bin_dataset_size(baseline_json: Path):
    info = extract_dataset_info(baseline_json)
    bins = bin_dataset_size(info)
    assert len(bins["<50"]) == 1
    assert len(bins["50-200"]) == 1
    assert len(bins[">200"]) == 1


def test_analyze_size_bin():
    # Small bin with a single entry
    small = [
        {
            "dataset_name": "ds_small",
            "n_samples": 30,
            "metrics": {"t_test": {"p_value": 0.04, "ci": [0.1, 0.5], "cohen_d": 0.6}},
        }
    ]
    result = analyze_size_bin("<50", small)
    assert result["dataset_count"] == 1
    assert result["average_p_value"] == 0.04
    assert result["average_ci_width"] == pytest.approx(0.4, rel=1e-3)
    assert result["average_effect_size"] == 0.6


def test_run_sensitivity_analysis(baseline_json: Path, tmp_path: Path):
    result = run_sensitivity_analysis(baseline_json)
    # Expect three bins with one dataset each
    assert result["<50"]["dataset_count"] == 1
    assert result["50-200"]["dataset_count"] == 1
    assert result[">200"]["dataset_count"] == 1


def test_write_output(tmp_path: Path):
    out_path = tmp_path / "out.json"
    sample = {"<50": {"dataset_count": 1}}
    write_output(sample, out_path)
    assert out_path.is_file()
    loaded = json.loads(out_path.read_text())
    assert loaded == sample