"""
Analysis module for User Story 3: Statistical Correlation Analysis.

This module handles data validation, independence checks, regression analysis,
and statistical tests for the llmXive pipeline.
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

# Import local utilities
from src.utils.logging import get_logger

# Custom exception for circular validation risks
class CircularValidationRiskError(Exception):
    """Raised when a high correlation indicates potential circular validation."""
    pass

logger = get_logger(__name__)

# Constants
THRESHOLD_CORRELATION = 0.5
DATA_FILTERED_DIR = Path("data/filtered")
OUTPUTS_DIR = Path("outputs")

def load_filtered_instances() -> List[Dict[str, Any]]:
    """
    Load all filtered instances from the data/filtered directory.
    
    Returns:
        List of dictionaries representing the filtered dataset.
        
    Raises:
        FileNotFoundError: If no filtered data files are found.
        ValueError: If data files are malformed.
    """
    if not DATA_FILTERED_DIR.exists():
        raise FileNotFoundError(f"Filtered data directory not found: {DATA_FILTERED_DIR}")
    
    instances = []
    found_files = list(DATA_FILTERED_DIR.glob("*.json"))
    
    if not found_files:
        # Check for CSV as fallback if JSON is empty
        csv_files = list(DATA_FILTERED_DIR.glob("*.csv"))
        if csv_files:
            for csv_file in csv_files:
                df = pd.read_csv(csv_file)
                instances.extend(df.to_dict(orient='records'))
        else:
            raise FileNotFoundError(f"No filtered data files found in {DATA_FILTERED_DIR}")
    else:
        for json_file in found_files:
            with open(json_file, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    if isinstance(data, list):
                        instances.extend(data)
                    elif isinstance(data, dict):
                        instances.append(data)
                except json.JSONDecodeError as e:
                    logger.error(f"Malformed JSON in {json_file}: {e}")
                    raise ValueError(f"Malformed JSON in {json_file}: {e}")
    
    return instances

def extract_human_judgment_score(instances: List[Dict[str, Any]]) -> np.ndarray:
    """
    Extract and validate the 'Human Judgment Score' field from filtered instances.
    
    This function ensures the field exists and is numeric for all records.
    
    Args:
        instances: List of dictionaries containing instance data.
        
    Returns:
        numpy array of human judgment scores.
        
    Raises:
        ValueError: If the 'Human Judgment Score' field is missing or non-numeric.
    """
    if not instances:
        raise ValueError("ERROR: Human Judgment Score missing - No instances provided")
    
    scores = []
    missing_count = 0
    non_numeric_count = 0
    
    for i, instance in enumerate(instances):
        # Check for common variations of the key
        human_score = None
        for key in ['human_judgment_score', 'human_score', 'Human Judgment Score', 'HumanScore']:
            if key in instance:
                human_score = instance[key]
                break
        
        if human_score is None:
            missing_count += 1
            logger.warning(f"Instance {i} missing 'Human Judgment Score' field")
            continue
        
        try:
            val = float(human_score)
            if np.isnan(val) or np.isinf(val):
                non_numeric_count += 1
                logger.warning(f"Instance {i} has invalid numeric value for Human Judgment Score: {human_score}")
            else:
                scores.append(val)
        except (TypeError, ValueError):
            non_numeric_count += 1
            logger.warning(f"Instance {i} has non-numeric 'Human Judgment Score': {human_score}")
    
    if missing_count > 0 or non_numeric_count > 0:
        error_msg = f"ERROR: Human Judgment Score missing or invalid. " \
                    f"Missing: {missing_count}, Non-numeric: {non_numeric_count}, " \
                    f"Valid: {len(scores)}"
        raise ValueError(error_msg)
    
    if len(scores) == 0:
        raise ValueError("ERROR: Human Judgment Score missing - No valid scores found")
    
    return np.array(scores)

def load_scores() -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Load Logic, Fidelity, and Human Judgment scores from the scores directory.
    
    Returns:
        Tuple of (human_scores, logic_scores, fidelity_scores) as numpy arrays.
        
    Raises:
        FileNotFoundError: If score files are missing.
        ValueError: If score data is malformed.
    """
    scores_dir = Path("data/scores")
    if not scores_dir.exists():
        raise FileNotFoundError(f"Scores directory not found: {scores_dir}")
    
    logic_scores = []
    fidelity_scores = []
    human_scores = []
    
    # We expect a single aggregated scores file or multiple per-instance files
    # Based on T021, results are written to data/scores/
    score_files = list(scores_dir.glob("*.json"))
    
    if not score_files:
        raise FileNotFoundError(f"No score files found in {scores_dir}")
    
    for score_file in score_files:
        try:
            with open(score_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict):
                # Check if it's a single record or a wrapper
                if 'records' in data:
                    records = data['records']
                else:
                    records = [data]
            else:
                logger.warning(f"Unexpected data format in {score_file}, skipping")
                continue
            
            for record in records:
                if 'logic_score' in record and 'fidelity_score' in record:
                    logic_scores.append(float(record['logic_score']))
                    fidelity_scores.append(float(record['fidelity_score']))
                else:
                    logger.warning(f"Record missing logic/fidelity scores in {score_file}")
                    
        except json.JSONDecodeError as e:
            logger.error(f"Malformed JSON in {score_file}: {e}")
            raise ValueError(f"Malformed JSON in {score_file}: {e}")
    
    if not logic_scores:
        raise ValueError("No valid logic/fidelity scores found in data/scores/")
    
    return (
        np.array(human_scores), 
        np.array(logic_scores), 
        np.array(fidelity_scores)
    )

