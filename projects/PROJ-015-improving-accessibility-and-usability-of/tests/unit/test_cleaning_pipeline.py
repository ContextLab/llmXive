import pytest
import pandas as pd
import json
import os
import tempfile
from pathlib import Path

from code.analysis.run_cleaning_pipeline import load_raw_sessions, coerce_types
from code.analysis.data_cleaner import DataCleaner

def test_load_raw_sessions():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create mock JSON files
        data1 = {"participant_id": "P1", "status": "complete", "sus_score": 80}
        data2 = {"participant_id": "P2", "status": "incomplete", "sus_score": 60}
        
        with open(os.path.join(tmpdir, "s1.json"), "w") as f:
            json.dump(data1, f)
        with open(os.path.join(tmpdir, "s2.json"), "w") as f:
            json.dump(data2, f)
        
        df = load_raw_sessions(tmpdir)
        assert len(df) == 2
        assert "P1" in df["participant_id"].values

def test_coerce_types():
    data = {
        "participant_id": [123, "P2"],
        "interface_type": ["traditional", "explainable"],
        "completion_time_seconds": ["10.5", 20],
        "error_count": [1.0, 2],
        "sus_score": [80, 90],
        "status": ["complete", "complete"]
    }
    df = pd.DataFrame(data)
    df = coerce_types(df)
    
    assert df["participant_id"].dtype == object
    assert df["completion_time_seconds"].dtype == float
    assert df["error_count"].dtype == int

def test_impute_sus_scores():
    # Test with individual questions
    data = {
        "participant_id": ["P1", "P2"],
        "SUS_Q1": [5, 4],
        "SUS_Q2": [4, 5],
        "SUS_Q3": [5, 4],
        "SUS_Q4": [4, 5],
        "SUS_Q5": [5, 4],
        "SUS_Q6": [4, 5],
        "SUS_Q7": [5, 4],
        "SUS_Q8": [4, 5],
        "SUS_Q9": [5, 4],
        "SUS_Q10": [4, None], # P2 has one missing
    }
    df = pd.DataFrame(data)
    cleaner = DataCleaner()
    df_clean = cleaner.impute_sus_scores(df)
    
    # P1 should have a score
    # P2 should have a score (imputed)
    assert df_clean["sus_score"].notna().all()

def test_impute_sus_more_than_one_missing():
    # Test with more than one missing (should result in NaN)
    data = {
        "participant_id": ["P1"],
        "SUS_Q1": [5],
        "SUS_Q2": [None],
        "SUS_Q3": [None],
        "SUS_Q4": [4],
        "SUS_Q5": [5],
        "SUS_Q6": [4],
        "SUS_Q7": [5],
        "SUS_Q8": [4],
        "SUS_Q9": [5],
        "SUS_Q10": [4],
    }
    df = pd.DataFrame(data)
    cleaner = DataCleaner()
    df_clean = cleaner.impute_sus_scores(df)
    
    # P1 should still be NaN because > 1 missing
    assert pd.isna(df_clean.loc[0, "sus_score"])
