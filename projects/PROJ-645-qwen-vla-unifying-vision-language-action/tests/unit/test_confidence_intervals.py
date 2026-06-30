"""
Unit tests for src/statistics/confidence_intervals.py (T026).
"""
import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.statistics.confidence_intervals import (
    bootstrap_confidence_interval,
    compute_ci_for_ratio,
    run_ablation_ci_analysis,
    load_eval_results
)

class TestBootstrapLogic:
    def test_empty_data_raises(self):
        with pytest.raises(ValueError):
            bootstrap_confidence_interval([])

    def test_single_value_ci(self):
        # With 1 value, mean is the value, CI should be the value
        data = [0.5]
        result = bootstrap_confidence_interval(data, n_iterations=100, seed=42)
        assert abs(result["mean"] - 0.5) < 1e-6
        assert abs(result["ci_lower"] - 0.5) < 1e-6
        assert abs(result["ci_upper"] - 0.5) < 1e-6

    def test_ci_bounds_validity(self):
        data = [0.1, 0.2, 0.3, 0.4, 0.5]
        result = bootstrap_confidence_interval(data, n_iterations=1000, seed=123)
        assert result["ci_lower"] <= result["mean"] <= result["ci_upper"]

    def test_reproducibility(self):
        data = [0.5, 0.6, 0.7]
        res1 = bootstrap_confidence_interval(data, seed=42)
        res2 = bootstrap_confidence_interval(data, seed=42)
        assert res1["ci_lower"] == res2["ci_lower"]
        assert res1["ci_upper"] == res2["ci_upper"]

class TestComputeCiForRatio:
    @pytest.fixture
    def mock_eval_data(self):
        return {
            "0.0": {
                "within-embodiment": {
                    "success_rate": [0.1, 0.2, 0.3, 0.4, 0.5]
                }
            },
            "1.0": {
                "within-embodiment": {
                    "success_rate": [0.8, 0.85, 0.9, 0.95, 0.92]
                }
            }
        }

    def test_find_ratio_key(self, mock_eval_data):
        result = compute_ci_for_ratio(mock_eval_data, 0.0, seed=42)
        assert result["ratio"] == 0.0
        assert "ci_lower" in result
        assert "ci_upper" in result

    def test_missing_ratio_raises(self, mock_eval_data):
        with pytest.raises(KeyError):
            compute_ci_for_ratio(mock_eval_data, 0.5, seed=42)

    def test_invalid_data_format_raises(self, mock_eval_data):
        bad_data = {"0.0": {"within-embodiment": {}}}
        with pytest.raises(ValueError):
            compute_ci_for_ratio(bad_data, 0.0)

class TestRunAblationCiAnalysis:
    def test_full_pipeline(self, tmp_path):
        input_file = tmp_path / "eval_results.json"
        output_file = tmp_path / "ci_results.json"

        data = {
            "0.0": {"within-embodiment": {"success_rate": [0.1, 0.2, 0.3, 0.4, 0.5]}},
            "1.0": {"within-embodiment": {"success_rate": [0.8, 0.85, 0.9, 0.95, 0.92]}}
        }
        with open(input_file, 'w') as f:
            json.dump(data, f)

        results = run_ablation_ci_analysis(
            input_path=str(input_file),
            output_path=str(output_file),
            ratios=[0.0, 1.0],
            seed=42
        )

        assert "0.0" in results
        assert "1.0" in results
        assert results["0.0"]["ci_lower"] < results["0.0"]["ci_upper"]
        assert results["1.0"]["ci_lower"] < results["1.0"]["ci_upper"]

        assert output_file.exists()
        with open(output_file, 'r') as f:
            saved = json.load(f)
        assert "0.0" in saved