"""
Unit tests for the analysis module.
"""

import pytest
import pandas as pd
import numpy as np
from code.analysis import normalize_cognitive_scores_zscore, exclude_missing_cognitive_scores


class TestZScoreNormalization:
    """Tests for the normalize_cognitive_scores_zscore function."""

    def test_basic_zscore_calculation(self):
        """Test that Z-scores are calculated correctly for a single cohort."""
        data = {
            'subject_id': ['S1', 'S2', 'S3', 'S4'],
            'cohort': ['Control', 'Control', 'Control', 'Control'],
            'cognitive_score': [10.0, 20.0, 30.0, 40.0]
        }
        df = pd.DataFrame(data)
        
        result = normalize_cognitive_scores_zscore(df, score_column='cognitive_score', cohort_column='cohort')
        
        # Expected mean = 25, std = 12.9099 (approx)
        # Z-scores: (10-25)/12.91, (20-25)/12.91, (30-25)/12.91, (40-25)/12.91
        expected_mean = 0.0
        expected_std = 1.0
        
        assert 'cognitive_score_zscore' in result.columns
        assert np.isclose(result['cognitive_score_zscore'].mean(), expected_mean, atol=1e-5)
        assert np.isclose(result['cognitive_score_zscore'].std(), expected_std, atol=1e-5)

    def test_per_cohort_normalization(self):
        """Test that normalization is applied independently per cohort."""
        data = {
            'subject_id': ['S1', 'S2', 'S3', 'S4', 'S5', 'S6'],
            'cohort': ['Control', 'Control', 'Control', 'AD', 'AD', 'AD'],
            'cognitive_score': [10.0, 20.0, 30.0, 5.0, 15.0, 25.0]
        }
        df = pd.DataFrame(data)
        
        result = normalize_cognitive_scores_zscore(df, score_column='cognitive_score', cohort_column='cohort')
        
        # Control cohort: mean=20, std=8.165 -> Z-scores: -1.225, 0, 1.225
        # AD cohort: mean=15, std=8.165 -> Z-scores: -1.225, 0, 1.225
        # Both cohorts should have mean ~0 and std ~1 independently
        
        control_scores = result[result['cohort'] == 'Control']['cognitive_score_zscore']
        ad_scores = result[result['cohort'] == 'AD']['cognitive_score_zscore']
        
        assert np.isclose(control_scores.mean(), 0.0, atol=1e-5)
        assert np.isclose(control_scores.std(), 1.0, atol=1e-5)
        assert np.isclose(ad_scores.mean(), 0.0, atol=1e-5)
        assert np.isclose(ad_scores.std(), 1.0, atol=1e-5)

    def test_zero_std_cohort(self):
        """Test handling of a cohort with zero standard deviation."""
        data = {
            'subject_id': ['S1', 'S2', 'S3'],
            'cohort': ['Control', 'Control', 'AD'],
            'cognitive_score': [10.0, 10.0, 15.0]  # Control has same score -> std=0
        }
        df = pd.DataFrame(data)
        
        result = normalize_cognitive_scores_zscore(df, score_column='cognitive_score', cohort_column='cohort')
        
        # Control cohort should have Z-scores of 0
        control_scores = result[result['cohort'] == 'Control']['cognitive_score_zscore']
        assert all(control_scores == 0.0)

    def test_missing_columns(self):
        """Test that KeyError is raised for missing columns."""
        data = {
            'subject_id': ['S1', 'S2'],
            'cohort': ['Control', 'AD'],
            'cognitive_score': [10.0, 15.0]
        }
        df = pd.DataFrame(data)
        
        # Test missing score column
        with pytest.raises(KeyError):
            normalize_cognitive_scores_zscore(df, score_column='missing_score', cohort_column='cohort')
        
        # Test missing cohort column
        with pytest.raises(KeyError):
            normalize_cognitive_scores_zscore(df, score_column='cognitive_score', cohort_column='missing_cohort')

    def test_original_data_unchanged(self):
        """Test that the original dataframe is not modified."""
        data = {
            'subject_id': ['S1', 'S2', 'S3'],
            'cohort': ['Control', 'Control', 'Control'],
            'cognitive_score': [10.0, 20.0, 30.0]
        }
        df = pd.DataFrame(data)
        original_df = df.copy()
        
        normalize_cognitive_scores_zscore(df, score_column='cognitive_score', cohort_column='cohort')
        
        # Original dataframe should be unchanged (no new column)
        assert 'cognitive_score_zscore' not in original_df.columns
        assert df.equals(original_df)


class TestExcludeMissingCognitiveScores:
    """Tests for the exclude_missing_cognitive_scores function (existing functionality)."""

    def test_excludes_null_values(self):
        """Test that rows with NaN cognitive scores are excluded."""
        data = {
            'subject_id': ['S1', 'S2', 'S3', 'S4'],
            'cognitive_score': [10.0, np.nan, 30.0, None]
        }
        df = pd.DataFrame(data)
        
        result = exclude_missing_cognitive_scores(df, score_column='cognitive_score')
        
        assert len(result) == 1
        assert result.iloc[0]['subject_id'] == 'S1'

    def test_excludes_empty_strings(self):
        """Test that rows with empty string cognitive scores are excluded."""
        data = {
            'subject_id': ['S1', 'S2', 'S3'],
            'cognitive_score': [10.0, '', 30.0]
        }
        df = pd.DataFrame(data)
        
        result = exclude_missing_cognitive_scores(df, score_column='cognitive_score')
        
        assert len(result) == 2
        assert list(result['subject_id']) == ['S1', 'S3']

    def test_missing_column_raises_error(self):
        """Test that KeyError is raised for missing score column."""
        data = {
            'subject_id': ['S1', 'S2'],
            'cognitive_score': [10.0, 20.0]
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(KeyError):
            exclude_missing_cognitive_scores(df, score_column='missing_column')