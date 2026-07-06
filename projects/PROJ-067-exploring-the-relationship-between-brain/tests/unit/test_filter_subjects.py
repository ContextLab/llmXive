"""
Unit tests for T015: Subject Filtering & N=50 Enforcement
"""
import json
import tempfile
from pathlib import Path
import pytest

from code.data.filter_subjects import (
    load_validated_metadata,
    filter_subjects_by_drf,
    sort_and_truncate,
    save_valid_subjects,
    FatalError
)

@pytest.fixture
def sample_metadata_list():
    return [
        {"participant_id": "sub-01", "dream_recall_frequency": 5},
        {"participant_id": "sub-02", "dream_recall_frequency": 12},
        {"participant_id": "sub-03", "age": 25}, # Missing DRF
        {"participant_id": "sub-04", "dream_recall_frequency": 3},
        {"participant_id": "sub-05", "dream_recall_frequency": 8},
    ]

@pytest.fixture
def sample_metadata_dict(sample_metadata_list):
    return {"participants": sample_metadata_list}

@pytest.fixture
def temp_metadata_file(tmp_path, sample_metadata_list):
    file_path = tmp_path / "validated_metadata.json"
    with open(file_path, 'w') as f:
        json.dump(sample_metadata_list, f)
    return file_path

def test_load_validated_metadata_list(temp_metadata_file):
    data = load_validated_metadata(temp_metadata_file)
    assert len(data) == 5
    assert data[0]["participant_id"] == "sub-01"

def test_load_validated_metadata_dict(tmp_path, sample_metadata_dict):
    file_path = tmp_path / "validated_metadata.json"
    with open(file_path, 'w') as f:
        json.dump(sample_metadata_dict, f)
    
    data = load_validated_metadata(file_path)
    assert len(data) == 5
    assert data[0]["participant_id"] == "sub-01"

def test_filter_subjects_by_drf(sample_metadata_list):
    valid = filter_subjects_by_drf(sample_metadata_list)
    assert len(valid) == 4
    ids = [p["participant_id"] for p in valid]
    assert "sub-03" not in ids
    assert "sub-01" in ids

def test_sort_and_truncate_enough():
    participants = [
        {"participant_id": "sub-10", "dream_recall_frequency": 1},
        {"participant_id": "sub-05", "dream_recall_frequency": 1},
        {"participant_id": "sub-01", "dream_recall_frequency": 1},
        {"participant_id": "sub-02", "dream_recall_frequency": 1},
        {"participant_id": "sub-03", "dream_recall_frequency": 1},
        {"participant_id": "sub-04", "dream_recall_frequency": 1},
        {"participant_id": "sub-06", "dream_recall_frequency": 1},
        {"participant_id": "sub-07", "dream_recall_frequency": 1},
        {"participant_id": "sub-08", "dream_recall_frequency": 1},
        {"participant_id": "sub-09", "dream_recall_frequency": 1},
    ]
    # We have 10, ask for 5
    result = sort_and_truncate(participants, target_n=5)
    assert len(result) == 5
    # Should be sorted by ID: 01, 02, 03, 04, 05
    ids = [p["participant_id"] for p in result]
    assert ids == ["sub-01", "sub-02", "sub-03", "sub-04", "sub-05"]

def test_sort_and_truncate_not_enough():
    participants = [
        {"participant_id": "sub-01", "dream_recall_frequency": 1},
        {"participant_id": "sub-02", "dream_recall_frequency": 1},
        {"participant_id": "sub-03", "dream_recall_frequency": 1},
    ]
    # We have 3, ask for 5 -> Should raise FatalError
    with pytest.raises(FatalError) as exc_info:
        sort_and_truncate(participants, target_n=5)
    assert "Insufficient subjects" in str(exc_info.value)
    assert "N=5" in str(exc_info.value)

def test_save_valid_subjects(tmp_path):
    subjects = [
        {"participant_id": "sub-01", "dream_recall_frequency": 5},
        {"participant_id": "sub-02", "dream_recall_frequency": 10},
    ]
    output_path = tmp_path / "valid_subjects.json"
    save_valid_subjects(subjects, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        loaded = json.load(f)
    assert len(loaded) == 2
    assert loaded[0]["participant_id"] == "sub-01"
