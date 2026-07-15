"""
Unit tests for the reporter module.
"""
import os
import json
import tempfile
from pathlib import Path
import pytest

import numpy as np
import pandas as pd

from code.analysis.reporter import (
    aggregate_metrics_to_records,
    generate_baseline_report,
    generate_comparative_report
)
from code.data.models import MetricRecord


class TestAggregateMetricsToRecords:
    def test_valid_metrics_conversion(self):
        """Test that valid metric dicts are converted to MetricRecord objects."""
        metrics = [
            {
                "clip_id": "clip_001",
                "inference_time_s": 1.5,
                "peak_memory_mb": 2048.0,
                "bss_score": 0.95,
                "flow_normalized_ssim": 0.92,
                "flow_magnitude_mean": 2.1,
                "invalid_flow_count": 0
            }
        ]

        records = aggregate_metrics_to_records(metrics, "test_run", "baseline")

        assert len(records) == 1
        assert isinstance(records[0], MetricRecord)
        assert records[0].clip_id == "clip_001"
        assert records[0].run_id == "test_run"
        assert records[0].run_type == "baseline"

    def test_invalid_metrics_skipped(self):
        """Test that invalid metric dicts are skipped."""
        metrics = [
            {
                "clip_id": "clip_001",
                "inference_time_s": "not_a_number",  # Invalid type
                "peak_memory_mb": 2048.0,
                "bss_score": 0.95,
                "flow_normalized_ssim": 0.92,
                "flow_magnitude_mean": 2.1,
                "invalid_flow_count": 0
            },
            {
                "clip_id": "clip_002",
                "inference_time_s": 1.5,
                "peak_memory_mb": 2048.0,
                "bss_score": 0.95,
                "flow_normalized_ssim": 0.92,
                "flow_magnitude_mean": 2.1,
                "invalid_flow_count": 0
            }
        ]

        records = aggregate_metrics_to_records(metrics, "test_run", "baseline")

        # First record should be skipped, second should be valid
        assert len(records) == 1
        assert records[0].clip_id == "clip_002"


class TestGenerateBaselineReport:
    def test_generates_json_and_parquet(self, tmp_path):
        """Test that the function creates both JSON and Parquet files."""
        metrics = [
            {
                "clip_id": "clip_001",
                "inference_time_s": 1.5,
                "peak_memory_mb": 2048.0,
                "bss_score": 0.95,
                "flow_normalized_ssim": 0.92,
                "flow_magnitude_mean": 2.1,
                "invalid_flow_count": 0
            }
        ]

        result = generate_baseline_report(metrics, output_dir=tmp_path, run_id="test_001")

        assert "json_path" in result
        assert "parquet_path" in result
        assert os.path.exists(result["json_path"])
        assert os.path.exists(result["parquet_path"])

    def test_json_content_valid(self, tmp_path):
        """Test that the JSON file contains expected structure."""
        metrics = [
            {
                "clip_id": "clip_001",
                "inference_time_s": 1.5,
                "peak_memory_mb": 2048.0,
                "bss_score": 0.95,
                "flow_normalized_ssim": 0.92,
                "flow_magnitude_mean": 2.1,
                "invalid_flow_count": 0
            }
        ]

        result = generate_baseline_report(metrics, output_dir=tmp_path, run_id="test_002")

        with open(result["json_path"], "r") as f:
            data = json.load(f)

        assert "run_id" in data
        assert "run_type" in data
        assert "stats" in data
        assert data["run_type"] == "baseline"
        assert "inference_time_s" in data["stats"]

    def test_empty_metrics_handled(self, tmp_path):
        """Test that empty metrics list generates a valid empty report."""
        result = generate_baseline_report([], output_dir=tmp_path, run_id="test_003")

        assert os.path.exists(result["json_path"])
        with open(result["json_path"], "r") as f:
            data = json.load(f)
        assert data["clip_count"] == 0


class TestGenerateComparativeReport:
    def test_generates_comparative_report(self, tmp_path):
        """Test generation of comparative report."""
        baseline_metrics = [
            {
                "clip_id": "clip_001",
                "inference_time_s": 1.5,
                "peak_memory_mb": 2048.0,
                "bss_score": 0.95,
                "flow_normalized_ssim": 0.92,
                "flow_magnitude_mean": 2.1,
                "invalid_flow_count": 0
            }
        ]
        flow_metrics = [
            {
                "clip_id": "clip_001",
                "inference_time_s": 1.2,
                "peak_memory_mb": 1024.0,
                "bss_score": 0.90,
                "flow_normalized_ssim": 0.88,
                "flow_magnitude_mean": 2.1,
                "invalid_flow_count": 0
            }
        ]

        result = generate_comparative_report(
            baseline_metrics,
            flow_metrics,
            output_dir=tmp_path,
            run_id="test_004"
        )

        assert os.path.exists(result["json_path"])
        with open(result["json_path"], "r") as f:
            data = json.load(f)

        assert "comparison_stats" in data
        assert "memory_reduction_pct" in data["comparison_stats"]