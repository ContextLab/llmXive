"""
Robustness and Sensitivity Analysis Module (User Story 3).

Implements:
- Alpha sweep for Ridge regression regularization
- Alternative metric analysis (Variance vs SD)
- Partial correlation analysis controlling for FD
- Generation of robustness_report.json
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

import numpy as np
from sklearn.linear_model import RidgeCV
from sklearn.preprocessing import StandardScaler
from scipy.stats import pearsonr

# Import shared utilities
from utils import read_csv, write_json, get_logger, ensure_file_directory
from config import ensure_directories

# Configure logging
logger = get_logger(__name__)

# Constants
DATA_PATH = Path("data/processed/cleaned_data.csv")
RESULTS_DIR = Path("data/results")
ROBUSTNESS_REPORT_PATH = RESULTS_DIR / "robustness_report.json"

# Alpha values for sweep (log-spaced)
ALPHA_SWEEP_VALUES = [0.01, 0.1, 1.0, 10.0, 100.0, 1000.0]


def load_cleaned_data_for_robustness() -> Dict[str, np.ndarray]:
    """
    Load the cleaned data required for robustness analysis.
    Returns a dictionary of numpy arrays.
    """
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Required data file not found: {DATA_PATH}. "
            "Please run the ingestion pipeline (T016) first."
        )

    df = read_csv(DATA_PATH)

    # Extract features and target
    # Target: MWQ_Score
    # Predictors: Global_Signal_SD (or Variance), FD, DVARS, Age, Sex
    y = df["MWQ_Score"].to_numpy().astype(float)

    # We will reconstruct X dynamically depending on the analysis,
    # but here we prepare the base columns.
    return {
        "y": y,
        "Global_Signal_SD": df["Global_Signal_SD"].to_numpy().astype(float),
        "FD": df["Mean_FD"].to_numpy().astype(float),
        "DVARS": df["Mean_DVARS"].to_numpy().astype(float),
        "Age": df["Age"].to_numpy().astype(float),
        "Sex": df["Sex"].to_numpy().astype(float),
    }


def run_alpha_sweep(data: Dict[str, np.ndarray]) -> Dict[str, Any]:
    """
    Run Ridge regression with a sweep of alpha values to check stability.
    Returns a dict with MAE and R2 for each alpha.
    """
    logger.info("Running alpha sweep analysis...")

    y = data["y"]
    # Full model features: Global_Signal_SD, FD, DVARS, Age, Sex
    X_cols = [
        data["Global_Signal_SD"],
        data["FD"],
        data["DVARS"],
        data["Age"],
        data["Sex"],
    ]
    X = np.column_stack(X_cols)

    # Standardize features (Ridge is sensitive to scale)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    results = []
    observed_maes = []
    observed_r2s = []

    for alpha in ALPHA_SWEEP_VALUES:
        # Use RidgeCV with a specific alpha to mimic single-alpha fit
        # We fit on the whole dataset here for the sweep visualization,
        # though T019 used nested CV. For robustness check, we check
        # how the coefficients/metrics behave across alphas.
        # To be consistent with T019's "nested CV" logic, we could re-run CV,
        # but a simple sweep on the full data is sufficient for stability check.
        model = RidgeCV(alphas=[alpha], store_cv_values=True)
        model.fit(X_scaled, y)

        # Calculate metrics
        y_pred = model.predict(X_scaled)

        # MAE
        mae = np.mean(np.abs(y - y_pred))
        # R2
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0

        results.append({
            "alpha": alpha,
            "mae": float(mae),
            "r2": float(r2),
            "coefficients": [float(c) for c in model.coef_]
        })

        observed_maes.append(mae)
        observed_r2s.append(r2)

    logger.info(f"Alpha sweep complete. Min MAE: {min(observed_maes):.4f}, Max MAE: {max(observed_maes):.4f}")

    return {
        "alpha_values": ALPHA_SWEEP_VALUES,
        "metrics": results,
        "stability_summary": {
            "mae_range": [float(min(observed_maes)), float(max(observed_maes))],
            "r2_range": [float(min(observed_r2s)), float(max(observed_r2s))]
        }
    }


def run_variance_metric_analysis(data: Dict[str, np.ndarray]) -> Dict[str, Any]:
    """
    Run analysis using Global Signal Variance instead of SD.
    Returns correlation between Variance-based prediction and MWQ.
    """
    logger.info("Running variance metric analysis...")

    y = data["y"]
    sd = data["Global_Signal_SD"]
    variance = sd ** 2  # Variance is SD squared

    # We can't directly compare SD and Variance coefficients without scaling,
    # but we can check the correlation of the raw metrics with MWQ.
    # However, the task asks for "Variance metric correlation".
    # We will compute the Pearson r between Global Signal Variance and MWQ_Score.
    # This is a simple bivariate check to see if the relationship holds for the alternative metric.

    r, p_value = pearsonr(variance, y)

    logger.info(f"Variance vs MWQ correlation: r={r:.4f}, p={p_value:.4f}")

    return {
        "metric": "Global_Signal_Variance",
        "pearson_r": float(r),
        "p_value": float(p_value),
        "sample_size": int(len(y))
    }


def run_partial_correlation_analysis(data: Dict[str, np.ndarray]) -> Dict[str, Any]:
    """
    Compute partial correlation between Global Signal SD and MWQ,
    controlling for Mean FD.
    """
    logger.info("Running partial correlation analysis (controlling for FD)...")

    y = data["y"]
    x = data["Global_Signal_SD"]
    z = data["FD"]  # Confound to control for

    # Partial correlation formula:
    # r_xy.z = (r_xy - r_xz * r_yz) / sqrt((1 - r_xz^2) * (1 - r_yz^2))

    r_xy, _ = pearsonr(x, y)
    r_xz, _ = pearsonr(x, z)
    r_yz, _ = pearsonr(y, z)

    numerator = r_xy - (r_xz * r_yz)
    denominator_sq = (1 - r_xz**2) * (1 - r_yz**2)

    if denominator_sq <= 0:
        # Should not happen with real data unless perfect collinearity
        logger.warning("Denominator zero in partial correlation. Setting r_partial to 0.")
        r_partial = 0.0
        p_partial = 1.0
    else:
        r_partial = numerator / np.sqrt(denominator_sq)

        # Approximate p-value for partial correlation
        # t = r * sqrt((n - 2 - k) / (1 - r^2)) where k is number of controlled vars (1 here)
        n = len(y)
        k = 1
        if abs(r_partial) >= 1.0:
            t_stat = float('inf') if r_partial > 0 else float('-inf')
            p_partial = 0.0
        else:
            t_stat = r_partial * np.sqrt((n - 2 - k) / (1 - r_partial**2))
            # Two-tailed p-value using scipy.stats.t (approximate without import if desired, but we have scipy)
            from scipy.stats import t
            p_partial = 2 * (1 - t.cdf(abs(t_stat), n - 2 - k))

    logger.info(f"Partial correlation (GSA vs MWQ | FD): r={r_partial:.4f}, p={p_partial:.4f}")

    return {
        "controlled_variable": "Mean_FD",
        "partial_correlation_r": float(r_partial),
        "p_value": float(p_partial),
        "degrees_of_freedom": int(n - 2 - k),
        "significant_at_0_05": p_partial < 0.05
    }


def generate_robustness_report(
    alpha_results: Dict[str, Any],
    variance_results: Dict[str, Any],
    partial_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Assemble the final robustness report dictionary.
    """
    report = {
        "analysis_type": "robustness_sensitivity",
        "alpha_sweep": alpha_results,
        "variance_metric_analysis": variance_results,
        "partial_correlation_analysis": partial_results,
        "summary": {
            "alpha_stable": (
                alpha_results["stability_summary"]["mae_range"][1] -
                alpha_results["stability_summary"]["mae_range"][0]
            ) < 0.1, # Arbitrary threshold for stability check
            "variance_correlation_significant": variance_results["p_value"] < 0.05,
            "partial_correlation_significant": partial_results["significant_at_0_05"]
        }
    }
    return report


def main():
    """
    Main entry point for the robustness analysis task (T031).
    1. Load cleaned data.
    2. Run alpha sweep.
    3. Run variance metric analysis.
    4. Run partial correlation analysis.
    5. Generate and save robustness_report.json.
    """
    ensure_directories()
    ensure_file_directory(ROBUSTNESS_REPORT_PATH)

    logger.info("Starting Robustness Analysis (T031)...")

    try:
        data = load_cleaned_data_for_robustness()
    except FileNotFoundError as e:
        logger.error(str(e))
        raise SystemExit(1)

    # Run analyses
    alpha_results = run_alpha_sweep(data)
    variance_results = run_variance_metric_analysis(data)
    partial_results = run_partial_correlation_analysis(data)

    # Generate report
    report = generate_robustness_report(alpha_results, variance_results, partial_results)

    # Write to file
    write_json(ROBUSTNESS_REPORT_PATH, report)
    logger.info(f"Robustness report saved to {ROBUSTNESS_REPORT_PATH}")

    return report


if __name__ == "__main__":
    main()
