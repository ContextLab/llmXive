"""
Unit tests for T017: code/01_download_and_filter.py
"""
import pytest
from pathlib import Path
import csv
import json
import tempfile
import os

# Import functions to test
from code import download_and_filter as df

class TestEligibilityLogic:
    def test_is_eligible_both_scores_present(self):
        row = {
            "participant_id": "sub-01",
            "ses-1_MMSE": "28.0",
            "ses-1_MOCA": "29.0",
            "ses-2_MMSE": "27.0",
            "ses-2_MOCA": "28.5"
        }
        assert df.is_eligible(row) is True

    def test_is_eligible_missing_timepoint_2(self):
        row = {
            "participant_id": "sub-02",
            "ses-1_MMSE": "28.0",
            "ses-1_MOCA": "29.0",
            "ses-2_MMSE": "",
            "ses-2_MOCA": "NaN"
        }
        assert df.is_eligible(row) is False

    def test_is_eligible_missing_timepoint_1(self):
        row = {
            "participant_id": "sub-03",
            "ses-1_MMSE": "",
            "ses-1_MOCA": "n/a",
            "ses-2_MMSE": "27.0",
            "ses-2_MOCA": "28.5"
        }
        assert df.is_eligible(row) is False

    def test_is_eligible_no_mmse_moca_columns(self):
        row = {
            "participant_id": "sub-04",
            "age": "65",
            "sex": "M"
        }
        assert df.is_eligible(row) is False

class TestFiltering:
    def test_filter_eligible_subjects(self):
        rows = [
            {"participant_id": "s1", "ses-1_MMSE": "20", "ses-2_MMSE": "20"},
            {"participant_id": "s2", "ses-1_MMSE": "", "ses-2_MMSE": "20"},
            {"participant_id": "s3", "ses-1_MMSE": "20", "ses-2_MMSE": ""},
            {"participant_id": "s4", "ses-1_MMSE": "20", "ses-2_MMSE": "20"}
        ]
        eligible, excluded = df.filter_eligible_subjects(rows)
        assert len(eligible) == 2
        assert len(excluded) == 2
        assert eligible[0]["participant_id"] == "s1"
        assert eligible[1]["participant_id"] == "s4"

class TestLimiting:
    def test_limit_subjects(self):
        rows = [{"participant_id": str(i)} for i in range(150)]
        limited = df.limit_subjects(rows, 100)
        assert len(limited) == 100
        assert limited[0]["participant_id"] == "0"
        assert limited[-1]["participant_id"] == "99"

    def test_limit_subjects_no_limit_needed(self):
        rows = [{"participant_id": str(i)} for i in range(50)]
        limited = df.limit_subjects(rows, 100)
        assert len(limited) == 50

class TestIO:
    def test_write_eligible_csv(self, tmp_path):
        rows = [{"participant_id": "s1", "score": "20"}, {"participant_id": "s2", "score": "22"}]
        out_file = tmp_path / "test.csv"
        df.write_eligible_csv(rows, out_file)
        
        assert out_file.exists()
        with open(out_file, "r") as f:
            reader = csv.DictReader(f)
            data = list(reader)
            assert len(data) == 2
            assert data[0]["participant_id"] == "s1"

    def test_write_elcluded_log(self, tmp_path):
        rows = [{"participant_id": "s1", "reason": "missing"}]
        out_file = tmp_path / "test.log"
        df.write_excluded_log(rows, out_file)
        
        assert out_file.exists()
        content = out_file.read_text()
        assert "s1" in content
        assert "Excluded Subjects Log" in content

    def test_write_status(self, tmp_path):
        status = {"key": "value", "count": 5}
        out_file = tmp_path / "status.json"
        df.write_status(status, out_file)
        
        assert out_file.exists()
        with open(out_file, "r") as f:
            loaded = json.load(f)
            assert loaded == status