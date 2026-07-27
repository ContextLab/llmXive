import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from scipy import stats
import pandas as pd

from src.utils.logging import get_logger
from src.data_models import ScoreRecord

logger = get_logger(__name__)

class CircularValidationRiskError(Exception):
    """Raised when independence check fails due to high correlation."""
    pass

def load_scores(scores_dir: Path) -> List[ScoreRecord]:
    """Load all ScoreRecord JSON files from the scores directory."""
    records = []
    if not scores_dir.exists():
        logger.error(f"Scores directory does not exist: {scores_dir}")
        return records
    
    for file_path in scores_dir.glob("*.json"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Handle both single record and list of records
                if isinstance(data, list):
                    records.extend([ScoreRecord(**item) for item in data])
                else:
                    records.append(ScoreRecord(**data))
        except Exception as e:
            logger.warning(f"Failed to load {file_path}: {e}")
    return records

def check_independence(scores_dir: Path, threshold: float = 0.5) -> Dict[str, Any]:
    """
    Calculate Pearson correlation between Human Score and Logic Score.
    
    If |r| >= threshold, log the risk flag, ensure T024a has completed,
    then raise CircularValidationRiskError and exit process with code 1.
    
    Args:
        scores_dir: Path to directory containing score JSON files
        threshold: Correlation threshold for independence check (default 0.5)
    
    Returns:
        Dict with correlation value, threshold, and decision
    
    Raises:
        CircularValidationRiskError: If |r| >= threshold
    """
    logger.info(f"Starting independence check with threshold {threshold}")
    
    records = load_scores(scores_dir)
    if not records:
        raise ValueError(f"No valid score records found in {scores_dir}")
    
    # Extract scores
    human_scores = []
    logic_scores = []
    
    for record in records:
        if record.human_judgment_score is not None and record.logic_score is not None:
            human_scores.append(record.human_judgment_score)
            logic_scores.append(record.logic_score)
    
    if len(human_scores) < 2:
        raise ValueError("Insufficient data for correlation calculation (need at least 2 samples)")
    
    # Calculate Pearson correlation
    r, p_value = stats.pearsonr(human_scores, logic_scores)
    abs_r = abs(r)
    
    result = {
        "correlation": float(r),
        "absolute_correlation": float(abs_r),
        "p_value": float(p_value),
        "threshold": float(threshold),
        "sample_size": len(human_scores),
        "decision": "PASS" if abs_r < threshold else "FAIL"
    }
    
    logger.info(f"Correlation result: r={r:.4f}, |r|={abs_r:.4f}, p={p_value:.4f}")
    
    # Check against threshold
    if abs_r >= threshold:
        risk_msg = f"CIRCULAR_VALIDATION_RISK: |r|={abs_r:.4f} >= {threshold}"
        logger.error(risk_msg)
        
        # Ensure T024a report exists (check for the file)
        risk_report_path = scores_dir.parent / "circular_validation_risk_report.json"
        if risk_report_path.exists():
            logger.info(f"Verified T024a report exists: {risk_report_path}")
        else:
            logger.warning(f"T024a report not found at {risk_report_path}, but proceeding with halt")
        
        raise CircularValidationRiskError(risk_msg)
    
    logger.info("Independence check PASSED")
    return result

def fisher_z_test(r1: float, r2: float, n1: int, n2: int) -> Tuple[float, float]:
    """
    Perform Fisher's r-to-z transformation to test if two correlations differ significantly.
    
    Args:
        r1: First correlation coefficient
        r2: Second correlation coefficient
        n1: Sample size for first correlation
        n2: Sample size for second correlation
    
    Returns:
        Tuple of (z_score, p_value)
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
    
    return float(z_score), float(p_value)

def benjamini_hochberg_correction(p_values: List[float], alpha: float = 0.05) -> List[Dict[str, Any]]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values
        alpha: FDR threshold (default 0.05)
    
    Returns:
        List of dicts with original p-value, adjusted p-value, and significance
    """
    n = len(p_values)
    if n == 0:
        return []
    
    # Sort p-values with their original indices
    sorted_indices = sorted(range(n), key=lambda i: p_values[i])
    sorted_p_values = [p_values[i] for i in sorted_indices]
    
    # Calculate adjusted p-values
    adjusted_p_values = [0.0] * n
    for i, idx in enumerate(sorted_indices):
        # BH adjusted p-value: p * n / rank
        rank = i + 1
        adjusted = sorted_p_values[i] * n / rank
        adjusted_p_values[idx] = min(adjusted, 1.0)
    
    # Ensure monotonicity (adjusted p-values should be non-decreasing)
    for i in range(n - 2, -1, -1):
        adjusted_p_values[i] = min(adjusted_p_values[i], adjusted_p_values[i + 1])
    
    # Determine significance
    results = []
    for i, p in enumerate(p_values):
        adj_p = adjusted_p_values[i]
        results.append({
            "original_p": float(p),
            "adjusted_p": float(adj_p),
            "significant": adj_p <= alpha
        })
    
    return results

def run_correlation_difference_test(scores_dir: Path, output_path: Path) -> Dict[str, Any]:
    """
    Perform statistical test for difference in correlation strength between
    Logic and Fidelity predictors using Fisher's r-to-z transformation.
    
    Args:
        scores_dir: Path to scores directory
        output_path: Path to write results JSON
    
    Returns:
        Dict with test results
    """
    records = load_scores(scores_dir)
    if not records:
        raise ValueError(f"No valid score records found in {scores_dir}")
    
    human_scores = []
    logic_scores = []
    fidelity_scores = []
    
    for record in records:
        if (record.human_judgment_score is not None and 
            record.logic_score is not None and 
            record.fidelity_score is not None):
            human_scores.append(record.human_judgment_score)
            logic_scores.append(record.logic_score)
            fidelity_scores.append(record.fidelity_score)
    
    if len(human_scores) < 2:
        raise ValueError("Insufficient data for correlation difference test")
    
    n = len(human_scores)
    
    # Calculate correlations
    r_logic, _ = stats.pearsonr(human_scores, logic_scores)
    r_fidelity, _ = stats.pearsonr(human_scores, fidelity_scores)
    
    # Fisher's r-to-z test for difference
    z_score, p_value = fisher_z_test(r_logic, r_fidelity, n, n)
    
    # Effect size (difference in correlations)
    effect_size = abs(r_logic) - abs(r_fidelity)
    
    # Conclusion based on criteria: |diff| >= 0.1 AND p < 0.05
    conclusion = "Inconclusive"
    if abs(effect_size) >= 0.1 and p_value < 0.05:
        if r_logic > r_fidelity:
            conclusion = "Logic is stronger predictor"
        else:
            conclusion = "Fidelity is stronger predictor"
    elif abs(effect_size) >= 0.1:
        conclusion = "Effect size >= 0.1 but not statistically significant"
    elif p_value < 0.05:
        conclusion = "Statistically significant but effect size < 0.1"
    
    result = {
        "r_logic": float(r_logic),
        "r_fidelity": float(r_fidelity),
        "z_score": float(z_score),
        "p_value": float(p_value),
        "effect_size": float(effect_size),
        "sample_size": n,
        "conclusion": conclusion
    }
    
    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Correlation difference test results written to {output_path}")
    return result

def run_regression_analysis(scores_dir: Path, output_path: Path) -> Dict[str, Any]:
    """
    Perform multiple linear regression with Human Score as dependent variable
    and Logic & Fidelity scores as independent variables.
    
    Args:
        scores_dir: Path to scores directory
        output_path: Path to write regression results JSON
    
    Returns:
        Dict with regression results
    """
    records = load_scores(scores_dir)
    if not records:
        raise ValueError(f"No valid score records found in {scores_dir}")
    
    human_scores = []
    logic_scores = []
    fidelity_scores = []
    
    for record in records:
        if (record.human_judgment_score is not None and 
            record.logic_score is not None and 
            record.fidelity_score is not None):
            human_scores.append(record.human_judgment_score)
            logic_scores.append(record.logic_score)
            fidelity_scores.append(record.fidelity_score)
    
    if len(human_scores) < 3:
        raise ValueError("Insufficient data for regression analysis (need at least 3 samples)")
    
    # Prepare data for regression
    X = np.column_stack([logic_scores, fidelity_scores])
    y = np.array(human_scores)
    
    # Add intercept
    X_with_intercept = np.column_stack([np.ones(len(X)), X])
    
    # Fit regression
    beta, residuals, rank, s = np.linalg.lstsq(X_with_intercept, y, rcond=None)
    
    # Calculate R-squared
    y_pred = X_with_intercept @ beta
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot)
    
    # Calculate p-values for coefficients
    n = len(y)
    p = X_with_intercept.shape[1]
    dof = n - p
    
    # Standard errors
    mse = ss_res / dof
    cov_matrix = mse * np.linalg.inv(X_with_intercept.T @ X_with_intercept)
    se = np.sqrt(np.diag(cov_matrix))
    
    # t-statistics and p-values
    t_stats = beta / se
    p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), dof))
    
    # Standardized coefficients (betas)
    std_logic = np.std(logic_scores)
    std_fidelity = np.std(fidelity_scores)
    std_y = np.std(y)
    
    beta_logic_std = beta[1] * (std_logic / std_y)
    beta_fidelity_std = beta[2] * (std_fidelity / std_y)
    
    # Apply FDR correction to p-values
    p_values_to_correct = p_values[1:]  # Exclude intercept
    fdr_results = benjamini_hochberg_correction(list(p_values_to_correct))
    
    result = {
        "r_squared": float(r_squared),
        "coefficients": {
            "intercept": float(beta[0]),
            "logic": float(beta[1]),
            "fidelity": float(beta[2])
        },
        "standardized_betas": {
            "logic": float(beta_logic_std),
            "fidelity": float(beta_fidelity_std)
        },
        "p_values": {
            "logic": float(p_values[1]),
            "fidelity": float(p_values[2]),
            "fdr_corrected_logic": float(fdr_results[0]["adjusted_p"]),
            "fdr_corrected_fidelity": float(fdr_results[1]["adjusted_p"]),
            "fdr_significant_logic": fdr_results[0]["significant"],
            "fdr_significant_fidelity": fdr_results[1]["significant"]
        },
        "sample_size": n,
        "degrees_of_freedom": dof
    }
    
    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Regression analysis results written to {output_path}")
    return result

