"""
Unit tests for data_loader module.

These tests verify that the data loader correctly:
1. Loads raw pilot data (real or mock)
2. Validates data integrity
3. Computes accuracy metrics
4. Aggregates results by stimulus
"""

import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from analysis.data_loader import (
    load_raw_judgments,
    validate_judgments,
    compute_accuracy,
    aggregate_judgments,
    RAW_COLUMNS,
    AGGREGATE_COLUMNS
)


def create_mock_pilot_csv(filepath: Path, n_participants: int = 5, n_stimuli: int = 10):
    """Helper to create a mock pilot CSV for testing."""
    np.random.seed(42)

    participants = [f"p{i:03d}" for i in range(1, n_participants + 1)]
    stimuli = [f"stim_{i:03d}" for i in range(1, n_stimuli + 1)]
    emotions = ['happy', 'sad', 'angry', 'fearful', 'neutral']

    data = []
    for p_id in participants:
        for s_id in stimuli:
            true_label = np.random.choice(emotions)
            # Simulate ~70% accuracy
            response_label = true_label if np.random.random() < 0.7 else np.random.choice(emotions)
            data.append({
                'participant_id': p_id,
                'stimulus_id': s_id,
                'true_label': true_label,
                'response_label': response_label,
                'timestamp': '2026-01-01T12:00:00'
            })

    df = pd.DataFrame(data)
    df.to_csv(filepath, index=False)
    return df


def create_mock_manifest(filepath: Path, stimuli: list):
    """Helper to create a mock stimuli manifest for testing."""
    manifest = []
    for i, s_id in enumerate(stimuli):
        manifest.append({
            'stimulus_id': s_id,
            'emotion_label': ['happy', 'sad', 'angry', 'fearful', 'neutral'][i % 5],
            'flanker_count': [3, 5, 7, 9, 11][i % 5]
        })

    with open(filepath, 'w') as f:
        json.dump(manifest, f, indent=2)


