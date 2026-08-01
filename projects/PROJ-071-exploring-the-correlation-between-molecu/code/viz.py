"""
Visualization module for T032, T033: Generate plots.
Implements scatter plots with regression lines and residual diagnostics.
Handles both Gate PASS (real data) and Gate FAIL (placeholder) scenarios.
"""
from __future__ import annotations

import json
import os
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for CI/Headless
import matplotlib.pyplot as plt
import seaborn as sns

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_data_path() -> Path:
    """Return the project data directory."""
    return Path(__file__).parent.parent / "data"

def check_gate_status() -> bool:
    """Check if the Data Availability Gate passed (N >= 30)."""
    gate_file = get_data_path() / "gate_status.json"
    if not gate_file.exists():
        logger.warning(f"Gate status file not found: {gate_file}. Assuming FAIL.")
        return False
    try:
        with open(gate_file, "r") as f:
            data = json.load(f)
        return data.get("status") == "PASS"
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse gate_status.json: {e}")
        return False

def check_statistical_gate() -> bool:
    """Check if the Statistical Gate passed (standard_subset N >= 30)."""
    path = get_data_path() / "processed" / "standard_subset.csv"
    if not path.exists():
        logger.warning(f"Statistical gate file not found: {path}. Assuming FAIL.")
        return False
    try:
        df = pd.read_csv(path)
        return len(df) >= 30
    except Exception as e:
        logger.error(f"Failed to read standard_subset.csv: {e}")
        return False

def load_analysis_results() -> Optional[Dict[str, Any]]:
    """Load analysis results from JSON."""
    path = get_data_path() / "processed" / "analysis_results.json"
    if not path.exists():
        return None
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load analysis_results.json: {e}")
        return None

def load_residuals_data() -> Optional[pd.DataFrame]:
    """
    Load residuals data for plotting.
    Tries to load from analysis_results.json if available, otherwise returns None.
    """
    results = load_analysis_results()
    if results and results.get("status") == "PASS" and "residuals" in results:
        return pd.DataFrame({"residuals": results["residuals"]})
    return None

def plot_scatter_with_regression(x: np.ndarray, y: np.ndarray, title: str, save_path: Path) -> None:
    """
    Generate a scatter plot with a regression line.
    Uses seaborn style and saves to disk.
    """
    plt.style.use('seaborn-whitegrid')
    plt.figure(figsize=(10, 6))
    
    # Scatter
    sns.scatterplot(x=x, y=y, alpha=0.6, edgecolor='k')
    
    # Regression line
    if len(x) > 1:
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)
        # Sort x for smooth line
        x_sorted = np.sort(x)
        plt.plot(x_sorted, p(x_sorted), "r--", linewidth=2, label=f'Fit: y={z[0]:.2f}x+{z[1]:.2f}')
        plt.legend()
    
    plt.title(title, fontsize=14, fontweight='bold')
    plt.xlabel(str(x.name) if hasattr(x, 'name') and x.name else 'X', fontsize=12)
    plt.ylabel(str(y.name) if hasattr(y, 'name') and y.name else 'Y', fontsize=12)
    
    # Ensure directory exists
    save_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved scatter plot: {save_path}")

def generate_placeholder_plot(save_path: Path, text: str) -> None:
    """Generate a placeholder plot with centered text."""
    plt.style.use('seaborn-whitegrid')
    plt.figure(figsize=(10, 6))
    plt.text(0.5, 0.5, text, ha='center', va='center', fontsize=18, fontweight='bold', color='red')
    plt.axis('off')
    save_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Generated placeholder plot: {save_path}")

def generate_correlation_scatter_plots() -> None:
    """
    T032 Implementation: Generate scatter plots with regression lines.
    Logic:
      1. Check Data Availability Gate (data/gate_status.json).
      2. IF PASS: Load merged_drugs.csv, plot TPSA vs Half-Life.
      3. IF FAIL: Generate placeholder plot "Data Insufficient (N < 30)".
    """
    gate_passed = check_gate_status()
    outputs_dir = get_data_path() / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    
    target_file = outputs_dir / "scatter_tpsa_vs_half_life.png"
    
    if not gate_passed:
        logger.info("Data Availability Gate FAILED. Generating placeholder plot.")
        generate_placeholder_plot(target_file, "Data Insufficient (N < 30)\n(Data Availability Gate Failed)")
        return

    # Gate Passed: Attempt to load real data
    merged_path = get_data_path() / "processed" / "merged_drugs.csv"
    if not merged_path.exists():
        logger.error(f"Gate passed but data file missing: {merged_path}. Generating placeholder.")
        generate_placeholder_plot(target_file, "Data File Missing\n(merged_drugs.csv not found)")
        return

    try:
        df = pd.read_csv(merged_path)
    except Exception as e:
        logger.error(f"Failed to read {merged_path}: {e}")
        generate_placeholder_plot(target_file, f"Data Read Error\n{str(e)}")
        return

    # Verify required columns
    required_cols = ['TPSA', 'half_life']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        logger.error(f"Missing required columns in {merged_path}: {missing}")
        generate_placeholder_plot(target_file, f"Missing Columns: {missing}")
        return

    # Filter out NaNs in key columns
    valid_df = df.dropna(subset=required_cols)
    if len(valid_df) < 2:
        logger.warning(f"Not enough valid data points (N={len(valid_df)}) for regression.")
        generate_placeholder_plot(target_file, f"Insufficient Data for Plot (N={len(valid_df)})")
        return

    x = valid_df['TPSA']
    y = valid_df['half_life']

    plot_scatter_with_regression(x, y, "TPSA vs Half-Life (Real Data)", target_file)

