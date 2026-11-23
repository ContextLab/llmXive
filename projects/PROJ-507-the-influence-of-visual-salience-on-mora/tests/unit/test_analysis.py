"""
Unit tests for CLMM model fitting with Positive/Negative controls.

This module validates the Cumulative Link Mixed Model (CLMM) implementation
in code/analysis.py by running it against synthetic datasets with known effects.

Positive Control: Dataset with a known strong positive effect of salience on blame.
Negative Control: Dataset with no effect of salience on blame.

The tests verify:
1. Model convergence on valid data.
2. Correct detection of significant effects in the positive control.
3. Correct detection of non-significant effects in the negative control.
4. Fallback logic triggers correctly when the primary model fails to converge.
"""
import os
import sys
import tempfile
import json
import logging
import math
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd
import pytest

# Add project root to path if not already present
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import seed_everything
from models import Response, Participant, StimulusVariant, Scenario, SalienceLevel, AmbiguityLabel
from data_cleaning import load_survey_data, detect_straight_lining, save_cleaned_data
from data_hygiene import DataHygieneError, verify_data_separation

# Import the analysis module functions directly
# We assume analysis.py contains: run_clmm_analysis, check_convergence_and_fallback, etc.
# Since analysis.py is not fully provided in the API surface, we will mock the heavy lifting
# and test the *logic* of the test harness and the integration points.
# However, the task requires testing the *model fitting* logic.
# We will import the analysis module and test its public API.

try:
    from analysis import (
        run_clmm_analysis,
        check_convergence_and_fallback,
        fit_lmm_fallback,
        fit_bootstrap_clmm,
        calculate_effect_size,
        perform_ordinal_post_hoc
    )
    ANALYSIS_MODULE_AVAILABLE = True
except ImportError as e:
    ANALYSIS_MODULE_AVAILABLE = False
    # Log the error but don't fail the test suite immediately
    # The test will skip if the module is not available
    pass

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for test data generation
N_PARTICIPANTS = 50
N_SCENARIOS = 20
N_REP_PER_COND = 5  # Each participant sees each scenario once per salience level (within-subject)
SEED = 42

def generate_synthetic_dataset(
    n_participants: int = N_PARTICIPANTS,
    n_scenarios: int = N_SCENARIOS,
    effect_size: float = 0.0,  # 0 for negative control, >0 for positive
    noise_level: float = 1.0,
    seed: int = SEED
) -> pd.DataFrame:
    """
    Generate a synthetic dataset for CLMM testing.
    
    Args:
        n_participants: Number of unique participants.
        n_scenarios: Number of unique scenarios.
        effect_size: The true effect of salience on the log-odds of higher blame.
                    0.0 means no effect (negative control).
                    Positive value means higher salience leads to higher blame (positive control).
        noise_level: Standard deviation of the random error term.
        seed: Random seed for reproducibility.
    
    Returns:
        A pandas DataFrame with columns:
            participant_id, scenario_id, salience_level, rating
    """
    seed_everything(seed)
    
    participants = [f"P{i:03d}" for i in range(n_participants)]
    scenarios = [f"S{i:03d}" for i in range(n_scenarios)]
    salience_levels = ["low", "medium", "high"]
    
    data = []
    
    # Generate participant and scenario random intercepts
    participant_intercepts = {p: np.random.normal(0, 0.5) for p in participants}
    scenario_intercepts = {s: np.random.normal(0, 0.5) for s in scenarios}
    
    # Salience level encoding (ordinal: low=0, medium=1, high=2)
    salience_map = {"low": 0, "medium": 1, "high": 2}
    
    for p in participants:
        for s in scenarios:
            for sal in salience_levels:
                # Base rating (1-7 scale)
                base_rating = 4.0 
                
                # Add random intercepts
                rating = base_rating + participant_intercepts[p] + scenario_intercepts[s]
                
                # Add salience effect
                rating += effect_size * salience_map[sal]
                
                # Add noise
                rating += np.random.normal(0, noise_level)
                
                # Clamp to 1-7 range
                rating = max(1.0, min(7.0, rating))
                
                # Round to nearest integer for ordinal rating (1-7)
                rating = int(round(rating))
                rating = max(1, min(7, rating))
                
                data.append({
                    "participant_id": p,
                    "scenario_id": s,
                    "salience_level": sal,
                    "rating": rating
                })
    
    return pd.DataFrame(data)

@pytest.mark.skipif(not ANALYSIS_MODULE_AVAILABLE, reason="analysis module not available")
class TestCLMMPositiveControl:
    """Test CLMM fitting with a dataset that has a known positive effect."""
    
    def test_positive_effect_detected(self):
        """
        Positive Control: Generate data with a strong positive effect.
        Verify that the CLMM model detects a significant positive coefficient for salience.
        """
        # Generate data with a strong positive effect (e.g., 0.5 per level)
        df = generate_synthetic_dataset(effect_size=0.5, noise_level=0.5, seed=SEED)
        
        # Save to a temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
            tmp_path = tmp.name
            df.to_csv(tmp_path, index=False)
        
        try:
            # Run the analysis
            # Note: The exact function signature might differ, adjust as needed
            # Assuming run_clmm_analysis takes a path and returns results
            results = run_clmm_analysis(
                input_path=tmp_path,
                output_path=tmp_path.replace('.csv', '_results.json')
            )
            
            # Verify convergence
            assert results.get('converged', False), "Model did not converge for positive control."
            
            # Verify effect direction and significance
            # The exact key names depend on the implementation of run_clmm_analysis
            # We assume it returns a dict with 'salience_coefficient', 'p_value', etc.
            coef = results.get('salience_coefficient')
            p_val = results.get('salience_p_value')
            
            assert coef is not None, "Salience coefficient not found in results."
            assert p_val is not None, "Salience p-value not found in results."
            
            # Check that the coefficient is positive
            assert coef > 0, f"Expected positive coefficient, got {coef}."
            
            # Check that the effect is statistically significant (p < 0.05)
            # Note: This is a heuristic. In a real test, we might use a more robust method
            # or check if the confidence interval excludes zero.
            assert p_val < 0.05, f"Expected significant p-value (<0.05), got {p_val}."
            
        finally:
            # Clean up temporary files
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            results_path = tmp_path.replace('.csv', '_results.json')
            if os.path.exists(results_path):
                os.remove(results_path)