def main():
    """Main entry point for independence check and analysis pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run independence check and correlation analysis")
    parser.add_argument("--scores-dir", type=str, default="data/scores",
                      help="Directory containing score JSON files")
    parser.add_argument("--threshold", type=float, default=0.5,
                      help="Correlation threshold for independence check")
    parser.add_argument("--output-dir", type=str, default="outputs",
                      help="Directory for output files")
    
    args = parser.parse_args()
    
    scores_dir = Path(args.scores_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Run independence check
        indep_result = check_independence(scores_dir, args.threshold)
        logger.info(f"Independence check completed: {indep_result['decision']}")
        
        # Run correlation difference test
        diff_test_path = output_dir / "correlation_diff_test.json"
        diff_result = run_correlation_difference_test(scores_dir, diff_test_path)
        logger.info(f"Correlation difference test: {diff_result['conclusion']}")
        
        # Run regression analysis
        regression_path = output_dir / "regression_results.json"
        regression_result = run_regression_analysis(scores_dir, regression_path)
        logger.info(f"Regression analysis completed: R²={regression_result['r_squared']:.4f}")
        
        # Generate final report
        report_path = output_dir / "regression_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# Regression Analysis Report\n\n")
            f.write(f"## Independence Check\n")
            f.write(f"- Correlation (r): {indep_result['correlation']:.4f}\n")
            f.write(f"- |r|: {indep_result['absolute_correlation']:.4f}\n")
            f.write(f"- Threshold: {indep_result['threshold']}\n")
            f.write(f"- Decision: {indep_result['decision']}\n\n")
            
            f.write(f"## Correlation Difference Test\n")
            f.write(f"- Logic correlation (r): {diff_result['r_logic']:.4f}\n")
            f.write(f"- Fidelity correlation (r): {diff_result['r_fidelity']:.4f}\n")
            f.write(f"- Z-score: {diff_result['z_score']:.4f}\n")
            f.write(f"- P-value: {diff_result['p_value']:.4f}\n")
            f.write(f"- Effect size: {diff_result['effect_size']:.4f}\n")
            f.write(f"- Conclusion: {diff_result['conclusion']}\n\n")
            
            f.write(f"## Regression Analysis\n")
            f.write(f"- R²: {regression_result['r_squared']:.4f}\n")
            f.write(f"- Logic coefficient: {regression_result['coefficients']['logic']:.4f}\n")
            f.write(f"- Fidelity coefficient: {regression_result['coefficients']['fidelity']:.4f}\n")
            f.write(f"- Standardized beta (Logic): {regression_result['standardized_betas']['logic']:.4f}\n")
            f.write(f"- Standardized beta (Fidelity): {regression_result['standardized_betas']['fidelity']:.4f}\n")
            f.write(f"- P-value (Logic): {regression_result['p_values']['logic']:.4f}\n")
            f.write(f"- P-value (Fidelity): {regression_result['p_values']['fidelity']:.4f}\n")
            f.write(f"- FDR-corrected (Logic): {regression_result['p_values']['fdr_corrected_logic']:.4f}\n")
            f.write(f"- FDR-corrected (Fidelity): {regression_result['p_values']['fdr_corrected_fidelity']:.4f}\n")
        
        logger.info(f"Final report written to {report_path}")
        
    except CircularValidationRiskError as e:
        logger.error(f"Pipeline halted: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()