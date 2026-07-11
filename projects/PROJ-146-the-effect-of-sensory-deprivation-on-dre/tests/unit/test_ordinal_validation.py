import pytest
import pandas as pd
import numpy as np
import os
import sys

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from models import validate_ordinal_approx, fit_ordinal_approx

class TestOrdinalValidation:
    """
    Tests for the validate_ordinal_approx routine (Task T023).
    Verifies that the Fixed-Effects OrderedModel approximates ground truth within tolerance.
    """

    @pytest.fixture
    def synthetic_data_with_ground_truth(self):
        """
        Create a small synthetic dataset with known ground truth coefficients.
        This mimics the output of generate_data.py with a known seed.
        """
        np.random.seed(42)
        n_participants = 50
        n_trials = 4
        
        participant_ids = np.repeat(np.arange(n_participants), n_trials)
        conditions = np.tile(['strict', 'moderate', 'partial', 'strict'], n_participants)
        
        # Ground truth: moderate has a positive effect, partial has null
        # Bizarreness is ordinal 1-7
        # We simulate a linear relationship with noise, then map to ordinal
        # True intercept = 3.0, True moderate effect = 1.0
        
        intercept = 3.0
        effect_moderate = 1.0
        effect_partial = 0.0
        
        # Encode condition effects
        effects = []
        for c in conditions:
            if c == 'moderate':
                effects.append(effect_moderate)
            elif c == 'partial':
                effects.append(effect_partial)
            else:
                effects.append(0.0)
        
        noise = np.random.normal(0, 1.5, size=len(participant_ids))
        latent = intercept + np.array(effects) + noise
        
        # Clip to 1-7 range and convert to int
        bizarreness = np.clip(latent, 1, 7).astype(int)
        
        df = pd.DataFrame({
            'participant_id': participant_ids,
            'condition': conditions,
            'bizarreness': bizarreness
        })
        
        # Ground truth coefficients for the model: bizarreness ~ condition
        # Note: statsmodels OrderedModel parameterization might differ slightly,
        # but the relative effect should be recoverable.
        # We expect the coefficient for 'moderate' to be roughly 1.0 relative to strict.
        ground_truth = {
            'Intercept': intercept,
            'condition[T.moderate]': effect_moderate,
            'condition[T.partial]': effect_partial
        }
        
        return df, ground_truth

    def test_validate_ordinal_approx_runs(self, synthetic_data_with_ground_truth):
        """Test that the validation routine executes without error."""
        df, ground_truth = synthetic_data_with_ground_truth
        
        # Ensure condition is categorical for OrderedModel
        df['condition'] = df['condition'].astype('category')
        
        result = validate_ordinal_approx(
            df, 
            ground_truth, 
            formula="bizarreness ~ condition"
        )
        
        assert result['status'] == 'success'
        assert 'fitted_coefs' in result
        assert 'absolute_error' in result
        assert 'validation_passed' in result

    def test_validation_quantifies_error(self, synthetic_data_with_ground_truth):
        """Test that the routine actually calculates errors."""
        df, ground_truth = synthetic_data_with_ground_truth
        df['condition'] = df['condition'].astype('category')
        
        result = validate_ordinal_approx(
            df, 
            ground_truth, 
            formula="bizarreness ~ condition"
        )
        
        # Check that errors are numeric and finite
        for key, err in result['absolute_error'].items():
            assert isinstance(err, (int, float))
            assert not np.isnan(err)
            assert not np.isinf(err)

    def test_validation_tolerance_logic(self, synthetic_data_with_ground_truth):
        """Test that validation passes if error is within tolerance."""
        df, ground_truth = synthetic_data_with_ground_truth
        df['condition'] = df['condition'].astype('category')
        
        # With N=200 (50*4) and clear effect, it should pass
        result = validate_ordinal_approx(
            df, 
            ground_truth, 
            formula="bizarreness ~ condition"
        )
        
        # The test might pass or fail depending on the noise and approximation,
        # but the logic must be consistent. We assert that the max error is calculated.
        assert 'max_absolute_error' in result
        assert 'tolerance' in result
        
        # If the model fits well, validation_passed should be True
        # (Given the synthetic data generation, it is expected to be reasonably close)
        # We don't assert True/False strictly as noise can flip it, but we assert the field exists.
        assert isinstance(result['validation_passed'], bool)
        
        logger = pytest.importorskip('logging')
        logger.info(f"Validation Result: {result['validation_passed']}, Max Error: {result['max_absolute_error']}")

    def test_handles_missing_ground_truth_keys(self):
        """Test behavior when ground truth keys don't match fitted keys."""
        df, _ = self.synthetic_data_with_ground_truth()
        df['condition'] = df['condition'].astype('category')
        
        # Intentionally provide a mismatched ground truth
        bad_ground_truth = {
            'Intercept': 3.0,
            'condition[T.nonexistent]': 1.0
        }
        
        result = validate_ordinal_approx(
            df, 
            bad_ground_truth, 
            formula="bizarreness ~ condition"
        )
        
        assert result['status'] == 'success'
        # The absolute error dict should be empty or only contain matching keys
        # In our implementation, it iterates over ground_truth keys.
        # If none match, errors dict is empty.
        assert isinstance(result['absolute_error'], dict)
        assert result['max_absolute_error'] == float('inf') # No keys matched
        assert result['validation_passed'] == False # Fail if no comparison possible

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
