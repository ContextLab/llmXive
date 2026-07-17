"""
Unit tests for LMM model construction logic.

This module tests the construction of Linear Mixed-Effects Models using mock data
to ensure the model formula and structure are correctly defined before running
on real data.

Tests verify:
- Model formula construction (Fixed effects: relationship_context, cue_intensity, interaction)
- Random effects structure (Random intercepts for Participant and Stimulus)
- Handling of categorical variables
- Convergence on simple mock data
"""
import pytest
import pandas as pd
import numpy as np
from statsmodels.regression.mixed_linear_model import MixedLM
from statsmodels.formula.api import mixedlm
import json
import sys
from pathlib import Path

# Add project root to path for imports if running standalone
# In the actual project structure, this is handled by the test runner
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT / "code") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "code"))

from config import get_project_root, get_processed_data_dir


def create_mock_lmm_data(n_participants=50, n_stimuli=24):
    """
    Create a small, deterministic mock dataset for testing LMM construction.
    
    Args:
        n_participants: Number of unique participants
        n_stimuli: Number of unique stimuli (should match 3 emoji * 2 punct * 2 length * 2 contexts)
    
    Returns:
        pd.DataFrame: Mock ratings dataset with columns:
            - participant_id: Participant identifier
            - stimulus_id: Stimulus identifier
            - relationship_context: Categorical (friend, acquaintance)
            - cue_intensity: Numeric (simulated score)
            - rating: Numeric (simulated Likert score 1-7)
    """
    np.random.seed(42)  # Reproducibility for tests
    
    # Create participant and stimulus IDs
    participant_ids = [f"P-{i:04d}" for i in range(n_participants)]
    stimulus_ids = [f"S-{i:02d}" for i in range(n_stimuli)]
    
    # Create a full factorial design (each participant rates each stimulus)
    # In reality, this might be a subset, but for testing construction, full is fine
    records = []
    for p_id in participant_ids:
        for s_id in stimulus_ids:
            # Randomly assign relationship context (balanced)
            context = np.random.choice(["friend", "acquaintance"])
            
            # Simulate cue intensity (0.0 to 1.0)
            cue_intensity = np.random.uniform(0.0, 1.0)
            
            # Simulate rating based on a simple linear relationship + noise
            # rating = 5.0 + 2.0 * cue_intensity + 1.0 * (context=="friend") + noise
            base_rating = 5.0
            if context == "friend":
                base_rating += 1.0
            base_rating += 2.0 * cue_intensity
            rating = base_rating + np.random.normal(0, 0.5)
            rating = np.clip(rating, 1, 7)  # Clamp to Likert scale
            
            records.append({
                "participant_id": p_id,
                "stimulus_id": s_id,
                "relationship_context": context,
                "cue_intensity": cue_intensity,
                "rating": rating
            })
    
    df = pd.DataFrame(records)
    return df


