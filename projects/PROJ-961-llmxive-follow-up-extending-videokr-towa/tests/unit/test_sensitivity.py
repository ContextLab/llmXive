"""
Unit tests for sensitivity sweep logic in code/analysis/sensitivity.py.

These tests verify the core logic of the sensitivity analysis for User Story 3:
- Threshold sweeping (2, 3, 4 hops)
- Bin merging logic for small sample sizes
- Statistical significance comparison across thresholds
"""
import json
import math
import os
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis.sensitivity import (
    calculate_effect_size,
    perform_threshold_sweep,
    merge_bins_if_needed,
    run_sensitivity_analysis,
)
from utils.config import get_project_root, get_path, ensure_dir, get_config


class TestCalculateEffectSize:
    """Test effect size calculation between two bins."""

    def test_calculate_effect_size_basic(self):
        """Test basic effect size calculation."""
        bin1_accuracy = 0.85
        bin2_accuracy = 0.65
        effect_size = calculate_effect_size(bin1_accuracy, bin2_accuracy)
        assert abs(effect_size - 0.20) < 1e-6

    def test_calculate_effect_size_negative(self):
        """Test negative effect size when bin2 > bin1."""
        bin1_accuracy = 0.60
        bin2_accuracy = 0.75
        effect_size = calculate_effect_size(bin1_accuracy, bin2_accuracy)
        assert abs(effect_size - (-0.15)) < 1e-6

    def test_calculate_effect_size_zero(self):
        """Test zero effect size when accuracies are equal."""
        bin1_accuracy = 0.70
        bin2_accuracy = 0.70
        effect_size = calculate_effect_size(bin1_accuracy, bin2_accuracy)
        assert abs(effect_size) < 1e-6


class TestMergeBinsIfNeeded:
    """Test bin merging logic for small sample sizes."""

    def test_no_merge_needed(self):
        """Test when 3+ bin has sufficient samples."""
        bin_counts = {"1": 100, "2": 80, "3+": 60}
        min_samples = 50
        merged_counts, status = merge_bins_if_needed(bin_counts, min_samples)
        assert status == "no_merge"
        assert merged_counts == bin_counts

    def test_merge_needed_and_successful(self):
        """Test when 3+ bin needs merging and succeeds."""
        bin_counts = {"1": 100, "2": 80, "3+": 30}
        min_samples = 50
        merged_counts, status = merge_bins_if_needed(bin_counts, min_samples)
        assert status == "merged"
        assert "3+" not in merged_counts
        assert merged_counts["2+"] == 110  # 80 + 30

    def test_merge_deferred_insufficient(self):
        """Test when even merged bin has insufficient samples."""
        bin_counts = {"1": 100, "2": 10, "3+": 5}
        min_samples = 50
        merged_counts, status = merge_bins_if_needed(bin_counts, min_samples)
        assert status == "deferred"
        assert "2+" not in merged_counts  # Should not create merged bin


class TestPerformThresholdSweep:
    """Test the threshold sweep logic."""

    def test_threshold_sweep_structure(self):
        """Test that sweep returns correct structure for multiple thresholds."""
        # Mock data for testing
        mock_data = {
            1: {"accuracy": 0.9, "count": 100},
            2: {"accuracy": 0.75, "count": 80},
            3: {"accuracy": 0.6, "count": 50},
            4: {"accuracy": 0.5, "count": 40},
            5: {"accuracy": 0.45, "count": 30},
        }

        thresholds = [2, 3, 4]
        results = perform_threshold_sweep(mock_data, thresholds, min_samples=30)

        assert len(results) == len(thresholds)
        for threshold in thresholds:
            assert threshold in results
            assert "p_value" in results[threshold]
            assert "effect_size" in results[threshold]
            assert "bin_status" in results[threshold]
            assert "threshold" in results[threshold]

    def test_threshold_sweep_deferred(self):
        """Test that sweep correctly handles deferred bins."""
        mock_data = {
            1: {"accuracy": 0.9, "count": 100},
            2: {"accuracy": 0.75, "count": 10},
            3: {"accuracy": 0.6, "count": 5},
            4: {"accuracy": 0.5, "count": 3},
        }

        thresholds = [2, 3, 4]
        results = perform_threshold_sweep(mock_data, thresholds, min_samples=50)

        # At least some thresholds should be deferred due to small bin sizes
        deferred_count = sum(
            1 for r in results.values() if r.get("bin_status") == "deferred"
        )
        assert deferred_count >= 1


