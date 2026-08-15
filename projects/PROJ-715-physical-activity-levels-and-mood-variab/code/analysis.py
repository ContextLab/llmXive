import os
import sys
import logging
import json
import random
from pathlib import Path
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.formula.api import mixedlm
from scipy import stats

from config import get_path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
BOOTSTRAP_ITERATIONS = 1000
BOOTSTRAP_SEED = 42
CONSISTENCY_THRESHOLD = 0.80

def load_daily_aggregates() -> pd.DataFrame:
    """Load the preprocessed daily aggregates."""
    path = get_path('data/processed/daily_aggregates.csv')
    if not os.path.exists(path):
        raise FileNotFoundError(f"Daily aggregates file not found at {path}. Run preprocessing first.")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows from daily aggregates.")
    return df

def fit_mood_std_model(df: pd.DataFrame, subset_mask: pd.Series = None) -> Any:
    """Fit LMM with log(mood_std + 0.01) as outcome."""
    data = df[subset_mask] if subset_mask is not None else df
    
    # Ensure we have enough data
    if len(data) < 20:
        raise ValueError("Insufficient data to fit model.")

    # Formula: outcome ~ total_steps + sleep_duration + C(day_of_week) + baseline_affect
    # Using log(mood_std + 0.01) as the outcome (pre-transformed in T015b)
    formula = "log_mood_std + 0.01 ~ total_steps + sleep_duration + C(day_of_week) + baseline_affect"
    
    try:
        model = mixedlm(formula, data, groups=data["participant_id"])
        result = model.fit(reml=False)
        return result
    except Exception as e:
        logger.error(f"Model fitting failed: {e}")
        raise

def fit_mean_mood_model(df: pd.DataFrame, subset_mask: pd.Series = None) -> Any:
    """Fit LMM with mean_mood as outcome."""
    data = df[subset_mask] if subset_mask is not None else df
    
    if len(data) < 20:
        raise ValueError("Insufficient data to fit model.")

    formula = "mean_mood ~ total_steps + sleep_duration + C(day_of_week) + baseline_affect"
    
    try:
        model = mixedlm(formula, data, groups=data["participant_id"])
        result = model.fit(reml=False)
        return result
    except Exception as e:
        logger.error(f"Model fitting failed: {e}")
        raise

def extract_coefficient(result: Any) -> float:
    """Extract the fixed effect coefficient for total_steps."""
    return result.fe_params['total_steps']

def run_sensitivity_analysis_exclude_single_ratings(df: pd.DataFrame) -> pd.DataFrame:
    """Return a subset of df excluding days with exactly 1 mood rating."""
    # Assuming 'n_ratings' column exists from T014 logic
    if 'n_ratings' not in df.columns:
        # Fallback if column missing, assume all are valid or filter by mood_std existence
        # But spec says T014 handles < 2 ratings. Let's assume n_ratings is present.
        # If not, we might need to infer from data or assume 0 exclusions.
        # For robustness, if column missing, return full df (conservative).
        logger.warning("n_ratings column missing, cannot exclude single-rating days. Returning full dataset.")
        return df
    
    mask = df['n_ratings'] >= 2
    return df[mask]

def run_sensitivity_analysis_impute_single_ratings(df: pd.DataFrame) -> pd.DataFrame:
    """Impute single-rating days using participant median mood."""
    if 'n_ratings' not in df.columns:
        logger.warning("n_ratings column missing, cannot impute. Returning full dataset.")
        return df

    df_imputed = df.copy()
    
    # Identify single-rating days
    single_mask = df_imputed['n_ratings'] == 1
    if not single_mask.any():
        return df_imputed

    # Calculate participant medians for mean_mood
    participant_medians = df_imputed.groupby('participant_id')['mean_mood'].transform('median')
    
    # Impute
    df_imputed.loc[single_mask, 'mean_mood'] = participant_medians[single_mask]
    
    # For consistency in the analysis, we might also want to adjust log_mood_std
    # If n_ratings is 1, variability is technically 0 or undefined. 
    # T015b handled 0 variability. Let's set it to a small epsilon or participant median std.
    participant_stds = df_imputed.groupby('participant_id')['mood_std'].transform('median')
    df_imputed.loc[single_mask, 'mood_std'] = participant_stds[single_mask].fillna(0.1)
    
    return df_imputed

