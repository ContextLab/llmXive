"""
Unit tests for User Story 1 (Data Ingestion).
Tests T010, T011, T012.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data_ingestion import (
    filter_cohort,
    calculate_ratio_score,
    handle_fallback,
    apply_frequency_threshold
)

class TestBirthYearFiltering:
    """Test T010: Unit test for birth year filtering logic."""
    
    def test_filter_cohort_removes_invalid_birth_years(self):
        """Test that records without birth_year or outside range are excluded."""
        data = {
            'track_id': [1, 2, 3, 4],
            'birth_year': [1990, None, 1800, 2010], # None, too old, too new
            'listen_year': [2010, 2010, 2000, 2015]
        }
        df = pd.DataFrame(data)
        
        result = filter_cohort(df)
        
        # Should only keep track_id 1 (1990 is valid)
        assert result is not None
        assert len(result) == 1
        assert result.iloc[0]['track_id'] == 1
        assert result.iloc[0]['birth_year'] == 1990

    def test_filter_cohort_calculates_adolescent_window(self):
        """Test that adolescent window is calculated correctly."""
        data = {
            'track_id': [1],
            'birth_year': [1990],
            'listen_year': [2005]
        }
        df = pd.DataFrame(data)
        
        result = filter_cohort(df)
        
        assert 'adolescent_start' in result.columns
        assert 'adolescent_end' in result.columns
        assert result.iloc[0]['adolescent_start'] == 1990 + 10
        assert result.iloc[0]['adolescent_end'] == 1990 + 19
        assert result.iloc[0]['is_adolescent_listen'] == True

class TestExposureScoreCalculation:
    """Test T011: Unit test for exposure score calculation."""
    
    def test_zero_listens_yields_zero_score(self):
        """Test that 0 adolescent listens results in score 0.0."""
        data = {
            'track_id': [1, 1, 1],
            'is_adolescent_listen': [False, False, False],
            'listen_year': [2000, 2001, 2002]
        }
        df = pd.DataFrame(data)
        
        result = calculate_ratio_score(df)
        
        assert result['adolescent_exposure_score'].iloc[0] == 0.0

    def test_all_adolescent_listens_yields_one_score(self):
        """Test that 100% adolescent listens results in score 1.0."""
        data = {
            'track_id': [1, 1, 1],
            'is_adolescent_listen': [True, True, True],
            'listen_year': [2000, 2001, 2002]
        }
        df = pd.DataFrame(data)
        
        result = calculate_ratio_score(df)
        
        assert result['adolescent_exposure_score'].iloc[0] == 1.0

    def test_mixed_listens_yields_correct_ratio(self):
        """Test correct calculation for mixed adolescent/non-adolescent listens."""
        data = {
            'track_id': [1, 1, 1, 1],
            'is_adolescent_listen': [True, True, False, False],
            'listen_year': [2000, 2001, 2002, 2003]
        }
        df = pd.DataFrame(data)
        
        result = calculate_ratio_score(df)
        
        assert result['adolescent_exposure_score'].iloc[0] == 0.5

class TestFallbackTrigger:
    """Test T012: Unit test for fallback 'global exposure' trigger."""
    
    def test_fallback_triggered_when_missing_gt_50(self):
        """Test that fallback is triggered when >50% missing birth years."""
        # 3 valid, 7 missing -> 70% missing
        data = {
            'track_id': list(range(10)),
            'birth_year': [1990, 1991, 1992] + [None] * 7
        }
        df = pd.DataFrame(data)
        
        result = handle_fallback(df)
        assert result is True

    def test_fallback_not_triggered_when_missing_le_50(self):
        """Test that fallback is NOT triggered when <=50% missing birth years."""
        # 5 valid, 5 missing -> 50% missing
        data = {
            'track_id': list(range(10)),
            'birth_year': [1990, 1991, 1992, 1993, 1994] + [None] * 5
        }
        df = pd.DataFrame(data)
        
        result = handle_fallback(df)
        assert result is False

    def test_fallback_triggered_on_empty_df(self):
        """Test that fallback is triggered on empty dataframe."""
        df = pd.DataFrame(columns=['track_id', 'birth_year'])
        result = handle_fallback(df)
        assert result is True

class TestFrequencyThreshold:
    """Test T015 logic (integrated into ingestion)."""
    
    def test_apply_frequency_threshold_filters_low_count(self):
        """Test that tracks with < 10 listens are filtered out."""
        data = {
            'track_id': [1] * 5 + [2] * 15, # Track 1: 5 listens, Track 2: 15 listens
            'listen_year': list(range(20))
        }
        df = pd.DataFrame(data)
        
        result = apply_frequency_threshold(df)
        
        # Should only keep track_id 2
        assert len(result) == 15
        assert result['track_id'].unique()[0] == 2
        
    def test_apply_frequency_threshold_keeps_exact_threshold(self):
        """Test that tracks with exactly 10 listens are kept."""
        data = {
            'track_id': [1] * 10,
            'listen_year': list(range(10))
        }
        df = pd.DataFrame(data)
        
        result = apply_frequency_threshold(df)
        
        assert len(result) == 10
        assert result['track_id'].unique()[0] == 1