@pytest.mark.skipif(not ANALYSIS_MODULE_AVAILABLE, reason="analysis module not available")
class TestCLMMNegativeControl:
    """Test CLMM fitting with a dataset that has no effect."""
    
    def test_no_effect_detected(self):
        """
        Negative Control: Generate data with no effect of salience.
        Verify that the CLMM model does NOT detect a significant effect.
        """
        # Generate data with no effect (effect_size=0)
        df = generate_synthetic_dataset(effect_size=0.0, noise_level=1.0, seed=SEED)
        
        # Save to a temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
            tmp_path = tmp.name
            df.to_csv(tmp_path, index=False)
        
        try:
            # Run the analysis
            results = run_clmm_analysis(
                input_path=tmp_path,
                output_path=tmp_path.replace('.csv', '_results.json')
            )
            
            # Verify convergence
            assert results.get('converged', False), "Model did not converge for negative control."
            
            # Verify that the effect is NOT significant
            coef = results.get('salience_coefficient')
            p_val = results.get('salience_p_value')
            
            assert coef is not None, "Salience coefficient not found in results."
            assert p_val is not None, "Salience p-value not found in results."
            
            # Check that the p-value is NOT significant (p >= 0.05)
            # Note: With a small sample size, we might occasionally get a false positive.
            # We'll use a less strict threshold or check the confidence interval.
            # For this test, we expect p >= 0.05.
            # If p < 0.05, it's a Type I error, which is possible but unlikely with this setup.
            # We'll assert that it's not *extremely* significant (e.g., p < 0.01) to be safe.
            # However, the strict requirement is that we don't claim an effect when there is none.
            # So we assert p >= 0.05.
            assert p_val >= 0.05, f"Expected non-significant p-value (>=0.05), got {p_val}."
            
        finally:
            # Clean up temporary files
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            results_path = tmp_path.replace('.csv', '_results.json')
            if os.path.exists(results_path):
                os.remove(results_path)

@pytest.mark.skipif(not ANALYSIS_MODULE_AVAILABLE, reason="analysis module not available")
class TestConvergenceFallback:
    """Test that the fallback logic triggers when the primary model fails to converge."""
    
    def test_fallback_triggers_on_non_convergence(self):
        """
        Verify that when the CLMM model fails to converge, the fallback model (LMM/Bootstrap)
        is used and the results are still generated.
        """
        # Generate data that might cause convergence issues (e.g., very small sample, or extreme imbalance)
        # For this test, we'll mock the convergence check to return False.
        df = generate_synthetic_dataset(n_participants=10, n_scenarios=5, effect_size=0.5, seed=SEED)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
            tmp_path = tmp.name
            df.to_csv(tmp_path, index=False)
        
        try:
            # Mock the convergence check to fail
            with patch('analysis.check_convergence_and_fallback') as mock_check:
                # Mock the return value to indicate non-convergence and trigger fallback
                mock_check.return_value = (MagicMock(converged=False), 'fallback_used')
                
                # Run the analysis
                results = run_clmm_analysis(
                    input_path=tmp_path,
                    output_path=tmp_path.replace('.csv', '_results.json')
                )
                
                # Verify that the fallback was used
                assert mock_check.called, "Convergence check was not called."
                assert results.get('method_used') == 'fallback_used', "Fallback method was not used."
                
        finally:
            # Clean up temporary files
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            results_path = tmp_path.replace('.csv', '_results.json')
            if os.path.exists(results_path):
                os.remove(results_path)

@pytest.mark.skipif(not ANALYSIS_MODULE_AVAILABLE, reason="analysis module not available")
class TestOrdinalPostHoc:
    """Test the ordinal post-hoc pairwise comparisons."""
    
    def test_post_hoc_correctness(self):
        """
        Verify that the ordinal post-hoc tests are performed correctly.
        We'll check that the function returns the expected number of comparisons.
        """
        # Generate a dataset
        df = generate_synthetic_dataset(effect_size=0.5, seed=SEED)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
            tmp_path = tmp.name
            df.to_csv(tmp_path, index=False)
        
        try:
            # Run the analysis to get the model object (mocked or real)
            # For this test, we'll just call the post-hoc function with a mock model
            mock_model = MagicMock()
            mock_model.converged = True
            
            # Call the post-hoc function
            # Assuming the function takes the model and returns a dict of comparisons
            comparisons = perform_ordinal_post_hoc(mock_model)
            
            # Verify that we got comparisons for all pairs (low-medium, medium-high, low-high)
            expected_pairs = [
                ('low', 'medium'),
                ('medium', 'high'),
                ('low', 'high')
            ]
            
            assert len(comparisons) == len(expected_pairs), f"Expected {len(expected_pairs)} comparisons, got {len(comparisons)}."
            
        finally:
            # Clean up temporary files
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

if __name__ == '__main__':
    # Run the tests
    pytest.main([__file__, '-v'])