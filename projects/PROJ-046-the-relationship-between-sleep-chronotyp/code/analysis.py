"""
Analysis utilities for the Chronotype-Moral Judgement study.
Includes ANCOVA modeling, effect size calculation, and multiplicity control.
"""

import math
from typing import List, Tuple

def apply_bonferroni_correction(p_values: List[float]) -> List[float]:
    """
    Apply Bonferroni correction to a list of p-values.
    
    The correction multiplies each p-value by the number of tests (m).
    If the result exceeds 1.0, it is capped at 1.0.
    
    Args:
        p_values: List of raw p-values from statistical tests.
        
    Returns:
        List of Bonferroni-corrected p-values.
    """
    if not p_values:
        return []
    
    m = len(p_values)
    corrected = []
    
    for p in p_values:
        # Ensure p is within valid range before correction
        if p < 0.0 or p > 1.0:
            raise ValueError(f"Invalid p-value: {p}. Must be between 0 and 1.")
        
        corrected_p = p * m
        # Cap at 1.0
        if corrected_p > 1.0:
            corrected_p = 1.0
        
        corrected.append(corrected_p)
        
    return corrected

def calculate_significance_mask(p_values: List[float], alpha: float = 0.05) -> List[bool]:
    """
    Determine significance status for a list of p-values against an alpha threshold.
    
    Args:
        p_values: List of corrected p-values.
        alpha: Significance threshold (default 0.05).
        
    Returns:
        List of booleans indicating significance (True if p <= alpha).
    """
    return [p <= alpha for p in p_values]

def run_ancova_simulation(subscales: List[str], n_per_group: int = 50) -> dict:
    """
    Placeholder for ANCOVA execution logic.
    
    In a full implementation, this would:
    1. Load data from data/derived/classified_data.csv
    2. Fit linear models: MFQ_subscale ~ chronotype + PSQI + acute_sleepiness + age + sex
    3. Extract p-values for the chronotype effect
    4. Calculate VIFs
    5. Return results for further processing.
    
    Args:
        subscales: List of MFQ subscale names to analyze.
        n_per_group: Simulated sample size per chronotype group.
        
    Returns:
        Dictionary containing simulated results structure.
    """
    # This is a structural placeholder. The actual R script or statsmodels
    # implementation would go here in a production environment.
    # For the purpose of this task (testing the Bonferroni logic), 
    # we return a dummy structure that the test can consume if needed,
    # though the primary focus is the correction function.
    return {
        "subscales": subscales,
        "status": "simulation_placeholder",
        "message": "Actual ANCOVA requires data loading and R/statsmodels integration."
    }