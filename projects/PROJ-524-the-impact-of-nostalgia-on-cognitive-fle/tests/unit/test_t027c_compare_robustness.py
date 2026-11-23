import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from task_t027c_compare_robustness import (
    load_report,
    compare_metrics,
    compare_reports,
    main,
    PRIMARY_REPORT_PATH,
    ROBUSTNESS_REPORT_PATH,
    OUTPUT_PATH
)

class TestLoadReport:
    def test_load_existing_report(self, tmp_path):
        report_data = {"metrics": {"test": 1}}
        report_file = tmp_path / "report.json"
        with open(report_file, "w") as f:
            json.dump(report_data, f)

        with patch("task_t027c_compare_robustness.load_json", return_value=report_data):
            result = load_report(report_file)
            assert result == report_data

    def test_load_missing_report(self, caplog):
        result = load_report(Path("/nonexistent/file.json"))
        assert result is None
        assert "not found" in caplog.text.lower()

    def test_load_invalid_json(self, tmp_path, caplog):
        report_file = tmp_path / "invalid.json"
        report_file.write_text("not valid json")

        with patch("task_t027c_compare_robustness.load_json", side_effect=ValueError("Invalid JSON")):
            result = load_report(report_file)
            assert result is None
            assert "failed to load" in caplog.text.lower()

class TestCompareMetrics:
    def test_both_missing(self):
        result = compare_metrics(None, None, "test_metric")
        assert result["status"] == "both_missing"
        assert result["difference"] is None

    def test_primary_missing(self):
        result = compare_metrics(None, 0.5, "test_metric")
        assert result["status"] == "primary_missing"

    def test_robustness_missing(self):
        result = compare_metrics(0.5, None, "test_metric")
        assert result["status"] == "robustness_missing"

    def test_significance_change_p_value(self):
        # Primary is significant (p < 0.05), Robustness is not
        result = compare_metrics(0.04, 0.06, "p_value")
        assert result["significance_changed"] is True
        assert result["status"] == "significant_change"
        assert abs(result["difference"]) == 0.02

    def test_no_significance_change_p_value(self):
        # Both significant
        result = compare_metrics(0.01, 0.02, "p_value")
        assert result["significance_changed"] is False
        assert result["status"] == "stable"

    def test_effect_size_interpretation_change(self):
        # Primary: small effect, Robustness: medium effect
        result = compare_metrics(0.1, 0.4, "cohens_d")
        assert result["effect_size_changed"] is True
        assert result["status"] == "interpretation_change"

    def test_effect_size_stable(self):
        # Both large effect
        result = compare_metrics(0.8, 0.9, "cohens_d")
        assert result["effect_size_changed"] is False
        assert result["status"] == "stable"

class TestCompareReports:
    def test_full_comparison(self):
        primary = {
            "metrics": {
                "perseverative_errors": {"p_value": 0.03, "cohens_d": 0.5},
                "categories_completed": {"p_value": 0.10, "cohens_d": 0.2}
            }
        }
        robust = {
            "metrics": {
                "perseverative_errors": {"p_value": 0.08, "cohens_d": 0.4}, # Sig change
                "categories_completed": {"p_value": 0.12, "cohens_d": 0.2}  # Stable
            }
        }

        result = compare_reports(primary, robust)

        # Check overall stability
        assert result["summary"]["overall_stability"] == "mostly_stable"

        # Check specific metric changes
        assert result["metrics"]["perseverative_errors"]["p_value"]["significance_changed"] is True
        assert result["metrics"]["categories_completed"]["p_value"]["significance_changed"] is False

class TestMain:
    def test_main_success(self, tmp_path, caplog):
        # Setup temp paths
        with patch("task_t027c_compare_robustness.PRIMARY_REPORT_PATH", tmp_path / "primary.json"), \
             patch("task_t027c_compare_robustness.ROBUSTNESS_REPORT_PATH", tmp_path / "robust.json"), \
             patch("task_t027c_compare_robustness.OUTPUT_PATH", tmp_path / "output.json"):

            primary_data = {"metrics": {"test": {"p_value": 0.05, "cohens_d": 0.1}}}
            robust_data = {"metrics": {"test": {"p_value": 0.06, "cohens_d": 0.1}}}

            with open(tmp_path / "primary.json", "w") as f:
                json.dump(primary_data, f)
            with open(tmp_path / "robust.json", "w") as f:
                json.dump(robust_data, f)

            with patch("task_t027c_compare_robustness.save_json") as mock_save:
                exit_code = main()
                assert exit_code == 0
                mock_save.assert_called_once()

    def test_main_missing_primary(self, tmp_path, caplog):
        with patch("task_t027c_compare_robustness.PRIMARY_REPORT_PATH", tmp_path / "primary.json"), \
             patch("task_t027c_compare_robustness.ROBUSTNESS_REPORT_PATH", tmp_path / "robust.json"):

            # Create robust but not primary
            with open(tmp_path / "robust.json", "w") as f:
                json.dump({}, f)

            exit_code = main()
            assert exit_code == 1
            assert "Primary statistical report missing" in caplog.text

    def test_main_missing_robustness(self, tmp_path, caplog):
        with patch("task_t027c_compare_robustness.PRIMARY_REPORT_PATH", tmp_path / "primary.json"), \
             patch("task_t027c_compare_robustness.ROBUSTNESS_REPORT_PATH", tmp_path / "robust.json"):

            # Create primary but not robust
            with open(tmp_path / "primary.json", "w") as f:
                json.dump({}, f)

            exit_code = main()
            assert exit_code == 1
            assert "Robustness report missing" in caplog.text