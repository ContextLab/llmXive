import json
import math
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm

# Ensure output directory exists
OUTPUT_DIR = Path("output/plots")
SUMMARY_FILE = Path("output/regression_summary.json")
PLOT_FILE = OUTPUT_DIR / "surface_plot.png"

def load_regression_summary(filepath: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the regression summary JSON containing coefficients and interaction terms.
    Falls back to the default path if none provided.
    """
    if filepath is None:
        filepath = SUMMARY_FILE

    if not filepath.exists():
        raise FileNotFoundError(f"Regression summary not found at {filepath}. "
                                "Run analyze_results.py first.")

    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_surface_grid(summary: Dict[str, Any], 
                          n_horizon: int = 20, 
                          n_density: int = 20) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate a 3D grid of points based on the regression model coefficients.
    
    The model is assumed to be a logistic regression with interaction:
    logit(p) = beta_0 + beta_1*horizon + beta_2*density + beta_3*(horizon*density)
    + spline terms for horizon.
    
    For visualization, we approximate the surface by evaluating the linear predictor
    on a grid and applying the sigmoid function. We simplify the spline component
    by using a linear approximation of the fitted spline basis for the grid generation,
    or by using the dominant linear interaction if splines are complex to reconstruct
    without the original basis matrix.
    
    To ensure a robust plot without the original design matrix, we will:
    1. Extract the interaction coefficient (beta_interaction).
    2. Extract the main effects (beta_horizon, beta_density).
    3. Create a grid of Horizon and Density.
    4. Compute logit = intercept + beta_h*H + beta_d*D + beta_int*(H*D).
    5. Apply sigmoid.
    
    Note: If the summary contains specific spline coefficients, they should be
    incorporated here. For this implementation, we assume the interaction term
    captures the primary curvature of interest for the "regime map".
    """
    # Extract coefficients from summary
    # Expected keys based on typical statsmodels output or custom summary
    # We look for 'interaction' or 'density:horizon' keys
    coeffs = summary.get('coefficients', {})
    
    # Heuristic to find the interaction term key
    interaction_key = None
    for key in coeffs:
        if 'interaction' in key.lower() or ('density' in key.lower() and 'horizon' in key.lower()):
            interaction_key = key
            break
    
    if interaction_key is None:
        # Fallback if naming convention differs
        if 'density:horizon' in coeffs:
            interaction_key = 'density:horizon'
        elif 'horizon:density' in coeffs:
            interaction_key = 'horizon:density'
        else:
            # If no interaction found, we cannot plot the interaction surface meaningfully.
            # We raise an error or assume 0 interaction (flat plane).
            raise ValueError("Could not find interaction term in regression summary. "
                             "Cannot generate 3D surface plot.")
    
    beta_int = float(coeffs[interaction_key])
    beta_h = float(coeffs.get('horizon', 0.0))
    beta_d = float(coeffs.get('density', 0.0))
    beta_0 = float(coeffs.get('intercept', 0.0))
    
    # Generate grid
    # Horizon range: typically 1 to T (e.g., 1 to 20 or 1 to 50)
    # Density range: typically 0.0 to 1.0 or 0.0 to 5.0 depending on entropy scale
    # We infer ranges from the summary metadata if available, else use defaults
    horizon_min = summary.get('horizon_min', 1)
    horizon_max = summary.get('horizon_max', 20)
    density_min = summary.get('density_min', 0.0)
    density_max = summary.get('density_max', 5.0)
    
    H = np.linspace(horizon_min, horizon_max, n_horizon)
    D = np.linspace(density_min, density_max, n_density)
    H_grid, D_grid = np.meshgrid(H, D)
    
    # Calculate logit
    # Linear predictor: beta_0 + beta_h*H + beta_d*D + beta_int*(H*D)
    # Note: This ignores the specific spline basis expansion for visualization simplicity.
    # A more accurate plot would require reconstructing the spline basis, which is
    # complex without the original training data. This linear-interaction approximation
    # highlights the "regime shift" caused by the interaction.
    logit = beta_0 + (beta_h * H_grid) + (beta_d * D_grid) + (beta_int * H_grid * D_grid)
    
    # Apply sigmoid to get probability (Success Rate)
    # Sigmoid: 1 / (1 + exp(-x))
    # Clamp to avoid overflow
    Z = 1.0 / (1.0 + np.exp(-np.clip(logit, -500, 500)))
    
    return H_grid, D_grid, Z

def plot_3d_surface(H_grid: np.ndarray, D_grid: np.ndarray, Z: np.ndarray, 
                    output_path: Path = PLOT_FILE) -> None:
    """
    Generate a 3D surface plot and save it to disk.
    Axes: 
      X: Masking Horizon
      Y: Semantic Density
      Z: Success Rate
    """
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # Plot surface
    surf = ax.plot_surface(H_grid, D_grid, Z, cmap=cm.viridis, 
                           edgecolor='none', alpha=0.9)
    
    # Labels
    ax.set_xlabel('Masking Horizon (Turns)')
    ax.set_ylabel('Semantic Density (Bits/Token)')
    ax.set_zlabel('Success Rate (Probability)')
    ax.set_title('Regime Map: Interaction of Masking Horizon and Semantic Density')
    
    # Add color bar
    cbar = fig.colorbar(surf, shrink=0.5, aspect=10)
    cbar.set_label('Success Rate')
    
    # Adjust view angle for better readability
    ax.view_init(elev=30, azim=45)
    
    # Save figure
    # Ensure file size is reasonable (PNG compression)
    plt.savefig(output_path, dpi=150, bbox_inches='tight', 
                format='png', optimize=True)
    plt.close(fig)
    
    # Verify file size
    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    if file_size_mb > 5.0:
        print(f"Warning: Generated plot is {file_size_mb:.2f} MB (> 5 MB limit). "
              "Consider reducing DPI or resolution in future runs.")

def main():
    """
    Main entry point to generate the 3D surface plot.
    """
    try:
        print("Loading regression summary...")
        summary = load_regression_summary()
        
        print("Generating surface grid...")
        H, D, Z = generate_surface_grid(summary)
        
        print(f"Plotting surface to {PLOT_FILE}...")
        plot_3d_surface(H, D, Z)
        
        print(f"Successfully generated 3D surface plot at {PLOT_FILE}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Configuration Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during visualization: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()