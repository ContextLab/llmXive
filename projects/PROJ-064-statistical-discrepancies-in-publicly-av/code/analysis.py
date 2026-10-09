import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from scipy import stats
import os
import json
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import yaml

from .models import Discrepancy, Jurisdiction
from .exceptions import ConfigurationError, StatisticalModelError
from .logger import get_logger, setup_logging

logger = get_logger(__name__)

# --- Existing Functions (Preserved from previous implementation) ---

def load_processed_discrepancies(file_path: str) -> pd.DataFrame:
    """Load processed discrepancies from a parquet or csv file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Discrepancy file not found: {file_path}")

    if path.suffix == '.parquet':
        return pd.read_parquet(path)
    elif path.suffix == '.csv':
        return pd.read_csv(path)
    else:
        # Fallback to parquet for consistency
        raise ValueError(f"Unsupported file format: {path.suffix}")

def load_null_distribution(file_path: str) -> Dict[str, Any]:
    """Load null distribution results from a JSON file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Null distribution file not found: {file_path}")

    with open(path, 'r') as f:
        return json.load(f)

def anderson_darling_test(observed: np.ndarray, simulated: np.ndarray) -> Tuple[float, float]:
    """
    Perform Anderson-Darling test between observed and simulated distributions.
    Returns (statistic, critical_values).
    """
    try:
        result = stats.anderson_ksim(observed, simulated)
        return result.statistic, result.pvalue
    except Exception as e:
        logger.error(f"Anderson-Darling test failed: {e}")
        raise StatisticalModelError("Anderson-Darling test failed") from e

def kolmogorov_smirnov_test(observed: np.ndarray, simulated: np.ndarray) -> Tuple[float, float]:
    """
    Perform Kolmogorov-Smirnov test between observed and simulated distributions.
    Returns (statistic, pvalue).
    """
    try:
        # Two-sample KS test
        result = stats.ks_2samp(observed, simulated)
        return result.statistic, result.pvalue
    except Exception as e:
        logger.error(f"KS test failed: {e}")
        raise StatisticalModelError("KS test failed") from e

def calculate_jurisdiction_p_values(discrepancies: pd.DataFrame, null_dist: np.ndarray) -> pd.DataFrame:
    """
    Calculate p-values for each jurisdiction based on the null distribution.
    """
    if 'discrepancy_pct' not in discrepancies.columns:
        raise ValueError("discrepancy_pct column missing in discrepancies")

    observed = discrepancies['discrepancy_pct'].values
    p_values = []

    for obs_val in observed:
        # Two-tailed p-value approximation based on null distribution
        count_extreme = np.sum(np.abs(null_dist) >= np.abs(obs_val))
        p_val = count_extreme / len(null_dist)
        p_values.append(p_val)

    discrepancies['p_value'] = p_values
    return discrepancies

