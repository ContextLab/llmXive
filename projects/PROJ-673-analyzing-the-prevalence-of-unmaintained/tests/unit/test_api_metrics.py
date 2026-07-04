"""
Unit tests for API Metrics Aggregation Utility (T007a).
"""

import json
import tempfile
from pathlib import Path
import pytest

from src.utils.api_metrics import APIMetricsAggregator, calculate_and_report_success_ratio


class TestAPIMetricsAggregator:
    """Tests for the APIMetricsAggregator class."""

    def test_empty_log_file(self, tmp_path):
        """Test aggregation with an empty log file."""
        log_file = tmp_path / "empty.log"
        log_file.write_text("")

        aggregator = APIMetricsAggregator(log_file)
        metrics = aggregator.aggregate()

        assert metrics["total_calls"] == 0
        assert metrics["successful_calls"] == 0
        assert metrics["failed_calls"] == 0
        assert metrics["success_ratio"] == 0.0
        assert metrics["failure_ratio"] == 0.0

    def test_successful_calls_only(self, tmp_path):
        """Test aggregation with only successful calls."""
        log_file = tmp_path / "success.log"
        entries = [
            {"service": "npm_api", "endpoint": "/search", "status_code": 200, "success": True},
            {"service": "npm_api", "endpoint": "/package/express", "status_code": 200, "success": True},
        ]
        log_file.write_text("\n".join(json.dumps(e) for e in entries))

        aggregator = APIMetricsAggregator(log_file)
        metrics = aggregator.aggregate()

        assert metrics["total_calls"] == 2
        assert metrics["successful_calls"] == 2
        assert metrics["failed_calls"] == 0
        assert metrics["success_ratio"] == 1.0
        assert metrics["failure_ratio"] == 0.0

    def test_failed_calls_only(self, tmp_path):
        """Test aggregation with only failed calls."""
        log_file = tmp_path / "fail.log"
        entries = [
            {"service": "github_api", "endpoint": "/repos/user/repo", "status_code": 404, "success": False},
            {"service": "github_api", "endpoint": "/repos/user/another", "status_code": 500, "success": False},
        ]
        log_file.write_text("\n".join(json.dumps(e) for e in entries))

        aggregator = APIMetricsAggregator(log_file)
        metrics = aggregator.aggregate()

        assert metrics["total_calls"] == 2
        assert metrics["successful_calls"] == 0
        assert metrics["failed_calls"] == 2
        assert metrics["success_ratio"] == 0.0
        assert metrics["failure_ratio"] == 1.0

    def test_mixed_calls(self, tmp_path):
        """Test aggregation with mixed success and failure."""
        log_file = tmp_path / "mixed.log"
        entries = [
            {"service": "npm_api", "endpoint": "/search", "status_code": 200, "success": True},
            {"service": "github_api", "endpoint": "/repos/user/repo", "status_code": 404, "success": False},
            {"service": "npm_api", "endpoint": "/package/express", "status_code": 200, "success": True},
            {"service": "github_api", "endpoint": "/repos/user/another", "status_code": 500, "success": False},
            {"service": "npm_api", "endpoint": "/package/lodash", "status_code": 200, "success": True},
        ]
        log_file.write_text("\n".join(json.dumps(e) for e in entries))

        aggregator = APIMetricsAggregator(log_file)
        metrics = aggregator.aggregate()

        assert metrics["total_calls"] == 5
        assert metrics["successful_calls"] == 3
        assert metrics["failed_calls"] == 2
        assert metrics["success_ratio"] == 0.6
        assert metrics["failure_ratio"] == 0.4

    def test_breakdown_by_service(self, tmp_path):
        """Test that breakdown by service is correct."""
        log_file = tmp_path / "breakdown.log"
        entries = [
            {"service": "npm_api", "endpoint": "/search", "status_code": 200, "success": True},
            {"service": "npm_api", "endpoint": "/package/express", "status_code": 404, "success": False},
            {"service": "github_api", "endpoint": "/repos/user/repo", "status_code": 200, "success": True},
            {"service": "github_api", "endpoint": "/repos/user/another", "status_code": 500, "success": False},
            {"service": "github_api", "endpoint": "/repos/user/third", "status_code": 200, "success": True},
        ]
        log_file.write_text("\n".join(json.dumps(e) for e in entries))

        aggregator = APIMetricsAggregator(log_file)
        metrics = aggregator.aggregate()

        assert metrics["breakdown_by_service"]["npm_api"]["total"] == 2
        assert metrics["breakdown_by_service"]["npm_api"]["success"] == 1
        assert metrics["breakdown_by_service"]["npm_api"]["failure"] == 1

        assert metrics["breakdown_by_service"]["github_api"]["total"] == 3
        assert metrics["breakdown_by_service"]["github_api"]["success"] == 2
        assert metrics["breakdown_by_service"]["github_api"]["failure"] == 1

    def test_breakdown_by_endpoint(self, tmp_path):
        """Test that breakdown by endpoint is correct."""
        log_file = tmp_path / "endpoint.log"
        entries = [
            {"service": "npm_api", "endpoint": "/search", "status_code": 200, "success": True},
            {"service": "npm_api", "endpoint": "/search", "status_code": 200, "success": True},
            {"service": "npm_api", "endpoint": "/package/express", "status_code": 404, "success": False},
        ]
        log_file.write_text("\n".join(json.dumps(e) for e in entries))

        aggregator = APIMetricsAggregator(log_file)
        metrics = aggregator.aggregate()

        assert metrics["breakdown_by_endpoint"]["/search"]["total"] == 2
        assert metrics["breakdown_by_endpoint"]["/search"]["success"] == 2
        assert metrics["breakdown_by_endpoint"]["/search"]["failure"] == 0

        assert metrics["breakdown_by_endpoint"]["/package/express"]["total"] == 1
        assert metrics["breakdown_by_endpoint"]["/package/express"]["success"] == 0
        assert metrics["breakdown_by_endpoint"]["/package/express"]["failure"] == 1

    def test_status_code_detection(self, tmp_path):
        """Test that status codes are correctly interpreted."""
        log_file = tmp_path / "status.log"
        entries = [
            {"service": "api", "endpoint": "/ok", "status_code": 200},  # Success
            {"service": "api", "endpoint": "/created", "status_code": 201},  # Success
            {"service": "api", "endpoint": "/not_found", "status_code": 404},  # Failure
            {"service": "api", "endpoint": "/error", "status_code": 500},  # Failure
        ]
        log_file.write_text("\n".join(json.dumps(e) for e in entries))

        aggregator = APIMetricsAggregator(log_file)
        metrics = aggregator.aggregate()

        assert metrics["successful_calls"] == 2
        assert metrics["failed_calls"] == 2

    def test_log_level_detection(self, tmp_path):
        """Test that log levels are correctly interpreted."""
        log_file = tmp_path / "level.log"
        entries = [
            {"service": "api", "endpoint": "/info", "level": "INFO"},  # Success
            {"service": "api", "endpoint": "/warning", "level": "WARNING"},  # Failure
            {"service": "api", "endpoint": "/error", "level": "ERROR"},  # Failure
            {"service": "api", "endpoint": "/debug", "level": "DEBUG"},  # Success (default)
        ]
        log_file.write_text("\n".join(json.dumps(e) for e in entries))

        aggregator = APIMetricsAggregator(log_file)
        metrics = aggregator.aggregate()

        # INFO and DEBUG are successes, WARNING and ERROR are failures
        assert metrics["successful_calls"] == 2
        assert metrics["failed_calls"] == 2

    def test_save_report(self, tmp_path):
        """Test that the report is saved correctly."""
        log_file = tmp_path / "input.log"
        entries = [
            {"service": "npm_api", "endpoint": "/search", "status_code": 200, "success": True},
        ]
        log_file.write_text("\n".join(json.dumps(e) for e in entries))

        output_file = tmp_path / "output.json"
        aggregator = APIMetricsAggregator(log_file)
        aggregator.aggregate()
        aggregator.save_report(output_file)

        assert output_file.exists()
        with open(output_file, 'r') as f:
            saved_metrics = json.load(f)

        assert saved_metrics["total_calls"] == 1
        assert saved_metrics["success_ratio"] == 1.0

    def test_nonexistent_log_file(self, tmp_path):
        """Test behavior when log file doesn't exist."""
        log_file = tmp_path / "nonexistent.log"
        aggregator = APIMetricsAggregator(log_file)
        metrics = aggregator.aggregate()

        assert metrics["total_calls"] == 0

    def test_invalid_json_handling(self, tmp_path):
        """Test that invalid JSON lines are skipped."""
        log_file = tmp_path / "invalid.log"
        entries = [
            '{"service": "api", "status_code": 200}',
            'not valid json',
            '{"service": "api", "status_code": 404}',
        ]
        log_file.write_text("\n".join(entries))

        aggregator = APIMetricsAggregator(log_file)
        metrics = aggregator.aggregate()

        # Should have processed 2 valid entries
        assert metrics["total_calls"] == 2


class TestCalculateAndReportSuccessRatio:
    """Tests for the convenience function."""

    def test_function_returns_metrics(self, tmp_path):
        """Test that the function returns the correct metrics."""
        log_file = tmp_path / "test.log"
        entries = [
            {"service": "api", "status_code": 200, "success": True},
            {"service": "api", "status_code": 404, "success": False},
        ]
        log_file.write_text("\n".join(json.dumps(e) for e in entries))

        metrics = calculate_and_report_success_ratio(log_file)

        assert metrics["total_calls"] == 2
        assert metrics["success_ratio"] == 0.5

    def test_function_saves_to_file(self, tmp_path):
        """Test that the function saves to the specified file."""
        log_file = tmp_path / "test.log"
        output_file = tmp_path / "output.json"
        entries = [
            {"service": "api", "status_code": 200, "success": True},
        ]
        log_file.write_text("\n".join(json.dumps(e) for e in entries))

        calculate_and_report_success_ratio(log_file, output_file)

        assert output_file.exists()
        with open(output_file, 'r') as f:
            saved_metrics = json.load(f)

        assert saved_metrics["success_ratio"] == 1.0