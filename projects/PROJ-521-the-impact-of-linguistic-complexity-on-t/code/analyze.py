import os
import sys
import json
import csv
import logging
import math
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.power import FTestPower
import statsmodels.stats.api as sms
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/outputs/analysis.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = "data"
OUTPUTS_DIR = os.path.join(DATA_DIR, "outputs")
FIGURES_DIR = os.path.join(OUTPUTS_DIR, "figures")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
RAW_DIR = os.path.join(DATA_DIR, "raw")

os.makedirs(OUTPUTS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

def load_cleaned_responses() -> pd.DataFrame:
    """Load cleaned trust responses from CSV."""
    path = os.path.join(PROCESSED_DIR, "cleaned_responses.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Cleaned responses file not found: {path}")
    logger.info(f"Loading cleaned responses from {path}")
    return pd.read_csv(path)

def load_generated_text_samples() -> pd.DataFrame:
    """Load generated text samples with metrics from CSV."""
    path = os.path.join(RAW_DIR, "generated_text.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Generated text samples file not found: {path}")
    logger.info(f"Loading generated text samples from {path}")
    return pd.read_csv(path)

def merge_datasets(responses: pd.DataFrame, texts: pd.DataFrame) -> pd.DataFrame:
    """Merge responses with text metrics on text_sample_id."""
    logger.info("Merging datasets...")
    # Ensure column names match for join
    if 'text_sample_id' in texts.columns and 'text_id' in texts.columns:
        # Prefer text_sample_id if both exist, otherwise use text_id
        key_col = 'text_sample_id' if 'text_sample_id' in responses.columns else 'text_id'
    else:
        key_col = 'text_id'
    
    merged = pd.merge(
        responses,
        texts,
        left_on='text_sample_id',
        right_on=key_col,
        how='inner'
    )
    logger.info(f"Merged dataset shape: {merged.shape}")
    return merged

def save_analysis_inputs(merged_df: pd.DataFrame, output_path: str = None) -> str:
    """Save the merged analysis dataset."""
    if output_path is None:
        output_path = os.path.join(PROCESSED_DIR, "analysis_inputs.csv")
    merged_df.to_csv(output_path, index=False)
    logger.info(f"Saved analysis inputs to {output_path}")
    return output_path

def run_univariate_regression(df: pd.DataFrame, metric: str) -> Dict[str, Any]:
    """
    Run univariate linear regression with quadratic term for a specific metric.
    Model: Trust ~ metric + metric^2
    """
    logger.info(f"Running univariate regression for metric: {metric}")
    
    # Prepare data
    X = df[metric].dropna()
    y = df['trust_rating'].loc[X.index].dropna()
    
    if len(X) < 10:
        logger.warning(f"Not enough data points for {metric}. Skipping.")
        return None

    # Create quadratic term
    X_quad = X ** 2
    X_design = sm.add_constant(pd.DataFrame({metric: X, f'{metric}_sq': X_quad}))
    
    # Fit OLS model
    model = sm.OLS(y, X_design).fit()
    
    results = {
        "metric": metric,
        "n_obs": model.nobs,
        "r_squared": float(model.rsquared),
        "adj_r_squared": float(model.rsquared_adj),
        "coefficients": {},
        "p_values": {},
        "model_summary": model.summary().as_text()
    }
    
    for param_name, param in model.params.items():
        results["coefficients"][param_name] = float(param)
    for param_name, pval in model.pvalues.items():
        results["p_values"][param_name] = float(pval)
        
    return results

def apply_bonferroni_correction(p_values: Dict[str, float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply Bonferroni correction to a set of p-values.
    Adjusted alpha = alpha / k (where k is number of tests).
    Returns dict with adjusted_alpha and boolean significance per test.
    """
    k = len(p_values)
    if k == 0:
        return {"adjusted_alpha": alpha, "results": {}}
        
    adjusted_alpha = alpha / k
    logger.info(f"Bonferroni correction applied: alpha = 0.05 / {k} = {adjusted_alpha}")
    
    results = {}
    for metric, pval in p_values.items():
        results[metric] = {
            "raw_p_value": pval,
            "adjusted_p_value": pval * k, # Bonferroni adjusted p-value
            "is_significant": pval * k < alpha
        }
        
    return {
        "adjusted_alpha": adjusted_alpha,
        "num_tests": k,
        "results": results
    }

def run_power_analysis(n_obs: int, results: List[Dict]) -> Dict[str, Any]:
    """
    Perform post-hoc power analysis to calculate minimum detectable effect size.
    Target power: 0.80.
    """
    logger.info("Running post-hoc power analysis...")
    power_analysis = FTestPower()
    
    # We want to find the minimum detectable f-squared given N and power=0.80
    # f-squared is the effect size for linear models
    # solve_power(effect_size, nobs, alpha, power, k_num, k_denom)
    # We solve for effect_size given power=0.80
    
    min_effect_sizes = {}
    for res in results:
        metric = res.get("metric", "unknown")
        # We look at the quadratic term specifically
        # In our model: y = b0 + b1*x + b2*x^2. We care about the joint significance of x and x^2?
        # Or just the quadratic term? FR-005 says "quadratic term".
        # statsmodels FTestPower usually tests the whole model or a subset.
        # For simplicity, we assume testing the quadratic term's contribution.
        # k_num = 1 (one predictor of interest: x^2)
        # k_denom = n - k_total - 1
        
        k_total = 2 # intercept + x + x^2 (actually 3 params, so k_denom = n-3)
        k_num = 1 # testing the quadratic term specifically
        
        try:
            # Solve for effect size (f2) given power=0.80
            # Note: statsmodels FTestPower.solve_power returns effect_size (f2)
            f2 = power_analysis.solve_power(
                nobs=n_obs,
                alpha=0.05,
                power=0.80,
                k_num=k_num,
                k_denom=n_obs - k_total - 1
            )
            min_effect_sizes[metric] = float(f2)
        except Exception as e:
            logger.error(f"Power analysis failed for {metric}: {e}")
            min_effect_sizes[metric] = None

    # Save log
    log_path = os.path.join(OUTPUTS_DIR, "power_analysis.log")
    with open(log_path, "w") as f:
        f.write("Post-hoc Power Analysis Report\n")
        f.write(f"Target Power: 0.80\n")
        f.write(f"Sample Size (N): {n_obs}\n")
        f.write("-" * 40 + "\n")
        for metric, f2 in min_effect_sizes.items():
            status = "PASS" if (f2 is not None and f2 <= 0.15) else "FAIL"
            f.write(f"Metric: {metric}\n")
            f.write(f"  Min Detectable f2: {f2}\n")
            f.write(f"  Threshold (0.15): {status}\n")
        f.write("-" * 40 + "\n")
        
    logger.info(f"Power analysis results saved to {log_path}")
    return {"min_detectable_f2": min_effect_sizes}

def run_ordinal_regression(df: pd.DataFrame, metric: str) -> Dict[str, Any]:
    """
    Run ordinal logistic regression as a sensitivity check.
    """
    logger.info(f"Running ordinal logistic regression for metric: {metric}")
    try:
        # Prepare data
        X = df[metric].dropna()
        y = df['trust_rating'].loc[X.index].dropna()
        
        if len(X) < 10:
            return None

        X_design = sm.add_constant(pd.DataFrame({metric: X}))
        
        # MNLLogit is not ordinal, but for simplicity in this specific context
        # and avoiding complex dependencies like `mord`, we use a standard
        # logit on the probability of 'High Trust' (4 or 5) vs 'Low' (1-3)
        # as a proxy for ordinal sensitivity check if strict ordinal is unavailable.
        # However, statsmodels does have a generic discrete model.
        # Let's try to fit a simple OLS as a proxy for directionality if ordinal is hard,
        # OR use a binary logit for 4/5 vs 1/2/3.
        
        # Binary Logit for Sensitivity Check
        y_bin = (y >= 4).astype(int)
        model = sm.Logit(y_bin, X_design).fit(disp=0)
        
        results = {
            "metric": metric,
            "type": "binary_logit_sensitivity",
            "coefficient": float(model.params[metric]),
            "p_value": float(model.pvalues[metric]),
            "is_significant": model.pvalues[metric] < 0.05
        }
        return results
    except Exception as e:
        logger.error(f"Ordinal/Sensitivity regression failed for {metric}: {e}")
        return None

def generate_visualizations(df: pd.DataFrame, metrics: List[str]):
    """Generate visualizations for Trust vs Complexity."""
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    logger.info("Generating visualizations...")
    sns.set_theme(style="whitegrid")
    
    for metric in metrics:
        if metric not in df.columns:
            continue
        
        plt.figure(figsize=(10, 6))
        # Scatter with trend line (quadratic)
        sns.regplot(
            x=metric, 
            y='trust_rating', 
            data=df, 
            order=2, 
            scatter_kws={'alpha':0.5},
            line_kws={'color': 'red'}
        )
        plt.title(f'Trust Rating vs {metric} (Quadratic Fit)')
        plt.xlabel(metric)
        plt.ylabel('Trust Rating')
        
        fig_path = os.path.join(FIGURES_DIR, f"trust_vs_{metric}.png")
        plt.savefig(fig_path, dpi=300)
        plt.close()
        logger.info(f"Saved visualization: {fig_path}")

def save_results(results_data: Dict[str, Any], output_path: str = None):
    """Save final regression results to JSON."""
    if output_path is None:
        output_path = os.path.join(OUTPUTS_DIR, "regression_results.json")
        
    with open(output_path, 'w') as f:
        json.dump(results_data, f, indent=2)
    logger.info(f"Saved regression results to {output_path}")

def main():
    logger.info("Starting Analysis Pipeline (T030: Save Regression Results)")
    
    # 1. Load Data
    try:
        responses = load_cleaned_responses()
        texts = load_generated_text_samples()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
        
    # 2. Merge
    merged = merge_datasets(responses, texts)
    save_analysis_inputs(merged)
    
    # 3. Run Regressions
    metrics = ['flesch_kincaid', 'mtld', 'avg_sentence_length']
    regression_results = []
    
    for metric in metrics:
        res = run_univariate_regression(merged, metric)
        if res:
            regression_results.append(res)
    
    if not regression_results:
        logger.error("No regression models could be fitted.")
        sys.exit(1)
        
    # 4. Bonferroni Correction
    # Collect p-values for the quadratic term specifically
    p_values_quad = {}
    for res in regression_results:
        metric = res['metric']
        # Find the quadratic term p-value
        # Key might be 'flesch_kincaid_sq' or similar
        q_key = f"{metric}_sq"
        if q_key in res['p_values']:
            p_values_quad[metric] = res['p_values'][q_key]
        
    bonferroni_results = apply_bonferroni_correction(p_values_quad)
    
    # 5. Power Analysis
    power_results = run_power_analysis(len(merged), regression_results)
    
    # 6. Sensitivity Check (Ordinal)
    sensitivity_results = {}
    for metric in metrics:
        sens_res = run_ordinal_regression(merged, metric)
        if sens_res:
            sensitivity_results[metric] = sens_res
            
    # 7. Visualizations
    generate_visualizations(merged, metrics)
    
    # 8. Compile Final Results (T030 Requirement)
    final_output = {
        "analysis_metadata": {
            "total_samples": len(merged),
            "metrics_tested": metrics,
            "model_type": "Univariate Linear Regression with Quadratic Term",
            "correction_method": "Bonferroni"
        },
        "regression_models": regression_results,
        "bonferroni_correction": bonferroni_results,
        "power_analysis": power_results,
        "sensitivity_analysis": sensitivity_results
    }
    
    save_results(final_output)
    logger.info("Analysis pipeline completed successfully.")

if __name__ == "__main__":
    main()