def calculate_vif_for_predictors(df: pd.DataFrame, predictors: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor for given predictors.
    """
    if not predictors:
        return {}

    # Ensure all predictors exist
    available = [p for p in predictors if p in df.columns]
    if len(available) < 2:
        return {p: 1.0 for p in predictors}  # No collinearity possible with < 2 vars

    from scipy.linalg import inv

    # Simple VIF calculation: VIF_j = 1 / (1 - R_j^2)
    # where R_j^2 is the R-squared of regressing predictor j on all other predictors
    vifs = {}
    X = df[available].values

    for i, col_name in enumerate(available):
        y = X[:, i]
        X_other = np.delete(X, i, axis=1)

        # Add intercept
        X_other_with_intercept = np.ones((X_other.shape[0], X_other.shape[1] + 1))
        X_other_with_intercept[:, 1:] = X_other

        try:
            # OLS: beta = (X'X)^-1 X'y
            XtX = X_other_with_intercept.T @ X_other_with_intercept
            if np.linalg.det(XtX) == 0:
                vifs[col_name] = float('inf')
                continue

            beta = np.linalg.solve(XtX, X_other_with_intercept.T @ y)
            y_pred = X_other_with_intercept @ beta

            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot)

            vif = 1 / (1 - r_squared) if r_squared < 1 else float('inf')
            vifs[col_name] = vif
        except np.linalg.LinAlgError:
            vifs[col_name] = float('inf')

    return vifs

# --- New: Sensitivity Threshold Loading (already present) ---

def load_sensitivity_thresholds(config_path: str) -> Dict[str, Any]:
    """
    Load sensitivity thresholds from a YAML configuration file.
    Expected structure:
    primary_threshold: 0.005 (0.5%)
    sweep_thresholds: [0.0001, 0.0005, 0.001] (0.01%, 0.05%, 0.1%)
    """
    path = Path(config_path)
    if not path.exists():
        # Create default if missing, but log warning
        logger.warning(f"Config {config_path} not found. Using defaults.")
        return {
            "primary_threshold": 0.005,
            "sweep_thresholds": [0.0001, 0.0005, 0.001]
        }

    with open(path, 'r') as f:
        config = yaml.safe_load(f)

    # Validate required keys
    if "primary_threshold" not in config:
        raise ConfigurationError("primary_threshold missing in sensitivity config")
    if "sweep_thresholds" not in config:
        raise ConfigurationError("sweep_thresholds missing in sensitivity config")

    return config

# --- New: Collinearity Report Generation (Task T035) ---

def generate_collinearity_report(
    discrepancies: pd.DataFrame,
    predictors_config_path: str,
    output_path: str
) -> None:
    """
    Generate a JSON collinearity report.

    The function looks for a configuration file (YAML) that lists predictor
    column names (e.g., population_density, precinct_size). If the listed
    predictors are present in the ``discrepancies`` DataFrame, VIF values
    are calculated and written to ``output_path``. If no predictors are
    configured or none of them exist in the data, a JSON object with a
    ``status`` field set to ``Not Applicable`` is written.

    The generated JSON conforms to the requirement of task T035:
    {
        "status": "Applicable",
        "vif": {"population_density": 1.23, "precinct_size": 2.34}
    }
    or
    {
        "status": "Not Applicable"
    }
    """
    # Load predictor configuration
    path = Path(predictors_config_path)
    if not path.exists():
        logger.warning(f"Predictors config {predictors_config_path} not found. Reporting Not Applicable.")
        report = {"status": "Not Applicable"}
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        return

    with open(path, 'r') as f:
        cfg = yaml.safe_load(f)

    predictors = cfg.get('predictors', [])
    if not predictors:
        logger.info("No predictors listed in config; collinearity report not applicable.")
        report = {"status": "Not Applicable"}
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        return

    # Determine which of the configured predictors actually exist in the data
    present = [p for p in predictors if p in discrepancies.columns]
    if len(present) < 2:
        logger.info("Insufficient predictor columns present for VIF calculation.")
        report = {"status": "Not Applicable"}
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        return

    # Compute VIF
    vif_dict = calculate_vif_for_predictors(discrepancies, present)

    report = {
        "status": "Applicable",
        "vif": vif_dict
    }

    # Write JSON report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Collinearity report written to {output_path}")

# --- Sensitivity Analysis Implementation (unchanged) ---

def run_sensitivity_analysis(
    discrepancies: pd.DataFrame,
    null_dist_nb: np.ndarray,
    null_dist_perm: np.ndarray,
    thresholds: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Run sensitivity analysis comparing Negative Binomial and Permutation models
    across different thresholds.

    Returns a dictionary containing:
    - primary_results: Results at primary threshold
    - sweep_results: Results across sweep thresholds
    - stability_metrics: Variation in flagged counts
    """
    primary_thresh = thresholds['primary_threshold']
    sweep_threshes = thresholds['sweep_thresholds']

    results = {
        "primary_threshold": primary_thresh,
        "sweep_thresholds": sweep_threshes,
        "primary_results": {},
        "sweep_results": {
            "nb_model": [],
            "perm_model": []
        },
        "stability_metrics": {}
    }

    # Helper to count flagged jurisdictions
    def count_flagged(df: pd.DataFrame, thresh: float, col: str = 'p_value') -> int:
        return int((df[col] < thresh).sum())

    # --- 1. Primary Threshold Analysis ---
    logger.info(f"Running analysis at primary threshold: {primary_thresh}")

    # Ensure p-value columns exist
    if 'p_value_nb' not in discrepancies.columns:
        obs_vals = discrepancies['discrepancy_pct'].values
        p_vals_nb = []
        for obs in obs_vals:
            count = np.sum(np.abs(null_dist_nb) >= np.abs(obs))
            p_vals_nb.append(count / len(null_dist_nb))
        discrepancies['p_value_nb'] = p_vals_nb

    if 'p_value_perm' not in discrepancies.columns:
        obs_vals = discrepancies['discrepancy_pct'].values
        p_vals_perm = []
        for obs in obs_vals:
            count = np.sum(np.abs(null_dist_perm) >= np.abs(obs))
            p_vals_perm.append(count / len(null_dist_perm))
        discrepancies['p_value_perm'] = p_vals_perm

    # Primary Counts
    nb_primary_flagged = count_flagged(discrepancies, primary_thresh, 'p_value_nb')
    perm_primary_flagged = count_flagged(discrepancies, primary_thresh, 'p_value_perm')

    results["primary_results"] = {
        "threshold": primary_thresh,
        "nb_flagged_count": nb_primary_flagged,
        "perm_flagged_count": perm_primary_flagged,
        "total_jurisdictions": len(discrepancies)
    }

    # --- 2. Sensitivity Sweep ---
    logger.info(f"Running sensitivity sweep across {len(sweep_threshes)} thresholds")

    nb_sweep_data = []
    perm_sweep_data = []

    for thresh in sweep_threshes:
        nb_count = count_flagged(discrepancies, thresh, 'p_value_nb')
        perm_count = count_flagged(discrepancies, thresh, 'p_value_perm')

        nb_sweep_data.append({"threshold": thresh, "flagged": nb_count})
        perm_sweep_data.append({"threshold": thresh, "flagged": perm_count})

    results["sweep_results"]["nb_model"] = nb_sweep_data
    results["sweep_results"]["perm_model"] = perm_sweep_data

    # --- 3. Stability Metrics ---
    nb_counts = [d['flagged'] for d in nb_sweep_data]
    perm_counts = [d['flagged'] for d in perm_sweep_data]

    results["stability_metrics"] = {
        "nb_std_variation": float(np.std(nb_counts)) if nb_counts else 0.0,
        "perm_std_variation": float(np.std(perm_counts)) if perm_counts else 0.0,
        "nb_range": [min(nb_counts), max(nb_counts)] if nb_counts else [0, 0],
        "perm_range": [min(perm_counts), max(perm_counts)] if perm_counts else [0, 0]
    }

    return results

def generate_sensitivity_report(
    analysis_results: Dict[str, Any],
    output_path: str
) -> None:
    """
    Generate a markdown report documenting the sensitivity analysis.
    """
    report_lines = [
        "# Sensitivity Analysis Report",
        "",
        f"**Generated:** {datetime.now().isoformat()}",
        "",
        "## Overview",
        "This report details the variation in flagged jurisdictions across different significance thresholds, comparing the Negative Binomial (NB) and Permutation null models.",
        "",
        f"## Primary Threshold ({analysis_results['primary_threshold']:.4f})",
        "",
        f"- **NB Model Flagged:** {analysis_results['primary_results']['nb_flagged_count']}",
        f"- **Permutation Model Flagged:** {analysis_results['primary_results']['perm_flagged_count']}",
        f"- **Total Jurisdictions:** {analysis_results['primary_results']['total_jurisdictions']}",
        "",
        "## Sensitivity Sweep",
        "",
        "### Negative Binomial Model",
        "| Threshold | Flagged Count |",
        "|-----------|---------------|"
    ]

    for item in analysis_results['sweep_results']['nb_model']:
        report_lines.append(f"| {item['threshold']:.5f} | {item['flagged']} |")

    report_lines.extend([
        "",
        "### Permutation Model",
        "| Threshold | Flagged Count |",
        "|-----------|---------------|"
    ])

    for item in analysis_results['sweep_results']['perm_model']:
        report_lines.append(f"| {item['threshold']:.5f} | {item['flagged']} |")

    report_lines.extend([
        "",
        "## Stability Metrics",
        "",
        f"- **NB Model Std Dev:** {analysis_results['stability_metrics']['nb_std_variation']:.2f}",
        f"- **Permutation Model Std Dev:** {analysis_results['stability_metrics']['perm_std_variation']:.2f}",
        f"- **NB Range:** {analysis_results['stability_metrics']['nb_range']}",
        f"- **Permutation Range:** {analysis_results['stability_metrics']['perm_range']}",
        "",
        "## Conclusion",
        "The analysis compares the stability of flagged anomalies under varying significance thresholds. A high standard deviation indicates that the number of flagged jurisdictions is highly sensitive to the chosen threshold, suggesting potential instability in the detection of statistical discrepancies.",
        ""
    ])

    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))

