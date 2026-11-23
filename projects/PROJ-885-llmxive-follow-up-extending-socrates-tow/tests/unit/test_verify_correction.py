"""
Unit tests for the verify_correction.py script.
"""
import json
import pytest
from pathlib import Path
import sys
import tempfile
import shutil

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analysis.verify_correction import (
    load_json_file,
    load_scope_adjustments,
    load_memory_profile,
    calculate_expected_factor,
    verify_correction
)

class TestLoadJsonFile:
    def test_load_existing_json(self, tmp_path):
        test_file = tmp_path / "test.json"
        test_data = {"key": "value"}
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        result = load_json_file(test_file)
        assert result == test_data

    def test_load_nonexistent_json(self, tmp_path):
        result = load_json_file(tmp_path / "nonexistent.json")
        assert result is None

    def test_load_invalid_json(self, tmp_path):
        test_file = tmp_path / "invalid.json"
        with open(test_file, 'w') as f:
            f.write("not valid json")
        
        result = load_json_file(test_file)
        assert result is None

class TestLoadScopeAdjustments:
    def test_load_valid_list(self, tmp_path):
        test_file = tmp_path / "scope.json"
        test_data = [{"model": "m1"}, {"model": "m2"}]
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        result = load_scope_adjustments(test_file)
        assert len(result) == 2

    def test_load_nonexistent_file(self, tmp_path):
        result = load_scope_adjustments(tmp_path / "nonexistent.json")
        assert result == []

    def test_load_non_list_json(self, tmp_path):
        test_file = tmp_path / "scope.json"
        with open(test_file, 'w') as f:
            json.dump({"not": "a list"}, f)
        
        result = load_scope_adjustments(test_file)
        assert result == []

class TestLoadMemoryProfile:
    def test_load_valid_memory_profile(self, tmp_path):
        test_file = tmp_path / "memory.json"
        test_data = {"active_models": ["m1", "m2"], "excluded_models": ["m3"]}
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        result = load_memory_profile(test_file)
        assert result == test_data

    def test_load_nonexistent_file(self, tmp_path):
        result = load_memory_profile(tmp_path / "nonexistent.json")
        assert result == {"active_models": []}

class TestCalculateExpectedFactor:
    def test_no_exclusions(self):
        scope_adjustments = []
        memory_profile = {"active_models": []}
        expected = 1.0 / 8.0
        result = calculate_expected_factor(scope_adjustments, memory_profile)
        assert abs(result - expected) < 1e-6

    def test_one_exclusion(self):
        scope_adjustments = [{"model": "m1"}]
        memory_profile = {"active_models": []}
        expected = 1.0 / 7.0
        result = calculate_expected_factor(scope_adjustments, memory_profile)
        assert abs(result - expected) < 1e-6

    def test_memory_exclusion(self):
        scope_adjustments = []
        memory_profile = {"excluded_models": ["m1", "m2"]}
        expected = 1.0 / 6.0
        result = calculate_expected_factor(scope_adjustments, memory_profile)
        assert abs(result - expected) < 1e-6

    def test_zero_actual_models(self):
        scope_adjustments = [{"model": f"m{i}"} for i in range(8)]
        memory_profile = {"active_models": []}
        result = calculate_expected_factor(scope_adjustments, memory_profile)
        assert result == 0.0

class TestVerifyCorrection:
    def test_match(self):
        stats_report = {"holm_bonferroni_factor": 0.125}
        expected_factor = 0.125
        result = verify_correction(stats_report, expected_factor)
        assert result["match"] is True

    def test_mismatch(self):
        stats_report = {"holm_bonferroni_factor": 0.125}
        expected_factor = 0.142857  # 1/7
        result = verify_correction(stats_report, expected_factor)
        assert result["match"] is False

    def test_missing_factor(self):
        stats_report = {}
        expected_factor = 0.125
        result = verify_correction(stats_report, expected_factor)
        assert result["match"] is False
        assert "error" in result