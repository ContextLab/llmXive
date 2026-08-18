"""
Integration module for T031: Integrate regression results into data/artifacts.

This module aggregates outputs from T029 (regression.py) and T030 (cross_validation.py)
into structured CSV and JSON artifacts within the data/artifacts directory.
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd
import numpy as np

# Project-relative imports based on API surface
from config import get_config
from utils.logging import get_logger, AnalysisError, log_duration
from utils.io import save_parquet

logger = get_logger(__name__)


def load_regression_results(regression_output_path: Path) -> Dict[str, Any]:
    """
    Load regression results from the JSON output of T029.
    Expected structure:
    {
        "baseline": { "coefficients": [...], "r2": float, "adj_r2": float, "aic": float, "bic": float },
        "full": { "coefficients": [...], "r2": float, "adj_r2": float, "aic": float, "bic": float },
        "vif_flags": [...],
        "metadata": { ... }
    }
    """
    if not regression_output_path.exists():
        raise FileNotFoundError(f"Regression output file not found: {regression_output_path}")

    with open(regression_output_path, 'r') as f:
        data = json.load(f)

    return data


def load_cross_validation_results(cv_output_path: Path) -> Dict[str, Any]:
    """
    Load cross-validation results from the JSON output of T030.
    Expected structure:
    {
        "baseline": { "mean_r2": float, "std_r2": float, "fold_r2s": [...] },
        "full": { "mean_r2": float, "std_r2": float, "fold_r2s": [...] },
        "delta_r2": float,
        "metadata": { ... }
    }
    """
    if not cv_output_path.exists():
        raise FileNotFoundError(f"Cross-validation output file not found: {cv_output_path}")

    with open(cv_output_path, 'r') as f:
        data = json.load(f)

    return data


def create_metrics_summary(regression_data: Dict[str, Any], cv_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a unified summary of model performance metrics.
    """
    summary = {
        "model_comparison": {
            "baseline": {
                "r2_in_sample": regression_data.get("baseline", {}).get("r2"),
                "r2_out_sample": cv_data.get("baseline", {}).get("mean_r2"),
                "std_out_sample": cv_data.get("baseline", {}).get("std_r2"),
                "aic": regression_data.get("baseline", {}).get("aic"),
                "bic": regression_data.get("baseline", {}).get("bic")
            },
            "full": {
                "r2_in_sample": regression_data.get("full", {}).get("r2"),
                "r2_out_sample": cv_data.get("full", {}).get("mean_r2"),
                "std_out_sample": cv_data.get("full", {}).get("std_r2"),
                "aic": regression_data.get("full", {}).get("aic"),
                "bic": regression_data.get("full", {}).get("bic")
            },
            "delta_r2_in_sample": None,
            "delta_r2_out_sample": cv_data.get("delta_r2")
        },
        "vif_flags": regression_data.get("vif_flags", []),
        "metadata": {
            "generated_at": pd.Timestamp.now().isoformat(),
            "source_regression": str(regression_data.get("metadata", {}).get("source_file", "unknown")),
            "source_cv": str(cv_data.get("metadata", {}).get("source_file", "unknown")),
            "data_label": regression_data.get("metadata", {}).get("data_label", "unknown")
        }
    }

    # Calculate in-sample delta R2
    if summary["model_comparison"]["baseline"]["r2_in_sample"] is not None and \
       summary["model_comparison"]["full"]["r2_in_sample"] is not None:
        summary["model_comparison"]["delta_r2_in_sample"] = \
            summary["model_comparison"]["full"]["r2_in_sample"] - \
            summary["model_comparison"]["baseline"]["r2_in_sample"]

    return summary


def create_coefficients_dataframe(regression_data: Dict[str, Any]) -> pd.DataFrame:
    """
    Convert regression coefficients into a tidy DataFrame for CSV export.
    """
    rows = []

    # Process Baseline Model
    if "baseline" in regression_data and "coefficients" in regression_data["baseline"]:
        for coef in regression_data["baseline"]["coefficients"]:
            rows.append({
                "model": "baseline",
                "predictor": coef.get("name"),
                "coefficient": coef.get("coef"),
                "std_err": coef.get("std_err"),
                "p_value": coef.get("pvalue"),
                "conf_int_low": coef.get("conf_int", [None, None])[0],
                "conf_int_high": coef.get("conf_int", [None, None])[1],
                "target": regression_data.get("metadata", {}).get("target_variable", "unknown")
            })

    # Process Full Model
    if "full" in regression_data and "coefficients" in regression_data["full"]:
        for coef in regression_data["full"]["coefficients"]:
            rows.append({
                "model": "full",
                "predictor": coef.get("name"),
                "coefficient": coef.get("coef"),
                "std_err": coef.get("std_err"),
                "p_value": coef.get("pvalue"),
                "conf_int_low": coef.get("conf_int", [None, None])[0],
                "conf_int_high": coef.get("conf_int", [None, None])[1],
                "target": regression_data.get("metadata", {}).get("target_variable", "unknown")
            })

    if not rows:
        logger.warning("No coefficients found in regression data. Returning empty DataFrame.")
        return pd.DataFrame()

    return pd.DataFrame(rows)


