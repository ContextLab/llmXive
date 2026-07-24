"""
Unit tests for T043: Sample Size Verification.
"""

import json
import os
import tempfile
import pytest
import pandas as pd
from pathlib import Path

# Import the module under test
# Note: We assume the module is added to sys.path or installed in editable mode
import sys
from code.analysis.verify_sample_size import verify_sample_size, write_verification_report, MIN_SAMPLE_SIZE


def create_test_csv(path: str, num_participants: int, num_sessions_per_participant: int = 2):
    """Helper to create a dummy cleaned_sessions.csv."""
    data = []
    for p_id in range(1, num_participants + 1):
        for s_id in range(num_sessions_per_participant):
            data.append({
                "participant_id": p_id,
                "interface_type": "traditional" if s_id == 0 else "explainable",
                "completion_time_seconds": 10.0 + s_id,
                "error_count": 0,
                "sus_score": 80,
                "explanation_engagement_time_seconds": 0.0 if s_id == 0 else 5.0
            })
    df = pd.DataFrame(data)
    df.to_csv(path, index=False)
    return df


def test_verify_sample_size_pass():
    """Test that verification passes when N >= 30."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "cleaned.csv")
        json_path = os.path.join(tmpdir, "result.json")

        # Create data with 30 participants
        create_test_csv(csv_path, num_participants=30, num_sessions_per_participant=2)
        df = pd.read_csv(csv_path)

        result = verify_sample_size(df)

        assert result["total_participants"] == 30
        assert result["meets_minimum"] is True
        assert result["status"] == "PASS"
        assert result["minimum_required"] == MIN_SAMPLE_SIZE

        write_verification_report(result, json_path)
        assert os.path.exists(json_path)
        with open(json_path, 'r') as f:
            loaded = json.load(f)
        assert loaded == result


def test_verify_sample_size_fail():
    """Test that verification fails when N < 30."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "cleaned.csv")
        json_path = os.path.join(tmpdir, "result.json")

        # Create data with 10 participants
        create_test_csv(csv_path, num_participants=10, num_sessions_per_participant=2)
        df = pd.read_csv(csv_path)

        result = verify_sample_size(df)

        assert result["total_participants"] == 10
        assert result["meets_minimum"] is False
        assert result["status"] == "FAIL"

        write_verification_report(result, json_path)
        with open(json_path, 'r') as f:
            loaded = json.load(f)
        assert loaded == result


def test_verify_sample_size_missing_column():
    """Test that verification raises error if participant_id is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "cleaned.csv")
        # Create CSV without participant_id
        df = pd.DataFrame({
            "interface_type": ["traditional", "explainable"],
            "value": [10, 20]
        })
        df.to_csv(csv_path, index=False)

        df_loaded = pd.read_csv(csv_path)

        with pytest.raises(ValueError, match="must contain 'participant_id'"):
            verify_sample_size(df_loaded)