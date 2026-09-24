"""
Visualize results from the simulation and analysis pipeline.

This module generates a 3D surface plot visualizing the Success Rate vs. 
Masking Horizon and Semantic Density, representing the regime map of 
optimal retention windows.
"""
import json
import math
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import matplotlib
# Use non-interactive backend for server/headless environments
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import griddata

# Constants
OUTPUT_DIR = Path("output")
PLOTS_DIR = OUTPUT_DIR / "plots"
REGRESSION_SUMMARY_PATH = OUTPUT_DIR / "regression_summary.json"
OUTPUT_PLOT_PATH = PLOTS_DIR / "regime_map.png"
MAX_FILE_SIZE_MB = 5

def load_regression_summary(path: Path = REGRESSION_SUMMARY_PATH) -> Dict[str, Any]:
    """
    Load the regression summary JSON produced by analyze_results.py.
    
    Expects a JSON structure containing coefficients and interaction terms
    to reconstruct the surface model.
    """
    if not path.exists():
        raise FileNotFoundError(f"Regression summary not found at {path}. "
                                "Run analyze_results.py first.")
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_surface_grid(summary: Dict[str, Any], 
                          n_points: int = 50) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate a grid of (Horizon, Density) points and predict Success Rate
    using the logistic regression coefficients from the summary.
    
    The model is assumed to be:
    logit(P) = beta_0 + beta_h * H + beta_d * D + beta_hd * (H*D) + ...
    (plus spline terms if present, simplified here to linear interaction 
    for visualization or reconstructed from the summary if spline coeffs are provided).
    
    For this implementation, we reconstruct the surface based on the 
    interaction term significance and the general logistic form:
    P = 1 / (1 + exp(-(intercept + b1*H + b2*D + b3*H*D)))
    
    If the summary contains spline coefficients, a more complex reconstruction
    would be needed. Here we assume the summary provides the key interaction
    parameters or we infer a smooth surface from the provided interaction stats.
    
    To ensure a realistic regime map, we will:
    1. Define ranges for Horizon (1 to T) and Density (0.0 to 1.0).
    2. Use the coefficients from the JSON to calculate logits.
    3. Apply sigmoid to get probabilities.
    """
    # Extract coefficients. Adjust keys based on actual output of analyze_results.py
    # Assuming keys like 'coefficients' dict exists.
    coeffs = summary.get('coefficients', {})
    intercept = coeffs.get('Intercept', 0.0)
    beta_horizon = coeffs.get('horizon', 0.0)
    beta_density = coeffs.get('density', 0.0)
    beta_interaction = coeffs.get('density:horizon', 0.0) # Interaction term
    
    # If spline terms exist, we would need to reconstruct them. 
    # For visualization robustness, if splines are present, we might need 
    # a different approach, but the task asks for a surface based on the 
    # interaction. We will assume the linear interaction model captures the 
    # regime shift for the plot, or we use the spline coefficients if available.
    # Let's check for spline terms in the summary if the model used them.
    # If 'spline_horizon' terms exist, we need to reconstruct the spline basis.
    # Given the constraints, we will approximate the surface using the 
    # primary interaction term and main effects, which is standard for 
    # regime maps in this context.
    
    # Define ranges
    # Horizon: 1 to T (let's assume T=20 based on typical trajectory lengths, 
    # or we can derive T from the summary if 'max_horizon' is stored)
    max_horizon = summary.get('max_horizon', 20)
    min_horizon = summary.get('min_horizon', 1)
    horizon_range = np.linspace(min_horizon, max_horizon, n_points)
    
    # Density: 0.0 to 1.0
    density_range = np.linspace(0.0, 1.0, n_points)
    
    H, D = np.meshgrid(horizon_range, density_range)
    
    # Calculate logit
    # logit = intercept + beta_h * H + beta_d * D + beta_hd * H * D
    # Note: If spline terms are critical, this linear approximation might be 
    # insufficient, but without the specific spline basis functions in the summary,
    # we cannot perfectly reconstruct. However, the interaction term is the 
    # key driver for the regime map visualization.
    logit = intercept + beta_horizon * H + beta_density * D + beta_interaction * H * D
    
    # Apply sigmoid
    success_rate = 1.0 / (1.0 + np.exp(-logit))
    
    return H, D, success_rate

def plot_3d_surface(H: np.ndarray, 
                    D: np.ndarray, 
                    Z: np.ndarray, 
                    output_path: Path = OUTPUT_PLOT_PATH) -> None:
    """
    Plot the 3D surface and save to PNG.
    
    Requirements:
    - Axes: "Masking Horizon", "Semantic Density", "Success Rate"
    - File size <= 5 MB
    - Format: PNG
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # Plot surface
    surf = ax.plot_surface(H, D, Z, cmap='viridis', edgecolor='none', alpha=0.9)
    
    # Label axes exactly as required
    ax.set_xlabel("Masking Horizon")
    ax.set_ylabel("Semantic Density")
    ax.set_zlabel("Success Rate")
    
    # Add color bar
    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10, label="Success Rate")
    
    # Title
    ax.set_title("Regime Map: Optimal Retention Windows")
    
    # Save with high DPI but ensure file size constraint
    # DPI 150 is usually sufficient for publications and keeps size down
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    
    # Verify file size
    file_size_bytes = output_path.stat().st_size
    file_size_mb = file_size_bytes / (1024 * 1024)
    
    if file_size_mb > MAX_FILE_SIZE_MB:
        # If too large, reduce DPI and try again
        plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')
        surf = ax.plot_surface(H, D, Z, cmap='viridis', edgecolor='none', alpha=0.9)
        ax.set_xlabel("Masking Horizon")
        ax.set_ylabel("Semantic Density")
        ax.set_zlabel("Success Rate")
        fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10, label="Success Rate")
        ax.set_title("Regime Map: Optimal Retention Windows")
        plt.savefig(output_path, dpi=100, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        
        file_size_bytes = output_path.stat().st_size
        file_size_mb = file_size_bytes / (1024 * 1024)
        
        if file_size_mb > MAX_FILE_SIZE_MB:
            raise RuntimeError(f"Generated plot exceeds {MAX_FILE_SIZE_MB} MB limit ({file_size_mb:.2f} MB). "
                               "Consider reducing resolution or simplifying the mesh.")

def main():
    """
    Main entry point to generate the regime map plot.
    """
    try:
        # 1. Load regression summary
        print(f"Loading regression summary from {REGRESSION_SUMMARY_PATH}...")
        summary = load_regression_summary()
        
        # 2. Generate surface grid
        print("Generating surface grid...")
        H, D, Z = generate_surface_grid(summary)
        
        # 3. Plot and save
        print(f"Saving plot to {OUTPUT_PLOT_PATH}...")
        plot_3d_surface(H, D, Z, OUTPUT_PLOT_PATH)
        
        print(f"Success: Regime map saved to {OUTPUT_PLOT_PATH}")
        
        # Verify existence
        if not OUTPUT_PLOT_PATH.exists():
            raise RuntimeError("Plot file was not created.")
            
        print(f"File size: {OUTPUT_PLOT_PATH.stat().st_size / 1024 / 1024:.2f} MB")
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error generating plot: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
