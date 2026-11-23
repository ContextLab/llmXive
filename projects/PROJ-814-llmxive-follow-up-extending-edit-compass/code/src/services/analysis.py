import os
import sys
import json
import logging
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests

from src.data_models import ScoreRecord, RegressionResult
from src.utils.logging import get_logger

logger = get_logger(__name__)

class CircularValidationRiskError(Exception):
    """Raised when independence check fails (|r| >= 0.5)."""
    pass

def load_filtered_instances(data_dir: str = "data/filtered") -> List[Dict[str, Any]]:
    """Load filtered instances from JSON files in data/filtered/."""
    instances = []
    filtered_dir = Path(data_dir)
    if not filtered_dir.exists():
        raise FileNotFoundError(f"Filtered data directory not found: {filtered_dir}")

    for file_path in filtered_dir.glob("*.json"):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                instances.extend(data)
            elif isinstance(data, dict):
                instances.append(data)
    
    if not instances:
        raise ValueError(f"No instances found in {filtered_dir}")
    
    logger.info(f"Loaded {len(instances)} filtered instances from {filtered_dir}")
    return instances

def load_scores(data_dir: str = "data/scores") -> List[Dict[str, Any]]:
    """Load score records from JSON files in data/scores/."""
    scores = []
    scores_dir = Path(data_dir)
    if not scores_dir.exists():
        raise FileNotFoundError(f"Scores directory not found: {scores_dir}")

    for file_path in scores_dir.glob("*.json"):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                scores.extend(data)
            elif isinstance(data, dict):
                scores.append(data)
    
    if not scores:
        raise ValueError(f"No scores found in {scores_dir}")
    
    logger.info(f"Loaded {len(scores)} score records from {scores_dir}")
    return scores

def extract_human_scores(instances: List[Dict[str, Any]]) -> np.ndarray:
    """Extract 'human_judgment_score' from instances."""
    scores = []
    for inst in instances:
        if 'human_judgment_score' not in inst:
            raise ValueError("ERROR: Human Judgment Score missing")
        val = inst['human_judgment_score']
        if not isinstance(val, (int, float)) or np.isnan(val):
            raise ValueError(f"Invalid human_judgment_score: {val}")
        scores.append(float(val))
    return np.array(scores)

def extract_logic_scores(scores: List[Dict[str, Any]]) -> np.ndarray:
    """Extract 'logic_score' from score records."""
    logic = []
    for rec in scores:
        if 'logic_score' not in rec:
            raise ValueError("Missing 'logic_score' in score record")
        val = rec['logic_score']
        if not isinstance(val, (int, float)) or np.isnan(val):
            raise ValueError(f"Invalid logic_score: {val}")
        logic.append(float(val))
    return np.array(logic)

def extract_fidelity_scores(scores: List[Dict[str, Any]]) -> np.ndarray:
    """Extract 'fidelity_score' from score records."""
    fidelity = []
    for rec in scores:
        if 'fidelity_score' not in rec:
            raise ValueError("Missing 'fidelity_score' in score record")
        val = rec['fidelity_score']
        if not isinstance(val, (int, float)) or np.isnan(val):
            raise ValueError(f"Invalid fidelity_score: {val}")
        fidelity.append(float(val))
    return np.array(fidelity)

def check_independence(human_scores: np.ndarray, logic_scores: np.ndarray) -> Tuple[float, float]:
    """
    Calculate Pearson correlation between Human Score and Logic Score.
    Returns (r, p_value).
    Raises CircularValidationRiskError if |r| >= 0.5.
    """
    r, p_value = stats.pearsonr(human_scores, logic_scores)
    logger.info(f"Independence check: Pearson r = {r:.4f}, p = {p_value:.4f}")
    return r, p_value