def run_bootstrap_sensitivity_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Execute bootstrap sampling loop (1000 iterations, seed 42).
    For each iteration:
      1. Sample rows with replacement.
      2. Fit exclusion model (T031a logic) on the sample.
      3. Fit imputation model (T031b logic) on the sample.
      4. Compare coefficients. Record if direction is consistent.
    Return consistency metrics.
    """
    logger.info(f"Starting Bootstrap Sensitivity Analysis ({BOOTSTRAP_ITERATIONS} iterations)...")
    
    random.seed(BOOTSTRAP_SEED)
    np.random.seed(BOOTSTRAP_SEED)
    
    consistent_directions = 0
    total_iterations = 0
    coefficients_exclusion = []
    coefficients_imputation = []
    failures = 0

    # Prepare base data
    # We need to handle the n_ratings column for the exclusion logic
    if 'n_ratings' not in df.columns:
        logger.error("n_ratings column missing. Cannot perform exclusion/imputation analysis.")
        raise ValueError("Missing n_ratings column. Ensure T014 completed successfully.")

    for i in range(BOOTSTRAP_ITERATIONS):
        try:
            # 1. Bootstrap sample (rows with replacement)
            # Sample size = original size
            sample_indices = np.random.choice(len(df), size=len(df), replace=True)
            df_sample = df.iloc[sample_indices].reset_index(drop=True)

            # 2. Fit Exclusion Model (T031a logic)
            # Exclude days with n_ratings < 2
            mask_exclusion = df_sample['n_ratings'] >= 2
            df_excl = df_sample[mask_exclusion]
            
            if len(df_excl) < 20:
                logger.warning(f"Iteration {i}: Exclusion sample too small ({len(df_excl)}). Skipping.")
                continue

            try:
                res_excl = fit_mood_std_model(df_excl) # Using mood_std model as primary for variability analysis
                coef_excl = extract_coefficient(res_excl)
            except Exception as e:
                logger.warning(f"Iteration {i}: Exclusion model failed: {e}")
                continue

            # 3. Fit Imputation Model (T031b logic)
            # Impute single-rating days
            df_imp = run_sensitivity_analysis_impute_single_ratings(df_sample)
            
            # Ensure we have data for the imputation model (might still be small if many single ratings)
            if len(df_imp) < 20:
                logger.warning(f"Iteration {i}: Imputation sample too small ({len(df_imp)}). Skipping.")
                continue

            try:
                res_imp = fit_mood_std_model(df_imp)
                coef_imp = extract_coefficient(res_imp)
            except Exception as e:
                logger.warning(f"Iteration {i}: Imputation model failed: {e}")
                continue

            # 4. Compare coefficients
            # Check if signs match
            sign_match = (np.sign(coef_excl) == np.sign(coef_imp)) and (coef_excl != 0)
            
            if sign_match:
                consistent_directions += 1
            
            coefficients_exclusion.append(coef_excl)
            coefficients_imputation.append(coef_imp)
            total_iterations += 1

        except Exception as e:
            logger.error(f"Iteration {i} failed unexpectedly: {e}")
            failures += 1
            continue

    if total_iterations == 0:
        raise RuntimeError("Bootstrap analysis failed: No successful iterations completed.")

    consistency_rate = consistent_directions / total_iterations
    logger.info(f"Bootstrap complete. Consistency rate: {consistency_rate:.2%} ({consistent_directions}/{total_iterations})")

    return {
        "total_iterations": total_iterations,
        "successful_iterations": total_iterations, # Assuming we only count those that made it to comparison
        "consistent_directions": consistent_directions,
        "consistency_rate": consistency_rate,
        "threshold_met": consistency_rate >= CONSISTENCY_THRESHOLD,
        "coefficient_stats": {
            "exclusion": {
                "mean": float(np.mean(coefficients_exclusion)),
                "std": float(np.std(coefficients_exclusion)),
                "median": float(np.median(coefficients_exclusion))
            },
            "imputation": {
                "mean": float(np.mean(coefficients_imputation)),
                "std": float(np.std(coefficients_imputation)),
                "median": float(np.median(coefficients_imputation))
            }
        },
        "failures": failures
    }

def run_analysis() -> Dict[str, Any]:
    """Main analysis pipeline including bootstrap sensitivity."""
    logger.info("Running full analysis pipeline...")
    
    df = load_daily_aggregates()
    
    results = {
        "primary_models": {},
        "lopo": {},
        "sensitivity": {},
        "bootstrap_sensitivity": {}
    }

    # Run primary models (T019, T020)
    # ... (Assuming these are called elsewhere or here, but task is T031c focus)
    # We focus on T031c implementation here, but ensure structure exists.
    
    # Run Bootstrap Sensitivity Analysis (T031c)
    try:
        bootstrap_results = run_bootstrap_sensitivity_analysis(df)
        results["bootstrap_sensitivity"] = bootstrap_results
        
        if not bootstrap_results["threshold_met"]:
            logger.warning(f"Bootstrap consistency ({bootstrap_results['consistency_rate']:.2%}) is below threshold ({CONSISTENCY_THRESHOLD:.2%}).")
        else:
            logger.info(f"Bootstrap consistency ({bootstrap_results['consistency_rate']:.2%}) meets threshold.")
            
    except Exception as e:
        logger.error(f"Bootstrap sensitivity analysis failed: {e}")
        results["bootstrap_sensitivity"] = {"error": str(e)}

    return results

def main():
    """Entry point for the analysis script."""
    results = run_analysis()
    
    # Save results
    output_path = get_path('data/processed/model_results.json')
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Analysis complete. Results saved to {output_path}")

if __name__ == "__main__":
    main()
