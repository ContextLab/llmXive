import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd

from download import validate_and_aggregate, download_dataset, get_subject_list
from models import Subject, BehavioralScore


def test_validate_and_aggregate_empty():
    """Test that validation fails when no subjects have scores."""
    subjects_224 = [
        Subject(id="sub-01", raw_data_path="/tmp", behavioral_score=None),
        Subject(id="sub-02", raw_data_path="/tmp", behavioral_score=None)
    ]
    subjects_230 = []

    with pytest.raises(ValueError, match="CRITICAL: No subjects with Fluid Intelligence scores found"):
        validate_and_aggregate(subjects_224, subjects_230, sample_limit=10)


def test_validate_and_aggregate_partial():
    """Test aggregation when only some subjects have scores."""
    subjects_224 = [
        Subject(id="sub-01", raw_data_path="/tmp", behavioral_score=BehavioralScore(value=10.5, source="FluidInt", subject_id="sub-01")),
        Subject(id="sub-02", raw_data_path="/tmp", behavioral_score=None)
    ]
    subjects_230 = [
        Subject(id="sub-03", raw_data_path="/tmp", behavioral_score=BehavioralScore(value=12.0, source="FluidInt", subject_id="sub-03"))
    ]

    result, summary = validate_and_aggregate(subjects_224, subjects_230, sample_limit=10)

    assert len(result) == 2
    assert summary["total_valid_subjects"] == 2
    assert summary["status"] == "ok"


def test_validate_and_aggregate_limit():
    """Test that aggregation respects sample limit."""
    subjects_224 = [
        Subject(id=f"sub-{i:02d}", raw_data_path="/tmp", behavioral_score=BehavioralScore(value=float(i), source="FluidInt", subject_id=f"sub-{i:02d}"))
        for i in range(15)
    ]
    subjects_230 = []

    result, summary = validate_and_aggregate(subjects_224, subjects_230, sample_limit=10)

    assert len(result) == 10
    assert summary["truncated_to"] == 10


@patch('download.openneuro_client')
def test_get_subject_list(mock_client):
    """Test fetching subject list from mock API."""
    mock_client.Client.return_value.get_subjects.return_value = [
        {"id": "sub-01"},
        {"id": "sub-02"}
    ]

    subjects = get_subject_list("ds000224", 10)
    
    assert len(subjects) == 2
    assert subjects[0] == "sub-01"


@patch('download.subprocess.run')
@patch('download.Path.exists')
@patch('download.pd.read_csv')
def test_download_dataset_with_score(mock_read_csv, mock_exists, mock_run):
    """Test download logic when score is found in participants.tsv."""
    # Mock file existence
    mock_exists.return_value = True
    
    # Mock DataFrame with score
    mock_df = pd.DataFrame({
        'participant_id': ['sub-01'],
        'FluidIntelligenceScore': [15.5]
    })
    mock_read_csv.return_value = mock_df

    # Mock subprocess success
    mock_run.return_value = MagicMock(returncode=0)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        subjects = download_dataset("ds000224", output_dir, ["sub-01"])
        
        assert len(subjects) == 1
        assert subjects[0].behavioral_score is not None
        assert subjects[0].behavioral_score.value == 15.5