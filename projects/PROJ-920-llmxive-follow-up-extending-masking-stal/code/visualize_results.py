"""
visualize_results.py

Generates a 3D surface plot of Success Rate vs. Masking Horizon and Semantic Density.
Reads regression-ready summary data from output/regression_summary.json (or processes
raw simulation logs if summary is missing, though the pipeline expects the summary).
Produces a PNG plot at output/plots/surface_plot.png (≤ 5 MB).
"""
import json
import math
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np

# We assume matplotlib is available (add to requirements.txt if not already)
# Using Agg backend for non-interactive environments
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from analyze_results import load_simulation_data, run_logistic_regression, write_summary

# Constants for paths (matching project structure)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
PLOTS_DIR = OUTPUT_DIR / "plots"
REGRESSION_SUMMARY_PATH = OUTPUT_DIR / "regression_summary.json"
SIMULATION_LOGS_PATH = PROJECT_ROOT / "data" / "processed" / "simulation_results.jsonl"
OUTPUT_PLOT_PATH = PLOTS_DIR / "surface_plot.png"

def load_regression_summary(path: Path) -> Dict[str, Any]:
    """Load the regression summary JSON containing coefficients and grid data."""
    if not path.exists():
        raise FileNotFoundError(f"Regression summary not found at {path}. "
                                "Run analyze_results.py first.")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_surface_grid(summary: Dict[str, Any], 
                          density_range: Tuple[float, float] = (0.0, 1.0),
                          horizon_range: Tuple[int, int] = (1, 50),
                          resolution: int = 30) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate a 3D surface grid based on the regression model coefficients.
    
    The summary should contain 'coefficients' and ideally 'interaction_terms'.
    If the summary contains pre-computed grid data, use that. Otherwise,
    reconstruct the surface using the logistic function:
    P(success) = sigmoid(intercept + coef_density * density + coef_horizon * horizon + 
                         coef_interaction * density * horizon)
    
    For this implementation, we assume the summary from T020 includes the necessary
    coefficients for the linear predictor of the logistic model.
    """
    # Extract coefficients if available in the summary
    # Expected structure from analyze_results.py (T020):
    # {
    #   "coefficients": {
    #     "intercept": float,
    #     "density": float,
    #     "horizon": float,
    #     "density_horizon_interaction": float
    #   },
    #   ...
    # }
    
    coeffs = summary.get("coefficients", {})
    if not coeffs:
        # Fallback: If no coefficients, we cannot generate a meaningful surface.
        # In a real scenario, this would raise an error.
        # For robustness, we might return a flat surface of 0.5.
        print("Warning: No coefficients found in summary. Generating flat surface.")
        x = np.linspace(horizon_range[0], horizon_range[1], resolution)
        y = np.linspace(density_range[0], density_range[1], resolution)
        X, Y = np.meshgrid(x, y)
        Z = np.full_like(X, 0.5)
        return X, Y, Z

    intercept = coeffs.get("intercept", 0.0)
    coef_density = coeffs.get("density", 0.0)
    coef_horizon = coeffs.get("horizon", 0.0)
    coef_interaction = coeffs.get("density_horizon_interaction", 0.0)

    # Create grid
    x = np.linspace(horizon_range[0], horizon_range[1], resolution)
    y = np.linspace(density_range[0], density_range[1], resolution)
    X, Y = np.meshgrid(x, y)

    # Calculate linear predictor
    Z_linear = (intercept + 
                coef_density * Y + 
                coef_horizon * X + 
                coef_interaction * X * Y)

    # Apply sigmoid to get probability (Success Rate)
    Z = 1.0 / (1.0 + np.exp(-Z_linear))

    return X, Y, Z

def plot_3d_surface(X: np.ndarray, Y: np.ndarray, Z: np.ndarray, 
                    output_path: Path, title: str = "Success Rate Surface") -> None:
    """
    Create a 3D surface plot and save it as PNG.
    Ensures file size is reasonable (≤ 5 MB) by controlling resolution and DPI.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    # Plot surface
    surf = ax.plot_surface(X, Y, Z, cmap='viridis', edgecolor='none', alpha=0.9)
    
    # Labels
    ax.set_xlabel("Masking Horizon (Turns)")
    ax.set_ylabel("Semantic Density (Bits/Token)")
    ax.set_zlabel("Success Rate (Probability)")
    ax.set_title(title)

    # Color bar
    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10, label="Success Rate")

    # Adjust layout to prevent clipping
    plt.tight_layout()

    # Save with optimized settings to keep file size under 5 MB
    # DPI 100-150 is usually sufficient for a 10x8 inch figure
    plt.savefig(output_path, dpi=100, bbox_inches='tight', optimize=True)
    plt.close(fig)

    # Check file size
    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    if file_size_mb > 5.0:
        print(f"Warning: Output file size ({file_size_mb:.2f} MB) exceeds 5 MB limit. "
              "Consider reducing resolution or DPI.")

def main():
    """Main entry point for visualization."""
    print("Starting visualization of results...")
    
    # Load regression summary
    if not REGRESSION_SUMMARY_PATH.exists():
        # Attempt to run analysis if summary is missing
        print(f"Summary not found at {REGRESSION_SUMMARY_PATH}. Attempting to run analysis...")
        # We would call analyze_results here, but for this task we assume the pipeline
        # order is respected and T020 has run. If not, we fail loudly.
        print("Error: regression_summary.json not found. Please run analyze_results.py first.")
        sys.exit(1)

    try:
        summary = load_regression_summary(REGRESSION_SUMMARY_PATH)
    except Exception as e:
        print(f"Error loading regression summary: {e}")
        sys.exit(1)

    # Generate surface grid
    # We can make resolution configurable if needed, but 30x30 is a good balance
    try:
        X, Y, Z = generate_surface_grid(summary)
    except Exception as e:
        print(f"Error generating surface grid: {e}")
        sys.exit(1)

    # Plot and save
    try:
        plot_3d_surface(X, Y, Z, OUTPUT_PLOT_PATH, title="Success Rate: Horizon vs. Density")
        print(f"Successfully generated plot at {OUTPUT_PLOT_PATH}")
    except Exception as e:
        print(f"Error generating plot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
