"""
Contract tests for schema validators.
"""
import pytest
import json
import tempfile
import os
from datetime import datetime
from data.models import VideoClip, MetricRecord, AnalysisResult
from contracts.dataset_validator import DatasetValidator
from contracts.metrics_validator import MetricsValidator
from contracts.analysis_validator import AnalysisValidator


class TestDatasetValidator:
    def test_valid_video_clip(self):
        clip = VideoClip(
            clip_id="test_001",
            source_dataset="davis",
            file_path="/data/test.mp4",
            duration_frames=30,
            width=640,
            height=480,
            fps=30.0,
            motion_category="static",
            mask_path="/data/mask.png",
            flow_path="/data/flow.npy",
            created_at=datetime.now().isoformat(),
        )
        result = DatasetValidator.validate_video_clip(clip)
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_invalid_motion_category(self):
        clip = VideoClip(
            clip_id="test_002",
            source_dataset="davis",
            file_path="/data/test.mp4",
            duration_frames=30,
            width=640,
            height=480,
            fps=30.0,
            motion_category="invalid_cat",
            mask_path="/data/mask.png",
            flow_path="/data/flow.npy",
            created_at=datetime.now().isoformat(),
        )
        result = DatasetValidator.validate_video_clip(clip)
        assert result["valid"] is False
        assert any("Invalid motion_category" in e for e in result["errors"])

    def test_missing_required_field(self):
        clip = VideoClip(
            clip_id="test_003",
            source_dataset="davis",
            file_path="/data/test.mp4",
            duration_frames=30,
            width=640,
            height=480,
            fps=30.0,
            motion_category="static",
            mask_path=None,
            flow_path="/data/flow.npy",
            created_at=datetime.now().isoformat(),
        )
        result = DatasetValidator.validate_video_clip(clip)
        assert result["valid"] is False
        assert any("mask_path" in e for e in result["errors"])


class TestMetricsValidator:
    def test_valid_metric_record(self):
        record = MetricRecord(
            clip_id="test_001",
            method="baseline",
            timestamp=datetime.now().isoformat(),
            inference_time_s=1.5,
            peak_memory_mb=512.0,
            ssim_score=0.95,
            bss_score=0.92,
            flow_normalized_ssim=0.94,
            avg_flow_magnitude=2.5,
            invalid_flow_count=0,
            motion_category="static",
        )
        result = MetricsValidator.validate_metric_record(record)
        assert result["valid"] is True

    def test_ssim_out_of_range(self):
        record = MetricRecord(
            clip_id="test_001",
            method="baseline",
            timestamp=datetime.now().isoformat(),
            inference_time_s=1.5,
            peak_memory_mb=512.0,
            ssim_score=1.5,
            bss_score=0.92,
            flow_normalized_ssim=0.94,
            avg_flow_magnitude=2.5,
            invalid_flow_count=0,
            motion_category="static",
        )
        result = MetricsValidator.validate_metric_record(record)
        assert result["valid"] is False
        assert any("ssim_score" in e and "range" in e for e in result["errors"])

    def test_invalid_method(self):
        record = MetricRecord(
            clip_id="test_001",
            method="unknown_method",
            timestamp=datetime.now().isoformat(),
            inference_time_s=1.5,
            peak_memory_mb=512.0,
            ssim_score=0.95,
            bss_score=0.92,
            flow_normalized_ssim=0.94,
            avg_flow_magnitude=2.5,
            invalid_flow_count=0,
            motion_category="static",
        )
        result = MetricsValidator.validate_metric_record(record)
        assert result["valid"] is False


class TestAnalysisValidator:
    def test_valid_analysis_result(self):
        result = AnalysisResult(
            analysis_id="analysis_001",
            timestamp=datetime.now().isoformat(),
            method_comparison="baseline_vs_flow",
            ks_test_p_value=0.03,
            ks_test_statistic=0.45,
            change_point_threshold=5.0,
            change_point_confidence=0.95,
            memory_reduction_pct=25.5,
            summary_text="Significant improvement observed.",
            cutoffs_tested=[0.01, 0.05, 0.1],
        )
        valid, errors = AnalysisValidator.validate_analysis_result(result)["valid"], AnalysisValidator.validate_analysis_result(result)["errors"]
        assert valid is True
        assert len(errors) == 0

    def test_p_value_out_of_range(self):
        result = AnalysisResult(
            analysis_id="analysis_002",
            timestamp=datetime.now().isoformat(),
            method_comparison="baseline_vs_flow",
            ks_test_p_value=1.5,
            ks_test_statistic=0.45,
            change_point_threshold=5.0,
            change_point_confidence=0.95,
            memory_reduction_pct=25.5,
            summary_text="Test.",
            cutoffs_tested=[0.01],
        )
        res = AnalysisValidator.validate_analysis_result(result)
        assert res["valid"] is False
        assert any("ks_test_p_value" in e for e in res["errors"])
