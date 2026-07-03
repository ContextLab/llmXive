"""
Unit tests for analysis module, specifically focusing on LME model fitting
and handling of missing predictors.
"""

import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from data_model import ModelResult
from analysis.lme_model import fit_lme_model, handle_missing_predictors, calculate_vif

# Mock data generator for testing
def create_mock_dataset(n_subjects=10, n_trials_per_subject=30, has_salience=True):
    """Create a mock dataset for LME testing."""
    data = []
    np.random.seed(42)
    
    for subject_id in range(n_subjects):
        for trial_id in range(n_trials_per_subject):
            row = {
                'subject_id': f'S{subject_id:02d}',
                'trial_id': trial_id,
                'search_time': np.random.exponential(2.0) + 1.0,  # Positive skew
                'fixation_count': np.random.poisson(5) + 1,
                'pupil_diameter': np.random.normal(4.0, 0.5)
            }
            
            if has_salience:
                row['target_salience'] = np.random.uniform(0.1, 0.9)
            else:
                row['target_salience'] = np.nan  # Missing predictor simulation
            
            data.append(row)
    
    return pd.DataFrame(data)

class TestLMEModelFitting:
    """Tests for LME model fitting functionality."""

    def test_fit_lme_model_basic(self):
        """Test basic LME model fitting with complete data."""
        df = create_mock_dataset(has_salience=True)
        
        result = fit_lme_model(
            df, 
            outcome='pupil_diameter', 
            fixed_effects=['search_time', 'fixation_count', 'target_salience'],
            random_intercept='subject_id'
        )
        
        assert result is not None
        assert isinstance(result, ModelResult)
        assert result.coefficients is not None
        assert len(result.coefficients) > 0
        assert result.p_values is not None

    def test_fit_lme_model_missing_predictor_handling(self):
        """Test that missing predictors (NaN) are handled correctly without crashing."""
        df = create_mock_dataset(has_salience=False)  # target_salience will be NaN
        
        # This should not raise an exception
        # The function should detect missing predictor and either:
        # 1. Drop it and fit reduced model
        # 2. Raise a specific warning but return a result
        result = fit_lme_model(
            df,
            outcome='pupil_diameter',
            fixed_effects=['search_time', 'fixation_count', 'target_salience'],
            random_intercept='subject_id'
        )
        
        assert result is not None
        assert isinstance(result, ModelResult)
        # If target_salience was dropped, it should not be in coefficients
        if 'target_salience' in result.coefficients:
            # If it's there, it should have valid values (not NaN)
            assert not np.isnan(result.coefficients['target_salience'])
        else:
            # If dropped, the model should still have other coefficients
            assert len(result.coefficients) >= 2  # search_time, fixation_count

    def test_handle_missing_predictors_function(self):
        """Test the helper function for handling missing predictors."""
        df = create_mock_dataset(has_salience=False)
        
        predictors = ['search_time', 'fixation_count', 'target_salience']
        cleaned_df, dropped_predictors = handle_missing_predictors(
            df, 
            predictors, 
            threshold=0.5  # Drop if >50% missing
        )
        
        assert 'target_salience' in dropped_predictors
        assert 'search_time' not in dropped_predictors
        assert 'fixation_count' not in dropped_predictors
        
        # Check that target_salience column is removed or handled
        assert 'target_salience' not in cleaned_df.columns or cleaned_df['target_salience'].isna().all()

    def test_vif_calculation(self):
        """Test Variance Inflation Factor calculation."""
        df = create_mock_dataset(has_salience=True)
        
        # Select numeric predictors
        predictors = ['search_time', 'fixation_count', 'target_salience']
        X = df[predictors]
        
        vif_scores = calculate_vif(X)
        
        assert len(vif_scores) == len(predictors)
        assert all(v >= 1.0 for v in vif_scores.values())
        
        # Basic sanity check: VIF should not be extremely high for random data
        assert max(vif_scores.values()) < 100

    def test_lme_model_with_high_vif(self):
        """Test that model handles high VIF by dropping predictors."""
        # Create data with high correlation between predictors
        df = create_mock_dataset(has_salience=True)
        # Artificially create collinearity
        df['search_time'] = df['fixation_count'] * 2.0 + np.random.normal(0, 0.1, len(df))
        
        predictors = ['search_time', 'fixation_count', 'target_salience']
        
        # This should either drop one of the collinear predictors or handle it gracefully
        result = fit_lme_model(
            df,
            outcome='pupil_diameter',
            fixed_effects=predictors,
            random_intercept='subject_id',
            vif_threshold=5.0
        )
        
        assert result is not None
        # The result should have fewer coefficients if one was dropped
        assert len(result.coefficients) <= len(predictors)

    def test_lme_model_insufficient_trials(self):
        """Test error handling for subjects with insufficient trials."""
        # Create dataset with one subject having very few trials
        df = create_mock_dataset(n_subjects=3, n_trials_per_subject=5)  # < 20 trials
        
        with pytest.raises(RuntimeError) as exc_info:
            fit_lme_model(
                df,
                outcome='pupil_diameter',
                fixed_effects=['search_time', 'fixation_count'],
                random_intercept='subject_id',
                min_trials_per_subject=20,
                allow_aggregation=False
            )
        
        assert "has < 20 trials" in str(exc_info.value)

    def test_lme_model_aggregation_flag(self):
        """Test that aggregation flag prevents error for low trial counts."""
        df = create_mock_dataset(n_subjects=3, n_trials_per_subject=5)
        
        # Should not raise error when aggregation is allowed
        result = fit_lme_model(
            df,
            outcome='pupil_diameter',
            fixed_effects=['search_time', 'fixation_count'],
            random_intercept='subject_id',
            min_trials_per_subject=20,
            allow_aggregation=True
        )
        
        assert result is not None

    def test_model_result_structure(self):
        """Test that ModelResult has all required attributes."""
        df = create_mock_dataset(has_salience=True)
        
        result = fit_lme_model(
            df,
            outcome='pupil_diameter',
            fixed_effects=['search_time', 'fixation_count'],
            random_intercept='subject_id'
        )
        
        # Verify all ModelResult fields are present
        assert hasattr(result, 'coefficients')
        assert hasattr(result, 'std_errors')
        assert hasattr(result, 'p_values')
        assert hasattr(result, 'log_likelihood')
        
        # Verify types
        assert isinstance(result.coefficients, dict)
        assert isinstance(result.std_errors, dict)
        assert isinstance(result.p_values, dict)
        assert isinstance(result.log_likelihood, (int, float))

    def test_missing_predictor_logging(self):
        """Test that missing predictors are logged appropriately."""
        import logging
        import io
        
        # Capture log output
        log_stream = io.StringIO()
        handler = logging.StreamHandler(log_stream)
        logger = logging.getLogger('analysis.lme_model')
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        df = create_mock_dataset(has_salience=False)
        
        result = fit_lme_model(
            df,
            outcome='pupil_diameter',
            fixed_effects=['search_time', 'fixation_count', 'target_salience'],
            random_intercept='subject_id'
        )
        
        log_contents = log_stream.getvalue()
        
        # Should contain a message about missing/dropped predictor
        assert 'target_salience' in log_contents or 'dropped' in log_contents or 'missing' in log_contents.lower()
        
        logger.removeHandler(handler)

