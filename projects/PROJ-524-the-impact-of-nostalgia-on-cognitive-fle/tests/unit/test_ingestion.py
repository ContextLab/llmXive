"""
Unit tests for code/ingestion.py data loading and validation functions.
Tests dataset loading, filtering, and exclusion logic.
"""
import pytest
import pandas as pd
import numpy as np
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.ingestion import (
    validate_and_filter_dataset,
    save_exclusion_log
)


class TestValidateAndFilterDataset:
    def test_filter_age_65_plus(self):
        """Test filtering for age >= 65."""
        data = {
            'participant_id': ['P1', 'P2', 'P3', 'P4'],
            'age': [60, 65, 70, 80],
            'stimulus_type': ['nostalgia', 'control', 'nostalgia', 'control'],
            'perseverative_errors': [10, 12, 8, 15],
            'categories_completed': [5, 6, 7, 4]
        }
        df = pd.DataFrame(data)

        result = validate_and_filter_dataset(df)

        assert len(result) == 3  # P2, P3, P4
        assert all(result['age'] >= 65)

    def test_filter_missing_stimulus_type(self):
        """Test exclusion of records with missing stimulus_type."""
        data = {
            'participant_id': ['P1', 'P2', 'P3'],
            'age': [65, 70, 75],
            'stimulus_type': ['nostalgia', None, 'control'],
            'perseverative_errors': [10, 12, 8],
            'categories_completed': [5, 6, 7]
        }
        df = pd.DataFrame(data)

        result = validate_and_filter_dataset(df)

        assert len(result) == 2  # P1, P3
        assert all(result['stimulus_type'].notna())

    def test_filter_missing_cognitive_scores(self):
        """Test exclusion of records with missing cognitive scores."""
        data = {
            'participant_id': ['P1', 'P2', 'P3'],
            'age': [65, 70, 75],
            'stimulus_type': ['nostalgia', 'control', 'nostalgia'],
            'perseverative_errors': [10, None, 8],
            'categories_completed': [5, 6, None]
        }
        df = pd.DataFrame(data)

        result = validate_and_filter_dataset(df)

        assert len(result) == 1  # Only P1

    def test_combined_filtering(self):
        """Test combined filtering for age, stimulus, and scores."""
        data = {
            'participant_id': ['P1', 'P2', 'P3', 'P4', 'P5'],
            'age': [60, 65, 70, 75, 80],
            'stimulus_type': ['nostalgia', 'control', None, 'nostalgia', 'control'],
            'perseverative_errors': [10, 12, 8, None, 15],
            'categories_completed': [5, 6, 7, 4, None]
        }
        df = pd.DataFrame(data)

        result = validate_and_filter_dataset(df)

        # Only P2 and P4 should pass (P1 age<65, P3 missing stimulus, P4 missing score, P5 missing score)
        # Actually: P2 (65, control, 12, 6) passes. P4 (75, nostalgia, None, 4) fails due to missing score.
        # P5 (80, control, 15, None) fails due to missing score.
        # Only P2 passes.
        assert len(result) == 1
        assert result.iloc[0]['participant_id'] == 'P2'

    def test_missing_age_field(self):
        """Test handling of missing age column."""
        data = {
            'participant_id': ['P1', 'P2'],
            'stimulus_type': ['nostalgia', 'control'],
            'perseverative_errors': [10, 12]
        }
        df = pd.DataFrame(data)

        # Should raise or return empty with error logged
        result = validate_and_filter_dataset(df)
        assert len(result) == 0  # No valid records


class TestSaveExclusionLog:
    def test_save_exclusion_log_basic(self):
        """Test saving exclusion log with basic counts."""
        exclusion_data = {
            'ERR_MISSING_AGE_FIELD': 5,
            'ERR_MISSING_BIRTH_YEAR': 2,
            'ERR_MISSING_SCORE': 3
        }

        with patch('code.ingestion.Path') as mock_path:
            mock_path.return_value.parent.mkdir.return_value = None
            mock_file = MagicMock()
            mock_path.return_value.open.return_value.__enter__.return_value = mock_file

            save_exclusion_log(exclusion_data, 'data/processed/exclusion_log.json')

            mock_file.write.assert_called_once()

    def test_save_exclusion_log_empty(self):
        """Test saving empty exclusion log."""
        exclusion_data = {}

        with patch('code.ingestion.Path') as mock_path:
            mock_path.return_value.parent.mkdir.return_value = None
            mock_file = MagicMock()
            mock_path.return_value.open.return_value.__enter__.return_value = mock_file

            save_exclusion_log(exclusion_data, 'data/processed/exclusion_log.json')

            mock_file.write.assert_called_once()
