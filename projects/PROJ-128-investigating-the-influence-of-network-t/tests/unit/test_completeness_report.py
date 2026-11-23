import os
import json
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the functions to test
# We need to handle the import path correctly
try:
    from analysis.completeness_report import (
        load_exclusion_log,
        load_structural_metrics,
        calculate_completeness_report,
        main
    )
except ImportError:
    # Fallback for test environment
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from analysis.completeness_report import (
        load_exclusion_log,
        load_structural_metrics,
        calculate_completeness_report,
        main
    )


class TestLoadExclusionLog:
    def test_load_valid_json(self, tmp_path):
        log_file = tmp_path / "exclusion_log.json"
        data = [{"subject_id": "1", "reason": "convergence failure"}, {"subject_id": "2", "reason": "sparsity >90%"}]
        log_file.write_text(json.dumps(data))
        
        result = load_exclusion_log(str(log_file))
        assert len(result) == 2
        assert result[0]["subject_id"] == "1"
        assert result[1]["reason"] == "sparsity >90%"

    def test_load_missing_file(self, tmp_path):
        result = load_exclusion_log(str(tmp_path / "nonexistent.json"))
        assert result == []

    def test_load_invalid_json(self, tmp_path):
        log_file = tmp_path / "invalid.json"
        log_file.write_text("not valid json")
        
        result = load_exclusion_log(str(log_file))
        assert result == []


class TestLoadStructuralMetrics:
    def test_load_valid_csv(self, tmp_path):
        csv_file = tmp_path / "metrics.csv"
        df = pd.DataFrame({"subject_id": ["1", "2"], "global_efficiency": [0.5, 0.6]})
        df.to_csv(csv_file, index=False)
        
        result = load_structural_metrics(str(csv_file))
        assert len(result) == 2
        assert "global_efficiency" in result.columns

    def test_load_missing_file(self, tmp_path):
        result = load_structural_metrics(str(tmp_path / "nonexistent.csv"))
        assert result.empty

    def test_load_empty_csv(self, tmp_path):
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("")
        
        result = load_structural_metrics(str(csv_file))
        assert result.empty


class TestCalculateCompletenessReport:
    def test_basic_calculation(self):
        exclusion_log = [
            {"subject_id": "1", "reason": "convergence failure"},
            {"subject_id": "2", "reason": "sparsity >90%"}
        ]
        metrics_df = pd.DataFrame({
            "subject_id": ["3", "4", "5"],
            "metric": [1.0, 2.0, 3.0]
        })
        
        report = calculate_completeness_report(exclusion_log, metrics_df, 5)
        
        assert report["total_cohort_size"] == 5
        assert report["processed_count"] == 3
        assert report["excluded_count"] == 2
        assert report["completion_percentage"] == 60.0
        assert report["exclusion_percentage"] == 40.0
        assert report["exclusion_reasons"]["convergence failure"] == 1
        assert report["exclusion_reasons"]["sparsity >90%"] == 1

    def test_zero_cohort_size(self):
        exclusion_log = []
        metrics_df = pd.DataFrame()
        
        report = calculate_completeness_report(exclusion_log, metrics_df, 0)
        
        assert report["completion_percentage"] == 0.0
        assert report["exclusion_percentage"] == 0.0

    def test_no_exclusions(self):
        exclusion_log = []
        metrics_df = pd.DataFrame({"subject_id": ["1", "2"]})
        
        report = calculate_completeness_report(exclusion_log, metrics_df, 2)
        
        assert report["excluded_count"] == 0
        assert report["completion_percentage"] == 100.0
        assert len(report["exclusion_reasons"]) == 0

    def test_no_processed(self):
        exclusion_log = [{"subject_id": "1", "reason": "error"}]
        metrics_df = pd.DataFrame()
        
        report = calculate_completeness_report(exclusion_log, metrics_df, 1)
        
        assert report["processed_count"] == 0
        assert report["completion_percentage"] == 0.0


class TestMain:
    @patch('analysis.completeness_report.get_config_dict')
    @patch('analysis.completeness_report.load_exclusion_log')
    @patch('analysis.completeness_report.load_structural_metrics')
    @patch('builtins.open')
    def test_main_runs_successfully(self, mock_open, mock_load_metrics, mock_load_log, mock_config, tmp_path):
        # Setup mocks
        mock_config.return_value = {"PROJECT_ROOT": str(tmp_path)}
        mock_load_log.return_value = [{"subject_id": "1", "reason": "error"}]
        mock_load_metrics.return_value = pd.DataFrame({"subject_id": ["2"]})
        
        # Create necessary directories
        (tmp_path / "data" / "logs").mkdir(parents=True)
        (tmp_path / "data" / "processed").mkdir(parents=True)
        
        # Run main
        result = main()
        
        # Verify output was created
        output_file = tmp_path / "data" / "processed" / "completeness_report.json"
        assert output_file.exists()
        
        # Verify result structure
        assert "total_cohort_size" in result
        assert "completion_percentage" in result