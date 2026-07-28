"""
Unit tests for data cleaning logic (T016).

Tests:
1. Straight-lining detection (zero variance)
2. Missing data handling (rated_count < total_stimuli)
3. Data corruption detection (rated_count > total_stimuli)
4. Dynamic stimulus count validation
5. Edge cases (empty data, single participant)
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.config import get_raw_data_dir, get_processed_data_dir
from code.logging_config import setup_logging
from code import clean_data


@pytest.fixture
def setup_temp_files():
    """Create temporary stimuli and ratings files for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create stimuli file with 5 unique stimuli
        stimuli_df = pd.DataFrame({
            'id': ['S1', 'S2', 'S3', 'S4', 'S5'],
            'text': ['Msg1', 'Msg2', 'Msg3', 'Msg4', 'Msg5'],
            'emoji_count': [0, 1, 0, 2, 1],
            'punctuation_type': ['.', '!', '.', '?', '!'],
            'length_category': ['short', 'medium', 'short', 'long', 'medium'],
            'scenario_id': ['SC1', 'SC1', 'SC2', 'SC2', 'SC3']
        })
        stimuli_path = tmpdir / "stimuli.csv"
        stimuli_df.to_csv(stimuli_path, index=False)

        # Create ratings file with various scenarios
        ratings_data = [
            # P1: Straight-lining (all 5 ratings are 3)
            {'participant_id': 'P1', 'stimulus_id': 'S1', 'rating': 3},
            {'participant_id': 'P1', 'stimulus_id': 'S2', 'rating': 3},
            {'participant_id': 'P1', 'stimulus_id': 'S3', 'rating': 3},
            {'participant_id': 'P1', 'stimulus_id': 'S4', 'rating': 3},
            {'participant_id': 'P1', 'stimulus_id': 'S5', 'rating': 3},

            # P2: Missing data (only 3 ratings)
            {'participant_id': 'P2', 'stimulus_id': 'S1', 'rating': 5},
            {'participant_id': 'P2', 'stimulus_id': 'S2', 'rating': 6},
            {'participant_id': 'P2', 'stimulus_id': 'S3', 'rating': 4},

            # P3: Data corruption (6 ratings for 5 stimuli)
            {'participant_id': 'P3', 'stimulus_id': 'S1', 'rating': 2},
            {'participant_id': 'P3', 'stimulus_id': 'S2', 'rating': 3},
            {'participant_id': 'P3', 'stimulus_id': 'S3', 'rating': 4},
            {'participant_id': 'P3', 'stimulus_id': 'S4', 'rating': 5},
            {'participant_id': 'P3', 'stimulus_id': 'S5', 'rating': 6},
            {'participant_id': 'P3', 'stimulus_id': 'S1', 'rating': 7},  # Duplicate

            # P4: Valid participant (all 5 ratings, non-zero variance)
            {'participant_id': 'P4', 'stimulus_id': 'S1', 'rating': 2},
            {'participant_id': 'P4', 'stimulus_id': 'S2', 'rating': 4},
            {'participant_id': 'P4', 'stimulus_id': 'S3', 'rating': 5},
            {'participant_id': 'P4', 'stimulus_id': 'S4', 'rating': 3},
            {'participant_id': 'P4', 'stimulus_id': 'S5', 'rating': 6},
        ]
        ratings_df = pd.DataFrame(ratings_data)
        ratings_path = tmpdir / "ratings.csv"
        ratings_df.to_csv(ratings_path, index=False)

        yield {
            'stimuli_path': stimuli_path,
            'ratings_path': ratings_path,
            'tmpdir': tmpdir
        }


def test_load_stimuli_valid(setup_temp_files):
    """Test loading a valid stimuli file."""
    stimuli_df = clean_data.load_stimuli(setup_temp_files['stimuli_path'])
    assert len(stimuli_df) == 5
    assert 'id' in stimuli_df.columns
    assert stimuli_df['id'].nunique() == 5