def plot_residual_histogram(residuals: np.ndarray, save_path: Path) -> None:
    """Plot histogram of residuals."""
    plt.style.use('seaborn-whitegrid')
    plt.figure(figsize=(10, 6))
    plt.hist(residuals, bins=20, edgecolor='black', alpha=0.7)
    plt.title("Residual Histogram", fontsize=14, fontweight='bold')
    plt.xlabel("Residuals", fontsize=12)
    plt.ylabel("Frequency", fontsize=12)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()

def plot_qq_plot(residuals: np.ndarray, save_path: Path) -> None:
    """Plot Q-Q plot of residuals."""
    plt.style.use('seaborn-whitegrid')
    plt.figure(figsize=(10, 6))
    from scipy.stats import probplot
    probplot(residuals, dist="norm", plot=plt)
    plt.title("Q-Q Plot of Residuals", fontsize=14, fontweight='bold')
    save_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()

def plot_residuals_vs_fitted(fitted: np.ndarray, residuals: np.ndarray, save_path: Path) -> None:
    """Plot residuals vs fitted values."""
    plt.style.use('seaborn-whitegrid')
    plt.figure(figsize=(10, 6))
    plt.scatter(fitted, residuals, alpha=0.6)
    plt.axhline(0, color='red', linestyle='--', linewidth=2)
    plt.title("Residuals vs Fitted", fontsize=14, fontweight='bold')
    plt.xlabel("Fitted Values", fontsize=12)
    plt.ylabel("Residuals", fontsize=12)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()

def generate_residual_diagnostic_plots() -> None:
    """
    T033 Implementation: Generate residual diagnostic plots.
    Logic:
      1. Check Data Availability Gate AND Statistical Gate.
      2. IF BOTH PASS: Generate real plots (Histogram, QQ, Residuals vs Fitted).
      3. IF EITHER FAIL: Generate placeholder plots with "Data Insufficient" text.
    """
    gate_passed = check_gate_status()
    stat_passed = check_statistical_gate()
    outputs_dir = get_data_path() / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    
    plots = [
        ("residuals.png", plot_residual_histogram),
        ("qq_plot.png", plot_qq_plot),
        ("residuals_vs_fitted.png", plot_residuals_vs_fitted)
    ]

    if not (gate_passed and stat_passed):
        logger.info("Gate or Statistical Gate FAILED. Generating placeholder residual plots.")
        for name, _ in plots:
            path = outputs_dir / name
            generate_placeholder_plot(path, "Data Insufficient (N < 30)\n(Gate or Statistical Gate Failed)")
        return

    # Load residuals from analysis results
    results = load_analysis_results()
    if not results or results.get("status") != "PASS":
        logger.warning("Analysis results missing or failed. Generating placeholders.")
        for name, _ in plots:
            path = outputs_dir / name
            generate_placeholder_plot(path, "Analysis Results Missing")
        return

    # Extract residuals and fitted values
    # Assuming analysis_results.json contains 'residuals' and 'fitted' lists
    residuals_data = results.get("residuals")
    fitted_data = results.get("fitted")

    if not residuals_data or not fitted_data:
        logger.warning("Residuals or Fitted values missing in analysis_results.json.")
        for name, _ in plots:
            path = outputs_dir / name
            generate_placeholder_plot(path, "Residual Data Missing")
        return

    residuals = np.array(residuals_data)
    fitted = np.array(fitted_data)

    if len(residuals) < 2 or len(fitted) < 2:
        logger.warning("Insufficient data points for residual plots.")
        for name, _ in plots:
            path = outputs_dir / name
            generate_placeholder_plot(path, "Insufficient Data (N < 2)")
        return

    # Generate plots
    plot_residual_histogram(residuals, outputs_dir / "residuals.png")
    plot_qq_plot(residuals, outputs_dir / "qq_plot.png")
    plot_residuals_vs_fitted(fitted, residuals, outputs_dir / "residuals_vs_fitted.png")
    logger.info("Saved all residual diagnostic plots.")

def main():
    """Main entry point for Visualization (T032, T033)."""
    logger.info("Starting Visualization module...")
    logger.info("Checking gates and generating plots...")
    
    # T032: Scatter plots
    generate_correlation_scatter_plots()
    
    # T033: Residual diagnostics
    generate_residual_diagnostic_plots()
    
    logger.info("Visualization complete.")

if __name__ == "__main__":
    main()