"""
SIMEX Correction for Misclassification Bias.

Implements the Simulation-Extrapolation (SIMEX) method to correct
Linear Mixed-Effects Regression coefficients for misclassification bias
in the 'origin_label' variable, using the false positive rate from T018.

Per Plan Override: Use SIMEX, not matrix correction.
Logic: If fp_rate > 0.05, apply correction; otherwise, skip.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import numpy as np
import pandas as pd
from scipy import optimize

# Local imports matching API surface
from analysis.load_fp_rate import load_fp_rate
from analysis.models import load_filtered_pr_data, run_mann_whitney_analysis
from data.logging_config import get_logger

logger = get_logger(__name__)

# Constants
SIMEX_BUDGET = 100  # Number of simulations per lambda
LAMBDAS = np.linspace(0, 2, 5)  # Lambda values for extrapolation
RANDOM_SEED = 42


def load_analysis_results() -> Dict[str, Any]:
    """Load existing analysis results from disk."""
    results_path = Path("data/analysis_results.json")
    if not results_path.exists():
        logger.error(f"Analysis results file not found: {results_path}")
        return {}
    
    with open(results_path, 'r') as f:
        return json.load(f)


def save_analysis_results(results: Dict[str, Any]) -> None:
    """Save updated analysis results to disk."""
    results_path = Path("data/analysis_results.json")
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved updated analysis results to {results_path}")


def simulate_misclassification(
    df: pd.DataFrame, 
    fp_rate: float, 
    fn_rate: float,
    seed: int
) -> pd.DataFrame:
    """
    Simulate misclassification in the origin_label column.
    
    Args:
        df: DataFrame with 'origin_label' column ('Disclosing' or 'Non-Disclosing')
        fp_rate: False positive rate (probability of labeling Non-Disclosing as Disclosing)
        fn_rate: False negative rate (probability of labeling Disclosing as Non-Disclosing)
        seed: Random seed for reproducibility
        
    Returns:
        DataFrame with simulated misclassified labels
    """
    np.random.seed(seed)
    df_sim = df.copy()
    
    # Convert labels to binary for easier manipulation
    # 1 = Disclosing, 0 = Non-Disclosing
    true_labels = (df_sim['origin_label'] == 'Disclosing').astype(int)
    
    simulated_labels = true_labels.copy()
    
    # Apply false positives: Non-Disclosing (0) -> Disclosing (1) with prob fp_rate
    non_disclosing_mask = (true_labels == 0)
    if non_disclosing_mask.any():
        fp_mask = np.random.random(non_disclosing_mask.sum()) < fp_rate
        simulated_labels[non_disclosing_mask] = fp_mask.astype(int)
    
    # Apply false negatives: Disclosing (1) -> Non-Disclosing (0) with prob fn_rate
    disclosing_mask = (true_labels == 1)
    if disclosing_mask.any():
        fn_mask = np.random.random(disclosing_mask.sum()) < fn_rate
        simulated_labels[disclosing_mask] = (1 - fn_mask).astype(int)
    
    # Convert back to string labels
    df_sim['simulated_origin_label'] = simulated_labels.map(
        {0: 'Non-Disclosing', 1: 'Disclosing'}
    )
    
    return df_sim


def fit_lmer_with_simulated_labels(
    df: pd.DataFrame, 
    lambda_val: float, 
    fp_rate: float,
    seed: int
) -> Dict[str, float]:
    """
    Fit LMER model with misclassified labels scaled by lambda.
    
    Note: For SIMEX with misclassification, we simulate at different lambda levels
    where lambda controls the amount of added noise.
    
    Args:
        df: Original DataFrame
        lambda_val: SIMEX lambda parameter (0 = no noise, higher = more noise)
        fp_rate: Estimated false positive rate
        seed: Random seed
        
    Returns:
        Dictionary with coefficient estimates
    """
    # Scale the misclassification probability by lambda
    # As lambda increases, we add more noise
    effective_fp = fp_rate * (1 + lambda_val)
    effective_fp = min(effective_fp, 0.5)  # Cap at 0.5 to avoid impossible rates
    
    # For simplicity, assume symmetric error rates (fn_rate = fp_rate)
    # In a full implementation, we'd estimate fn_rate separately
    effective_fn = effective_fp
    
    # Simulate misclassification
    df_sim = simulate_misclassification(df, effective_fp, effective_fn, seed + int(lambda_val * 1000))
    
    # Fit LMER with simulated labels
    # We use the same model structure as in models.py
    try:
        import statsmodels.api as sm
        import statsmodels.formula.api as smf
        
        # Prepare data
        df_fit = df_sim.copy()
        df_fit['origin_binary'] = (df_fit['simulated_origin_label'] == 'Disclosing').astype(int)
        
        # Fit LMER model: review_time ~ origin + code_lines_changed + (1|repo_id)
        # Using origin_binary as the variable of interest
        if 'total_review_time' not in df_fit.columns or 'code_lines_changed' not in df_fit.columns:
            logger.warning("Required columns missing for LMER fit")
            return {'origin_coef': np.nan}
        
        # Drop rows with missing values
        df_fit = df_fit.dropna(subset=['total_review_time', 'origin_binary', 'code_lines_changed', 'repo_id'])
        
        if len(df_fit) < 10:
            logger.warning("Insufficient data for LMER fit after filtering")
            return {'origin_coef': np.nan}
        
        # Fit the model
        formula = "total_review_time ~ origin_binary + code_lines_changed"
        model = smf.mixedlm(formula, df_fit, groups=df_fit["repo_id"])
        result = model.fit(reml=False)
        
        # Extract origin coefficient (origin_binary)
        origin_coef = result.params.get('origin_binary', np.nan)
        
        return {'origin_coef': origin_coef}
        
    except Exception as e:
        logger.warning(f"LMER fit failed for lambda={lambda_val}: {e}")
        return {'origin_coef': np.nan}


def extrapolate_to_zero_noise(
    coefficients: List[float], 
    lambdas: np.ndarray
) -> float:
    """
    Extrapolate coefficients to lambda = -1 (no measurement error).
    
    Uses quadratic extrapolation as is common in SIMEX.
    
    Args:
        coefficients: List of coefficients at different lambda values
        lambdas: Array of lambda values
        
    Returns:
        Extrapolated coefficient at lambda = -1
    """
    # Filter out NaN coefficients
    valid_mask = ~np.isnan(coefficients)
    if valid_mask.sum() < 3:
        logger.warning("Insufficient valid coefficients for extrapolation")
        return np.nan
    
    valid_coefs = np.array(coefficients)[valid_mask]
    valid_lambdas = lambdas[valid_mask]
    
    try:
        # Fit quadratic polynomial: coef = a*lambda^2 + b*lambda + c
        # We want to extrapolate to lambda = -1
        coeffs = np.polyfit(valid_lambdas, valid_coefs, 2)
        
        # Evaluate at lambda = -1
        extrapolated = np.polyval(coeffs, -1)
        
        return extrapolated
        
    except Exception as e:
        logger.warning(f"Extrapolation failed: {e}")
        return np.nan


def apply_simex_correction(
    df: pd.DataFrame, 
    fp_rate: float, 
    results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Apply SIMEX correction to LMER coefficients.
    
    Args:
        df: Filtered PR data with review times and labels
        fp_rate: Estimated false positive rate
        results: Existing analysis results to update
        
    Returns:
        Updated results dictionary with SIMEX-corrected coefficients
    """
    logger.info(f"Applying SIMEX correction with fp_rate={fp_rate:.4f}")
    
    # Check if correction is needed (fp_rate > 5%)
    if fp_rate <= 0.05:
        logger.info("False positive rate <= 5%, skipping SIMEX correction")
        results['simex_corrected_coefficients'] = {
            'applied': False,
            'reason': 'fp_rate <= 0.05',
            'fp_rate': fp_rate
        }
        return results
    
    logger.info("False positive rate > 5%, applying SIMEX correction")
    
    # Collect coefficients at different lambda levels
    all_coefficients = []
    
    for lambda_val in LAMBDAS:
        sims = []
        for i in range(SIMEX_BUDGET):
            coef_dict = fit_lmer_with_simulated_labels(df, lambda_val, fp_rate, RANDOM_SEED + i)
            sims.append(coef_dict['origin_coef'])
        
        # Average over simulations
        avg_coef = np.nanmean(sims)
        all_coefficients.append(avg_coef)
        logger.debug(f"Lambda={lambda_val:.2f}, Avg Coef={avg_coef:.4f}")
    
    # Extrapolate to lambda = -1
    corrected_coef = extrapolate_to_zero_noise(all_coefficients, LAMBDAS)
    
    if np.isnan(corrected_coef):
        logger.warning("SIMEX extrapolation failed, cannot compute corrected coefficient")
        results['simex_corrected_coefficients'] = {
            'applied': True,
            'status': 'failed',
            'fp_rate': fp_rate,
            'corrected_origin_coef': None
        }
    else:
        logger.info(f"SIMEX correction successful. Corrected origin coefficient: {corrected_coef:.4f}")
        
        # Get original coefficient for comparison
        original_coef = None
        if 'lmer' in results and 'coefficients' in results['lmer']:
            lmer_coefs = results['lmer']['coefficients']
            if isinstance(lmer_coefs, dict):
                original_coef = lmer_coefs.get('origin_binary', lmer_coefs.get('origin', None))
            elif isinstance(lmer_coefs, list) and len(lmer_coefs) > 0:
                # Assume first element or find by name
                original_coef = lmer_coefs[0] if isinstance(lmer_coefs[0], (int, float)) else None
        
        results['simex_corrected_coefficients'] = {
            'applied': True,
            'status': 'success',
            'fp_rate': fp_rate,
            'corrected_origin_coef': corrected_coef,
            'original_origin_coef': original_coef,
            'lambdas_used': LAMBDAS.tolist(),
            'coefficients_at_lambdas': all_coefficients
        }
    
    return results


