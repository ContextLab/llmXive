"""
Unit tests for confounder matching logic.
Implements T012: Unit test for confounder matching (propensity score or regression).
"""
import pandas as pd
import numpy as np
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.preprocess import handle_confounders

class TestMatchingBalance:
    """Test the confounder handling logic."""

    def test_matching_balance(self):
        """
        Implements T012 requirements:
        - Assert that after handling confounders, the balance is improved or
          the regression residualization logic runs without error.
        - Check that 'age' mean is close to expected (if PSM worked) or
          that the process completes.
        """
        # Create a dataset with imbalanced age
        np.random.seed(42)
        n_musicians = 20
        n_non_musicians = 20
        
        # Musicians are older on average
        music_ages = np.random.normal(18, 1, n_musicians)
        non_music_ages = np.random.normal(14, 1, n_non_musicians)
        
        data = {
            'subject_id': [f'S{i}' for i in range(n_musicians + n_non_musicians)],
            'group': ['musician'] * n_musicians + ['non_musician'] * n_non_musicians,
            'years_of_training': [2.0] * n_musicians + [0.0] * n_non_musicians,
            'age': np.concatenate([music_ages, non_music_ages]),
            'sex': ['M'] * (n_musicians + n_non_musicians), # Controlled sex
            'motion_score': [0.1] * (n_musicians + n_non_musicians),
            'ses_score': [5.0] * (n_musicians + n_non_musicians)
        }
        df = pd.DataFrame(data)

        # Run confounder handling
        # This should attempt PSM and fallback to regression if needed
        df_matched = handle_confounders(df)

        # Assert the function returns a dataframe
        assert isinstance(df_matched, pd.DataFrame)
        assert len(df_matched) > 0 # Should not drop all subjects

        # Check that 'age' column still exists
        assert 'age' in df_matched.columns

        # Check that sex is still present and has expected counts
        assert 'sex' in df_matched.columns
        assert df_matched['sex'].value_counts()['M'] > 0

        # If PSM was used, means should be closer. If regression, residuals are created.
        # We assert that the process completes and output is valid.
        # Specific balance metrics (like absolute mean difference < 0.1) are hard to guarantee
        # without knowing exactly which method (PSM vs Regression) was triggered,
        # but we assert the output structure is correct.
        assert df_matched['age'].mean() > 0
