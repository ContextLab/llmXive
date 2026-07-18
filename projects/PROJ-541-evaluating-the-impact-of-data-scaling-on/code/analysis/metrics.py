import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional
from scipy import stats
from pathlib import Path
import statsmodels.api as sm
from statsmodels.regression.mixed_linear_model import MixedLM
import os

# Ensure the results directory exists
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

logger = logging.getLogger(__name__)

def calculate_aggregate_metrics(p_values: List[float], alpha: float = 0.05) -> Dict[str, float]:
    """
    Calculate empirical Type I error rate and power from a list of p-values.
    
    Args:
        p_values: List of p-values from hypothesis tests.
        alpha: Nominal significance level.
        
    Returns:
        Dictionary with 'error_rate' and 'power' (if applicable).
    """
    if not p_values:
        return {'error_rate': 0.0, 'power': 0.0, 'n': 0}
    
    n = len(p_values)
    rejections = sum(1 for p in p_values if p < alpha)
    error_rate = rejections / n
    
    # Power calculation requires knowledge of true alternative hypothesis,
    # which is context-dependent. For a general utility, we return the rejections rate.
    # In a specific simulation context, this would be calculated based on ground truth.
    return {
        'error_rate': error_rate,
        'power': error_rate, # Placeholder; real power needs ground truth
        'n': n,
        'rejections': rejections
    }

def save_aggregate_metrics(metrics: Dict[str, float], filepath: str) -> None:
    """Save aggregate metrics to a JSON file."""
    import json
    with open(filepath, 'w') as f:
        json.dump(metrics, f, indent=2)

def calculate_deviation_summary(results_df: pd.DataFrame, nominal_alpha: float = 0.05) -> pd.DataFrame:
    """
    Calculate deviation of empirical error rates from nominal alpha.
    
    Args:
        results_df: DataFrame containing test results with columns including 'p_value' and 'scaling_method'.
        nominal_alpha: The target significance level.
        
    Returns:
        DataFrame with mean deviation per scaling method.
    """
    if results_df.empty:
        return pd.DataFrame()
    
    # Calculate empirical error rate per scaling method
    results_df['rejected'] = (results_df['p_value'] < nominal_alpha).astype(int)
    summary = results_df.groupby('scaling_method')['rejected'].agg(['mean', 'count']).reset_index()
    summary.rename(columns={'mean': 'empirical_rate', 'count': 'n_tests'}, inplace=True)
    summary['deviation'] = summary['empirical_rate'] - nominal_alpha
    
    return summary

def fit_synthetic_mixed_effects_model(results_df: pd.DataFrame) -> Tuple[object, str]:
    """
    Fit a mixed-effects model for synthetic data analysis.
    
    Formula: deviation ~ scaling_method + distribution_type + (1|simulation_batch)
    
    Args:
        results_df: DataFrame with columns: scaling_method, distribution_type, simulation_batch, deviation.
        
    Returns:
        Tuple of (fitted model object, summary string).
    """
    if results_df.empty:
        raise ValueError("Input DataFrame is empty.")
    
    # Ensure categorical columns are treated as such
    results_df['scaling_method'] = results_df['scaling_method'].astype('category')
    results_df['distribution_type'] = results_df['distribution_type'].astype('category')
    results_df['simulation_batch'] = results_df['simulation_batch'].astype('category')
    
    formula = "deviation ~ C(scaling_method) + C(distribution_type) + (1|simulation_batch)"
    
    try:
        model = MixedLM.from_formula(formula, data=results_df, groups=results_df["simulation_batch"])
        result = model.fit()
        summary = result.summary().as_text()
        logger.info("Synthetic mixed-effects model fitted successfully.")
        return result, summary
    except Exception as e:
        logger.error(f"Failed to fit synthetic mixed-effects model: {e}")
        raise

def fit_real_world_mixed_effects_model(results_df: pd.DataFrame) -> Tuple[object, str]:
    """
    Fit a mixed-effects model for real-world data analysis.
    
    Formula: deviation ~ scaling_method + (1|dataset_id)
    
    Args:
        results_df: DataFrame with columns: scaling_method, dataset_id, deviation.
        
    Returns:
        Tuple of (fitted model object, summary string).
    """
    if results_df.empty:
        raise ValueError("Input DataFrame is empty.")
    
    # Ensure categorical columns are treated as such
    results_df['scaling_method'] = results_df['scaling_method'].astype('category')
    results_df['dataset_id'] = results_df['dataset_id'].astype('category')
    
    formula = "deviation ~ C(scaling_method) + (1|dataset_id)"
    
    try:
        # Use groups for the random effect
        model = MixedLM.from_formula(formula, data=results_df, groups=results_df["dataset_id"])
        result = model.fit()
        summary = result.summary().as_text()
        logger.info("Real-world mixed-effects model fitted successfully.")
        
        # Save the model summary to CSV as required by T031b
        # We extract key coefficients and p-values for the CSV
        summary_df = pd.DataFrame({
            'term': result.params.index,
            'estimate': result.params.values,
            'std_err': result.bse.values,
            'z_value': result.tvalues.values,
            'p_value': result.pvalues.values
        })
        
        output_path = RESULTS_DIR / "mixed_effects_summary.csv"
        summary_df.to_csv(output_path, index=False)
        logger.info(f"Model summary saved to {output_path}")
        
        return result, summary
    except Exception as e:
        logger.error(f"Failed to fit real-world mixed-effects model: {e}")
        raise

def generate_summary_report(deviation_summary: pd.DataFrame) -> None:
    """Generate a text summary report of deviations."""
    report_path = RESULTS_DIR / "summary_report.txt"
    with open(report_path, 'w') as f:
        f.write("Summary Report: Deviations from Nominal Alpha (0.05)\n")
        f.write("=" * 50 + "\n")
        f.write(deviation_summary.to_string(index=False))
        f.write("\n")
    logger.info(f"Summary report saved to {report_path}")

def run_full_analysis_pipeline(results_df: pd.DataFrame) -> None:
    """Orchestrate the full analysis pipeline."""
    logger.info("Starting full analysis pipeline.")
    
    # Calculate deviations
    dev_summary = calculate_deviation_summary(results_df)
    
    # Fit models if data supports it
    if 'simulation_batch' in results_df.columns:
        try:
            fit_synthetic_mixed_effects_model(results_df)
        except Exception as e:
            logger.warning(f"Could not fit synthetic model: {e}")
    
    if 'dataset_id' in results_df.columns:
        try:
            fit_real_world_mixed_effects_model(results_df)
        except Exception as e:
            logger.warning(f"Could not fit real-world model: {e}")
    
    generate_summary_report(dev_summary)
    logger.info("Full analysis pipeline completed.")

def generate_comparison_report(results_df: pd.DataFrame) -> None:
    """Generate a comparison report for scaling methods."""
    report_path = RESULTS_DIR / "comparison_report.csv"
    # Simple aggregation for comparison
    comparison = results_df.groupby('scaling_method').agg({
        'p_value': ['mean', 'std', 'count'],
        'deviation': ['mean', 'std']
    }).reset_index()
    comparison.to_csv(report_path, index=False)
    logger.info(f"Comparison report saved to {report_path}")
