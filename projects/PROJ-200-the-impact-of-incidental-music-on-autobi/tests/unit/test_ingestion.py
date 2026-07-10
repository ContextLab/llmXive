"""
Unit tests for data ingestion functions.

Tests:
  test_birth_year_filtering: Verifies filtering for valid birth years.
  test_exposure_score_calculation: Verifies exposure score calculation (0 listens = 0.0).
  test_fallback_trigger: Verifies fallback "global exposure" trigger when >50% missing birth years.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data_ingestion import filter_cohort, handle_fallback, calculate_ratio_score

class TestBirthYearFiltering:
    """Tests for birth year filtering logic."""

    def test_birth_year_filtering(self):
        """Test that records without birth_year are filtered out."""
        df = pd.DataFrame({
            'track_id': [1, 2, 3, 4],
            'birth_year': [1990, None, 1995, 1980],
            'listen_year': [2010, 2011, 2012, 2013]
        })

        result = filter_cohort(df, birth_year_col='birth_year')

        assert len(result) == 3
        assert result['birth_year'].notna().all()

    def test_birth_year_conversion_to_int(self):
        """Test that birth_year is converted to integer."""
        df = pd.DataFrame({
            'track_id': [1, 2, 3],
            'birth_year': [1990.0, 1995.0, 1980.0],
            'listen_year': [2010, 2011, 2012]
        })

        result = filter_cohort(df, birth_year_col='birth_year')

        assert result['birth_year'].dtype == np.int64

class TestExposureScoreCalculation:
    """Tests for exposure score calculation."""

    def test_zero_listens_score(self):
        """Test that 0 adolescent listens results in score of 0.0."""
        df = pd.DataFrame({
            'track_id': [1, 1, 1],
            'listen_year': [2005, 2005, 2005],
            'early_adolescence_start': [2000, 2000, 2000],
            'early_adolescence_end': [2004, 2004, 2004],
            'late_adolescence_start': [2005, 2005, 2005],
            'late_adolescence_end': [2009, 2009, 2009],
            'is_adolescent_listen': [False, False, False]
        })

        result = calculate_ratio_score(df)

        assert result['adolescent_exposure_score'].iloc[0] == 0.0

    def test_full_adolescent_listens_score(self):
        """Test that all adolescent listens results in score of 1.0."""
        df = pd.DataFrame({
            'track_id': [1, 1, 1],
            'listen_year': [2002, 2003, 2004],
            'early_adolescence_start': [2000, 2000, 2000],
            'early_adolescence_end': [2004, 2004, 2004],
            'late_adolescence_start': [2005, 2005, 2005],
            'late_adolescence_end': [2009, 2009, 2009],
            'is_adolescent_listen': [True, True, True]
        })

        result = calculate_ratio_score(df)

        assert result['adolescent_exposure_score'].iloc[0] == 1.0

class TestFallbackTrigger:
    """Tests for fallback global exposure trigger."""

    def test_fallback_triggered(self):
        """Test that fallback is triggered when >50% missing birth years."""
        df = pd.DataFrame({
            'track_id': [1, 2, 3, 4, 5],
            'birth_year': [1990, None, None, None, 1995]
        })

        result = handle_fallback(df, birth_year_col='birth_year')

        assert 'adolescent_exposure_score' in result.columns
        assert result['adolescent_exposure_score'].iloc[0] == 0.5

    def test_fallback_not_triggered(self):
        """Test that fallback is not triggered when <50% missing birth years."""
        df = pd.DataFrame({
            'track_id': [1, 2, 3, 4, 5],
            'birth_year': [1990, 1991, 1992, None, 1995]
        })

        result = handle_fallback(df, birth_year_col='birth_year')

        assert 'adolescent_exposure_score' not in result.columns