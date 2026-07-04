"""
Contract tests for User Story 2: Statistical Modeling and Interaction Analysis.

This module contains tests to verify the convergence and coefficient recovery
of the mixed-effects models used in the analysis pipeline.
"""
import os
import sys
import tempfile
import shutil
import pytest
import numpy as np
import pandas as pd
from statsmodels.formula.api import mixedlm

# Ensure project root is in path for imports
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from code.utils.config import set_random_seed
from code.analysis.modeling import fit_mixed_effects_model


def generate_test_dataset(n_users=100, n_weeks=12, seed=42):
    """
    Generate a synthetic dataset with known coefficients for testing model recovery.
    
    The data is generated such that:
    - Gamification has a known positive effect (beta=0.5)
    - Conscientiousness has a known positive effect (beta=0.3)
    - The interaction is zero (beta=0.0)
    - Random intercepts are added per user
    
    Args:
        n_users (int): Number of unique users
        n_weeks (int): Number of weeks per user
        seed (int): Random seed for reproducibility
        
    Returns:
        pd.DataFrame: Synthetic dataset with columns:
            User_ID, Gamified, Conscientiousness, Adherence, Week
    """
    set_random_seed(seed)
    
    # Generate user-level traits
    user_ids = [f"U{i:03d}" for i in range(n_users)]
    gamified_status = np.random.choice([0, 1], size=n_users, p=[0.3, 0.7])
    conscientiousness = np.random.normal(loc=3.0, scale=1.0, size=n_users)
    
    # Create true coefficients
    beta_gamified = 0.5
    beta_conscientiousness = 0.3
    beta_interaction = 0.0
    intercept = -1.0
    
    # Generate data
    data_rows = []
    for i, uid in enumerate(user_ids):
        g_status = gamified_status[i]
        c_score = conscientiousness[i]
        
        for w in range(1, n_weeks + 1):
            # Linear predictor
            eta = (
                intercept +
                beta_gamified * g_status +
                beta_conscientiousness * c_score +
                beta_interaction * g_status * c_score +
                np.random.normal(0, 0.5) # Random noise
            )
            
            # Convert to probability (logistic link)
            prob = 1.0 / (1.0 + np.exp(-eta))
            
            # Generate binary adherence
            adherence = 1 if np.random.random() < prob else 0
            
            data_rows.append({
                "User_ID": uid,
                "Gamified": g_status,
                "Conscientiousness": c_score,
                "Adherence": adherence,
                "Week": w
            })
    
    return pd.DataFrame(data_rows)


def test_model_convergence():
    """
    Contract test: Assert the mixed-effects model converges and recovers 
    known coefficients within 0.01 variance on a synthetic test set.
    
    This test:
    1. Generates a synthetic dataset with known ground-truth coefficients.
    2. Runs the modeling pipeline.
    3. Verifies the model converged successfully.
    4. Verifies the recovered coefficients are within 0.01 of the true values.
    """
    # 1. Generate test data with known coefficients
    # True values: Gamified=0.5, Conscientiousness=0.3, Interaction=0.0
    test_df = generate_test_dataset(n_users=150, n_weeks=10, seed=123)
    
    # Save to a temporary CSV to simulate pipeline input
    with tempfile.TemporaryDirectory() as tmp_dir:
        input_path = os.path.join(tmp_dir, "test_data.csv")
        test_df.to_csv(input_path, index=False)
        
        # 2. Run the modeling function
        # We capture the output to check convergence and coefficients
        try:
            results = fit_mixed_effects_model(
                data_path=input_path,
                output_path=os.path.join(tmp_dir, "model_results.csv"),
                formula="Adherence ~ Gamified * Conscientiousness",
                groups="User_ID"
            )
        except Exception as e:
            pytest.fail(f"Model fitting failed unexpectedly: {e}")
        
        # 3. Verify convergence
        # The results object should have a convergence flag or similar
        # Since fit_mixed_effects_model returns a summary dict, we check for success
        assert results.get("converged", False) is True, "Model failed to converge"
        
        # 4. Verify coefficient recovery
        # We expect the fixed effects to be close to the true values
        fixed_effects = results.get("fixed_effects", {})
        
        # Extract coefficients (keys might vary slightly based on statsmodels output)
        # Typically: 'Gamified', 'Conscientiousness', 'Gamified:Conscientiousness'
        # We need to map the keys carefully. Assuming standard statsmodels naming.
        
        # Helper to find the closest key
        def get_coef(key):
            for k, v in fixed_effects.items():
                if key in k:
                    return v
            return None
        
        # Check Gamified (True: 0.5)
        coef_gamified = get_coef("Gamified")
        assert coef_gamified is not None, "Gamified coefficient not found"
        assert abs(coef_gamified - 0.5) < 0.01, f"Gamified coefficient {coef_gamified} deviates > 0.01 from 0.5"
        
        # Check Conscientiousness (True: 0.3)
        coef_consc = get_coef("Conscientiousness")
        assert coef_consc is not None, "Conscientiousness coefficient not found"
        assert abs(coef_consc - 0.3) < 0.01, f"Conscientiousness coefficient {coef_consc} deviates > 0.01 from 0.3"
        
        # Check Interaction (True: 0.0)
        # Note: statsmodels often names interaction as 'Gamified:Conscientiousness' or similar
        coef_inter = get_coef(":")
        if coef_inter is None:
            # Try alternative naming if standard ':' not found
            for k, v in fixed_effects.items():
                if "Gamified" in k and "Conscientiousness" in k and "Gamified" != k and "Conscientiousness" != k:
                    coef_inter = v
                    break
        
        assert coef_inter is not None, "Interaction coefficient not found"
        assert abs(coef_inter - 0.0) < 0.01, f"Interaction coefficient {coef_inter} deviates > 0.01 from 0.0"

        print("Test passed: Model converged and recovered coefficients within tolerance.")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
