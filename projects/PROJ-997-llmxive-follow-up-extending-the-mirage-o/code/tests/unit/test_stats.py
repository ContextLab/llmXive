import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np

from src.utils.stats import (
    TTestResult,
    load_metrics_from_json,
    perform_paired_ttest,
    run_statistical_comparison,
)


@pytest.fixture
def temp_metrics_files(tmp_path):
    """Create temporary baseline and proxy metrics files."""
    baseline_data = {
        "acceptance_rate": [0.8, 0.85, 0.9, 0.75, 0.82],
        "reasoning_score": [0.7, 0.75, 0.8, 0.65, 0.72]
    }
    proxy_data = {
        "acceptance_rate": [0.82, 0.87, 0.92, 0.77, 0.84],
        "reasoning_score": [0.72, 0.77, 0.82, 0.67, 0.74]
    }

    baseline_path = tmp_path / "baseline_metrics.json"
    proxy_path = tmp_path / "proxy_metrics.json"

    with open(baseline_path, "w") as f:
        json.dump(baseline_data, f)

    with open(proxy_path, "w") as f:
        json.dump(proxy_data, f)

    return baseline_path, proxy_path


def test_ttest_result_to_dict():
    """Test TTestResult serialization."""
    result = TTestResult(
        statistic=2.5,
        p_value=0.01,
        method="bonferroni_corrected_t_test",
        alpha=0.05
    )

    d = result.to_dict()
    assert d["statistic"] == 2.5
    assert d["p_value"] == 0.01
    assert d["method"] == "bonferroni_corrected_t_test"
    assert d["alpha"] == 0.05
    assert d["adjusted_alpha"] == 0.025  # 0.05 / 2
    assert d["is_significant"] is True  # 0.01 < 0.025


def test_load_metrics_from_json_success(tmp_path):
    """Test loading metrics from a valid JSON file."""
    data = {"acceptance_rate": [0.8, 0.9, 0.95]}
    file_path = tmp_path / "test.json"

    with open(file_path, "w") as f:
        json.dump(data, f)

    result = load_metrics_from_json(file_path, "acceptance_rate")
    assert result == [0.8, 0.9, 0.95]


def test_load_metrics_from_json_file_not_found():
    """Test loading from non-existent file raises error."""
    with pytest.raises(FileNotFoundError):
        load_metrics_from_json(Path("/nonexistent/file.json"), "key")


def test_load_metrics_from_json_key_not_found(tmp_path):
    """Test loading with missing key raises error."""
    data = {"other_key": [1, 2, 3]}
    file_path = tmp_path / "test.json"

    with open(file_path, "w") as f:
        json.dump(data, f)

    with pytest.raises(KeyError):
        load_metrics_from_json(file_path, "missing_key")


def test_perform_paired_ttest():
    """Test paired t-test calculation."""
    baseline = [0.8, 0.85, 0.9, 0.75, 0.82]
    proxy = [0.82, 0.87, 0.92, 0.77, 0.84]

    result = perform_paired_ttest(baseline, proxy, "test_metric")

    assert isinstance(result.statistic, float)
    assert isinstance(result.p_value, float)
    assert result.method == "bonferroni_corrected_t_test"


def test_perform_paired_ttest_length_mismatch():
    """Test that length mismatch raises error."""
    with pytest.raises(ValueError):
        perform_paired_ttest([1, 2, 3], [1, 2])


def test_perform_paired_ttest_insufficient_samples():
    """Test that insufficient samples raises error."""
    with pytest.raises(ValueError):
        perform_paired_ttest([1], [2])


def test_run_statistical_comparison(temp_metrics_files, tmp_path):
    """Test end-to-end statistical comparison."""
    baseline_path, proxy_path = temp_metrics_files
    output_path = tmp_path / "t_test_results.json"

    results = run_statistical_comparison(baseline_path, proxy_path, output_path)

    assert "acceptance_rate" in results
    assert "reasoning_score" in results
    assert results["method"] == "bonferroni_corrected_t_test"
    assert "bonferroni_correction" in results

    # Verify output file was written
    assert output_path.exists()
    with open(output_path, "r") as f:
        saved_results = json.load(f)
    assert saved_results == results
