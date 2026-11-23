"""
Unit tests for T049b: latency_ratio_comparator.py
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from utils.latency_ratio_comparator import (
    compute_latency_ratio,
    generate_comparison_report,
    save_comparison_report,
    run_latency_comparison,
    load_json_file,
    ensure_results_dir,
)


class TestComputeLatencyRatio:
    def test_normal_case(self):
        ast_latency = 1.0
        baseline_latency = 15.0
        ratio, status = compute_latency_ratio(ast_latency, baseline_latency)
        assert ratio == 15.0
        assert status == "success"

    def test_ratio_below_threshold(self):
        ast_latency = 10.0
        baseline_latency = 15.0
        ratio, status = compute_latency_ratio(ast_latency, baseline_latency)
        assert ratio == 1.5
        assert status == "success"

    def test_zero_ast_latency_raises(self):
        with pytest.raises(ValueError, match="AST latency must be positive"):
            compute_latency_ratio(0.0, 10.0)

    def test_zero_baseline_latency_raises(self):
        with pytest.raises(ValueError, match="Baseline latency must be positive"):
            compute_latency_ratio(10.0, 0.0)

    def test_negative_ast_latency_raises(self):
        with pytest.raises(ValueError, match="AST latency must be positive"):
            compute_latency_ratio(-1.0, 10.0)


class TestGenerateComparisonReport:
    def test_meets_threshold(self):
        ast_latency = 1.0
        baseline_latency = 20.0
        ratio = 20.0
        report = generate_comparison_report(ast_latency, baseline_latency, ratio, threshold=10.0)
        assert report["meets_threshold"] is True
        assert report["status"] == "PASS"
        assert report["latency_reduction_ratio"] == 20.0

    def test_fails_threshold(self):
        ast_latency = 5.0
        baseline_latency = 20.0
        ratio = 4.0
        report = generate_comparison_report(ast_latency, baseline_latency, ratio, threshold=10.0)
        assert report["meets_threshold"] is False
        assert report["status"] == "FAIL"
        assert report["latency_reduction_ratio"] == 4.0


class TestSaveComparisonReport:
    def test_saves_correctly(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_report.json"
            report = {"test": "data"}
            save_comparison_report(report, output_path)
            assert output_path.exists()
            with open(output_path, "r") as f:
                loaded = json.load(f)
            assert loaded == report


class TestRunLatencyComparison:
    @patch("utils.latency_ratio_comparator.Path")
    @patch("utils.latency_ratio_comparator.load_json_file")
    @patch("utils.latency_ratio_comparator.save_comparison_report")
    @patch("utils.latency_ratio_comparator.ensure_results_dir")
    def test_run_success(
        self, mock_ensure_dir, mock_save, mock_load_json, mock_path
    ):
        # Mock paths
        mock_ast_path = MagicMock()
        mock_baseline_path = MagicMock()
        mock_t040_path = MagicMock()

        mock_path.side_effect = [
            mock_ast_path,  # First call: ast_latency_path
            mock_baseline_path,  # Second call: baseline_latency_path
            mock_t040_path,  # Third call: t040_output_path (if needed)
            Path("/fake/results"),  # ensure_results_dir return
        ]

        mock_ast_path.exists.return_value = True
        mock_baseline_path.exists.return_value = True
        mock_t040_path.exists.return_value = False

        # Mock load_json_file to return expected data
        def mock_load(path):
            if path == mock_ast_path:
                return {"ast_generation_latency_seconds": 2.0}
            elif path == mock_baseline_path:
                return {"baseline_generation_latency_seconds": 20.0}
            return {}

        mock_load_json.side_effect = mock_load

        mock_ensure_dir.return_value = Path("/fake/results")

        report = run_latency_comparison()

        assert report["latency_reduction_ratio"] == 10.0
        assert report["meets_threshold"] is True
        assert report["status"] == "PASS"

    @patch("utils.latency_ratio_comparator.Path")
    @patch("utils.latency_ratio_comparator.load_json_file")
    def test_run_missing_ast_latency(self, mock_load_json, mock_path):
        mock_ast_path = MagicMock()
        mock_baseline_path = MagicMock()

        mock_path.side_effect = [mock_ast_path, mock_baseline_path]

        mock_ast_path.exists.return_value = False
        mock_baseline_path.exists.return_value = True

        def mock_load(path):
            if path == mock_baseline_path:
                return {"baseline_generation_latency_seconds": 20.0}
            return {}

        mock_load_json.side_effect = mock_load

        with pytest.raises(FileNotFoundError, match="Could not find AST generation latency"):
            run_latency_comparison()

    @patch("utils.latency_ratio_comparator.Path")
    @patch("utils.latency_ratio_comparator.load_json_file")
    def test_run_missing_baseline_latency(self, mock_load_json, mock_path):
        mock_ast_path = MagicMock()
        mock_baseline_path = MagicMock()

        mock_path.side_effect = [mock_ast_path, mock_baseline_path]

        mock_ast_path.exists.return_value = True
        mock_baseline_path.exists.return_value = True

        def mock_load(path):
            if path == mock_ast_path:
                return {"ast_generation_latency_seconds": 2.0}
            return {}  # Missing baseline key

        mock_load_json.side_effect = mock_load

        with pytest.raises(KeyError, match="Could not find baseline_generation_latency_seconds"):
            run_latency_comparison()
