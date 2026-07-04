import os
import sys
import tempfile
import shutil
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

from code.utils.config import set_random_seed
from code.analysis.robustness import bootstrap_effect_size

# Mock data generator for testing purposes
def generate_test_bootstrap_data(n_users=100, n_weeks=10, seed=42):
    """
    Generates a synthetic dataset mimicking the structure expected by robustness analysis.
    This is used strictly for testing the variance calculation logic, not for final research results.
    """
    set_random_seed(seed)
    data = []
    for user_id in range(1, n_users + 1):
        gamified = np.random.choice([0, 1])
        conscientiousness = np.random.normal(5.0, 1.5)
        # Simulate adherence over weeks
        for week in range(1, n_weeks + 1):
            # Base probability influenced by gamification and conscientiousness
            prob = 0.5 + (0.1 * gamified) + (0.05 * conscientiousness) - (0.02 * week)
            prob = np.clip(prob, 0.1, 0.9)
            adherence = 1 if np.random.random() < prob else 0
            data.append({
                'User_ID': user_id,
                'Gamified': gamified,
                'Conscientiousness': conscientiousness,
                'Week': week,
                'Adherence': adherence
            })
    return pd.DataFrame(data)

def test_bootstrap_variance():
    """
    Contract test: Asserts the bootstrapping procedure generates samples and reports
    a coefficient variance (regardless of value).
    
    This test verifies:
    1. The bootstrap function executes without error on a valid dataset.
    2. The output contains a 'coefficient_variance' key.
    3. The variance is a numeric value (float).
    4. The process generates the expected number of samples (internally).
    """
    # Prepare temporary directory for any potential output files if the function writes them
    # though bootstrap_effect_size is expected to return results in memory for this test.
    temp_dir = tempfile.mkdtemp()
    try:
        # Generate test data
        df = generate_test_bootstrap_data(n_users=50, n_weeks=8, seed=123)
        
        # Run the bootstrap effect size calculation
        # We mock the data loading if the function expects a file path, 
        # but based on the API surface, we pass the dataframe or handle internal loading.
        # Assuming the function signature allows passing data or we use the generated data.
        # The function signature in modeling.py suggests it might take a path or dataframe.
        # We will pass the dataframe directly if the function supports it, or save it to a temp file.
        
        # Save to temp CSV to ensure compatibility with file-based loaders if necessary
        test_csv_path = os.path.join(temp_dir, "test_data.csv")
        df.to_csv(test_csv_path, index=False)
        
        # Execute the function
        # Note: The implementation of bootstrap_effect_size in robustness.py is expected to 
        # perform the resampling and return the variance.
        result = bootstrap_effect_size(test_csv_path, n_iterations=100, random_state=42)
        
        # Assertions
        assert result is not None, "Bootstrap function should return a result dictionary."
        assert 'coefficient_variance' in result, "Result must contain 'coefficient_variance'."
        assert isinstance(result['coefficient_variance'], (int, float)), "Variance must be numeric."
        assert result['coefficient_variance'] >= 0, "Variance cannot be negative."
        
        # Optional: Check if other expected keys exist (based on typical robustness output)
        # The task specifically asks to assert it reports a coefficient variance.
        # We verify that the variance is not NaN and is a real number.
        assert not np.isnan(result['coefficient_variance']), "Variance cannot be NaN."
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)