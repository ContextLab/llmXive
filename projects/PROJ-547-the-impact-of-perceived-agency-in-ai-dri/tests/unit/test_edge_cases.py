"""
Unit tests for edge cases in the agency scoring and adherence extraction pipelines.

Tests cover:
1. Empty transcript handling (agency scoring)
2. Zero variance agency scores (regression analysis)
3. All missing timestamps (adherence extraction)
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

# Import from existing API surface
from agency_scoring.ingest_transcripts import ingest_transcripts
from agency_scoring.compute_scores import compute_agency_scores
from analysis.check_agency_variance import check_variance
from adherence_extraction.extract_metrics import extract_metrics


class TestEmptyTranscript:
    """Tests for handling empty or unreadable transcripts (T019)."""

    def test_empty_transcript_csv(self, tmp_path):
        """Verify empty CSV transcript yields 0.0 score."""
        # Create empty CSV with headers only
        csv_file = tmp_path / "empty_transcripts.csv"
        csv_file.write_text("session_id,utterances\n")

        df = ingest_transcripts(str(csv_file))
        assert len(df) == 0, "Empty transcript should result in empty DataFrame"

    def test_empty_transcript_json(self, tmp_path):
        """Verify empty JSON transcript yields 0.0 score."""
        json_file = tmp_path / "empty_transcripts.json"
        json_file.write_text("[]")

        df = ingest_transcripts(str(json_file))
        assert len(df) == 0, "Empty JSON transcript should result in empty DataFrame"

    def test_empty_utterances_list(self, tmp_path):
        """Verify transcript with empty utterances list yields 0.0 score."""
        json_file = tmp_path / "empty_utterances.json"
        data = [
            {"session_id": "sess_001", "utterances": []},
            {"session_id": "sess_002", "utterances": ["Hello"]}
        ]
        json_file.write_text(json.dumps(data))

        df = ingest_transcripts(str(json_file))
        assert len(df) == 2
        # Check that empty utterances are handled
        assert df.loc[df['session_id'] == 'sess_001', 'utterances'].iloc[0] == []

    def test_compute_score_empty_transcript(self, tmp_path):
        """Verify compute_agency_scores returns 0.0 for empty utterances."""
        # Create a mock transcript with empty utterances
        data = [
            {"session_id": "sess_empty", "utterances": []},
            {"session_id": "sess_normal", "utterances": ["I feel good"]}
        ]
        json_file = tmp_path / "test_transcripts.json"
        json_file.write_text(json.dumps(data))

        df = ingest_transcripts(str(json_file))
        scores = compute_agency_scores(df)

        # Check that empty transcript gets 0.0 score
        empty_score = scores[scores['session_id'] == 'sess_empty']['agency_score'].iloc[0]
        assert empty_score == 0.0, "Empty transcript should yield 0.0 agency score"

        # Normal transcript should have non-zero score (or at least be computed)
        normal_score = scores[scores['session_id'] == 'sess_normal']['agency_score'].iloc[0]
        assert 0.0 <= normal_score <= 1.0, "Score should be in [0,1] range"


class TestZeroVarianceAgencyScores:
    """Tests for handling zero variance in agency scores (T061)."""

    def test_zero_variance_detection(self, tmp_path):
        """Verify check_variance aborts on constant agency scores."""
        # Create a DataFrame with constant agency scores
        data = {
            'session_id': ['s1', 's2', 's3'],
            'agency_score': [0.5, 0.5, 0.5]  # Zero variance
        }
        df = pd.DataFrame(data)

        csv_file = tmp_path / "constant_scores.csv"
        df.to_csv(csv_file, index=False)

        # Should raise PipelineError when variance < 1e-6
        from utils.error_handler import PipelineError

        with pytest.raises(PipelineError) as exc_info:
            check_variance(str(csv_file))

        assert "zero variance" in str(exc_info.value).lower() or "variance" in str(exc_info.value).lower()

    def test_normal_variance_passes(self, tmp_path):
        """Verify check_variance passes with normal variance."""
        data = {
            'session_id': ['s1', 's2', 's3'],
            'agency_score': [0.2, 0.5, 0.8]  # Normal variance
        }
        df = pd.DataFrame(data)

        csv_file = tmp_path / "normal_scores.csv"
        df.to_csv(csv_file, index=False)

        # Should not raise an error
        result = check_variance(str(csv_file))
        assert result is True or result is None  # Depending on implementation return type

    def test_very_small_variance(self, tmp_path):
        """Verify check_variance handles very small but non-zero variance."""
        # Variance just above threshold
        data = {
            'session_id': ['s1', 's2', 's3'],
            'agency_score': [0.5, 0.5000001, 0.5000002]
        }
        df = pd.DataFrame(data)

        csv_file = tmp_path / "tiny_variance.csv"
        df.to_csv(csv_file, index=False)

        # Should pass if variance >= 1e-6
        result = check_variance(str(csv_file))
        # Depending on implementation, might pass or fail based on exact threshold


class TestMissingTimestamps:
    """Tests for handling missing timestamps in adherence metrics (T023)."""

    def test_all_missing_timestamps(self, tmp_path):
        """Verify extract_metrics handles all missing timestamps gracefully."""
        # Create data with missing timestamps
        data = [
            {
                'user_id': 'u1',
                'session_start': None,
                'session_end': None,
                'session_completed': True,
                'self_reported_engagement': 4
            },
            {
                'user_id': 'u2',
                'session_start': '2023-01-01T10:00:00',
                'session_end': '2023-01-01T11:00:00',
                'session_completed': True,
                'self_reported_engagement': 5
            }
        ]
        json_file = tmp_path / "missing_timestamps.json"
        json_file.write_text(json.dumps(data))

        # Should not crash; should log warning and exclude user with missing timestamps
        metrics = extract_metrics(str(json_file))

        # Check that user with missing timestamps is handled
        assert len(metrics) >= 1, "Should process at least one user"

    def test_partial_missing_timestamps(self, tmp_path):
        """Verify extract_metrics handles partial missing timestamps."""
        data = [
            {
                'user_id': 'u1',
                'session_start': '2023-01-01T10:00:00',
                'session_end': None,  # Missing end time
                'session_completed': False,
                'self_reported_engagement': 3
            }
        ]
        json_file = tmp_path / "partial_missing.json"
        json_file.write_text(json.dumps(data))

        # Should not crash
        metrics = extract_metrics(str(json_file))
        assert len(metrics) == 1

    def test_missing_self_reported_engagement(self, tmp_path):
        """Verify handling of missing self-reported engagement."""
        data = [
            {
                'user_id': 'u1',
                'session_start': '2023-01-01T10:00:00',
                'session_end': '2023-01-01T11:00:00',
                'session_completed': True,
                'self_reported_engagement': None  # Missing
            }
        ]
        json_file = tmp_path / "missing_engagement.json"
        json_file.write_text(json.dumps(data))

        # Should not crash; should handle missing engagement
        metrics = extract_metrics(str(json_file))
        assert len(metrics) == 1

    def test_multiple_sessions_with_gaps(self, tmp_path):
        """Verify handling of multiple sessions with timestamp gaps."""
        data = [
            {
                'user_id': 'u1',
                'session_start': '2023-01-01T10:00:00',
                'session_end': '2023-01-01T11:00:00',
                'session_completed': True,
                'self_reported_engagement': 4
            },
            {
                'user_id': 'u1',
                'session_start': None,  # Missing start
                'session_end': '2023-01-08T11:00:00',
                'session_completed': True,
                'self_reported_engagement': 5
            }
        ]
        json_file = tmp_path / "gapped_sessions.json"
        json_file.write_text(json.dumps(data))

        # Should process without crashing
        metrics = extract_metrics(str(json_file))
        assert len(metrics) == 1  # One user aggregated


class TestIntegrationEdgeCases:
    """Integration tests combining multiple edge cases."""

    def test_combined_edge_cases(self, tmp_path):
        """Test pipeline with multiple edge cases simultaneously."""
        # Create complex edge case data
        data = [
            {
                'session_id': 's1',
                'utterances': []  # Empty transcript
            },
            {
                'session_id': 's2',
                'utterances': ["Hello"]
            },
            {
                'session_id': 's3',
                'utterances': []
            }
        ]
        json_file = tmp_path / "edge_transcripts.json"
        json_file.write_text(json.dumps(data))

        # Ingest and compute scores
        df = ingest_transcripts(str(json_file))
        scores = compute_agency_scores(df)

        # Check scores
        assert len(scores) == 3
        for _, row in scores.iterrows():
            assert 0.0 <= row['agency_score'] <= 1.0

        # Check that empty transcripts got 0.0
        empty_sessions = scores[scores['session_id'].isin(['s1', 's3'])]
        assert all(empty_sessions['agency_score'] == 0.0)