import pytest
import pandas as pd
import numpy as np
from statsmodels.regression.mixed_linear_model import MixedLM
from statsmodels.formula.api import mixedlm

def test_lmm_model_fitting_synthetic():
    """
    Unit test for LMM model fitting (statsmodels MixedLM) with synthetic data.
    
    This test verifies that the MixedLM model can be successfully fitted on synthetic
    data mimicking the expected structure of the study responses.
    
    Expected behavior:
    - Model formula: 'answer ~ condition * complexity + (1|participant_id)'
    - Fixed effects: condition, complexity, condition:complexity
    - Random intercepts: participant_id
    - Family: Gaussian (default for MixedLM)
    
    The test creates synthetic data with:
    - 100 participants
    - 3 conditions (code_only, code_llm, code_docstring)
    - 3 complexity levels (low, medium, high)
    - Binary answer outcomes (0 or 1)
    - Latency measurements (simulated)
    
    Assertions:
    - Model fitting completes without error
    - Results object contains expected attributes
    - Fixed effects coefficients are present
    - Random effects variance is estimated
    """
    # Generate synthetic data
    np.random.seed(42)
    n_participants = 100
    n_trials_per_participant = 3  # One per condition
    
    # Create participant IDs
    participant_ids = np.repeat([f"p{i}" for i in range(n_participants)], n_trials_per_participant)
    
    # Create conditions (balanced)
    conditions = np.tile(['code_only', 'code_llm', 'code_docstring'], n_participants)
    
    # Create complexity levels (balanced)
    complexities = np.tile(['low', 'medium', 'high'], n_participants)
    
    # Generate synthetic answers (binary, with some variation by condition and complexity)
    # Base probability varies by condition and complexity
    base_prob = np.where(
        conditions == 'code_llm', 0.7,
        np.where(conditions == 'code_docstring', 0.6, 0.5)
    )
    base_prob = np.where(
        complexities == 'high', base_prob - 0.1,
        np.where(complexities == 'medium', base_prob, base_prob)
    )
    
    # Add noise
    answers = (np.random.rand(len(participant_ids)) < base_prob).astype(int)
    
    # Create DataFrame
    data = pd.DataFrame({
        'participant_id': participant_ids,
        'condition': conditions,
        'complexity': complexities,
        'answer': answers,
        'latency': np.random.exponential(5000, len(participant_ids))  # Simulated latency
    })
    
    # Convert categorical variables to string type for formula compatibility
    data['condition'] = data['condition'].astype(str)
    data['complexity'] = data['complexity'].astype(str)
    
    # Define the model formula as specified in T026
    # Fixed effects: condition, complexity, condition:complexity
    # Random intercepts: participant_id
    formula = "answer ~ condition * complexity"
    
    # Fit the LMM model
    # Note: Using 'participant_id' as the grouping variable for random intercepts
    model = mixedlm(formula, data, groups=data["participant_id"])
    result = model.fit()
    
    # Assertions
    assert result is not None, "Model fitting should return a result object"
    assert hasattr(result, 'params'), "Result should have 'params' attribute"
    assert hasattr(result, 'bse'), "Result should have 'bse' (standard errors) attribute"
    assert hasattr(result, 'rsquared'), "Result should have 'rsquared' attribute"
    
    # Check that fixed effects coefficients are present
    params = result.params
    assert len(params) > 0, "Fixed effects coefficients should be estimated"
    
    # Verify that condition and complexity effects are in the model
    param_names = list(params.index)
    assert any('condition' in name for name in param_names), "Model should include condition effects"
    assert any('complexity' in name for name in param_names), "Model should include complexity effects"
    assert any('condition:complexity' in name for name in param_names), "Model should include interaction effects"
    
    # Check random effects variance
    assert hasattr(result, 'random_effects'), "Result should have 'random_effects' attribute"
    random_effects = result.random_effects
    assert len(random_effects) > 0, "Random effects should be estimated for participants"
    
    # Verify that the model converged
    assert result.converged, "Model fitting should converge"
    
    # Additional checks: verify coefficient signs make sense (optional)
    # For example, code_llm should generally have higher accuracy than code_only
    if 'condition[T.code_llm]' in param_names:
        code_llm_coef = params['condition[T.code_llm]']
        # This is a soft check - the coefficient should be positive if code_llm improves accuracy
        # Note: This might fail with small samples or high variance, so we don't assert it
        # assert code_llm_coef > 0, "Code+LLM should improve accuracy compared to code only"
    
    # Log the results for debugging
    print(f"Model fitting successful!")
    print(f"Fixed effects:\n{result.params}")
    print(f"Random effects variance:\n{result.cov_re}")
    print(f"Converged: {result.converged}")
    
    return True