def check_independence() -> Dict[str, Any]:
    """
    Perform the independence check: Calculate Pearson correlation between 
    Human Score and Logic Score.
    
    If |r| >= 0.5, it writes a risk report atomically and raises an error.
    
    Returns:
        Dictionary with correlation details if successful.
        
    Raises:
        CircularValidationRiskError: If correlation threshold is exceeded.
    """
    # Load filtered instances to get Human Judgment Scores
    logger.info("Loading filtered instances for Human Judgment Score extraction...")
    instances = load_filtered_instances()
    human_scores = extract_human_judgment_score(instances)
    
    # Load scores to get Logic Scores
    logger.info("Loading computed scores for Logic Score extraction...")
    _, logic_scores, _ = load_scores()
    
    # Ensure alignment (assuming 1:1 mapping based on pipeline flow)
    min_len = min(len(human_scores), len(logic_scores))
    if min_len == 0:
        raise ValueError("Insufficient data for correlation check.")
    
    h_scores = human_scores[:min_len]
    l_scores = logic_scores[:min_len]
    
    # Calculate Pearson correlation
    r, p_value = stats.pearsonr(l_scores, h_scores)
    
    logger.info(f"Correlation (Human vs Logic): r={r:.4f}, p={p_value:.4f}")
    
    result = {
        "r": float(r),
        "p_value": float(p_value),
        "threshold": THRESHOLD_CORRELATION,
        "decision": "PASS" if abs(r) < THRESHOLD_CORRELATION else "FAIL",
        "timestamp": str(pd.Timestamp.now())
    }
    
    if abs(r) >= THRESHOLD_CORRELATION:
        # Atomically write the risk report
        report_path = OUTPUTS_DIR / "circular_validation_risk_report.json"
        temp_path = OUTPUTS_DIR / "circular_validation_risk_report.json.tmp"
        
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        
        # Atomic rename
        os.rename(temp_path, report_path)
        
        error_msg = f"CIRCULAR_VALIDATION_RISK: |r|={abs(r):.4f} >= {THRESHOLD_CORRELATION}"
        logger.error(error_msg)
        raise CircularValidationRiskError(error_msg)
    
    logger.info("Independence check passed.")
    return result

