"""
Unit tests for the contradiction_analyzer module.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add code root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.contradiction_analyzer import (
    load_contradiction_log,
    calculate_contradiction_rate,
    verify_contradiction_rate,
    flag_study_if_high_rate,
    run_contradiction_analysis,
    StudyFlagError
)

class TestLoadContradictionLog:
    def test_load_existing_log(self, tmp_path):
        log_data = {
            "contradictions": [{"id": 1, "reason": "overlap"}],
            "total_scenes": 10,
            "contradiction_count": 1
        }
        log_file = tmp_path / "contradiction_log.json"
        with open(log_file, 'w') as f:
            json.dump(log_data, f)
        
        result = load_contradiction_log(str(log_file))
        assert result == log_data

    def test_load_missing_log_returns_default(self, tmp_path):
        # If file doesn't exist, it should return empty structure
        # (Note: current implementation returns empty dict if not found in load_contradiction_log
        # but run_contradiction_analysis expects specific keys. 
        # Let's verify the behavior matches the implementation.)
        fake_path = tmp_path / "nonexistent.json"
        # The implementation currently returns an empty dict if not found?
        # Actually, looking at the code: if not exists, returns {"contradictions": [], ...}
        # Let's verify that logic is in place or test the specific behavior.
        # Re-reading code: if not exists: return {"contradictions": [], "total_scenes": 0, ...}
        result = load_contradiction_log(str(fake_path))
        assert "total_scenes" in result
        assert result["total_scenes"] == 0

class TestCalculateContradictionRate:
    def test_rate_calculation(self):
        data = {"total_scenes": 100, "contradiction_count": 5}
        total, count, rate = calculate_contradiction_rate(data)
        assert total == 100
        assert count == 5
        assert rate == 5.0

    def test_zero_scenes_no_division_error(self):
        data = {"total_scenes": 0, "contradiction_count": 0}
        total, count, rate = calculate_contradiction_rate(data)
        assert rate == 0.0

    def test_partial_rate(self):
        data = {"total_scenes": 10, "contradiction_count": 1}
        _, _, rate = calculate_contradiction_rate(data)
        assert abs(rate - 10.0) < 0.001

class TestVerifyContradictionRate:
    def test_valid_rate(self):
        assert verify_contradiction_rate(4.9) is True
        assert verify_contradiction_rate(0.0) is True

    def test_invalid_rate(self):
        assert verify_contradiction_rate(5.0) is False
        assert verify_contradiction_rate(6.0) is False

    def test_custom_threshold(self):
        assert verify_contradiction_rate(4.9, threshold=5.0) is True
        assert verify_contradiction_rate(4.9, threshold=4.0) is False

class TestFlagStudyIfHighRate:
    def test_no_flag_on_valid_rate(self):
        try:
            flag_study_if_high_rate(4.0)
        except StudyFlagError:
            pytest.fail("StudyFlagError raised unexpectedly")

    def test_raises_on_high_rate(self):
        with pytest.raises(StudyFlagError):
            flag_study_if_high_rate(6.0)

    def test_raises_on_threshold_boundary(self):
        # SC-004 says < 5%. So 5.0 should be flagged.
        with pytest.raises(StudyFlagError):
            flag_study_if_high_rate(5.0)

class TestRunContradictionAnalysis:
    def test_success_case(self, tmp_path):
        log_data = {
            "total_scenes": 100,
            "contradiction_count": 2
        }
        log_file = tmp_path / "contradiction_log.json"
        with open(log_file, 'w') as f:
            json.dump(log_data, f)
        
        result = run_contradiction_analysis(str(log_file))
        assert result["is_within_limit"] is True
        assert result["status"] == "PASS"
        assert result["contradiction_rate_percentage"] == 2.0

    def test_failure_case(self, tmp_path):
        log_data = {
            "total_scenes": 100,
            "contradiction_count": 10
        }
        log_file = tmp_path / "contradiction_log.json"
        with open(log_file, 'w') as f:
            json.dump(log_data, f)
        
        with pytest.raises(StudyFlagError):
            run_contradiction_analysis(str(log_file))