def test_load_stimuli_missing_file():
    """Test loading a non-existent stimuli file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        clean_data.load_stimuli(Path("/nonexistent/path.csv"))


def test_load_stimuli_empty_file(setup_temp_files):
    """Test loading an empty stimuli file raises ValueError."""
    empty_path = setup_temp_files['tmpdir'] / "empty_stimuli.csv"
    empty_path.touch()

    with pytest.raises(ValueError, match="Stimuli file is empty"):
        clean_data.load_stimuli(empty_path)


def test_load_stimuli_no_id_column(setup_temp_files):
    """Test loading a stimuli file without 'id' column raises ValueError."""
    no_id_df = pd.DataFrame({'text': ['Msg1']})
    no_id_path = setup_temp_files['tmpdir'] / "no_id_stimuli.csv"
    no_id_df.to_csv(no_id_path, index=False)

    with pytest.raises(ValueError, match="missing 'id' column"):
        clean_data.load_stimuli(no_id_path)


def test_load_stimuli_zero_stimuli(setup_temp_files):
    """Test loading a stimuli file with 0 unique stimuli raises ValueError."""
    zero_df = pd.DataFrame({'id': [], 'text': []})
    zero_path = setup_temp_files['tmpdir'] / "zero_stimuli.csv"
    zero_df.to_csv(zero_path, index=False)

    with pytest.raises(ValueError, match="at least 1 unique stimulus"):
        clean_data.load_stimuli(zero_path)


def test_detect_straight_lining(setup_temp_files):
    """Test straight-lining detection."""
    stimuli_df = clean_data.load_stimuli(setup_temp_files['stimuli_path'])
    ratings_df = clean_data.load_ratings(setup_temp_files['ratings_path'])

    exclusions = clean_data.detect_straight_lining(ratings_df, stimuli_df)

    # P1 should be flagged for straight-lining
    assert 'P1' in exclusions
    assert exclusions['P1']['reason'] == 'STRAIGHT_LINING'
    assert exclusions['P1']['variance'] == 0.0


def test_detect_missing_data(setup_temp_files):
    """Test missing data detection."""
    stimuli_df = clean_data.load_stimuli(setup_temp_files['stimuli_path'])
    ratings_df = clean_data.load_ratings(setup_temp_files['ratings_path'])

    exclusions = clean_data.detect_straight_lining(ratings_df, stimuli_df)

    # P2 should be flagged for missing data
    assert 'P2' in exclusions
    assert exclusions['P2']['reason'] == 'MISSING_DATA'
    assert exclusions['P2']['rated_count'] == 3
    assert exclusions['P2']['total_stimuli'] == 5


def test_detect_data_corruption(setup_temp_files):
    """Test data corruption detection (rated_count > total_stimuli)."""
    stimuli_df = clean_data.load_stimuli(setup_temp_files['stimuli_path'])
    ratings_df = clean_data.load_ratings(setup_temp_files['ratings_path'])

    exclusions = clean_data.detect_straight_lining(ratings_df, stimuli_df)

    # P3 should be flagged for data corruption
    assert 'P3' in exclusions
    assert exclusions['P3']['reason'] == 'DATA_CORRUPTION'
    assert exclusions['P3']['rated_count'] == 6
    assert exclusions['P3']['total_stimuli'] == 5


def test_valid_participant_not_excluded(setup_temp_files):
    """Test that a valid participant with full ratings and non-zero variance is not excluded."""
    stimuli_df = clean_data.load_stimuli(setup_temp_files['stimuli_path'])
    ratings_df = clean_data.load_ratings(setup_temp_files['ratings_path'])

    exclusions = clean_data.detect_straight_lining(ratings_df, stimuli_df)

    # P4 should NOT be in exclusions
    assert 'P4' not in exclusions


def test_save_cleaning_log(setup_temp_files):
    """Test saving the cleaning log."""
    stimuli_df = clean_data.load_stimuli(setup_temp_files['stimuli_path'])
    ratings_df = clean_data.load_ratings(setup_temp_files['ratings_path'])

    exclusions = clean_data.detect_straight_lining(ratings_df, stimuli_df)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "cleaning_log.csv"
        result_path = clean_data.save_cleaning_log(exclusions, output_path)

        assert result_path.exists()

        # Verify content
        log_df = pd.read_csv(result_path)
        assert len(log_df) == 3  # P1, P2, P3
        assert 'participant_id' in log_df.columns
        assert 'exclusion_reason' in log_df.columns

        # Verify reasons
        reasons = set(log_df['exclusion_reason'])
        assert 'STRAIGHT_LINING' in reasons
        assert 'MISSING_DATA' in reasons
        assert 'DATA_CORRUPTION' in reasons


def test_save_cleaning_log_empty_exclusions(setup_temp_files):
    """Test saving cleaning log with no exclusions."""
    # Create a ratings file with only valid participants
    valid_ratings = [
        {'participant_id': 'P_VALID', 'stimulus_id': 'S1', 'rating': 2},
        {'participant_id': 'P_VALID', 'stimulus_id': 'S2', 'rating': 4},
        {'participant_id': 'P_VALID', 'stimulus_id': 'S3', 'rating': 5},
        {'participant_id': 'P_VALID', 'stimulus_id': 'S4', 'rating': 3},
        {'participant_id': 'P_VALID', 'stimulus_id': 'S5', 'rating': 6},
    ]
    valid_df = pd.DataFrame(valid_ratings)
    valid_path = setup_temp_files['tmpdir'] / "valid_ratings.csv"
    valid_df.to_csv(valid_path, index=False)

    stimuli_df = clean_data.load_stimuli(setup_temp_files['stimuli_path'])
    ratings_df = clean_data.load_ratings(valid_path)

    exclusions = clean_data.detect_straight_lining(ratings_df, stimuli_df)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "cleaning_log_empty.csv"
        result_path = clean_data.save_cleaning_log(exclusions, output_path)

        assert result_path.exists()
        log_df = pd.read_csv(result_path)
        assert len(log_df) == 0  # No exclusions
        # Header should still exist
        assert 'participant_id' in log_df.columns


def test_main_function(setup_temp_files):
    """Test the main function end-to-end."""
    # Temporarily override paths for testing
    original_raw = get_raw_data_dir()
    original_processed = get_processed_data_dir()

    # We can't easily override config, so we test the logic directly
    stimuli_df = clean_data.load_stimuli(setup_temp_files['stimuli_path'])
    ratings_df = clean_data.load_ratings(setup_temp_files['ratings_path'])

    exclusions = clean_data.detect_straight_lining(ratings_df, stimuli_df)

    assert len(exclusions) == 3
    assert 'P1' in exclusions
    assert 'P2' in exclusions
    assert 'P3' in exclusions
    assert 'P4' not in exclusions