def run_regression_analysis() -> Dict[str, Any]:
    """
    Perform multiple linear regression: Dependent=Human Score, Independent=Logic & Fidelity Scores.
    
    Returns:
        Dictionary containing regression results (betas, p-values, r-squared).
    """
    logger.info("Running multiple linear regression analysis...")
    _, logic_scores, fidelity_scores = load_scores()
    human_scores = extract_human_judgment_score(load_filtered_instances())
    
    min_len = min(len(human_scores), len(logic_scores), len(fidelity_scores))
    if min_len == 0:
        raise ValueError("Insufficient data for regression analysis.")
    
    y = human_scores[:min_len]
    X_logic = logic_scores[:min_len]
    X_fidelity = fidelity_scores[:min_len]
    
    # Prepare design matrix (add intercept)
    X = np.column_stack([np.ones(min_len), X_logic, X_fidelity])
    
    # OLS Regression
    try:
        # Using scipy.linalg.lstsq for basic regression
        beta, residuals, rank, s = np.linalg.lstsq(X, y, rcond=None)
        
        # Calculate predictions and R-squared
        y_pred = X @ beta
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
        
        # Standard errors and t-statistics (approximate)
        # Residual variance
        dof = len(y) - X.shape[1]
        if dof > 0:
            mse = ss_res / dof
            # Covariance matrix of coefficients
            cov_beta = mse * np.linalg.inv(X.T @ X)
            se_beta = np.sqrt(np.diag(cov_beta))
            t_stats = beta / se_beta
            # Two-tailed p-values
            p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), dof))
        else:
            se_beta = [0.0] * len(beta)
            t_stats = [0.0] * len(beta)
            p_values = [1.0] * len(beta)
        
        result = {
            "model_r_squared": float(r_squared),
            "beta_intercept": float(beta[0]),
            "beta_logic": float(beta[1]),
            "beta_fidelity": float(beta[2]),
            "p_value_intercept": float(p_values[0]),
            "p_value_logic": float(p_values[1]),
            "p_value_fidelity": float(p_values[2]),
            "fdr_corrected_p_logic": float(p_values[1]), # Placeholder, updated in T026
            "fdr_corrected_p_fidelity": float(p_values[2]) # Placeholder, updated in T026
        }
        
        logger.info(f"Regression R-squared: {r_squared:.4f}")
        logger.info(f"Betas: Logic={beta[1]:.4f}, Fidelity={beta[2]:.4f}")
        
        return result
        
    except np.linalg.LinAlgError as e:
        logger.error(f"Regression failed due to linear algebra error: {e}")
        raise ValueError("Regression analysis failed: Matrix singularity or data issues.")

