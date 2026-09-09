"""
Analysis metrics: aggregation, confidence intervals, mixed-effects, sensitivity.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Constants
AGGREGATE_METRICS_PATH = "results/aggregate_metrics.csv"
SENSITIVITY_ANALYSIS_PATH = "results/sensitivity_analysis.csv"
SIMULATION_RESULTS_PATH = "results/simulation_results.csv"
ALPHA = 0.05


def load_simulation_results(path: str = SIMULATION_RESULTS_PATH) -> pd.DataFrame:
    """Loads simulation results from CSV."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Simulation results not found at {path}")
    return pd.read_csv(path)


def load_real_world_results(path: str = "results/real_world_results.csv") -> pd.DataFrame:
    """Loads real-world results from CSV."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Real-world results not found at {path}")
    return pd.read_csv(path)


def calculate_confidence_interval(count: int, nobs: int, alpha: float = 0.05) -> Tuple[float, float]:
    """
    Calculates Clopper-Pearson exact confidence interval for a binomial proportion.
    Uses statsmodels if available, else approximates or raises.
    """
    try:
        from statsmodels.stats.proportion import proportion_confint
        # method='beta' corresponds to Clopper-Pearson
        lower, upper = proportion_confint(count=count, nobs=nobs, alpha=alpha, method='beta')
        return float(lower), float(upper)
    except ImportError:
        # Fallback to scipy if statsmodels not available (approximation)
        try:
            from scipy.stats import beta
            lower = beta.ppf(alpha/2, count, nobs - count + 1) if count > 0 else 0.0
            upper = beta.ppf(1 - alpha/2, count + 1, nobs - count) if count < nobs else 1.0
            return float(lower), float(upper)
        except ImportError:
            raise ImportError("statsmodels or scipy required for confidence intervals")


def calculate_aggregate_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes Type I error and Power with Clopper-Pearson CIs.
    Writes results to results/aggregate_metrics.csv.
    """
    if df.empty:
        logger.warning("Empty dataframe provided to calculate_aggregate_metrics")
        return pd.DataFrame()

    # Group by config, scaling, test
    # We assume ground_truth indicates 'null' or 'alternative'
    groups = df.groupby(["config_id", "scaling_method", "test_type", "ground_truth"])

    results = []

    for (config_id, scaling_method, test_type, ground_truth), group in groups:
        total = len(group)
        if total == 0:
            continue

        # Count rejections (p < 0.05)
        rejections = (group["p_value"] < ALPHA).sum()

        # Calculate error rate / power
        rate = rejections / total

        # Calculate CI
        lower, upper = calculate_confidence_interval(int(rejections), total, alpha=0.05)

        results.append({
            "config_id": config_id,
            "scaling_method": scaling_method,
            "test_type": test_type,
            "ground_truth": ground_truth,
            "error_rate": rate,
            "ci_lower": lower,
            "ci_upper": upper,
            "total_iterations": total,
            "rejections": rejections
        })

    result_df = pd.DataFrame(results)
    
    # Ensure directory exists
    Path(AGGREGATE_METRICS_PATH).parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(AGGREGATE_METRICS_PATH, index=False)
    logger.info(f"Aggregate metrics written to {AGGREGATE_METRICS_PATH}")
    
    return result_df


