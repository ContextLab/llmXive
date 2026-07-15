"""
Unit tests for code/01_download_and_filter.py
"""
import pytest
import pandas as pd
from pathlib import Path
import csv
import json
import tempfile
import os

# Import the module functions
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from code_01_download_and_filter import (
    has_valid_score,
    is_eligible,
    filter_eligible_subjects,
    limit_subjects,
    write_eligible_csv,
    write_excluded_log,
    write_status
)


class TestHasValidScore:
    def test_valid_score(self):
        row = {"MMSE": 28.0, "MOCA": 25.0}
        assert has_valid_score(row, ["MMSE"]) is True
        assert has_valid_score(row, ["MOCA"]) is True

    def test_invalid_score(self):
        row = {"MMSE": None, "MOCA": ""}
        assert has_valid_score(row, ["MMSE"]) is False
        assert has_valid_score(row, ["MOCA"]) is False

    def test_string_score(self):
        row = {"MMSE": "25"}
        assert has_valid_score(row, ["MMSE"]) is True


class TestIsEligible:
    def test_eligible_mmse(self):
        row = {
            "participant_id": "sub-01",
            "MMSE": 28.0,
            "MMSE_2": 27.0
        }
        assert is_eligible(row) is True

    def test_eligible_moca(self):
        row = {
            "participant_id": "sub-02",
            "MOCA": 25.0,
            "MOCA_2": 24.0
        }
        assert is_eligible(row) is True

    def test_ineligible_missing_second(self):
        row = {
            "participant_id": "sub-03",
            "MMSE": 28.0,
            "MMSE_2": None
        }
        assert is_eligible(row) is False

    def test_ineligible_missing_first(self):
        row = {
            "participant_id": "sub-04",
            "MMSE": None,
            "MMSE_2": 27.0
        }
        assert is_eligible(row) is False

    def test_ineligible_no_scores(self):
        row = {
            "participant_id": "sub-05",
            "age": 65
        }
        assert is_eligible(row) is False

    def test_eligible_fallback_two_scores(self):
        # Test fallback logic when specific pairs are not found
        row = {
            "participant_id": "sub-06",
            "Timepoint1_MMSE": 28.0,
            "Timepoint2_MMSE": 27.0
        }
        # This should pass the fallback check if it finds 2 valid score columns
        assert is_eligible(row) is True


class TestFilterEligibleSubjects:
    def test_filter(self):
        records = [
            {"participant_id": "sub-01", "MMSE": 28.0, "MMSE_2": 27.0},
            {"participant_id": "sub-02", "MMSE": None, "MMSE_2": 27.0},
            {"participant_id": "sub-03", "MOCA": 25.0, "MOCA_2": 24.0},
        ]
        eligible, excluded = filter_eligible_subjects(records)
        assert len(eligible) == 2
        assert len(excluded) == 1
        assert eligible[0]["participant_id"] == "sub-01"
        assert eligible[1]["participant_id"] == "sub-03"


class TestLimitSubjects:
    def test_limit(self):
        subjects = [{"participant_id": f"sub-{i}"} for i in range(10)]
        limited = limit_subjects(subjects, 5)
        assert len(limited) == 5

    def test_no_limit(self):
        subjects = [{"participant_id": f"sub-{i}"} for i in range(5)]
        limited = limit_subjects(subjects, 10)
        assert len(limited) == 5


class TestWriteEligibleCSV:
    def test_write_csv(self, tmp_path):
        subjects = [
            {"participant_id": "sub-01", "MMSE": 28.0},
            {"participant_id": "sub-02", "MMSE": 27.0}
        ]
        output_path = tmp_path / "eligible.csv"
        write_eligible_csv(subjects, output_path)
        
        assert output_path.exists()
        with open(output_path, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 2
        assert rows[0]["participant_id"] == "sub-01"


class TestWriteExcludedLog:
    def test_write_log(self, tmp_path):
        excluded = [
            {"participant_id": "sub-01", "reason": "missing scores"},
            {"participant_id": "sub-02", "reason": "missing scores"}
        ]
        output_path = tmp_path / "excluded.log"
        write_excluded_log(excluded, output_path)
        
        assert output_path.exists()
        with open(output_path, "r") as f:
            content = f.read()
        assert "sub-01" in content
        assert "sub-02" in content


class TestWriteStatus:
    def test_write_status(self, tmp_path):
        # Change output path for testing
        import code_01_download_and_filter as module
        original_path = module.OUTPUT_FILE_STATUS
        module.OUTPUT_FILE_STATUS = tmp_path / "status.json"
        
        try:
            write_status(10, 5, "success")
            assert module.OUTPUT_FILE_STATUS.exists()
            with open(module.OUTPUT_FILE_STATUS, "r") as f:
                data = json.load(f)
            assert data["eligible_count"] == 10
            assert data["excluded_count"] == 5
            assert data["status"] == "success"
        finally:
            module.OUTPUT_FILE_STATUS = original_path