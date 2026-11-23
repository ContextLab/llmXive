"""
Unit tests for Task T023b: Descriptive Statistics.
"""
import os
import sys
import pandas as pd
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.analysis.run_descriptive_stats import (
    load_raw_session_data,
    compute_descriptive_stats,
    log_exclusion,
    write_output
)

def test_load_raw_session_data():
    """Test loading JSON files into a DataFrame."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create mock JSON files
        session1 = {
            "participant_id": "P1",
            "status": "complete",
            "interface_type": "traditional",
            "explanation_engagement_time_seconds": 5.0
        }
        session2 = {
            "participant_id": "P2",
            "status": "complete",
            "interface_type": "explainable",
            "explanation_engagement_time_seconds": 10.5
        }
        
        with open(os.path.join(tmpdir, "s1.json"), 'w') as f:
            json.dump(session1, f)
        with open(os.path.join(tmpdir, "s2.json"), 'w') as f:
            json.dump(session2, f)
        
        df = load_raw_session_data(tmpdir)
        
        assert len(df) == 2
        assert "explanation_engagement_time_seconds" in df.columns
        assert df.iloc[0]["participant_id"] == "P1"

def test_compute_descriptive_stats():
    """Test descriptive stats calculation."""
    data = [
        {"participant_id": "P1", "status": "complete", "interface_type": "traditional", "explanation_engagement_time_seconds": 5.0},
        {"participant_id": "P2", "status": "complete", "interface_type": "traditional", "explanation_engagement_time_seconds": 7.0},
        {"participant_id": "P3", "status": "complete", "interface_type": "explainable", "explanation_engagement_time_seconds": 10.0},
        {"participant_id": "P4", "status": "incomplete", "interface_type": "explainable", "explanation_engagement_time_seconds": 20.0}, # Should be excluded
    ]
    df = pd.DataFrame(data)
    
    stats_df = compute_descriptive_stats(df)
    
    assert len(stats_df) == 2 # Two interface types
    
    # Check traditional stats
    trad_row = stats_df[stats_df['interface_type'] == 'traditional'].iloc[0]
    assert abs(trad_row['mean'] - 6.0) < 0.001
    assert trad_row['count'] == 2
    
    # Check explainable stats (only P3 should count, P4 is incomplete)
    expl_row = stats_df[stats_df['interface_type'] == 'explainable'].iloc[0]
    assert abs(expl_row['mean'] - 10.0) < 0.001
    assert expl_row['count'] == 1

def test_log_exclusion():
    """Test that exclusion log is written correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "exclusion_log.txt")
        log_exclusion(log_path)
        
        assert os.path.exists(log_path)
        with open(log_path, 'r') as f:
            content = f.read()
        
        assert "explanation_engagement_time_seconds" in content
        assert "EXCLUDED" in content
        assert "ANOVA" in content

def test_write_output():
    """Test writing CSV output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "stats.csv")
        df = pd.DataFrame([{"a": 1, "b": 2}])
        
        write_output(df, csv_path)
        
        assert os.path.exists(csv_path)
        loaded = pd.read_csv(csv_path)
        assert len(loaded) == 1
        assert "a" in loaded.columns