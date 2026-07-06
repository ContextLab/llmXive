"""
Unit tests for code/data/filter_subjects.py (T015)
"""
import json
import pytest
from pathlib import Path
import tempfile
import os

# Import the module functions
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data.filter_subjects import (
    load_validated_metadata,
    filter_subjects_with_dream_recall,
    sort_and_select_subjects,
    save_valid_subjects,
    FatalError,
    TARGET_N,
    DREAM_RECALL_FIELD
)


class TestLoadValidatedMetadata:
    def test_load_list_format(self, tmp_path):
        """Test loading metadata that is a direct list."""
        data = [{"subject_id": "sub-01"}, {"subject_id": "sub-02"}]
        file_path = tmp_path / "metadata.json"
        file_path.write_text(json.dumps(data))

        result = load_validated_metadata(file_path)
        assert len(result) == 2
        assert result[0]["subject_id"] == "sub-01"

    def test_load_dict_with_subjects_key(self, tmp_path):
        """Test loading metadata wrapped in a dict with 'subjects' key."""
        data = {"subjects": [{"subject_id": "sub-01"}]}
        file_path = tmp_path / "metadata.json"
        file_path.write_text(json.dumps(data))

        result = load_validated_metadata(file_path)
        assert len(result) == 1
        assert result[0]["subject_id"] == "sub-01"

    def test_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised if file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_validated_metadata(tmp_path / "nonexistent.json")


class TestFilterSubjects:
    def test_filter_present_and_valid(self):
        """Test filtering subjects with valid dream recall frequency."""
        subjects = [
            {"subject_id": "s1", DREAM_RECALL_FIELD: 5},
            {"subject_id": "s2", DREAM_RECALL_FIELD: 0},
            {"subject_id": "s3", DREAM_RECALL_FIELD: 12},
        ]
        result = filter_subjects_with_dream_recall(subjects)
        assert len(result) == 3

    def test_filter_missing_field(self):
        """Test filtering subjects missing the field."""
        subjects = [
            {"subject_id": "s1", "other_field": 10},
            {"subject_id": "s2", DREAM_RECALL_FIELD: 5},
        ]
        result = filter_subjects_with_dream_recall(subjects)
        assert len(result) == 1
        assert result[0]["subject_id"] == "s2"

    def test_filter_null_value(self):
        """Test filtering subjects with null value."""
        subjects = [
            {"subject_id": "s1", DREAM_RECALL_FIELD: None},
            {"subject_id": "s2", DREAM_RECALL_FIELD: 5},
        ]
        result = filter_subjects_with_dream_recall(subjects)
        assert len(result) == 1

    def test_filter_non_numeric(self):
        """Test filtering subjects with non-numeric values."""
        subjects = [
            {"subject_id": "s1", DREAM_RECALL_FIELD: "high"},
            {"subject_id": "s2", DREAM_RECALL_FIELD: 5},
        ]
        result = filter_subjects_with_dream_recall(subjects)
        assert len(result) == 1


class TestSortAndSelect:
    def test_sort_by_id(self):
        """Test sorting by subject_id ascending."""
        subjects = [
            {"subject_id": "sub-03"},
            {"subject_id": "sub-01"},
            {"subject_id": "sub-02"},
        ]
        result = sort_and_select_subjects(subjects, n=3)
        assert result[0]["subject_id"] == "sub-01"
        assert result[1]["subject_id"] == "sub-02"
        assert result[2]["subject_id"] == "sub-03"

    def test_truncate_to_n(self):
        """Test that selection truncates to N."""
        subjects = [{"subject_id": f"sub-{i:02d}"} for i in range(100)]
        result = sort_and_select_subjects(subjects, n=10)
        assert len(result) == 10
        assert result[0]["subject_id"] == "sub-00"
        assert result[9]["subject_id"] == "sub-09"

    def test_insufficient_subjects_raises_fatal(self):
        """Test that FatalError is raised if fewer than N subjects."""
        subjects = [{"subject_id": "s1"}, {"subject_id": "s2"}]
        with pytest.raises(FatalError) as exc_info:
            sort_and_select_subjects(subjects, n=50)
        assert "Insufficient subjects" in str(exc_info.value)


class TestSaveValidSubjects:
    def test_save_creates_file(self, tmp_path):
        """Test that save creates the file with correct content."""
        subjects = [{"subject_id": "s1", DREAM_RECALL_FIELD: 5}]
        output_path = tmp_path / "valid_subjects.json"
        
        save_valid_subjects(subjects, output_path)
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data["n_subjects"] == 1
        assert data["target_n"] == TARGET_N
        assert len(data["subjects"]) == 1
        assert data["subjects"][0]["subject_id"] == "s1"