class TestRunSensitivityAnalysis:
    """Test the full sensitivity analysis pipeline."""

    def test_run_sensitivity_analysis_basic(self):
        """Test basic sensitivity analysis execution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create mock input data
            input_file = tmpdir / "annotated_videokr.csv"
            input_file.write_text(
                "question_id,chain_length,correctness\n"
                "q1,1,1\n"
                "q2,1,1\n"
                "q3,2,1\n"
                "q4,2,0\n"
                "q5,3,0\n"
                "q6,3,0\n"
                "q7,4,0\n"
                "q8,5,0\n"
            )

            output_file = tmpdir / "sensitivity_report.md"

            # Run sensitivity analysis
            results = run_sensitivity_analysis(
                input_data_path=input_file,
                output_path=output_file,
                thresholds=[2, 3, 4],
                min_samples=2,  # Lower for small test data
            )

            # Verify output file exists
            assert output_file.exists()
            assert "Sensitivity Analysis Report" in output_file.read_text()

            # Verify results structure
            assert "thresholds" in results
            assert "summary" in results
            assert len(results["thresholds"]) == 3

    def test_run_sensitivity_analysis_with_mock_data(self):
        """Test with larger mock dataset to ensure proper binning."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create larger mock data with known distribution
            data_lines = ["question_id,chain_length,correctness"]
            for i in range(100):
                data_lines.append(f"q{i},1,1")
            for i in range(100, 180):
                data_lines.append(f"q{i},2,1")
            for i in range(180, 230):
                data_lines.append(f"q{i},3,0")
            for i in range(230, 260):
                data_lines.append(f"q{i},4,0")
            for i in range(260, 280):
                data_lines.append(f"q{i},5,0")

            input_file = tmpdir / "annotated_videokr.csv"
            input_file.write_text("\n".join(data_lines))

            output_file = tmpdir / "sensitivity_report.md"

            results = run_sensitivity_analysis(
                input_data_path=input_file,
                output_path=output_file,
                thresholds=[2, 3, 4],
                min_samples=20,
            )

            assert output_file.exists()
            assert len(results["thresholds"]) == 3

            # Verify that we get reasonable effect sizes
            for threshold, result in results["thresholds"].items():
                assert "effect_size" in result
                assert -1 <= result["effect_size"] <= 1

    def test_run_sensitivity_analysis_deferred_cases(self):
        """Test that analysis correctly handles cases requiring deferral."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create data with very small high-hop bins
            data_lines = ["question_id,chain_length,correctness"]
            for i in range(100):
                data_lines.append(f"q{i},1,1")
            for i in range(100, 150):
                data_lines.append(f"q{i},2,1")
            for i in range(150, 155):
                data_lines.append(f"q{i},3,0")
            for i in range(155, 157):
                data_lines.append(f"q{i},4,0")
            for i in range(157, 158):
                data_lines.append(f"q{i},5,0")

            input_file = tmpdir / "annotated_videokr.csv"
            input_file.write_text("\n".join(data_lines))

            output_file = tmpdir / "sensitivity_report.md"

            results = run_sensitivity_analysis(
                input_data_path=input_file,
                output_path=output_file,
                thresholds=[2, 3, 4],
                min_samples=50,  # High threshold to trigger deferral
            )

            assert output_file.exists()
            
            # At least one threshold should be deferred
            deferred_count = sum(
                1 for r in results["thresholds"].values() 
                if r.get("bin_status") == "deferred"
            )
            assert deferred_count >= 1


class TestIntegrationWithMockedDependencies:
    """Integration tests with mocked external dependencies."""

    @patch("analysis.sensitivity.load_raw_annotated_data")
    @patch("analysis.sensitivity.perform_threshold_sweep")
    @patch("analysis.sensitivity.save_results")
    def test_full_pipeline_with_mocked_components(
        self, mock_save, mock_sweep, mock_load
    ):
        """Test full pipeline with mocked components."""
        # Setup mocks
        mock_load.return_value = {
            1: {"accuracy": 0.9, "count": 100},
            2: {"accuracy": 0.75, "count": 80},
            3: {"accuracy": 0.6, "count": 50},
            4: {"accuracy": 0.5, "count": 40},
            5: {"accuracy": 0.45, "count": 30},
        }
        
        mock_sweep.return_value = {
            2: {"p_value": 0.01, "effect_size": 0.15, "bin_status": "ok"},
            3: {"p_value": 0.03, "effect_size": 0.10, "bin_status": "ok"},
            4: {"p_value": 0.08, "effect_size": 0.05, "bin_status": "ok"},
        }
        
        mock_save.return_value = True

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_file = tmpdir / "annotated_videokr.csv"
            input_file.write_text("question_id,chain_length,correctness\nq1,1,1\n")
            
            output_file = tmpdir / "sensitivity_report.md"

            results = run_sensitivity_analysis(
                input_data_path=input_file,
                output_path=output_file,
                thresholds=[2, 3, 4],
                min_samples=30,
            )

            # Verify mocks were called
            mock_load.assert_called_once()
            mock_sweep.assert_called_once()
            mock_save.assert_called_once()

            # Verify results structure
            assert "thresholds" in results
            assert len(results["thresholds"]) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
