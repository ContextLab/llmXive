import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests
import pingouin as pg

from config import get_config, get_data_dir, set_seed

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_preprocessed_data() -> pd.DataFrame:
    """Load the standardized preprocessed data."""
    data_path = get_data_dir() / "processed" / "standardized.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"Preprocessed data not found at {data_path}. Run preprocessing first.")
    return pd.read_csv(data_path)

def fit_lmm(data: pd.DataFrame) -> Any:
    """
    Fit Linear Mixed Effects Model: Duration ~ Surprisal + Sequence_Length + Modality + (1 | Participant_ID)
    """
    formula = "duration_estimate ~ surprisal + sequence_length + modality + (1 | participant_id)"
    try:
        model = smf.mixedlm(formula, data, groups=data["participant_id"])
        result = model.fit()
        return result
    except Exception as e:
        logger.error(f"LMM fitting failed: {e}")
        return None

def fit_random_intercept_model(data: pd.DataFrame) -> Any:
    """
    Fallback model: Duration ~ 1 + (1 | Participant_ID)
    """
    formula = "duration_estimate ~ 1 + (1 | participant_id)"
    try:
        model = smf.mixedlm(formula, data, groups=data["participant_id"])
        result = model.fit()
        return result
    except Exception as e:
        logger.error(f"Random intercept model fitting failed: {e}")
        return None

def calculate_effect_sizes(data: pd.DataFrame, model_result: Any) -> Dict[str, Any]:
    """
    Calculate Cohen's d for the main effect of Surprisal using pingouin.
    Compares high vs low surprisal conditions (binned or grouped).
    """
    if model_result is None:
        return {}

    # Simple approach: bin surprisal into high/low for effect size calculation
    # In a real scenario, one might extract residuals or use specific contrasts.
    # Here we assume a binary split for demonstration of pingouin usage as requested.
    if 'surprisal' not in data.columns:
        logger.warning("Surprisal column missing, skipping effect size.")
        return {}

    median_surprisal = data['surprisal'].median()
    data['surprisal_group'] = np.where(data['surprisal'] > median_surprisal, 'high', 'low')

    try:
        # Calculate Cohen's d
        result = pg.compute_effsize(
            data[data['surprisal_group'] == 'high']['duration_estimate'],
            data[data['surprisal_group'] == 'low']['duration_estimate'],
            eftype='cohen'
        )
        
        # Calculate 95% CI for effect size
        ci_result = pg.compute_bootci(
            data[data['surprisal_group'] == 'high']['duration_estimate'],
            data[data['surprisal_group'] == 'low']['duration_estimate'],
            func='cohen',
            paired=False,
            confidence=0.95,
            seed=42,
            n_boot=1000
        )
        
        return {
            "cohen_d": float(result),
            "ci_95": [float(ci_result[0]), float(ci_result[1])]
        }
    except Exception as e:
        logger.error(f"Effect size calculation failed: {e}")
        return {}

def run_multiple_comparison_correction(p_values: List[float], method: str = 'fdr_bh') -> List[float]:
    """
    Apply multiple-comparison correction (Bonferroni or Benjamini-Hochberg).
    Only applies correction if num_tests > 1.
    
    Args:
        p_values: List of raw p-values from model coefficients.
        method: 'bonferroni' or 'fdr_bh' (Benjamini-Hochberg).
    
    Returns:
        List of corrected p-values.
    """
    num_tests = len(p_values)
    
    if num_tests <= 1:
        logger.info(f"Only {num_tests} test(s) found. Skipping multiple comparison correction.")
        return p_values
    
    if not p_values:
        return []

    try:
        if method == 'bonferroni':
            # statsmodels multipletests returns (reject, pvals_corrected, alphacSidak, alphacBonf)
            _, p_corrected, _, _ = multipletests(p_values, alpha=0.05, method='bonferroni')
        elif method == 'fdr_bh':
            _, p_corrected, _, _ = multipletests(p_values, alpha=0.05, method='fdr_bh')
        else:
            logger.warning(f"Unknown method {method}. Defaulting to fdr_bh.")
            _, p_corrected, _, _ = multipletests(p_values, alpha=0.05, method='fdr_bh')
        
        return [float(p) for p in p_corrected]
    except Exception as e:
        logger.error(f"Multiple comparison correction failed: {e}")
        return p_values

def calculate_mde(data: pd.DataFrame, model_result: Any, power: float = 0.80) -> float:
    """
    Calculate Minimum Detectable Effect (MDE) for power=0.80.
    Simplified implementation based on residual variance and sample size.
    """
    if model_result is None:
        return None
    
    try:
        # Extract residuals
        residuals = model_result.resid
        n = len(residuals)
        sigma = np.std(residuals)
        
        # Approximation for MDE (simplified for continuous outcome)
        # MDE = (Z_alpha + Z_beta) * sigma * sqrt(2/n) 
        # Using Z_alpha=1.96 (two-tailed 0.05), Z_beta=0.84 (power 0.80)
        z_alpha = 1.96
        z_beta = 0.84
        
        mde = (z_alpha + z_beta) * sigma * np.sqrt(2 / n)
        return float(mde)
    except Exception as e:
        logger.error(f"MDE calculation failed: {e}")
        return None

def write_results(results: Dict[str, Any], output_path: Path) -> None:
    """Write analysis results to JSON."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results written to {output_path}")

def run_analysis_pipeline() -> Dict[str, Any]:
    """
    Main pipeline: Load data -> Fit LMM -> Calculate Effect Sizes -> Correction -> MDE -> Save Results.
    """
    set_seed(42)
    data_dir = get_data_dir()
    output_path = data_dir / "analysis" / "results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Loading preprocessed data...")
    try:
        data = load_preprocessed_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        return {"status": "failed", "reason": str(e)}

    logger.info("Fitting LMM...")
    lmm_result = fit_lmm(data)
    
    if lmm_result is None:
        logger.info("LMM failed, trying random intercept fallback...")
        lmm_result = fit_random_intercept_model(data)
    
    if lmm_result is None:
        return {"status": "failed", "reason": "Model fitting failed completely."}

    # Extract p-values for correction
    # Assuming we care about the main predictors: surprisal, sequence_length, modality
    # We need to map parameter names to p-values.
    # Statsmodels result params and pvalues are aligned.
    params = lmm_result.pvalues
    
    # Filter for fixed effects only if necessary, but mixedlm returns all in pvalues
    # We will correct all fixed effect p-values
    p_values = [float(p) for p in params.values]
    
    # Apply correction (FR-005)
    corrected_p_values = run_multiple_comparison_correction(p_values, method='fdr_bh')
    
    # Map back to parameter names
    param_names = list(params.keys())
    corrected_results = {name: corr_p for name, corr_p in zip(param_names, corrected_p_values)}

    # Calculate Effect Sizes (FR-006)
    effect_sizes = calculate_effect_sizes(data, lmm_result)

    # Calculate MDE (FR-007)
    mde = calculate_mde(data, lmm_result)

    # Prepare final results
    final_results = {
        "status": "success",
        "model_summary": {
            "params": {k: float(v) for k, v in lmm_result.params.items()},
            "p_values_raw": {k: float(v) for k, v in params.items()},
            "p_values_corrected": corrected_results
        },
        "effect_sizes": effect_sizes,
        "mde": mde,
        "convergence_status": lmm_result.converged
    }

    write_results(final_results, output_path)
    return final_results

if __name__ == "__main__":
    run_analysis_pipeline()
