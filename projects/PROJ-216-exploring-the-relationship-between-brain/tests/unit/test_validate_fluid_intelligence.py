import os
import json
import pytest
from pathlib import Path
import pandas as pd

# Add code directory to path
sys_path = Path(__file__).parent.parent.parent / "code"
if str(sys_path) not in __import__('sys').path:
    __import__('sys').path.insert(0, str(sys_path))

from validate_fluid_intelligence import (
    load_behavioral_scores,
    scan_subjects_for_scores,
    validate_and_aggregate,
    main
)

@pytest.fixture
def mock_data_dir(tmp_path):
    """Create a mock data structure with valid and invalid subjects."""
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    
    # Create a valid subject with a TSV file
    sub_valid = raw_dir / "sub-001"
    sub_valid.mkdir()
    behav_tsv = sub_valid / "behav.tsv"
    df = pd.DataFrame({
        'participant_id': ['sub-001'],
        'fluid_intelligence_score': [1.25]
    })
    df.to_csv(behav_tsv, sep='\t', index=False)
    
    # Create a subject with missing score
    sub_invalid = raw_dir / "sub-002"
    sub_invalid.mkdir()
    behav_tsv_invalid = sub_invalid / "behav.tsv"
    df_invalid = pd.DataFrame({
        'participant_id': ['sub-002'],
        'other_score': [0.5]
    })
    df_invalid.to_csv(behav_tsv_invalid, sep='\t', index=False)

    # Create a subject with NaN score
    sub_nan = raw_dir / "sub-003"
    sub_nan.mkdir()
    behav_tsv_nan = sub_nan / "behav.tsv"
    df_nan = pd.DataFrame({
        'participant_id': ['sub-003'],
        'fluid_intelligence_score': [float('nan')]
    })
    df_nan.to_csv(behav_tsv_nan, sep='\t', index=False)

    return tmp_path

def test_load_behavioral_scores_valid(monkeypatch, mock_data_dir):
    """Test loading a valid fluid intelligence score."""
    monkeypatch.chdir(mock_data_dir)
    score = load_behavioral_scores("sub-001")
    assert score is not None
    assert score['score'] == 1.25

def test_load_behavioral_scores_missing(monkeypatch, mock_data_dir):
    """Test loading returns None when score is missing."""
    monkeypatch.chdir(mock_data_dir)
    score = load_behavioral_scores("sub-002")
    assert score is None

def test_load_behavioral_scores_nan(monkeypatch, mock_data_dir):
    """Test loading returns None when score is NaN."""
    monkeypatch.chdir(mock_data_dir)
    score = load_behavioral_scores("sub-003")
    assert score is None

def test_scan_subjects_for_scores(monkeypatch, mock_data_dir):
    """Test scanning multiple subjects."""
    monkeypatch.chdir(mock_data_dir)
    subjects = ["sub-001", "sub-002", "sub-003"]
    valid = scan_subjects_for_scores(subjects)
    
    assert len(valid) == 1
    assert valid[0]['id'] == 'sub-001'
    assert valid[0]['score'] == 1.25

def test_validate_and_aggregate(monkeypatch, tmp_path, mock_data_dir):
    """Test aggregation and file writing."""
    monkeypatch.chdir(mock_data_dir)
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    output_file = processed_dir / "valid_subjects.json"
    
    valid_subjects = [{"id": "sub-001", "score": 1.25}]
    result = validate_and_aggregate(valid_subjects, output_file)
    
    assert result['count'] == 1
    assert result['subjects'][0]['id'] == 'sub-001'
    
    assert output_file.exists()
    with open(output_file, 'r') as f:
        data = json.load(f)
    assert data['count'] == 1
    assert 'subjects' in data