def run_sensitivity_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Re-calculates error rates for a range of alpha levels.
    Writes to results/sensitivity_analysis.csv.
    """
    alpha_levels = [0.01, 0.05, 0.10]
    results = []

    for alpha in alpha_levels:
        # Filter by ground_truth if needed, or aggregate all
        # Here we assume we want to see the effect of alpha on the whole set or per config
        # For simplicity, we group by config, scaling, test, ground_truth
        
        groups = df.groupby(["config_id", "scaling_method", "test_type", "ground_truth"])
        
        for (config_id, scaling_method, test_type, ground_truth), group in groups:
            total = len(group)
            if total == 0:
                continue
            
            rejections = (group["p_value"] < alpha).sum()
            rate = rejections / total
            
            results.append({
                "alpha": alpha,
                "config_id": config_id,
                "scaling_method": scaling_method,
                "test_type": test_type,
                "ground_truth": ground_truth,
                "error_rate": rate,
                "total_iterations": total,
                "rejections": rejections
            })

    result_df = pd.DataFrame(results)
    
    Path(SENSITIVITY_ANALYSIS_PATH).parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(SENSITIVITY_ANALYSIS_PATH, index=False)
    logger.info(f"Sensitivity analysis written to {SENSITIVITY_ANALYSIS_PATH}")
    
    return result_df


def fit_mixed_effects_model(df: pd.DataFrame) -> Any:
    """
    Fits a mixed-effects model to the aggregate metrics.
    For synthetic data: deviation ~ scaling_method + (1 | config_id) [config_id as fixed effect in statsmodels terms if using OLS, but here we use MixedLM]
    Note: The requirement says config_id is FIXED effect. In statsmodels MixedLM, random effects are specified.
    If config_id is fixed, we might use OLS or include it as a factor.
    However, the spec says "deviation ~ scaling_method + (1 | config_id)" where config_id is FIXED.
    This is slightly contradictory in standard mixed model terminology (usually (1|id) is random).
    We will interpret as: Use MixedLM with config_id as a random effect for real data,
    and for synthetic data, we treat config_id as a grouping factor but maybe we just want to see scaling_method effect.
    Given the ambiguity, we will use statsmodels MixedLM with config_id as random effect for both,
    but note that for synthetic data, the "fixed" nature implies we might want to control for it.
    Actually, the spec says: "For Synthetic Data: ... config_id as a FIXED effect".
    In statsmodels, if it's fixed, it goes in exog. If random, in groups.
    We will try to fit: y ~ scaling_method, groups=config_id.
    """
    try:
        import statsmodels.api as sm
        import statsmodels.formula.api as smf
    except ImportError:
        logger.error("statsmodels not installed. Cannot fit mixed effects model.")
        return None

    # Prepare data: calculate deviation = |p_value - alpha|?
    # The spec says: deviation = |p_value - alpha|.
    # But we are using aggregate metrics (error_rate).
    # Let's assume we are fitting on the aggregate error_rate.
    # deviation = |error_rate - 0.05|
    
    df["deviation"] = (df["error_rate"] - 0.05).abs()

    # Model: deviation ~ scaling_method + (1 | config_id)
    # Note: If config_id is fixed, we might do: deviation ~ scaling_method + C(config_id)
    # But the spec says "config_id as a FIXED effect" but uses notation (1|config_id) which is random.
    # We will follow the notation (1|config_id) as random effect for grouping.
    model = smf.mixedlm("deviation ~ scaling_method", df, groups=df["config_id"])
    result = model.fit()
    
    logger.info(f"Mixed-effects model fit: {result.summary()}")
    return result


def run_full_analysis_pipeline(df: pd.DataFrame = None) -> Dict[str, Any]:
    """
    Runs the full analysis pipeline: aggregate metrics, sensitivity, mixed effects.
    """
    if df is None:
        try:
            df = load_simulation_results()
        except FileNotFoundError:
            logger.error("No simulation results found. Cannot run pipeline.")
            return {}

    results = {}
    
    # 1. Aggregate Metrics
    try:
        agg = calculate_aggregate_metrics(df)
        results["aggregate"] = agg.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Aggregate metrics failed: {e}")
    
    # 2. Sensitivity Analysis
    try:
        sens = run_sensitivity_analysis(df)
        results["sensitivity"] = sens.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
    
    # 3. Mixed Effects (if data allows)
    try:
        if not agg.empty:
            me = fit_mixed_effects_model(agg)
            results["mixed_effects"] = str(me.summary()) if me else None
    except Exception as e:
        logger.error(f"Mixed effects failed: {e}")
        
    return results


def generate_comparison_report(synthetic_df: pd.DataFrame, real_df: pd.DataFrame) -> str:
    """Generates a markdown comparison report."""
    # Placeholder implementation
    report = "# Comparison Report\n\n"
    report += "## Synthetic vs Real World\n\n"
    # ... fill in metrics ...
    return report