class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_dataframe(self):
        """Test handling of empty dataframe."""
        df = pd.DataFrame(columns=['subject_id', 'trial_id', 'search_time', 'pupil_diameter'])
        
        with pytest.raises(ValueError):
            fit_lme_model(
                df,
                outcome='pupil_diameter',
                fixed_effects=['search_time'],
                random_intercept='subject_id'
            )

    def test_single_subject(self):
        """Test handling of single subject (cannot estimate random effects)."""
        df = create_mock_dataset(n_subjects=1, n_trials_per_subject=50)
        
        # Should handle gracefully or raise appropriate error
        try:
            result = fit_lme_model(
                df,
                outcome='pupil_diameter',
                fixed_effects=['search_time'],
                random_intercept='subject_id'
            )
            # If it doesn't raise, it should handle the single subject case
            assert result is not None
        except ValueError as e:
            # Expected behavior for single subject
            assert "subject" in str(e).lower() or "random" in str(e).lower()

    def test_all_nan_predictor(self):
        """Test handling of predictor that is all NaN."""
        df = create_mock_dataset(has_salience=False)
        
        # Explicitly set all values to NaN
        df['target_salience'] = np.nan
        
        result = fit_lme_model(
            df,
            outcome='pupil_diameter',
            fixed_effects=['search_time', 'target_salience'],
            random_intercept='subject_id'
        )
        
        # Should handle by dropping the all-NaN predictor
        assert result is not None
        if 'target_salience' in result.coefficients:
            assert not np.isnan(result.coefficients['target_salience'])

    def test_mixed_missing_patterns(self):
        """Test handling of predictors with different missing patterns."""
        df = create_mock_dataset(has_salience=True)
        
        # Create mixed missing patterns
        df.loc[df.index[:10], 'search_time'] = np.nan
        df.loc[df.index[10:20], 'fixation_count'] = np.nan
        df.loc[df.index[20:30], 'target_salience'] = np.nan
        
        result = fit_lme_model(
            df,
            outcome='pupil_diameter',
            fixed_effects=['search_time', 'fixation_count', 'target_salience'],
            random_intercept='subject_id'
        )
        
        assert result is not None
        # Should have handled the mixed missing patterns
        assert len(result.coefficients) > 0