def integrate_results(
    regression_output: Path,
    cv_output: Path,
    output_dir: Path,
    base_name: str = "regression_summary"
) -> Dict[str, Path]:
    """
    Main integration function. Loads regression and CV results, creates summary artifacts,
    and writes them to data/artifacts.

    Args:
        regression_output: Path to JSON from T029
        cv_output: Path to JSON from T030
        output_dir: Directory to write artifacts (should be data/artifacts)
        base_name: Prefix for output files

    Returns:
        Dictionary mapping artifact type to file path
    """
    logger.info(f"Starting integration of regression results from {regression_output} and {cv_output}")

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    try:
        regression_data = load_regression_results(regression_output)
        cv_data = load_cross_validation_results(cv_output)
    except Exception as e:
        raise AnalysisError(f"Failed to load input results: {e}")

    # Create summary dictionary
    summary = create_metrics_summary(regression_data, cv_data)

    # Create coefficients DataFrame
    coef_df = create_coefficients_dataframe(regression_data)

    # Define output paths
    summary_json_path = output_dir / f"{base_name}_metrics.json"
    coefficients_csv_path = output_dir / f"{base_name}_coefficients.csv"
    summary_csv_path = output_dir / f"{base_name}_metrics.csv"

    # Write JSON summary
    with open(summary_json_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    logger.info(f"Wrote JSON summary to {summary_json_path}")

    # Write Coefficients CSV
    if not coef_df.empty:
        coef_df.to_csv(coefficients_csv_path, index=False)
        logger.info(f"Wrote coefficients CSV to {coefficients_csv_path}")
    else:
        logger.warning("Skipping coefficients CSV write (empty DataFrame)")

    # Write Metrics CSV (flatten summary for CSV)
    # Flatten the nested structure for CSV export
    flat_rows = []
    for model_type in ["baseline", "full"]:
        metrics = summary["model_comparison"][model_type]
        flat_row = {
            "model": model_type,
            "r2_in_sample": metrics.get("r2_in_sample"),
            "r2_out_sample": metrics.get("r2_out_sample"),
            "std_out_sample": metrics.get("std_out_sample"),
            "aic": metrics.get("aic"),
            "bic": metrics.get("bic")
        }
        flat_rows.append(flat_row)

    # Add delta row
    flat_rows.append({
        "model": "delta",
        "r2_in_sample": summary["model_comparison"]["delta_r2_in_sample"],
        "r2_out_sample": summary["model_comparison"]["delta_r2_out_sample"],
        "std_out_sample": None,
        "aic": None,
        "bic": None
    })

    flat_df = pd.DataFrame(flat_rows)
    flat_df.to_csv(summary_csv_path, index=False)
    logger.info(f"Wrote metrics CSV to {summary_csv_path}")

    return {
        "json_summary": summary_json_path,
        "coefficients_csv": coefficients_csv_path,
        "metrics_csv": summary_csv_path
    }


def main():
    """
    Entry point for the integration script.
    Reads configuration to determine input/output paths.
    """
    config = get_config()
    project_root = config.get("project_root", Path.cwd())
    data_dir = project_root / "data"
    processed_dir = data_dir / "processed"
    artifacts_dir = data_dir / "artifacts"

    # Expected input paths based on T029 and T030 outputs
    # Assuming T029 writes to data/processed/regression_results.json
    # and T030 writes to data/processed/cross_validation_results.json
    # Adjust based on actual T029/T030 output paths if different
    regression_input = processed_dir / "regression_results.json"
    cv_input = processed_dir / "cross_validation_results.json"

    # If files are in artifacts from previous steps (unlikely for raw results), check there
    if not regression_input.exists() and (artifacts_dir / "regression_results.json").exists():
        regression_input = artifacts_dir / "regression_results.json"
    if not cv_input.exists() and (artifacts_dir / "cross_validation_results.json").exists():
        cv_input = artifacts_dir / "cross_validation_results.json"

    if not regression_input.exists():
        raise FileNotFoundError(f"Required regression results file not found: {regression_input}")
    if not cv_input.exists():
        raise FileNotFoundError(f"Required cross-validation results file not found: {cv_input}")

    logger.info(f"Using regression input: {regression_input}")
    logger.info(f"Using CV input: {cv_input}")
    logger.info(f"Output directory: {artifacts_dir}")

    try:
        artifacts = integrate_results(
            regression_output=regression_input,
            cv_output=cv_input,
            output_dir=artifacts_dir,
            base_name="regression_summary"
        )
        logger.info("Integration completed successfully.")
        for name, path in artifacts.items():
            logger.info(f"  - {name}: {path}")
    except Exception as e:
        logger.error(f"Integration failed: {e}")
        raise


if __name__ == "__main__":
    main()
