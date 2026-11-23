"""
Unit tests for the stability report generation logic (T035).

Tests verify:
1. Jaccard similarity calculation correctness.
2. Stability verification logic.
3. Failure handling (exit code 1, failure report generation).
4. Success handling (exit code 0, success report generation).
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from models.generate_stability_report import (
    calculate_jaccard_similarity,
    verify_cluster_stability,
    write_failed_report,
    write_success_report,
    main
)


class TestJaccardSimilarity:
    def test_identical_sets(self):
        set_a = {1, 2, 3}
        set_b = {1, 2, 3}
        assert calculate_jaccard_similarity(set_a, set_b) == 1.0

    def test_disjoint_sets(self):
        set_a = {1, 2, 3}
        set_b = {4, 5, 6}
        assert calculate_jaccard_similarity(set_a, set_b) == 0.0

    def test_partial_overlap(self):
        set_a = {1, 2, 3, 4}
        set_b = {3, 4, 5, 6}
        # Intersection: {3, 4} -> 2
        # Union: {1, 2, 3, 4, 5, 6} -> 6
        assert calculate_jaccard_similarity(set_a, set_b) == 2/6

    def test_empty_sets(self):
        assert calculate_jaccard_similarity(set(), set()) == 1.0

    def test_one_empty_set(self):
        assert calculate_jaccard_similarity({1, 2}, set()) == 0.0


class TestVerifyClusterStability:
    def test_high_stability(self):
        # Simulate high overlap across resamples
        bootstrap_results = {
            "resamples": [
                {"top_cluster_indices": [1, 2, 3, 4, 5]},
                {"top_cluster_indices": [1, 2, 3, 4, 6]},
                {"top_cluster_indices": [1, 2, 3, 5, 6]},
            ]
        }
        metrics = verify_cluster_stability(bootstrap_results)
        assert metrics["passed"] is True
        assert metrics["average_jaccard"] >= 0.7

    def test_low_stability(self):
        # Simulate low overlap across resamples
        bootstrap_results = {
            "resamples": [
                {"top_cluster_indices": [1, 2, 3]},
                {"top_cluster_indices": [4, 5, 6]},
                {"top_cluster_indices": [7, 8, 9]},
            ]
        }
        metrics = verify_cluster_stability(bootstrap_results)
        assert metrics["passed"] is False
        assert metrics["average_jaccard"] < 0.7

    def test_insufficient_resamples(self):
        bootstrap_results = {"resamples": [{"top_cluster_indices": [1, 2, 3]}]}
        with pytest.raises(ValueError, match="Insufficient bootstrap resamples"):
            verify_cluster_stability(bootstrap_results)

    def test_missing_indices(self):
        bootstrap_results = {
            "resamples": [
                {"top_cluster_indices": []},
                {"top_cluster_indices": [1, 2, 3]},
            ]
        }
        with pytest.raises(ValueError, match="Could not extract top cluster indices"):
            verify_cluster_stability(bootstrap_results)


class TestWriteReports:
    def test_write_failed_report(self, tmp_path):
        metrics = {
            "average_jaccard": 0.5,
            "min_jaccard": 0.2,
            "max_jaccard": 0.8,
            "num_resamples": 5,
            "threshold": 0.7
        }
        output_path = tmp_path / "stability_failed.json"
        write_failed_report(metrics, output_path)

        assert output_path.exists()
        with open(output_path, 'r') as f:
            report = json.load(f)
        assert report["status"] == "failed"
        assert report["metrics"]["average_jaccard"] == 0.5

    def test_write_success_report(self, tmp_path):
        metrics = {
            "average_jaccard": 0.85,
            "min_jaccard": 0.75,
            "max_jaccard": 0.95,
            "num_resamples": 10,
            "threshold": 0.7
        }
        output_path = tmp_path / "stability_report.json"
        write_success_report(metrics, output_path)

        assert output_path.exists()
        with open(output_path, 'r') as f:
            report = json.load(f)
        assert report["status"] == "passed"


class TestMainFunction:
    def test_main_success(self, tmp_path, monkeypatch):
        # Mock bootstrap results with high stability
        bootstrap_data = {
            "resamples": [
                {"top_cluster_indices": [1, 2, 3, 4, 5]},
                {"top_cluster_indices": [1, 2, 3, 4, 5]},
                {"top_cluster_indices": [1, 2, 3, 4, 5]},
            ]
        }
        bootstrap_file = tmp_path / "shap_bootstrap_results.json"
        with open(bootstrap_file, 'w') as f:
            json.dump(bootstrap_data, f)

        # Mock ANALYSIS_DIR
        with patch('models.generate_stability_report.ANALYSIS_DIR', tmp_path):
            exit_code = main()
            assert exit_code == 0
            assert (tmp_path / "stability_report.json").exists()

    def test_main_failure(self, tmp_path, monkeypatch):
        # Mock bootstrap results with low stability
        bootstrap_data = {
            "resamples": [
                {"top_cluster_indices": [1, 2, 3]},
                {"top_cluster_indices": [4, 5, 6]},
                {"top_cluster_indices": [7, 8, 9]},
            ]
        }
        bootstrap_file = tmp_path / "shap_bootstrap_results.json"
        with open(bootstrap_file, 'w') as f:
            json.dump(bootstrap_data, f)

        # Mock ANALYSIS_DIR
        with patch('models.generate_stability_report.ANALYSIS_DIR', tmp_path):
            exit_code = main()
            assert exit_code == 1
            assert (tmp_path / "stability_failed.json").exists()

    def test_main_missing_bootstrap_file(self, tmp_path, monkeypatch):
        # Mock ANALYSIS_DIR without bootstrap file
        with patch('models.generate_stability_report.ANALYSIS_DIR', tmp_path):
            exit_code = main()
            assert exit_code == 1