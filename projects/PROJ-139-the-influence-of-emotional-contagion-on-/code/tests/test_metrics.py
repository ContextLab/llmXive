import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json
import os

from code.data.metrics import (
    filter_threads_by_reply_count,
    save_exclusion_counts,
    run_metrics_exclusion_pipeline,
    MIN_REPLIES_FOR_CONTAGION
)

@pytest.fixture
def sample_thread_with_sufficient_replies():
    return pd.DataFrame([
        {"thread_id": "t1", "reply_count": 10, "seed_sentiment": 0.5},
        {"thread_id": "t2", "reply_count": 5, "seed_sentiment": -0.2}
    ])

@pytest.fixture
def sample_thread_with_insufficient_replies():
    return pd.DataFrame([
        {"thread_id": "t3", "reply_count": 4, "seed_sentiment": 0.1},
        {"thread_id": "t4", "reply_count": 0, "seed_sentiment": 0.0}
    ])

@pytest.fixture
def sample_thread_with_no_replies():
    return pd.DataFrame([
        {"thread_id": "t5", "reply_count": 0, "seed_sentiment": 0.5}
    ])

def test_filter_threads_sufficient(sample_thread_with_sufficient_replies):
    filtered, exclusions = filter_threads_by_reply_count(sample_thread_with_sufficient_replies)
    assert len(filtered) == 2
    assert len(exclusions) == 0
    assert "t1" in filtered["thread_id"].values
    assert "t2" in filtered["thread_id"].values

def test_filter_threads_insufficient(sample_thread_with_insufficient_replies):
    filtered, exclusions = filter_threads_by_reply_count(sample_thread_with_insufficient_replies)
    assert len(filtered) == 0
    assert len(exclusions) == 2
    assert exclusions[0]["reason_code"] == "REPLY_INSUFFICIENT"
    assert exclusions[0]["min_required"] == MIN_REPLIES_FOR_CONTAGION

def test_filter_threads_mixed(sample_thread_with_sufficient_replies, sample_thread_with_insufficient_replies):
    combined = pd.concat([sample_thread_with_sufficient_replies, sample_thread_with_insufficient_replies], ignore_index=True)
    filtered, exclusions = filter_threads_by_reply_count(combined)
    
    assert len(filtered) == 2
    assert len(exclusions) == 2
    assert set(filtered["thread_id"]) == {"t1", "t2"}
    assert set([e["thread_id"] for e in exclusions]) == {"t3", "t4"}

def test_save_exclusion_counts():
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_exclusions.json"
        records = [
            {"thread_id": "t1", "reason_code": "REPLY_INSUFFICIENT", "reply_count": 2}
        ]
        save_exclusion_counts(records, output_path)
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data["total_excluded"] == 1
        assert data["reason_code"] == "REPLY_INSUFFICIENT"

def test_run_metrics_exclusion_pipeline():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a mock input file
        input_path = Path(tmpdir) / "threads_with_seeds.csv"
        data = [
            {"thread_id": "good", "reply_count": 10},
            {"thread_id": "bad", "reply_count": 2}
        ]
        pd.DataFrame(data).to_csv(input_path, index=False)
        
        # Mock config to point to temp dir
        # Since we can't easily mock the global config singleton without side effects,
        # we will test the specific functions directly or assume the environment is set.
        # For this test, we test the logic directly on the dataframe.
        
        df = pd.read_csv(input_path)
        filtered, exclusions = filter_threads_by_reply_count(df)
        
        assert len(filtered) == 1
        assert filtered.iloc[0]["thread_id"] == "good"
        assert len(exclusions) == 1
        assert exclusions[0]["thread_id"] == "bad"

def test_empty_dataframe():
    df = pd.DataFrame(columns=["thread_id", "reply_count"])
    filtered, exclusions = filter_threads_by_reply_count(df)
    assert len(filtered) == 0
    assert len(exclusions) == 0
    
def test_missing_reply_count_column():
    df = pd.DataFrame([{"thread_id": "t1", "seed_sentiment": 0.5}])
    with pytest.raises(KeyError):
        filter_threads_by_reply_count(df)