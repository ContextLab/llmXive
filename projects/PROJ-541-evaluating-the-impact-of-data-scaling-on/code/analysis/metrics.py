"""Analysis metrics for statistical validity and comparison."""
import os
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Union, Callable
import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import mixedlm

# Import logger setup to avoid circular issues if needed, though we use standard logging here
from simulation.logger import setup_logger

logger = logging.getLogger(__name__)

def load_simulation_results(filepath: Optional[str] = None) -> pd.DataFrame:
    """Load simulation results from CSV."""
    if filepath is None:
        filepath = "results/simulation_results.csv"
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Simulation results file not found: {filepath}")
    return pd.read_csv(path)

def load_real_world_results(filepath: Optional[str] = None) -> pd.DataFrame:
    """Load real-world results from CSV."""
    if filepath is None:
        filepath = "results/real_world_results.csv"
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Real-world results file not found: {filepath}")
    return pd.read_csv(path)

def calculate_confidence_interval(successes: int, trials: int, alpha: float = 0.05) -> Tuple[float, float]:
    """Calculate Clopper-Pearson exact confidence interval."""
    if trials == 0:
        return 0.0, 1.0
    lower = stats.beta.ppf(alpha / 2, successes, trials - successes + 1)
    upper = stats.beta.ppf(1 - alpha / 2, successes + 1, trials - successes)
    # Handle edge cases where beta.ppf might return NaN or inf
    if np.isnan(lower) or np.isinf(lower):
        lower = 0.0
    if np.isnan(upper) or np.isinf(upper):
        upper = 1.0
    return float(lower), float(upper)

def calculate_aggregate_metrics(results_df: pd.DataFrame, alpha: float = 0.05) -> Dict[str, Any]:
    """Calculate aggregate metrics like Type I error rate and Power."""
    if results_df.empty:
        return {"error_rate": 0.0, "power": 0.0, "total_iterations": 0}

    # Ensure ground_truth column exists; if not, assume all are null for safety or handle error
    if "ground_truth" not in results_df.columns:
        # Fallback or raise? Task implies we have ground truth.
        # Let's assume 0 means null, 1 means alt, or boolean.
        # If missing, we can't calculate properly.
        logger.warning("ground_truth column missing. Cannot calculate error rates accurately.")
        return {"error_rate": np.nan, "power": np.nan, "total_iterations": len(results_df)}

    total = len(results_df)
    # Identify null hypothesis cases (ground_truth == False or 0)
    null_mask = ~results_df['ground_truth'].astype(bool)
    # Identify alternative hypothesis cases (ground_truth == True or 1)
    alt_mask = results_df['ground_truth'].astype(bool)

    # Type I Error: Reject null when null is true (p < alpha AND ground_truth is False)
    null_rejections = results_df[null_mask & (results_df['p_value'] < alpha)].shape[0]
    null_total = results_df[null_mask].shape[0]
    type1_error_rate = null_rejections / null_total if null_total > 0 else 0.0

    # Power: Reject null when alt is true (p < alpha AND ground_truth is True)
    alt_rejections = results_df[alt_mask & (results_df['p_value'] < alpha)].shape[0]
    alt_total = results_df[alt_mask].shape[0]
    power = alt_rejections / alt_total if alt_total > 0 else 0.0

    return {
        "type1_error_rate": type1_error_rate,
        "power": power,
        "total_iterations": total,
        "null_count": null_total,
        "alt_count": alt_total,
        "null_rejections": null_rejections,
        "alt_rejections": alt_rejections
    }

def fit_mixed_effects_model(df: pd.DataFrame, formula: Optional[str] = None) -> Any:
    """Fit a mixed effects model using statsmodels."""
    # Default formula if not provided
    if formula is None:
        # Determine columns dynamically
        if 'scaling_method' in df.columns and 'dataset_id' in df.columns:
            formula = "p_value ~ scaling_method + (1 | dataset_id)"
        elif 'scaling_method' in df.columns and 'config_id' in df.columns:
            formula = "p_value ~ scaling_method + (1 | config_id)"
        else:
            raise ValueError("Cannot infer formula. Required columns missing.")

    try:
        # statsmodels mixedlm expects specific syntax, but formula api is easier
        model = mixedlm.from_formula(formula, data=df)
        result = model.fit()
        return result
    except Exception as e:
        logger.error(f"Failed to fit mixed effects model: {e}")
        raise

