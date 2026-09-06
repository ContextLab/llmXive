"""
Aggregate Robustness Metrics Module (T026)

This module consolidates results from:
1. Bootstrap analysis (T021)
2. Alpha sweep (T022)
3. Covariate adjustment (T023)
4. Binary model (T024b)

It produces a single `results/robustness_metrics.csv` file containing
the comparative metrics required for the US2 robustness checkpoint.
"""

import os
import pandas as pd
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Import from project API surface
from config_manager import get_results_path, get_config
from logging_config import get_logger
from robustness import save_robustness_results
from binary_model import save_binary_model_results

logger = get_logger(__name__)


def load_csv_safely(file_path: Path, description: str) -> Optional[pd.DataFrame]:
    """
    Safely load a CSV file if it exists. Returns None if not found.
    """
    if not file_path.exists():
        logger.warning(f"{description} file not found at {file_path}. "
                       "This may indicate a prerequisite task has not run yet.")
        return None
    try:
        return pd.read_csv(file_path)
    except Exception as e:
        logger.error(f"Failed to load {description} from {file_path}: {e}")
        return None


def extract_bootstrap_metrics(df: Optional[pd.DataFrame]) -> Dict[str, Any]:
    """
    Extract key metrics from the bootstrap results dataframe.
    Expected columns: interaction_coef, interaction_ci_lower, interaction_ci_upper, interaction_p_val
    """
    if df is None or df.empty:
        return {
            "bootstrap_interaction_coef": None,
            "bootstrap_ci_lower": None,
            "bootstrap_ci_upper": None,
            "bootstrap_se": None,
            "bootstrap_significant": None
        }

    # Assuming the dataframe contains one row of summary stats or we take the mean/last
    # Based on typical robustness output structure
    row = df.iloc[-1] if hasattr(df, 'iloc') else df

    coef = row.get('interaction_coef') if 'interaction_coef' in row else row.get('coef', None)
    ci_lower = row.get('interaction_ci_lower') if 'interaction_ci_lower' in row else row.get('ci_lower', None)
    ci_upper = row.get('interaction_ci_upper') if 'interaction_ci_upper' in row else row.get('ci_upper', None)
    p_val = row.get('interaction_p_val') if 'interaction_p_val' in row else row.get('p_val', None)
    se = row.get('interaction_se') if 'interaction_se' in row else row.get('se', None)

    return {
        "bootstrap_interaction_coef": coef,
        "bootstrap_ci_lower": ci_lower,
        "bootstrap_ci_upper": ci_upper,
        "bootstrap_se": se,
        "bootstrap_significant": (p_val is not None and p_val < 0.05)
    }


def extract_alpha_sweep_metrics(df: Optional[pd.DataFrame]) -> Dict[str, Any]:
    """
    Extract metrics from alpha sweep.
    Expected columns: alpha_level, significant, interaction_p_val
    """
    if df is None or df.empty:
        return {
            "alpha_sweep_001_significant": None,
            "alpha_sweep_005_significant": None,
            "alpha_sweep_010_significant": None
        }

    # Pivot or filter to get significance at each alpha
    results = {
        "alpha_sweep_001_significant": None,
        "alpha_sweep_005_significant": None,
        "alpha_sweep_010_significant": None
    }

    for _, row in df.iterrows():
        alpha = row.get('alpha_level')
        sig = row.get('significant')
        if alpha == 0.01:
            results["alpha_sweep_001_significant"] = sig
        elif alpha == 0.05:
            results["alpha_sweep_005_significant"] = sig
        elif alpha == 0.10:
            results["alpha_sweep_010_significant"] = sig

    return results


def extract_covariate_metrics(df: Optional[pd.DataFrame]) -> Dict[str, Any]:
    """
    Extract metrics from covariate adjustment model.
    Expected columns: interaction_coef, interaction_p_val
    """
    if df is None or df.empty:
        return {
            "covariate_interaction_coef": None,
            "covariate_interaction_p_val": None,
            "covariate_stability_ratio": None
        }

    row = df.iloc[-1]
    coef = row.get('interaction_coef')
    p_val = row.get('interaction_p_val')

    return {
        "covariate_interaction_coef": coef,
        "covariate_interaction_p_val": p_val,
        "covariate_stability_ratio": None # Calculated later if primary model is available
    }