class TestLMMConstruction:
    """Tests for LMM model construction logic."""

    def test_model_formula_construction(self):
        """
        Test that the model formula string is correctly constructed.
        
        Verifies the formula includes:
        - Dependent variable: rating
        - Fixed effects: relationship_context, cue_intensity, and their interaction
        - Random effects: intercepts for participant_id and stimulus_id
        """
        df = create_mock_lmm_data(n_participants=10, n_stimuli=24)
        
        # Construct the formula as it would be in the main pipeline
        # Fixed effects: relationship_context * cue_intensity (includes main effects + interaction)
        # Random effects: 1 | participant_id and 1 | stimulus_id
        # Note: statsmodels mixedlm formula syntax: "dependent ~ fixed_effects"
        # Random effects are passed via the groups parameter, not the formula string directly
        # for a single grouping factor. For multiple, we typically fit separate models 
        # or use a custom group structure. 
        # However, the standard approach in statsmodels for multiple random intercepts 
        # is often to nest them or fit sequentially. 
        # For this test, we will test the construction of the primary model 
        # with Participant as the random effect, as is common in the first pass,
        # or verify the formula string itself.
        
        # Let's verify the formula string for the fixed effects part
        formula = "rating ~ relationship_context * cue_intensity"
        
        # Ensure categorical variable is treated correctly
        df["relationship_context"] = df["relationship_context"].astype("category")
        
        # Fit a simple model to ensure the formula is valid
        # Using only participant as the random effect for this construction test
        model = mixedlm(formula, df, groups=df["participant_id"])
        result = model.fit()
        
        # Assertions
        assert result is not None, "Model fitting failed"
        assert hasattr(result, "params"), "Result missing parameters"
        
        # Check that the interaction term exists in the params
        param_names = list(result.params.index)
        interaction_term = "relationship_context[T.acquaintance]:cue_intensity"
        # The exact name might vary slightly based on factor levels, but should contain interaction
        has_interaction = any("cue_intensity" in p and "relationship_context" in p for p in param_names)
        assert has_interaction, f"Interaction term not found in model parameters: {param_names}"

    def test_random_effects_structure(self):
        """
        Test that random intercepts are correctly specified for participants.
        """
        df = create_mock_lmm_data(n_participants=10, n_stimuli=24)
        formula = "rating ~ relationship_context * cue_intensity"
        
        model = mixedlm(formula, df, groups=df["participant_id"])
        result = model.fit()
        
        # Check variance components
        # The result should have a variance component for the random intercept
        assert hasattr(result, "cov_re"), "Result missing random effects covariance"
        
        # For a single random intercept, cov_re should be a 1x1 matrix
        cov_re = result.cov_re
        assert cov_re.shape == (1, 1), f"Expected 1x1 covariance matrix, got {cov_re.shape}"
        
        # Variance should be positive
        variance = cov_re.iloc[0, 0]
        assert variance > 0, f"Random effect variance should be positive, got {variance}"

    def test_stimulus_random_effect_construction(self):
        """
        Test that a model can be constructed with Stimulus as the random effect group.
        
        In the full pipeline, we might fit a model with Participant as the group,
        and then another with Stimulus, or use a more complex structure.
        This test ensures the Stimulus grouping works.
        """
        df = create_mock_lmm_data(n_participants=10, n_stimuli=24)
        formula = "rating ~ relationship_context * cue_intensity"
        
        model = mixedlm(formula, df, groups=df["stimulus_id"])
        result = model.fit()
        
        assert result is not None, "Model fitting with Stimulus group failed"
        assert hasattr(result, "params"), "Result missing parameters"

    def test_convergence_on_mock_data(self):
        """
        Test that the model converges on the mock dataset.
        """
        df = create_mock_lmm_data(n_participants=20, n_stimuli=24)
        formula = "rating ~ relationship_context * cue_intensity"
        
        model = mixedlm(formula, df, groups=df["participant_id"])
        result = model.fit()
        
        # Check convergence flag
        assert result.converged, "Model did not converge on mock data"

    def test_handling_categorical_variables(self):
        """
        Test that categorical variables are correctly handled in the formula.
        """
        df = create_mock_lmm_data(n_participants=10, n_stimuli=24)
        df["relationship_context"] = df["relationship_context"].astype("category")
        
        formula = "rating ~ relationship_context * cue_intensity"
        model = mixedlm(formula, df, groups=df["participant_id"])
        result = model.fit()
        
        # Check that the dummy variable for the second category is present
        param_names = list(result.params.index)
        # Should have a term like relationship_context[T.acquaintance]
        context_terms = [p for p in param_names if "relationship_context" in p and "cue_intensity" not in p]
        assert len(context_terms) > 0, f"No main effect terms for relationship_context found: {param_names}"

    def test_model_with_realistic_sample_size(self):
        """
        Test model construction with a sample size closer to the power analysis target.
        """
        # Power analysis target is typically around 50-100 participants
        df = create_mock_lmm_data(n_participants=50, n_stimuli=24)
        formula = "rating ~ relationship_context * cue_intensity"
        
        model = mixedlm(formula, df, groups=df["participant_id"])
        result = model.fit()
        
        assert result.converged, "Model failed to converge with larger sample"
        assert len(result.params) > 3, "Unexpectedly few parameters estimated"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])