def benjamini_hochberg_correction(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg correction for False Discovery Rate.
    
    Args:
        p_values: List of raw p-values.
        
    Returns:
        List of FDR-corrected p-values.
    """
    if not p_values:
        return []
    
    m = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array([p_values[i] for i in sorted_indices])
    
    # BH correction
    ranks = np.arange(1, m + 1)
    corrected_p = sorted_p * m / ranks
    corrected_p = np.minimum(corrected_p, 1.0)
    corrected_p = np.minimum.accumulate(corrected_p[::-1])[::-1] # Ensure monotonicity
    
    # Reorder to original indices
    result = [0.0] * m
    for i, idx in enumerate(sorted_indices):
        result[idx] = float(corrected_p[i])
    
    return result

def fisher_z_test(r1: float, r2: float, n1: int, n2: int) -> Tuple[float, float]:
    """
    Perform Fisher's r-to-z transformation to test the difference between two correlations.
    
    Args:
        r1: First correlation coefficient.
        r2: Second correlation coefficient.
        n1: Sample size for r1.
        n2: Sample size for r2.
        
    Returns:
        Tuple of (z_score, p_value).
    """
    # Fisher transformation
    z1 = 0.5 * np.log((1 + r1) / (1 - r1))
    z2 = 0.5 * np.log((1 + r2) / (1 - r2))
    
    # Standard error of the difference
    se_diff = np.sqrt(1 / (n1 - 3) + 1 / (n2 - 3))
    
    z_score = (z1 - z2) / se_diff
    p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
    
    return float(z_score), float(p_value)

def run_correlation_difference_test() -> Dict[str, Any]:
    """
    Test if Logic correlation exceeds Fidelity correlation by at least 0.1 with p < 0.05.
    
    Returns:
        Dictionary with z_score, p_value, effect_size, conclusion, threshold_met.
    """
    logger.info("Running correlation difference test...")
    
    # We need correlations of Logic vs Human and Fidelity vs Human
    # Re-load data
    _, logic_scores, fidelity_scores = load_scores()
    human_scores = extract_human_judgment_score(load_filtered_instances())
    
    min_len = min(len(human_scores), len(logic_scores), len(fidelity_scores))
    if min_len == 0:
        raise ValueError("Insufficient data for correlation difference test.")
    
    h = human_scores[:min_len]
    l = logic_scores[:min_len]
    f = fidelity_scores[:min_len]
    
    r_logic, _ = stats.pearsonr(l, h)
    r_fidelity, _ = stats.pearsonr(f, h)
    
    n = min_len
    z_score, p_value = fisher_z_test(r_logic, r_fidelity, n, n)
    
    effect_size = abs(r_logic) - abs(r_fidelity)
    threshold = 0.1
    threshold_met = (effect_size >= threshold) and (p_value < 0.05)
    
    conclusion = "Logic is significantly stronger" if threshold_met else "Difference not significant or below threshold"
    
    result = {
        "r_logic": float(r_logic),
        "r_fidelity": float(r_fidelity),
        "z_score": z_score,
        "p_value": p_value,
        "effect_size": effect_size,
        "threshold_met": threshold_met,
        "threshold_value": threshold,
        "conclusion": conclusion
    }
    
    logger.info(f"Correlation Difference Test: z={z_score:.4f}, p={p_value:.4f}, Met={threshold_met}")
    return result

def main():
    """
    Main entry point for the analysis stage.
    Validates Human Judgment Score extraction as a prerequisite.
    """
    try:
        logger.info("Starting Analysis Stage (T024a: Validation)...")
        
        # Step 1: Validate Human Judgment Score (T024a)
        logger.info("Validating Human Judgment Score field...")
        instances = load_filtered_instances()
        human_scores = extract_human_judgment_score(instances)
        logger.info(f"Successfully extracted {len(human_scores)} Human Judgment Scores.")
        
        # Step 2: Independence Check (T024)
        logger.info("Performing independence check...")
        indep_result = check_independence()
        logger.info(f"Independence check result: {indep_result['decision']}")
        
        # Step 3: Regression (T025)
        logger.info("Performing regression analysis...")
        reg_result = run_regression_analysis()
        
        # Step 4: FDR Correction (T026)
        logger.info("Applying Benjamini-Hochberg correction...")
        p_values = [reg_result['p_value_logic'], reg_result['p_value_fidelity']]
        corrected_p = benjamini_hochberg_correction(p_values)
        reg_result['fdr_corrected_p_logic'] = corrected_p[0]
        reg_result['fdr_corrected_p_fidelity'] = corrected_p[1]
        
        # Step 5: Correlation Difference Test (T028a)
        logger.info("Running correlation difference test...")
        diff_result = run_correlation_difference_test()
        
        # Final Output
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        report_path = OUTPUTS_DIR / "regression_analysis_results.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                "independence_check": indep_result,
                "regression": reg_result,
                "correlation_difference": diff_result
            }, f, indent=2)
        
        logger.info(f"Analysis complete. Results written to {report_path}")
        
    except CircularValidationRiskError as e:
        logger.critical(f"Pipeline halted due to circular validation risk: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.critical(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error during analysis: {e}")
        raise

if __name__ == "__main__":
    main()