class TestDataLoader:
    """Test suite for data_loader module."""

    def test_load_raw_judgments_valid_file(self, tmp_path):
        """Test loading a valid pilot CSV file."""
        mock_csv = tmp_path / "mock_pilot.csv"
        create_mock_pilot_csv(mock_csv, n_participants=5, n_stimuli=10)

        # Temporarily set MOCK_CSV for the test
        import analysis.data_loader as dl
        original_mock_csv = dl.MOCK_CSV
        dl.MOCK_CSV = mock_csv

        try:
            df = load_raw_judgments(mock_csv, test_mode=True)
            assert len(df) == 50  # 5 participants * 10 stimuli
            assert set(df.columns) == set(RAW_COLUMNS)
            assert df['participant_id'].nunique() == 5
        finally:
            dl.MOCK_CSV = original_mock_csv

    def test_load_raw_judgments_missing_file(self, tmp_path):
        """Test loading a non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            load_raw_judgments(tmp_path / "nonexistent.csv", test_mode=False)

    def test_load_raw_judgments_missing_columns(self, tmp_path):
        """Test that missing columns raise an error."""
        df = pd.DataFrame({'wrong_col': [1, 2, 3]})
        csv_path = tmp_path / "bad.csv"
        df.to_csv(csv_path, index=False)

        with pytest.raises(ValueError, match="Missing required columns"):
            load_raw_judgments(csv_path, test_mode=False)

    def test_load_raw_judgments_empty_file(self, tmp_path):
        """Test that an empty file raises an error."""
        df = pd.DataFrame(columns=RAW_COLUMNS)
        csv_path = tmp_path / "empty.csv"
        df.to_csv(csv_path, index=False)

        with pytest.raises(ValueError, match="Raw pilot data file is empty"):
            load_raw_judgments(csv_path, test_mode=False)

    def test_validate_judgments_valid_data(self, tmp_path):
        """Test validation of valid data passes."""
        mock_csv = tmp_path / "valid.csv"
        create_mock_pilot_csv(mock_csv, n_participants=5, n_stimuli=10)

        df = load_raw_judgments(mock_csv, test_mode=True)
        assert validate_judgments(df) is True

    def test_validate_judgments_null_values(self, tmp_path):
        """Test validation fails with null values."""
        df = pd.DataFrame({
            'participant_id': ['p1', None, 'p3'],
            'stimulus_id': ['s1', 's2', 's3'],
            'true_label': ['happy', 'sad', 'angry'],
            'response_label': ['happy', 'sad', 'angry'],
            'timestamp': ['t1', 't2', 't3']
        })

        assert validate_judgments(df) is False

    def test_compute_accuracy(self, tmp_path):
        """Test accuracy computation."""
        mock_csv = tmp_path / "acc_test.csv"
        df = create_mock_pilot_csv(mock_csv, n_participants=2, n_stimuli=2)

        result_df = compute_accuracy(df)

        assert 'correct' in result_df.columns
        assert result_df['correct'].dtype in [np.int64, np.int32]
        assert all(result_df['correct'].isin([0, 1]))

    def test_aggregate_judgments(self, tmp_path):
        """Test aggregation of judgments."""
        mock_csv = tmp_path / "agg_test.csv"
        mock_manifest = tmp_path / "manifest.json"

        n_stimuli = 5
        create_mock_pilot_csv(mock_csv, n_participants=5, n_stimuli=n_stimuli)
        create_mock_manifest(mock_manifest, [f"stim_{i:03d}" for i in range(1, n_stimuli + 1)])

        df = load_raw_judgments(mock_csv, test_mode=True)
        df = compute_accuracy(df)

        aggregated = aggregate_judgments(df, mock_manifest)

        assert len(aggregated) == n_stimuli
        assert set(aggregated.columns) == set(AGGREGATE_COLUMNS)
        assert all(aggregated['accuracy'].between(0, 1))
        assert all(aggregated['n_trials'] == 5)  # 5 participants per stimulus

    def test_aggregate_judgments_no_manifest(self, tmp_path):
        """Test aggregation without manifest uses fallback values."""
        mock_csv = tmp_path / "no_manifest_test.csv"
        create_mock_pilot_csv(mock_csv, n_participants=2, n_stimuli=2)

        df = load_raw_judgments(mock_csv, test_mode=True)
        df = compute_accuracy(df)

        aggregated = aggregate_judgments(df, None)

        assert len(aggregated) == 2
        assert all(aggregated['emotion_label'] == 'unknown')
        assert all(aggregated['flanker_count'] == 0)

    def test_aggregate_judgments_null_in_output(self, tmp_path):
        """Test that aggregation fails if it produces null values."""
        # Create data that might cause issues
        df = pd.DataFrame({
            'participant_id': ['p1', 'p2'],
            'stimulus_id': ['s1', 's1'],  # Same stimulus
            'true_label': ['happy', 'happy'],
            'response_label': ['happy', 'happy'],
            'timestamp': ['t1', 't2'],
            'correct': [1, 1]
        })

        # This should work fine
        aggregated = aggregate_judgments(df, None)
        assert not aggregated.isnull().any().any()

    def test_integration_full_pipeline(self, tmp_path):
        """Integration test: full load -> validate -> compute -> aggregate pipeline."""
        mock_csv = tmp_path / "integration_test.csv"
        mock_manifest = tmp_path / "manifest.json"

        n_participants = 6
        n_stimuli = 8

        create_mock_pilot_csv(mock_csv, n_participants=n_participants, n_stimuli=n_stimuli)
        create_mock_manifest(mock_manifest, [f"stim_{i:03d}" for i in range(1, n_stimuli + 1)])

        # Full pipeline
        raw_df = load_raw_judgments(mock_csv, test_mode=True)
        assert validate_judgments(raw_df)

        raw_df = compute_accuracy(raw_df)
        aggregated = aggregate_judgments(raw_df, mock_manifest)

        # Verify final output
        assert len(aggregated) == n_stimuli
        assert aggregated['accuracy'].mean() > 0  # Should have some accuracy
        assert aggregated['n_trials'].sum() == n_participants * n_stimuli
        assert all(aggregated['flanker_count'] > 0)  # From manifest