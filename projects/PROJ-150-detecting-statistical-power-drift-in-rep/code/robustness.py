import os
import sys
import json
import pickle
import logging
import time
import pandas as pd
import numpy as np
import statsmodels.api as sm
import scipy.stats as stats
from statsmodels.regression.mixed_linear_model import MixedLM
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Helper: Power calculation (reused from T011a logic)
def calculate_power(effect_size, n, alpha=0.05):
    if pd.isna(effect_size) or pd.isna(n) or n < 2:
        return np.nan
    d = effect_size
    ncp = d * np.sqrt(n / 2)
    df = n - 2
    critical_t = stats.t.ppf(1 - alpha/2, df)
    power = 1 - stats.t.cdf(critical_t, df, ncp)
    return power

def load_lmm_summary(summary_path):
    if not os.path.exists(summary_path):
        raise FileNotFoundError(f"LMM summary file not found at {summary_path}")
    with open(summary_path, 'r') as f:
        return json.load(f)

def load_permutation_pvalue(perm_path):
    if not os.path.exists(perm_path):
        return None
    with open(perm_path, 'r') as f:
        return json.load(f)

def compare_pvalues(observed_p, perm_p, alpha=0.05):
    """Compare observed p-value against permutation empirical p-value."""
    return {
        "observed_significant_at_alpha": observed_p < alpha,
        "perm_significant_at_alpha": perm_p < alpha if perm_p else None,
        "discrepancy": (observed_p < alpha) != (perm_p < alpha) if perm_p else None
    }

def generate_consistency_report(observed_slope, perm_result):
    """Generate a report comparing observed slope to permutation null."""
    if not perm_result:
        return {"status": "no_permutation_data"}
    
    null_dist = perm_result.get('null_distribution', [])
    if not null_dist:
        return {"status": "empty_null_distribution"}
    
    null_mean = np.mean(null_dist)
    null_std = np.std(null_dist)
    z_score = (observed_slope - null_mean) / null_std if null_std > 0 else 0
    
    return {
        "observed_slope": observed_slope,
        "null_mean": null_mean,
        "null_std": null_std,
        "z_score": z_score,
        "empirical_p_value": perm_result.get('p_value_input_perm')
    }

def run_permutation_test(residuals_path, summary_path, output_path, max_iterations=10000, fallback_iterations=1000):
    """
    Year Permutation Test: Shuffle year column, refit model, compare slopes.
    """
    if not os.path.exists(residuals_path):
        raise FileNotFoundError(f"Residuals file not found at {residuals_path}")
    
    df = pd.read_csv(residuals_path)
    summary = load_lmm_summary(summary_path)
    observed_slope = summary['slope_year']

    # Prepare exog_re for original_study_id (crossed random effect)
    unique_studies = df['original_study_id'].unique()
    study_to_idx = {s: i for i, s in enumerate(unique_studies)}
    exog_re = np.zeros((len(df), len(unique_studies)))
    for i, study in enumerate(df['original_study_id']):
        exog_re[i, study_to_idx[study]] = 1

    null_slopes = []
    iterations_run = 0
    fallback_used = False

    for i in range(max_iterations):
        try:
            # Shuffle year
            df_perm = df.copy()
            df_perm['year'] = np.random.permutation(df_perm['year'])

            # Prepare fixed effects
            exog = df_perm[['year']]
            exog = sm.add_constant(exog)

            # Fit model
            model = MixedLM(df_perm['model_residual'], exog, groups=df_perm['field'], exog_re=exog_re)
            result = model.fit(disp=False)
            null_slopes.append(result.params['year'])
            iterations_run += 1
        except Exception as e:
            logger.warning(f"Permutation iteration {i} failed: {e}. Falling back to reduced count.")
            fallback_used = True
            max_iterations = i + fallback_iterations
            break

    if len(null_slopes) > 0:
        empirical_p_value = (sum(np.abs(null_slopes) >= np.abs(observed_slope)) + 1) / (len(null_slopes) + 1)
    else:
        empirical_p_value = 1.0

    result = {
        "observed_slope": float(observed_slope),
        "empirical_p_value": float(empirical_p_value),
        "iterations": iterations_run,
        "fallback_used": fallback_used
    }

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    logger.info(f"Saved permutation results to {output_path}")
    return result

def run_sensitivity_analysis(input_path, summary_path, output_path, alphas=[0.01, 0.05, 0.1]):
    """
    Sensitivity Analysis: Re-run LMM pipeline with different alpha thresholds for significance.
    Note: Power calculation alpha is fixed at 0.05 per spec, but LRT significance threshold varies.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input data file not found at {input_path}")
    
    df = pd.read_csv(input_path)
    summary = load_lmm_summary(summary_path)
    observed_slope = summary['slope_year']

    results = []

    # We need to re-calculate power and residuals for each alpha? 
    # Spec says: "Note: This task sweeps the significance threshold for the LRT p-value, 
    # while the power calculation definition (alpha=0.05) remains constant as per the spec's primary definition."
    # So we use fixed alpha=0.05 for power calculation, but vary alpha for LRT significance check.
    
    # Calculate power once with alpha=0.05
    df['power_estimate'] = df.apply(
        lambda row: calculate_power(row['effect_size'], row['sample_size'], alpha=0.05),
        axis=1
    )
    df = df.dropna(subset=['power_estimate'])

    # Prepare exog_re for original_study_id
    unique_studies = df['original_study_id'].unique()
    study_to_idx = {s: i for i, s in enumerate(unique_studies)}
    exog_re = np.zeros((len(df), len(unique_studies)))
    for i, study in enumerate(df['original_study_id']):
        exog_re[i, study_to_idx[study]] = 1

    # Fit the model ONCE (since data and model structure don't change with alpha threshold)
    # The alpha threshold only affects the significance decision, not the model fit itself.
    exog = df[['year', 'effect_size', 'sample_size']]
    exog = sm.add_constant(exog)

    model = MixedLM(df['power_estimate'], exog, groups=df['field'], exog_re=exog_re)
    result = model.fit(disp=False)
    p_val_year = result.pvalues['year']

    # Try to load permutation result for false_positive_rate
    false_positive_rate = 0.0
    try:
        with open("results/input_permutation.json", 'r') as f:
            perm_result = json.load(f)
            false_positive_rate = perm_result.get('p_value_input_perm', 0.0)
    except FileNotFoundError:
        logger.warning("input_permutation.json not found. Using default false_positive_rate=0.0")
    except Exception as e:
        logger.warning(f"Could not load input_permutation.json: {e}. Using default false_positive_rate=0.0")

    for alpha in alphas:
        drift_significant = p_val_year < alpha

        results.append({
            "alpha_value": float(alpha),
            "drift_significant": bool(drift_significant),
            "false_positive_rate": float(false_positive_rate)
        })

    output_data = {"results": results}
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Saved sensitivity report to {output_path}")
    return output_data

def main():
    """
    Main entry point for robustness checks.
    Currently focuses on Sensitivity Analysis (T021b).
    """
    # Paths
    input_path = "data/derived/cleaned_data.csv"
    summary_path = "results/lmm_final_summary.json"
    output_path = "results/sensitivity_report.json"

    # Run Sensitivity Analysis
    logger.info("Starting Sensitivity Analysis (T021b)...")
    try:
        run_sensitivity_analysis(input_path, summary_path, output_path)
        logger.info("Sensitivity Analysis completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Missing required file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during Sensitivity Analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()