"""
Unit tests for data_ingestion.py
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data_ingestion import _find_participant_id_column, impute_missing_values, filter_primary_outcomes


class TestFindParticipantIdColumn:
    """Test the logic for finding the participant ID column."""

    def test_priority_participant_id(self):
        """Test that 'participant_id' is chosen if present."""
        df = pd.DataFrame({'participant_id': [1, 2], 'eid': [10, 20], 'subject_id': [100, 200]})
        assert _find_participant_id_column(df) == 'participant_id'

    def test_priority_eid_over_subject_id(self):
        """Test that 'eid' is chosen over 'subject_id' if 'participant_id' is missing."""
        df = pd.DataFrame({'eid': [1, 2], 'subject_id': [10, 20]})
        assert _find_participant_id_column(df) == 'eid'

    def test_priority_subject_id(self):
        """Test that 'subject_id' is chosen if it's the only option."""
        df = pd.DataFrame({'subject_id': [1, 2]})
        assert _find_participant_id_column(df) == 'subject_id'

    def test_no_id_column_raises(self):
        """Test that FileNotFoundError is raised if no ID column is found."""
        df = pd.DataFrame({'age': [1, 2], 'sex': ['M', 'F']})
        with pytest.raises(FileNotFoundError):
            _find_participant_id_column(df)


class TestImputation:
    """Test imputation logic."""

    def test_imputation_sex_mode_returns_most_frequent(self):
        """Test that Sex is imputed using Mode (most frequent)."""
        # Fixture data: majority 'M', minority 'F', one NaN
        df = pd.DataFrame({
            'age': [25, 30, 35, 40],
            'sex': ['M', 'M', 'M', np.nan],  # Mode is 'M'
            'bmi': [22.0, 24.0, 25.0, 26.0]
        })

        result = impute_missing_values(df)

        # Check that the NaN was filled with 'M'
        assert result['sex'].iloc[3] == 'M'
        # Check that no NaNs remain in sex
        assert result['sex'].isnull().sum() == 0

    def test_imputation_age_median(self):
        """Test that Age is imputed using Median."""
        df = pd.DataFrame({
            'age': [20, 30, 40, np.nan],  # Median of [20, 30, 40] is 30
            'sex': ['M', 'F', 'M', 'M']
        })

        result = impute_missing_values(df)

        # Check that the NaN was filled with 30
        assert result['age'].iloc[3] == 30.0

    def test_imputation_bmi_median(self):
        """Test that BMI is imputed using Median."""
        df = pd.DataFrame({
            'bmi': [20.0, 25.0, 30.0, np.nan],  # Median is 25.0
            'age': [20, 30, 40, 50]
        })

        result = impute_missing_values(df)

        assert result['bmi'].iloc[3] == 25.0


class TestFiltering:
    """Test filtering logic."""

    def test_filtering_excludes_null_primary_outcomes(self):
        """Test that rows with null fluid_intelligence are excluded."""
        df = pd.DataFrame({
            'participant_id': [1, 2, 3, 4],
            'fluid_intelligence': [100.0, 110.0, np.nan, 120.0],
            'shannon_index': [3.0, 3.5, 4.0, 3.2],
            'age': [20, 30, 40, 50]
        })

        result = filter_primary_outcomes(df)

        # Should have 3 rows (index 0, 1, 3)
        assert len(result) == 3
        # The row with null fluid_intelligence should be gone
        assert 2 not in result.index

    def test_filtering_excludes_null_dqs_if_present(self):
        """Test that rows with null DQS are excluded if DQS column exists."""
        df = pd.DataFrame({
            'participant_id': [1, 2, 3],
            'fluid_intelligence': [100.0, 110.0, 120.0],
            'dqs': [50.0, np.nan, 60.0]
        })

        result = filter_primary_outcomes(df)

        # Should have 2 rows
        assert len(result) == 2
        # Row with null DQS (index 1) should be gone
        assert 1 not in result.index
