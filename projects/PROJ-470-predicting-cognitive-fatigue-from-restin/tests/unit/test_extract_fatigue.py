"""
Test T011: Extract Fatigue Scores.
"""
import csv
import json
import os
import tempfile
from pathlib import Path
import pytest

# We need to import the module under test. 
# Since the code is in code/extract_fatigue.py, we add the parent to path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from extract_fatigue import load_manifest, extract_fatigue_scores, write_scores_to_csv

def test_extract_fatigue_scores_from_manifest():
    """Test that the script correctly extracts scores from a manifest."""
    # Create a mock manifest
    mock_manifest = {
        "participants": [
            {
                "id": "sub-001",
                "fatigue_rating": {"pre": 2.5, "post": 4.1}
            },
            {
                "id": "sub-002",
                "fatigue_rating": {"pre": 1.2, "post": 3.8}
            }
        ]
    }

    scores = extract_fatigue_scores(mock_manifest, Path("/dummy"))
    
    assert len(scores) == 4  # 2 participants * 2 timepoints
    
    # Check structure
    participant_ids = {s["participant_id"] for s in scores}
    assert participant_ids == {"sub-001", "sub-002"}
    
    timepoints = {s["timepoint"] for s in scores}
    assert timepoints == {"pre", "post"}
    
    # Check specific values
    sub001_pre = next(s for s in scores if s["participant_id"] == "sub-001" and s["timepoint"] == "pre")
    assert sub001_pre["fatigue_score"] == 2.5

def test_write_scores_to_csv(tmp_path):
    """Test that scores are written to CSV correctly."""
    scores = [
        {"participant_id": "sub-001", "timepoint": "pre", "fatigue_score": 2.5},
        {"participant_id": "sub-001", "timepoint": "post", "fatigue_score": 4.1}
    ]
    
    output_file = tmp_path / "fatigue_scores.csv"
    write_scores_to_csv(scores, output_file)
    
    assert output_file.exists()
    
    with open(output_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 2
    assert rows[0]["participant_id"] == "sub-001"
    assert rows[0]["timepoint"] == "pre"
    assert float(rows[0]["fatigue_score"]) == 2.5

def test_empty_scores_raises():
    """Test that empty scores list raises ValueError."""
    with pytest.raises(ValueError):
        write_scores_to_csv([], Path("dummy.csv"))
