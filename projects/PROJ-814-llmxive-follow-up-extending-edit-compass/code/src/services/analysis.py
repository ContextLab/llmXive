"""
Statistical analysis services for the llmXive pipeline.
Implements independence checks, regression, and correlation difference tests.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from scipy import stats
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests

from src.utils.logging import get_logger

logger = get_logger(__name__)

class CircularValidationRiskError(Exception):
    """Custom exception raised when correlation between metrics exceeds safety threshold."""
    pass

def check_independence(human_scores: np.ndarray, logic_scores: np.ndarray, threshold: float = 0.5) -> float:
    """
    Calculate Pearson correlation between human and logic scores.
    
    If |r| >= threshold, logs risk, writes risk report, and raises CircularValidationRiskError.
    
    Args:
        human_scores: Array of human judgment scores.
        logic_scores: Array of logic scores.
        threshold: Correlation threshold for risk flag (default 0.5).
        
    Returns:
        The calculated Pearson correlation coefficient r.
        
    Raises:
        CircularValidationRiskError: If |r| >= threshold.
    """
    if len(human_scores) != len(logic_scores) or len(human_scores) == 0:
        raise ValueError("Input arrays must be non-empty and of equal length.")

    r, p_value = stats.pearsonr(human_scores, logic_scores)
    abs_r = abs(r)
    
    logger.info(f"Independence Check: r = {r:.4f}, p-value = {p_value:.4e}")

    if abs_r >= threshold:
        # Ensure outputs directory exists
        outputs_dir = Path("outputs")
        outputs_dir.mkdir(parents=True, exist_ok=True)
        
        risk_report_path = outputs_dir / "circular_validation_risk_report.json"
        report_data = {
            "correlation_r": float(r),
            "absolute_correlation": float(abs_r),
            "threshold": threshold,
            "p_value": float(p_value),
            "halt_decision": True,
            "message": f"CIRCULAR_VALIDATION_RISK: |r|={abs_r:.4f} >= {threshold}"
        }
        
        with open(risk_report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.error(f"Circular validation risk detected: |r|={abs_r:.4f} >= {threshold}. Report saved to {risk_report_path}")
        raise CircularValidationRiskError(f"CIRCULAR_VALIDATION_RISK: |r|={abs_r:.4f} >= {threshold}")
    
    return r

def fisher_z_test(r1: float, r2: float, n1: int, n2: int) -> Tuple[float, float]:
    """
    Perform Fisher's r-to-z transformation to test the difference between two independent correlations.
    
    Args:
        r1: First correlation coefficient.
        r2: Second correlation coefficient.
        n1: Sample size for first correlation.
        n2: Sample size for second correlation.
        
    Returns:
        Tuple of (z_score, p_value).
    """
    # Fisher's r-to-z transformation
    z1 = 0.5 * np.log((1 + r1) / (1 - r1))
    z2 = 0.5 * np.log((1 + r2) / (1 - r2))
    
    # Standard error of the difference
    se_diff = np.sqrt(1 / (n1 - 3) + 1 / (n2 - 3))
    
    # Z-score
    z_score = (z1 - z2) / se_diff
    
    # Two-tailed p-value
    p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
    
    return z_score, p_value

def benjamini_hochberg_correction(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """
    Apply Benjamini-Hochberg False Discovery Rate correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values.
        alpha: Significance level (default 0.05).
        
    Returns:
        List of adjusted p-values.
    """
    if not p_values:
        return []
        
    # Use statsmodels for robust BH correction
    # method='fdr_bh' implements the Benjamini-Hochberg procedure
    reject, pvals_corrected, _, _ = multipletests(p_values, alpha=alpha, method='fdr_bh')
    
    return pvals_corrected.tolist()

def run_correlation_difference_test(human_scores: np.ndarray, logic_scores: np.ndarray, fidelity_scores: np.ndarray) -> Dict[str, Any]:
    """
    Perform statistical test for the difference in correlation strength between Logic and Fidelity predictors.
    
    Verifies if Logic correlation exceeds Fidelity correlation by at least 0.1 AND p-value < 0.05.
    
    Args:
        human_scores: Array of human scores.
        logic_scores: Array of logic scores.
        fidelity_scores: Array of fidelity scores.
        
    Returns:
        Dictionary with z_score, p_value, effect_size, and conclusion.
    """
    n = len(human_scores)
    
    r_logic, _ = stats.pearsonr(human_scores, logic_scores)
    r_fidelity, _ = stats.pearsonr(human_scores, fidelity_scores)
    
    z_score, p_value = fisher_z_test(r_logic, r_fidelity, n, n)
    
    effect_size = abs(r_logic) - abs(r_fidelity)
    
    # Decision logic
    if effect_size >= 0.1 and p_value < 0.05:
        conclusion = "Logic is stronger predictor"
    elif abs(effect_size) >= 0.1 and p_value < 0.05:
        conclusion = "Fidelity is stronger predictor"
    else:
        conclusion = "Inconclusive"
        
    return {
        "z_score": float(z_score),
        "p_value": float(p_value),
        "effect_size": float(effect_size),
        "correlation_logic": float(r_logic),
        "correlation_fidelity": float(r_fidelity),
        "conclusion": conclusion
    }

def run_regression_analysis(human_scores: np.ndarray, logic_scores: np.ndarray, fidelity_scores: np.ndarray) -> Dict[str, Any]:
    """
    Perform multiple linear regression: Human ~ Logic + Fidelity.
    
    Args:
        human_scores: Dependent variable.
        logic_scores: Independent variable 1.
        fidelity_scores: Independent variable 2.
        
    Returns:
        Dictionary containing regression statistics (betas, p-values, R-squared).
    """
    X = np.column_stack((logic_scores, fidelity_scores))
    y = human_scores
    
    # Add intercept
    X = sm.add_constant(X)
    
    model = sm.OLS(y, X).fit()
    
    results = {
        "r_squared": float(model.rsquared),
        "adj_r_squared": float(model.rsquared_adj),
        "coefficients": {
            "intercept": float(model.params[0]),
            "logic": float(model.params[1]),
            "fidelity": float(model.params[2])
        },
        "p_values": {
            "intercept": float(model.pvalues[0]),
            "logic": float(model.pvalues[1]),
            "fidelity": float(model.pvalues[2])
        },
        "f_statistic": float(model.f_pvalue)
    }
    
    return results

def main():
    """
    Entry point for analysis stage.
    Loads scores from data/scores/, performs independence check, regression, and correlation tests.
    """
    logger.info("Starting Analysis Stage")
    
    # Load data (simplified for now, assumes JSONL or CSV in data/scores/)
    # In a real implementation, this would load the actual score files generated by T021
    scores_dir = Path("data/scores")
    if not scores_dir.exists():
        logger.error(f"Scores directory not found: {scores_dir}")
        sys.exit(1)
        
    # Placeholder for actual data loading logic
    # This would iterate over files in data/scores/ and aggregate into arrays
    logger.warning("Data loading logic for analysis stage not fully implemented in this task context.")
    logger.info("Analysis stage structure defined.")

if __name__ == "__main__":
    main()