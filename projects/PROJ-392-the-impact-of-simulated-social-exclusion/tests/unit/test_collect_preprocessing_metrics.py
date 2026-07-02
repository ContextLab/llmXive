"""
Unit tests for code/analysis/collect_preprocessing_metrics.py (Task T016).
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Adjust import path based on project structure
# Assuming tests are at tests/unit/ and code is at code/
import sys
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from code.analysis.collect_preprocessing_metrics import (
    calculate_completion_rate,
    generate_flags,
    MIN_SUBJECTS_PER_GROUP,
    TARGET_COMPLETION_RATE
)


class TestCompletionRate:
    def test_normal_case(self):
        # 90 processed, 10 failed -> 90%
        rate = calculate_completion_rate(90, 10, 0)
        assert rate == 0.90

    def test_zero_attempted(self):
        # Avoid division by zero
        rate = calculate_completion_rate(0, 0, 0)
        assert rate == 0.0

    def test_all_skipped(self):
        # 0 processed, 0 failed, 10 skipped -> 0%
        rate = calculate_completion_rate(0, 0, 10)
        assert rate == 0.0

    def test_all_processed(self):
        rate = calculate_completion_rate(100, 0, 0)
        assert rate == 1.0


class TestGenerateFlags:
    def test_exploratory_small_sample(self):
        # N=15 per group -> exploratory
        counts = {"excluded": 15, "included": 15}
        flags = generate_flags(counts, 0.95)
        
        assert flags["exploratory"] is True
        assert len(flags["recommendations"]) > 0
        assert "exploratory" in flags["recommendations"][0].lower()

    def test_not_exploratory_large_sample(self):
        # N=30 per group -> not exploratory
        counts = {"excluded": 30, "included": 30}
        flags = generate_flags(counts, 0.95)
        
        assert flags["exploratory"] is False
        # Should not have sample size recommendation
        sample_recs = [r for r in flags["recommendations"] if "sample" in r.lower()]
        assert len(sample_recs) == 0

    def test_target_not_met(self):
        # Rate < 90%
        counts = {"excluded": 30, "included": 30}
        flags = generate_flags(counts, 0.80)
        
        assert flags["target_met"] is False
        assert any("completion rate" in r.lower() for r in flags["recommendations"])

    def test_target_met(self):
        # Rate >= 90%
        counts = {"excluded": 30, "included": 30}
        flags = generate_flags(counts, 0.95)
        
        assert flags["target_met"] is True


class TestIntegrationMock:
    @patch("code.analysis.collect_preprocessing_metrics.PROJECT_ROOT")
    @patch("code.analysis.collect_preprocessing_metrics.METRICS_FILE")
    @patch("code.analysis.collect_preprocessing_metrics.UNIFIED_METADATA_FILE")
    def test_collect_metrics_integration(self, mock_meta_file, mock_metrics_file, mock_root):
        # Setup mocks
        mock_root.__truediv__ = lambda self, other: Path(f"/fake/{other}")
        mock_metrics_file.exists.return_value = False
        mock_meta_file.exists.return_value = False
        
        # We can't easily test the full file system walk without real data,
        # but we can test the logic flow when files are missing
        from code.analysis.collect_preprocessing_metrics import collect_metrics
        
        # This should not raise an exception even if files are missing
        metrics = collect_metrics()
        
        assert "summary" in metrics
        assert "flags" in metrics
        assert metrics["flags"]["exploratory"] is True # Default when meta missing