def write_circular_validation_risk_report(r: float, threshold: float = 0.5, output_path: str = "outputs/circular_validation_risk_report.json"):
    """
    Atomically write the circular validation risk report.
    Uses a temporary file + os.rename for atomicity.
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    report = {
        "r": float(r),
        "threshold": float(threshold),
        "decision": "FAIL" if abs(r) >= threshold else "PASS",
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    # Atomic write: write to tmp, then rename
    fd, tmp_path = tempfile.mkstemp(suffix='.tmp', dir=str(output_dir))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        shutil.move(tmp_path, output_path)
        logger.info(f"Atomically wrote circular validation risk report to {output_path}")
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

def run_regression_analysis(
    human_scores: np.ndarray,
    logic_scores: np.ndarray,
    fidelity_scores: np.ndarray
) -> RegressionResult:
    """
    Perform multiple linear regression:
    Dependent: Human Score
    Independent: Logic Score, Fidelity Score
    
    Returns RegressionResult with:
    - model_r_squared
    - beta_logic, beta_fidelity (standardized)
    - p_value_logic, p_value_fidelity
    - fdr_corrected_p_logic, fdr_corrected_p_fidelity
    """
    if len(human_scores) != len(logic_scores) or len(human_scores) != len(fidelity_scores):
        raise ValueError("Input arrays must have the same length")
    
    # Prepare data
    y = human_scores
    X = np.column_stack([logic_scores, fidelity_scores])
    
    # Add intercept
    X_with_intercept = sm.add_constant(X)
    
    # Fit OLS model
    model = sm.OLS(y, X_with_intercept).fit()
    
    # Extract coefficients and p-values
    # Coefficients: [intercept, beta_logic, beta_fidelity]
    params = model.params
    p_values = model.pvalues
    
    beta_logic = params[1]
    beta_fidelity = params[2]
    p_value_logic = p_values[1]
    p_value_fidelity = p_values[2]
    r_squared = model.rsquared
    
    # Standardized betas (beta coefficients)
    # beta_std = beta * (std_x / std_y)
    std_logic = np.std(logic_scores, ddof=1)
    std_fidelity = np.std(fidelity_scores, ddof=1)
    std_human = np.std(human_scores, ddof=1)
    
    if std_human == 0:
        raise ValueError("Standard deviation of human scores is zero; cannot standardize.")
    
    beta_logic_std = beta_logic * (std_logic / std_human)
    beta_fidelity_std = beta_fidelity * (std_fidelity / std_human)
    
    # Benjamini-Hochberg FDR correction on p-values
    p_values_array = np.array([p_value_logic, p_value_fidelity])
    reject, fdr_p_values, _, _ = multipletests(p_values_array, alpha=0.05, method='fdr_bh')
    
    fdr_corrected_p_logic = fdr_p_values[0]
    fdr_corrected_p_fidelity = fdr_p_values[1]
    
    logger.info(f"Regression R^2: {r_squared:.4f}")
    logger.info(f"Standardized Beta Logic: {beta_logic_std:.4f}, Beta Fidelity: {beta_fidelity_std:.4f}")
    logger.info(f"P-values (raw): Logic={p_value_logic:.4f}, Fidelity={p_value_fidelity:.4f}")
    logger.info(f"P-values (FDR): Logic={fdr_corrected_p_logic:.4f}, Fidelity={fdr_corrected_p_fidelity:.4f}")
    
    return RegressionResult(
        model_r_squared=r_squared,
        beta_logic=float(beta_logic_std),
        beta_fidelity=float(beta_fidelity_std),
        p_value_logic=float(p_value_logic),
        p_value_fidelity=float(p_value_fidelity),
        fdr_corrected_p_logic=float(fdr_corrected_p_logic),
        fdr_corrected_p_fidelity=float(fdr_corrected_p_fidelity)
    )

def fisher_z_test(r1: float, r2: float, n1: int, n2: int) -> Tuple[float, float]:
    """
    Fisher's r-to-z transformation to test difference between two correlations.
    Returns (z_score, p_value).
    """
    # Transform r to z
    z1 = 0.5 * np.log((1 + r1) / (1 - r1))
    z2 = 0.5 * np.log((1 + r2) / (1 - r2))
    
    # Standard error of the difference
    se_diff = np.sqrt(1 / (n1 - 3) + 1 / (n2 - 3))
    
    # Z-score
    z_score = (z1 - z2) / se_diff
    
    # Two-tailed p-value
    p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
    
    return z_score, p_value

def run_correlation_difference_test(
    human_scores: np.ndarray,
    logic_scores: np.ndarray,
    fidelity_scores: np.ndarray,
    output_path: str = "outputs/correlation_diff_test.json"
) -> Dict[str, Any]:
    """
    Perform statistical test for difference in correlation strength between
    Logic and Fidelity predictors vs Human Score.
    
    Tests if Logic correlation exceeds Fidelity correlation by at least 0.1
    AND p-value of the difference is < 0.05.
    
    Returns dict with: z_score, p_value, effect_size, conclusion, threshold_met, threshold_value
    """
    n = len(human_scores)
    
    # Calculate correlations
    r_logic, _ = stats.pearsonr(human_scores, logic_scores)
    r_fidelity, _ = stats.pearsonr(human_scores, fidelity_scores)
    
    # Fisher's Z test
    z_score, p_value = fisher_z_test(r_logic, r_fidelity, n, n)
    
    # Effect size: difference in correlations
    effect_size = r_logic - r_fidelity
    
    # Threshold check
    threshold = 0.1
    threshold_met = (effect_size >= threshold) and (p_value < 0.05)
    
    if threshold_met:
        conclusion = "Logic is significantly stronger predictor (diff >= 0.1, p < 0.05)"
    elif p_value < 0.05:
        conclusion = "Difference is significant, but effect size < 0.1 threshold"
    else:
        conclusion = "Inconclusive: Neither predictor significantly exceeds the 0.1 threshold with p < 0.05"
    
    result = {
        "z_score": float(z_score),
        "p_value": float(p_value),
        "effect_size": float(effect_size),
        "conclusion": conclusion,
        "threshold_met": threshold_met,
        "threshold_value": threshold,
        "r_logic": float(r_logic),
        "r_fidelity": float(r_fidelity),
        "n": n
    }
    
    # Write to file
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Wrote correlation difference test results to {output_path}")
    return result

def main():
    """
    Main entry point for the analysis stage.
    Executes:
    1. Load filtered instances and scores
    2. Extract human, logic, fidelity scores
    3. Independence check (T024) - raises if |r| >= 0.5
    4. Multiple linear regression (T025)
    5. Benjamini-Hochberg correction (T026) - done inside run_regression_analysis
    6. Correlation difference test (T028a)
    7. Generate final report (T029)
    """
    logger.info("Starting analysis stage...")
    
    # Load data
    instances = load_filtered_instances()
    scores = load_scores()
    
    # Extract scores
    human_scores = extract_human_scores(instances)
    logic_scores = extract_logic_scores(scores)
    fidelity_scores = extract_fidelity_scores(scores)
    
    # Independence check (T024)
    r_logic_human, _ = check_independence(human_scores, logic_scores)
    
    if abs(r_logic_human) >= 0.5:
        write_circular_validation_risk_report(r_logic_human)
        raise CircularValidationRiskError(f"CIRCULAR_VALIDATION_RISK: |r|={r_logic_human:.4f} >= 0.5")
    
    # Multiple linear regression (T025)
    regression_result = run_regression_analysis(human_scores, logic_scores, fidelity_scores)
    
    # Save regression result to JSON
    regression_json_path = "outputs/regression_result.json"
    with open(regression_json_path, 'w', encoding='utf-8') as f:
        json.dump(regression_result.model_dump(), f, indent=2)
    logger.info(f"Wrote regression result to {regression_json_path}")
    
    # Correlation difference test (T028a)
    diff_test_result = run_correlation_difference_test(human_scores, logic_scores, fidelity_scores)
    
    # Generate final report (T029)
    report_path = "outputs/regression_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Regression Analysis Report\n\n")
        f.write("## Summary\n\n")
        f.write(f"- **Model R²**: {regression_result.model_r_squared:.4f}\n")
        f.write(f"- **Standardized Beta (Logic)**: {regression_result.beta_logic:.4f}\n")
        f.write(f"- **Standardized Beta (Fidelity)**: {regression_result.beta_fidelity:.4f}\n")
        f.write(f"- **P-value (Logic)**: {regression_result.p_value_logic:.4f}\n")
        f.write(f"- **P-value (Fidelity)**: {regression_result.p_value_fidelity:.4f}\n")
        f.write(f"- **FDR-corrected P (Logic)**: {regression_result.fdr_corrected_p_logic:.4f}\n")
        f.write(f"- **FDR-corrected P (Fidelity)**: {regression_result.fdr_corrected_p_fidelity:.4f}\n\n")
        
        f.write("## Correlation Difference Test (Fisher's Z)\n\n")
        f.write(f"- **Z-score**: {diff_test_result['z_score']:.4f}\n")
        f.write(f"- **P-value**: {diff_test_result['p_value']:.4f}\n")
        f.write(f"- **Effect Size (r_logic - r_fidelity)**: {diff_test_result['effect_size']:.4f}\n")
        f.write(f"- **Threshold Met**: {diff_test_result['threshold_met']}\n")
        f.write(f"- **Threshold Value**: {diff_test_result['threshold_value']}\n\n")
        
        f.write("## Conclusion\n\n")
        f.write(f"{diff_test_result['conclusion']}\n\n")
        
        # Explicit SC-001 verification
        f.write("## SC-001 Verification\n\n")
        f.write(f"- **threshold_met**: {diff_test_result['threshold_met']}\n")
        f.write(f"- **threshold_value**: {diff_test_result['threshold_value']}\n")
    
    logger.info(f"Wrote final report to {report_path}")
    logger.info("Analysis stage completed successfully.")
    
    return regression_result, diff_test_result

if __name__ == "__main__":
    main()