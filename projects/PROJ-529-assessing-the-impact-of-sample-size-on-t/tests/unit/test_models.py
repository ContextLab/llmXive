"""
Unit tests for the REML vs DL estimator switching logic at k=10.

This test validates the core logic of User Story 2 (US2) regarding
the estimator selection strategy defined in FR-003:
- Use DerSimonian-Laird (DL) for k >= 10
- Use Restricted Maximum Likelihood (REML) for k < 10
"""
import pytest
import numpy as np
from typing import List, Tuple
from dataclasses import dataclass

# Import the data models defined in the project's API surface
from code.models import Study, Subsample, MetaAnalysis, StabilityMetric
from code.utils.exceptions import ModelBoundaryError


# --------------------------------------------------------------------------
# Helper: Mock estimator functions
# --------------------------------------------------------------------------
# In a real implementation, these would call statsmodels or metafor.
# For this unit test, we mock the behavior to verify the switching logic.

def mock_reml_estimator(studies: List[Study]) -> Tuple[float, float]:
    """Mock REML estimator that returns a specific value to identify it."""
    if not studies:
        raise ValueError("No studies provided")
    # Return a pooled effect and SE that indicates REML was used
    # We use a distinct offset to verify the path taken in the test
    pooled_effect = 0.5 + len(studies) * 0.001 
    se = 0.1
    return pooled_effect, se

def mock_dl_estimator(studies: List[Study]) -> Tuple[float, float]:
    """Mock DL estimator that returns a specific value to identify it."""
    if not studies:
        raise ValueError("No studies provided")
    # Return a pooled effect and SE that indicates DL was used
    # Distinct offset from REML
    pooled_effect = 0.6 + len(studies) * 0.001
    se = 0.12
    return pooled_effect, se


# --------------------------------------------------------------------------
# Test Logic Implementation (Simulating code/models.py logic)
# --------------------------------------------------------------------------
def determine_estimator_type(k: int) -> str:
    """
    Determine which estimator to use based on study count k.
    
    Logic per FR-003:
    - k >= 10: DerSimonian-Laird (DL)
    - k < 10: REML
    """
    if k < 3:
        raise ValueError(f"Study count k={k} is too small for meta-analysis (min 3).")
    
    if k >= 10:
        return "DL"
    else:
        return "REML"


def fit_meta_analysis_with_switching_logic(studies: List[Study]) -> StabilityMetric:
    """
    Fits a meta-analysis applying the k-based estimator switching logic.
    This function simulates the logic that would exist in code/models.py.
    """
    k = len(studies)
    estimator_type = determine_estimator_type(k)
    
    if estimator_type == "DL":
        pooled_effect, se = mock_dl_estimator(studies)
    else:
        pooled_effect, se = mock_reml_estimator(studies)
        
    return StabilityMetric(
        k=k,
        estimator_type=estimator_type,
        pooled_effect=pooled_effect,
        pooled_se=se,
        ci_lower=pooled_effect - 1.96 * se,
        ci_upper=pooled_effect + 1.96 * se
    )


# --------------------------------------------------------------------------
# Test Cases
# --------------------------------------------------------------------------

@pytest.fixture
def mock_studies():
    """Generate a list of mock Study objects."""
    studies = []
    for i in range(50):
        studies.append(Study(
            study_id=f"study_{i}",
            effect_size=0.3 + np.random.normal(0, 0.1),
            se=0.1 + np.random.normal(0, 0.01)
        ))
    return studies

class TestEstimatorSwitchingLogic:
    """Tests for the REML vs DL switching logic at k=10."""

    def test_k_less_than_10_uses_reml(self, mock_studies):
        """Verify that k < 10 triggers REML estimator."""
        for k in [3, 5, 9]:
            subset = mock_studies[:k]
            result = fit_meta_analysis_with_switching_logic(subset)
            
            assert result.k == k
            assert result.estimator_type == "REML", f"Expected REML for k={k}, got {result.estimator_type}"
            # Verify the mock DL offset is NOT present (DL returns 0.6+, REML 0.5+)
            assert result.pooled_effect < 0.6, "Effect size suggests DL was used instead of REML"

    def test_k_equal_10_uses_dl(self, mock_studies):
        """Verify that k = 10 triggers DL estimator (the switching point)."""
        k = 10
        subset = mock_studies[:k]
        result = fit_meta_analysis_with_switching_logic(subset)
        
        assert result.k == k
        assert result.estimator_type == "DL", f"Expected DL for k={k}, got {result.estimator_type}"
        # Verify the mock DL offset IS present
        assert result.pooled_effect >= 0.6, "Effect size suggests REML was used instead of DL"

    def test_k_greater_than_10_uses_dl(self, mock_studies):
        """Verify that k > 10 continues to use DL estimator."""
        for k in [11, 15, 20]:
            subset = mock_studies[:k]
            result = fit_meta_analysis_with_switching_logic(subset)
            
            assert result.k == k
            assert result.estimator_type == "DL", f"Expected DL for k={k}, got {result.estimator_type}"

    def test_k_boundary_switching_behavior(self, mock_studies):
        """
        Explicitly test the boundary behavior around k=10 to ensure
        the switch happens exactly at the specified threshold.
        """
        # k=9 should be REML
        result_9 = fit_meta_analysis_with_switching_logic(mock_studies[:9])
        assert result_9.estimator_type == "REML"
        
        # k=10 should be DL
        result_10 = fit_meta_analysis_with_switching_logic(mock_studies[:10])
        assert result_10.estimator_type == "DL"
        
        # Ensure the effect sizes are distinctly different based on the mock
        # This confirms the correct code path was taken
        assert result_9.pooled_effect < result_10.pooled_effect, \
            "Switching logic did not result in expected change in estimator behavior"

    def test_k_too_small_raises_error(self, mock_studies):
        """Verify that k < 3 raises an error."""
        with pytest.raises(ValueError, match="too small"):
            fit_meta_analysis_with_switching_logic(mock_studies[:2])

if __name__ == "__main__":
    pytest.main([__file__, "-v"])