def extract_binary_model_metrics(df: Optional[pd.DataFrame]) -> Dict[str, Any]:
    """
    Extract metrics from binary ideology model.
    Expected columns: interaction_coef, interaction_p_val
    """
    if df is None or df.empty:
        return {
            "binary_interaction_coef": None,
            "binary_interaction_p_val": None
        }

    row = df.iloc[-1]
    coef = row.get('interaction_coef')
    p_val = row.get('interaction_p_val')

    return {
        "binary_interaction_coef": coef,
        "binary_interaction_p_val": p_val
    }


def aggregate_robustness_metrics() -> pd.DataFrame:
    """
    Main entry point for T026.
    Loads results from prerequisite tasks (T021, T022, T023, T024b)
    and aggregates them into a single CSV file: results/robustness_metrics.csv
    """
    logger.info("Starting aggregation of robustness metrics (T026)...")

    results_dir = get_results_path()
    if not results_dir.exists():
        results_dir.mkdir(parents=True, exist_ok=True)

    # Define paths to prerequisite outputs
    # These paths are derived from the task descriptions and standard naming conventions
    bootstrap_path = results_dir / "bootstrap_results.csv"
    alpha_sweep_path = results_dir / "alpha_sweep.csv"
    covariate_path = results_dir / "covariate_adjustment.csv"
    binary_path = results_dir / "binary_model_results.csv" # From T024b

    # Load data
    df_boot = load_csv_safely(bootstrap_path, "Bootstrap")
    df_alpha = load_csv_safely(alpha_sweep_path, "Alpha Sweep")
    df_cov = load_csv_safely(covariate_path, "Covariate Adjustment")
    df_bin = load_csv_safely(binary_path, "Binary Model")

    # Extract metrics
    boot_metrics = extract_bootstrap_metrics(df_boot)
    alpha_metrics = extract_alpha_sweep_metrics(df_alpha)
    cov_metrics = extract_covariate_metrics(df_cov)
    bin_metrics = extract_binary_model_metrics(df_bin)

    # Merge all metrics into a single dictionary
    aggregated = {**boot_metrics, **alpha_metrics, **cov_metrics, **bin_metrics}

    # Calculate stability ratio if both primary (covariate) and primary (no covariate) are available
    # Note: We assume the primary model results are in a separate file or we can infer from context.
    # For this specific task, we focus on the metrics explicitly requested.
    # If primary model results are needed for ratio, we would load primary_model_results.csv
    primary_path = results_dir / "primary_model_results.csv"
    df_primary = load_csv_safely(primary_path, "Primary Model")
    if df_primary is not None and not df_primary.empty and cov_metrics['covariate_interaction_coef'] is not None:
        primary_coef = df_primary.iloc[-1].get('interaction_coef')
        if primary_coef is not None and primary_coef != 0:
            ratio = cov_metrics['covariate_interaction_coef'] / primary_coef
            aggregated['covariate_stability_ratio'] = ratio

    # Create DataFrame
    # We expect a single row of summary metrics
    summary_df = pd.DataFrame([aggregated])

    # Define output path
    output_path = results_dir / "robustness_metrics.csv"

    # Save to CSV
    summary_df.to_csv(output_path, index=False)
    logger.info(f"Successfully saved aggregated robustness metrics to {output_path}")

    return summary_df


def run_aggregation_pipeline():
    """
    Wrapper to run the aggregation pipeline as a script or module call.
    """
    setup_logger = get_logger(__name__)
    setup_logger.info("Running robustness aggregation pipeline...")
    df = aggregate_robustness_metrics()
    setup_logger.info(f"Aggregation complete. Rows: {len(df)}")
    return df

if __name__ == "__main__":
    run_aggregation_pipeline()
