import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Import the module functions directly
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
from alignment import align_and_filter_data, save_exclusions_log

def test_align_and_filter_missing_student_scalar():
    """Test that samples with missing student_scalar are correctly identified and excluded."""
    data = {
        "sample_id": ["s1", "s2", "s3", "s4"],
        "image_path": ["img1.jpg", "img2.jpg", "img3.jpg", "img4.jpg"],
        "species_id": [1, 2, 3, 4],
        "prompt_text": ["p1", "p2", "p3", "p4"],
        "teacher_scores": [
            [[1.0, 2.0, 3.0, 4.0]],
            [[1.0, 2.0, 3.0, 4.0]],
            [[1.0, 2.0, 3.0, 4.0]],
            [[1.0, 2.0, 3.0, 4.0]]
        ],
        "student_scalar": [0.5, np.nan, 0.7, 0.8],
        "human_annotations": [
            [[0.4, 0.5, 0.6, 0.7]],
            [[0.4, 0.5, 0.6, 0.7]],
            [[0.4, 0.5, 0.6, 0.7]],
            [[0.4, 0.5, 0.6, 0.7]]
        ],
        "primary_dimension": [0, 1, 2, 3]
    }
    df = pd.DataFrame(data)
    
    # Mock logger
    class MockLogger:
        def info(self, msg): pass
        def warning(self, msg): pass
        def error(self, msg): pass

    logger = MockLogger()
    
    aligned_df, exclusions = align_and_filter_data(df, logger)
    
    # Check that the sample with missing student_scalar is excluded
    assert len(aligned_df) == 3
    assert len(exclusions) == 1
    assert exclusions[0]["sample_id"] == "s2"
    assert exclusions[0]["excluded_reason"] == "missing_student_scalar"
    
    # Check that the remaining samples have valid student_scalar
    assert aligned_df["student_scalar"].notna().all()

def test_align_and_filter_all_valid():
    """Test that all samples are kept when no student_scalar is missing."""
    data = {
        "sample_id": ["s1", "s2"],
        "image_path": ["img1.jpg", "img2.jpg"],
        "species_id": [1, 2],
        "prompt_text": ["p1", "p2"],
        "teacher_scores": [
            [[1.0, 2.0, 3.0, 4.0]],
            [[1.0, 2.0, 3.0, 4.0]]
        ],
        "student_scalar": [0.5, 0.7],
        "human_annotations": [
            [[0.4, 0.5, 0.6, 0.7]],
            [[0.4, 0.5, 0.6, 0.7]]
        ],
        "primary_dimension": [0, 1]
    }
    df = pd.DataFrame(data)
    
    class MockLogger:
        def info(self, msg): pass
        def warning(self, msg): pass
        def error(self, msg): pass

    logger = MockLogger()
    
    aligned_df, exclusions = align_and_filter_data(df, logger)
    
    assert len(aligned_df) == 2
    assert len(exclusions) == 0

def test_save_exclusions_log():
    """Test that exclusions log is saved correctly."""
    exclusions = [
        {"sample_id": "s2", "excluded_reason": "missing_student_scalar"}
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "exclusions_log.json"
        
        class MockLogger:
            def info(self, msg): pass
            def warning(self, msg): pass
            def error(self, msg): pass

        logger = MockLogger()
        save_exclusions_log(exclusions, output_path, logger)
        
        assert output_path.exists()
        with open(output_path, "r") as f:
            loaded_exclusions = json.load(f)
        
        assert loaded_exclusions == exclusions