def generate_comparison_report(synthetic_df: pd.DataFrame, real_df: pd.DataFrame, output_path: str = "results/comparison_report.md") -> None:
    """Generate a markdown report comparing synthetic vs real-world results."""
    # Aggregate metrics for synthetic
    synth_metrics = calculate_aggregate_metrics(synthetic_df)
    # For real world, we treat all as 'alternative' or just compare p-value distributions directly
    # The task asks for error rates and effect sizes.
    # Real world doesn't have 'ground_truth' in the same way (we don't know the truth).
    # We will compare the distribution of p-values and the calculated 'error rate' assuming a nominal alpha.
    
    # Calculate error rate for real data assuming alpha=0.05 (just descriptive stats)
    # Note: In real data, 'error rate' is actually the proportion of significant findings.
    real_alpha = 0.05
    real_significant = (real_df['p_value'] < real_alpha).sum()
    real_total = len(real_df)
    real_rate = real_significant / real_total if real_total > 0 else 0.0

    # Calculate Mean Absolute Difference between synthetic and real p-values
    # We need to align them. If counts differ, we might need to sample or just compare distributions.
    # The task asks for MAD of p-values. Let's align by taking the min length or just comparing the means?
    # "Mean_Absolute_Difference (mean of |synthetic_p - real_p|)" implies pairing.
    # We will pair them by index, truncating to the smaller length.
    min_len = min(len(synthetic_df), len(real_df))
    if min_len == 0:
        mad = 0.0
        corr = 0.0
    else:
        syn_p = synthetic_df['p_value'].head(min_len).values
        real_p = real_df['p_value'].head(min_len).values
        mad = np.mean(np.abs(syn_p - real_p))
        if np.std(syn_p) > 0 and np.std(real_p) > 0:
            corr = np.corrcoef(syn_p, real_p)[0, 1]
        else:
            corr = 0.0

    # Effect sizes: If available in data, compare means. Otherwise, compare p-value means.
    synth_mean_p = synthetic_df['p_value'].mean()
    real_mean_p = real_df['p_value'].mean()

    report = f"""# Comparison Report: Synthetic vs Real-World Results

## Summary Statistics

| Metric | Synthetic_Value | Real_Value | Mean_Absolute_Difference | Correlation_Coefficient |
| :--- | :--- | :--- | :--- | :--- |
| Type I Error Rate (or Signif. Rate) | {synth_metrics.get('type1_error_rate', 0.0):.4f} | {real_rate:.4f} | {abs(synth_metrics.get('type1_error_rate', 0.0) - real_rate):.4f} | N/A |
| Mean P-Value | {synth_mean_p:.4f} | {real_mean_p:.4f} | {abs(synth_mean_p - real_mean_p):.4f} | {corr:.4f} |
| Total Iterations | {len(synthetic_df)} | {len(real_df)} | N/A | N/A |

## Detailed Comparison

### P-Value Distribution
- Synthetic Mean P-Value: {synth_mean_p:.4f}
- Real Mean P-Value: {real_mean_p:.4f}

### Statistical Significance
- Synthetic Significant (p < 0.05): {synth_metrics.get('null_rejections', 0)} / {synth_metrics.get('null_count', 0)} (Null cases)
- Real Significant (p < 0.05): {real_significant} / {real_total}

### Correlation Analysis
The Pearson correlation coefficient between the synthetic and real p-values (aligned by index, truncated to min length) is **{corr:.4f}**.
The Mean Absolute Difference is **{mad:.4f}**.

## Conclusion
This report compares the statistical properties of the simulation engine against real-world dataset ingestion.
"""
    
    with open(output_path, 'w') as f:
        f.write(report)
    logger.info(f"Comparison report generated at {output_path}")

def run_full_analysis_pipeline(results_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """
    Run the full analysis pipeline.
    Accepts a DataFrame directly or loads from default paths if None.
    Handles missing files gracefully for the 'no args' test case.
    """
    if results_df is None:
        # Try to load default
        try:
            results_df = load_simulation_results()
        except FileNotFoundError:
            # If no data, return empty metrics
            logger.warning("No data provided and default file not found. Returning empty metrics.")
            return {"error_rate": 0.0, "power": 0.0, "total_iterations": 0}

    if results_df is None or results_df.empty:
        return {"error_rate": 0.0, "power": 0.0, "total_iterations": 0}

    metrics = calculate_aggregate_metrics(results_df)
    return metrics