def main():
    """Main entry point for SIMEX correction task."""
    logger.info("Starting SIMEX correction for misclassification bias")
    
    # 1. Load false positive rate from T018
    fp_result = load_fp_rate()
    if fp_result is None:
        logger.error("Failed to load false positive rate from baseline corpus")
        sys.exit(1)
    
    fp_rate = fp_result.get('fp_rate', 0.0)
    logger.info(f"Loaded false positive rate: {fp_rate:.4f}")
    
    # 2. Load filtered PR data
    df = load_filtered_pr_data()
    if df is None or df.empty:
        logger.error("Failed to load filtered PR data")
        sys.exit(1)
    
    logger.info(f"Loaded {len(df)} filtered PRs for analysis")
    
    # 3. Load existing analysis results
    results = load_analysis_results()
    if not results:
        logger.error("No existing analysis results found. Run T024 first.")
        sys.exit(1)
    
    # 4. Apply SIMEX correction
    updated_results = apply_simex_correction(df, fp_rate, results)
    
    # 5. Save updated results
    save_analysis_results(updated_results)
    
    logger.info("SIMEX correction completed successfully")
    
    # Print summary
    simex_result = updated_results.get('simex_corrected_coefficients', {})
    if simex_result.get('applied'):
        if simex_result.get('status') == 'success':
            print(f"\nSIMEX Correction Applied:")
            print(f"  False Positive Rate: {simex_result['fp_rate']:.4f}")
            print(f"  Original Coefficient: {simex_result.get('original_origin_coef', 'N/A')}")
            print(f"  Corrected Coefficient: {simex_result['corrected_origin_coef']:.4f}")
        else:
            print(f"\nSIMEX Correction Failed: {simex_result.get('reason', 'Unknown error')}")
    else:
        print(f"\nSIMEX Correction Skipped: {simex_result.get('reason', 'fp_rate <= 0.05')}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
