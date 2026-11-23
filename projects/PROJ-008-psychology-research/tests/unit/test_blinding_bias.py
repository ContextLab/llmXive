import pytest
import pandas as pd
import numpy as np
from code.analysis.meta_analysis import perform_blinding_bias_quantification
from code.utils.logging import get_logger

logger = get_logger(__name__)

def test_blinding_bias_detection():
    """
    Test that the blinding bias quantification correctly identifies
    a statistically significant difference between blinded and unblinded studies.
    
    Simulate a dataset where 'unblinded' studies show a substantially larger
    effect size and 'blinded' studies show a smaller effect size.
    """
    # Create synthetic data for testing
    # Unblinded studies: larger effect size (mean ~0.8)
    # Blinded studies: smaller effect size (mean ~0.3)
    
    n_unblinded = 6
    n_blinded = 6
    
    # Generate effect sizes with known difference
    np.random.seed(42)
    unblinded_effects = np.random.normal(loc=0.8, scale=0.15, size=n_unblinded)
    blinded_effects = np.random.normal(loc=0.3, scale=0.15, size=n_blinded)
    
    # Create DataFrame
    df = pd.DataFrame({
        "study_id": [f"study_{i}" for i in range(n_unblinded + n_blinded)],
        "hedges_g": list(unblinded_effects) + list(blinded_effects),
        "se": [0.1] * (n_unblinded + n_blinded),
        "blinded_assessment_flag": [False] * n_unblinded + [True] * n_blinded
    })
    
    # Run blinding bias quantification
    result = perform_blinding_bias_quantification(df)
    
    # Verify results
    assert result is not None, "Blinding bias quantification should return a result"
    assert "p_value" in result, "Result should contain p_value"
    assert "effect_difference" in result, "Result should contain effect_difference"
    
    # The p-value should be < 0.05 given the simulated difference
    assert result["p_value"] < 0.05, f"Expected significant p-value (<0.05), got {result['p_value']}"
    
    # The effect difference should be positive (unblinded > blinded)
    assert result["effect_difference"] > 0, f"Expected positive effect difference, got {result['effect_difference']}"
    
    logger.info(f"Blinding bias test passed: p={result['p_value']:.4f}, diff={result['effect_difference']:.4f}")

def test_blinding_bias_insufficient_sample():
    """
    Test that the function handles N < 10 gracefully by skipping analysis.
    """
    # Create small dataset (< 10 studies)
    df = pd.DataFrame({
        "study_id": ["study_1", "study_2", "study_3"],
        "hedges_g": [0.5, 0.6, 0.7],
        "se": [0.1, 0.1, 0.1],
        "blinded_assessment_flag": [False, True, False]
    })
    
    # Run blinding bias quantification
    result = perform_blinding_bias_quantification(df)
    
    # Should return None or a warning message when N < 10
    assert result is None or result.get("skipped", False), \
        "Should skip analysis when N < 10"
    
    logger.info("Insufficient sample test passed")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
