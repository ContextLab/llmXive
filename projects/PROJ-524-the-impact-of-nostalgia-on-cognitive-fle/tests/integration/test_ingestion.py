import os
import json
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# Mock config for testing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from ingestion import validate_and_filter_dataset, save_exclusion_log

class TestIngestionValidation:
    def setup_method(self):
        # Create a sample dataframe for testing
        self.raw_data = pd.DataFrame({
            'participant_id': ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7'],
            'age': [70, 60, None, 65, 75, None, 80],
            'birth_year': [1954, 1964, 1960, 1959, 1949, 1950, 1944],
            'perseverative_errors': [10, 20, 30, 40, 50, None, 60],
            'categories_completed': [5, 3, 4, 2, 1, 6, 3],
            'stimulus_type': ['nostalgia', 'control', 'nostalgia', 'control', 'nostalgia', 'control', 'nostalgia']
        })

    def test_valid_age_filtering(self):
        """Test that records with age < 65 are excluded."""
        df, exclusions = validate_and_filter_dataset(self.raw_data)
        assert len(df) == 5  # P1, P4, P5, P6 (if birth_year valid), P7
        # P2 (age 60) excluded
        # P3 (age None, birth_year 1960 -> 64) excluded
        # P6 (age None, birth_year 1950 -> 74) included?
        # Wait, 2024 - 1950 = 74. So P6 should be included.
        # Let's re-calculate:
        # P1: 70 -> Valid
        # P2: 60 -> Invalid
        # P3: None, 1960 -> 64 -> Invalid
        # P4: 65 -> Valid
        # P5: 75 -> Valid
        # P6: None, 1950 -> 74 -> Valid
        # P7: 80 -> Valid
        # Total valid: 5 (P1, P4, P5, P6, P7)
        assert len(df) == 5
        assert 'P2' not in df['participant_id'].values
        assert 'P3' not in df['participant_id'].values

    def test_missing_age_and_birth_year(self):
        """Test exclusion when both age and birth_year are missing."""
        data = pd.DataFrame({
            'participant_id': ['P1', 'P2'],
            'age': [None, None],
            'birth_year': [None, None],
            'perseverative_errors': [10, 20],
            'categories_completed': [5, 6]
        })
        df, exclusions = validate_and_filter_dataset(data)
        assert len(df) == 0
        assert exclusions['ERR_MISSING_BIRTH_YEAR'] == 2
        assert exclusions['total_excluded'] == 2

    def test_missing_score_exclusion(self):
        """Test exclusion when cognitive scores are missing."""
        data = pd.DataFrame({
            'participant_id': ['P1', 'P2'],
            'age': [70, 75],
            'perseverative_errors': [None, 20],
            'categories_completed': [None, 6]
        })
        df, exclusions = validate_and_filter_dataset(data)
        assert len(df) == 1
        assert df['participant_id'].iloc[0] == 'P2'
        assert exclusions['ERR_MISSING_SCORE'] == 1

    def test_exclusion_log_structure(self):
        """Test that the exclusion log has the correct structure."""
        df, exclusions = validate_and_filter_dataset(self.raw_data)
        assert 'ERR_MISSING_AGE_FIELD' in exclusions
        assert 'ERR_MISSING_BIRTH_YEAR' in exclusions
        assert 'ERR_MISSING_SCORE' in exclusions
        assert 'total_raw' in exclusions
        assert 'total_excluded' in exclusions

    def test_save_exclusion_log(self):
        """Test saving the exclusion log to a file."""
        df, exclusions = validate_and_filter_dataset(self.raw_data)
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'exclusion_log.json')
            save_exclusion_log(exclusions, output_path)
            assert os.path.exists(output_path)
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            assert loaded == exclusions
