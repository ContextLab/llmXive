"""
Unit tests for statistical analysis utilities in src/utils/stats.py
"""
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
    run_statistical_comparison
)


@pytest.fixture
def temp_metrics_files(tmp_path):
    """Create temporary metrics files for testing."""
    baseline_data = {
        "acceptance_rates": [0.8, 0.85, 0.9, 0.75, 0.82],
        "reasoning_scores": [0.95, 0.92, 0.98, 0.88, 0.94]
    }
    proxy_data = {
        "acceptance_rates": [0.81, 0.86, 0.91, 0.76, 0.83],
        "reasoning_scores": [0.94, 0.93, 0.97, 0.89, 0.95]
    }

    baseline_path = tmp_path / "baseline_metrics.json"
    proxy_path = tmp_path / "proxy_metrics.json"

    with open(baseline_path, 'w') as f:
        json.dump(baseline_data, f)

    with open(proxy_path, 'w') as f:
        json.dump(proxy_data, f)

    return baseline_path, proxy_path


def test_ttest_result_to_dict():
    """Test that TTestResult can be converted to dictionary."""
    result = TTestResult(
        statistic=2.5,
        p_value=0.03,
        method="bonferroni_corrected_t_test",
        alternative="two-sided",
        n_samples=100
    )

    result_dict = result.to_dict()

    assert result_dict["statistic"] == 2.5
    assert result_dict["p_value"] == 0.03
    assert result_dict["method"] == "bonferroni_corrected_t_test"
    assert result_dict["alternative"] == "two-sided"
    assert result_dict["n_samples"] == 100


def test_load_metrics_from_json_success(tmp_path):
    """Test successful loading of metrics from JSON."""
    data = {"values": [1.0, 2.0, 3.0, 4.0, 5.0]}
    file_path = tmp_path / "test_metrics.json"

    with open(file_path, 'w') as f:
        json.dump(data, f)

    loaded = load_metrics_from_json(file_path, "values")

    assert loaded == [1.0, 2.0, 3.0, 4.0, 5.0]
    assert all(isinstance(v, float) for v in loaded)


def test_load_metrics_from_json_file_not_found():
    """Test that FileNotFoundError is raised when file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        load_metrics_from_json(Path("nonexistent.json"), "values")


def test_load_metrics_from_json_key_not_found(tmp_path):
    """Test that KeyError is raised when key is not found."""
    data = {"other_key": [1.0, 2.0]}
    file_path = tmp_path / "test_metrics.json"

    with open(file_path, 'w') as f:
        json.dump(data, f)

    with pytest.raises(KeyError):
        load_metrics_from_json(file_path, "missing_key")


def test_perform_paired_ttest():
    """Test paired t-test with known values."""
    baseline = [1.0, 2.0, 3.0, 4.0, 5.0]
    proxy = [1.1, 2.1, 3.1, 4.1, 5.1]

    result = perform_paired_ttest(baseline, proxy, "test_metric", correction_factor=2)

    assert isinstance(result, TTestResult)
    assert result.method == "bonferroni_corrected_t_test"
    assert result.n_samples == 5
    assert result.statistic != 0  # Should detect the small difference
    assert 0 <= result.p_value <= 1


def test_perform_paired_ttest_length_mismatch():
    """Test that ValueError is raised for mismatched lengths."""
    baseline = [1.0, 2.0, 3.0]
    proxy = [1.0, 2.0]

    with pytest.raises(ValueError, match="different lengths"):
        perform_paired_ttest(baseline, proxy, "test_metric")


def test_perform_paired_ttest_insufficient_samples():
    """Test that ValueError is raised for insufficient samples."""
    baseline = [1.0]
    proxy = [1.1]

    with pytest.raises(ValueError, match="Insufficient samples"):
        perform_paired_ttest(baseline, proxy, "test_metric")


def test_run_statistical_comparison(temp_metrics_files):
    """Test end-to-end statistical comparison."""
    baseline_path, proxy_path = temp_metrics_files
    output_path = temp_metrics_files[0].parent / "t_test_results.json"

    results = run_statistical_comparison(baseline_path, proxy_path, output_path)

    # Verify output file was created
    assert output_path.exists()

    # Verify results structure
    assert "acceptance_rate" in results
    assert "reasoning_score" in results
    assert "method" in results
    assert results["method"] == "bonferroni_corrected_t_test"
    assert results["correction_factor"] == 2

    # Verify individual test results
    assert "statistic" in results["acceptance_rate"]
    assert "p_value" in results["acceptance_rate"]
    assert "n_samples" in results["acceptance_rate"]
    assert results["acceptance_rate"]["n_samples"] == 5

    # Verify JSON file content
    with open(output_path, 'r') as f:
        saved_results = json.load(f)

    assert saved_results == results