def generate_stability_plot(
    analysis_results: Dict[str, Any],
    output_path: str
) -> None:
    """
    Generate a plot showing the stability of flagged counts across thresholds.
    """
    plt.figure(figsize=(10, 6))

    nb_thresholds = [d['threshold'] for d in analysis_results['sweep_results']['nb_model']]
    nb_counts = [d['flagged'] for d in analysis_results['sweep_results']['nb_model']]

    perm_thresholds = [d['threshold'] for d in analysis_results['sweep_results']['perm_model']]
    perm_counts = [d['flagged'] for d in analysis_results['sweep_results']['perm_model']]

    plt.plot(nb_thresholds, nb_counts, marker='o', label='Negative Binomial', color='blue')
    plt.plot(perm_thresholds, perm_counts, marker='s', label='Permutation', color='red')

    plt.xlabel('Threshold (p-value)')
    plt.ylabel('Number of Flagged Jurisdictions')
    plt.title('Sensitivity Analysis: Flagged Jurisdictions vs Threshold')
    plt.xscale('log')
    plt.legend()
    plt.grid(True, which="both", ls="-", alpha=0.2)

    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Stability plot saved to {output_path}")

def run_analysis(
    discrepancies: pd.DataFrame,
    null_dist_nb: np.ndarray,
    null_dist_perm: np.ndarray,
    config_path: str,
    output_dir: str
) -> Dict[str, Any]:
    """
    Main function to orchestrate sensitivity analysis and reporting.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Starting Sensitivity Analysis")

    # 1. Load Thresholds
    thresholds = load_sensitivity_thresholds(config_path)

    # 2. Run Analysis
    results = run_sensitivity_analysis(discrepancies, null_dist_nb, null_dist_perm, thresholds)

    # 3. Generate Reports
    report_path = output_dir / "sensitivity_report.md"
    generate_sensitivity_report(results, str(report_path))

    plot_path = output_dir / "stability_plot.png"
    generate_stability_plot(results, str(plot_path))

    # 4. Save Results JSON
    json_path = output_dir / "sensitivity_results.json"
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)

    # 5. Generate Collinearity Report (Task T035)
    col_report_path = output_dir / "collinearity_report.json"
    generate_collinearity_report(
        discrepancies,
        predictors_config_path="config/predictors.yaml",
        output_path=str(col_report_path)
    )

    logger.info(f"Sensitivity analysis complete. Report: {report_path}, Plot: {plot_path}, Collinearity: {col_report_path}")
    return results

def main():
    """
    CLI Entry point for Sensitivity Analysis.
    Usage: python code/analysis.py --input data/processed/analysis_results.json --config config/sensitivity_thresholds.yaml --output-dir data/processed/
    """
    import argparse

    parser = argparse.ArgumentParser(description="Run Sensitivity Analysis")
    parser.add_argument('--input', type=str, required=True, help="Path to processed discrepancies (parquet/csv)")
    parser.add_argument('--null-nb', type=str, required=True, help="Path to NB null distribution JSON")
    parser.add_argument('--null-perm', type=str, required=True, help="Path to Permutation null distribution JSON")
    parser.add_argument('--config', type=str, default='config/sensitivity_thresholds.yaml', help="Path to sensitivity config")
    parser.add_argument('--output-dir', type=str, default='data/processed', help="Output directory for reports")

    args = parser.parse_args()

    # Setup logging
    setup_logging()

    try:
        # Load Data
        logger.info(f"Loading discrepancies from {args.input}")
        discrepancies = load_processed_discrepancies(args.input)

        logger.info(f"Loading NB null distribution from {args.null_nb}")
        nb_data = load_null_distribution(args.null_nb)
        null_dist_nb = np.array(nb_data.get('distribution', nb_data.get('samples', [])))

        logger.info(f"Loading Perm null distribution from {args.null_perm}")
        perm_data = load_null_distribution(args.null_perm)
        null_dist_perm = np.array(perm_data.get('distribution', perm_data.get('samples', [])))

        if len(null_dist_nb) == 0 or len(null_dist_perm) == 0:
            raise ValueError("Null distributions are empty. Check input files.")

        # Run Analysis
        results = run_analysis(discrepancies, null_dist_nb, null_dist_perm, args.config, args.output_dir)

        print(f"Analysis complete. Results saved to {args.output_dir}")

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
