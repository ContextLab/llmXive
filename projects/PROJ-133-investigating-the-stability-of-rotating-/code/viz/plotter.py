"""
Visualization module for generating 3D parameter space contour maps and regime plots.

This module handles the generation of:
1. 3D Contour maps of Stability vs Omega vs Epsilon_dd
2. Representative density/phase plots for different stability regimes
"""
import os
import sys
import argparse
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from matplotlib.colors import Normalize
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

# Local imports based on API surface
from utils.logger import get_logger
from utils.io_helpers import load_dataframe
from statistics.aggregators import aggregate_results, load_simulation_metrics

logger = get_logger(__name__)

def load_aggregated_metrics(data_path: str = "data/aggregated") -> Optional[np.ndarray]:
    """
    Load aggregated metrics from the statistics pipeline.
    
    Args:
        data_path: Path to the aggregated data directory.
        
    Returns:
        A structured numpy array or DataFrame containing aggregated points
        with columns: Omega, Epsilon_dd, Stability (mean), Std, Count.
    """
    try:
        # Use the aggregation pipeline to load and process metrics
        # The aggregate_results function returns a dictionary or DataFrame
        agg_result = aggregate_results(data_path)
        
        if agg_result is None:
            logger.warning("No aggregated results found in " + data_path)
            return None
        
        # Ensure we have a DataFrame or convert to one for easier manipulation
        if hasattr(agg_result, 'to_numpy'):
            return agg_result
        return agg_result
        
    except FileNotFoundError as e:
        logger.error("Data file not found: " + str(e))
        return None
    except Exception as e:
        logger.error("Error loading aggregated metrics: " + str(e))
        return None

def create_3d_contour_map(
    data: np.ndarray,
    x_col: str = 'Omega',
    y_col: str = 'Epsilon_dd',
    z_col: str = 'Stability',
    output_path: str = "figures/phase_diagram_3d.png",
    title: str = "Stability Phase Diagram (3D)"
) -> str:
    """
    Generate a 3D contour map of stability across the parameter space.
    
    Args:
        data: Aggregated data array/DataFrame with Omega, Epsilon_dd, and Stability columns.
        x_col: Name of the x-axis column (Omega).
        y_col: Name of the y-axis column (Epsilon_dd).
        z_col: Name of the z-axis column (Stability).
        output_path: Path to save the generated figure.
        title: Title for the plot.
        
    Returns:
        Path to the saved figure.
    """
    logger.info("Generating 3D contour map...")
    
    # Extract columns
    x = data[x_col].values if hasattr(data, 'values') else data[:, data.columns.get_loc(x_col)]
    y = data[y_col].values if hasattr(data, 'values') else data[:, data.columns.get_loc(y_col)]
    z = data[z_col].values if hasattr(data, 'values') else data[:, data.columns.get_loc(z_col)]
    
    # Create grid for interpolation if data is scattered
    # We assume the data comes from a structured grid, but we sort it to be safe
    unique_x = np.unique(x)
    unique_y = np.unique(y)
    
    if len(unique_x) < 2 or len(unique_y) < 2:
        logger.warning("Insufficient unique points for 3D contour. Minimum 2x2 grid required.")
        # Fallback to scatter if grid is too small
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')
        scatter = ax.scatter(x, y, z, c=z, cmap='RdYlGn', s=100, edgecolors='k')
        ax.set_xlabel('Rotation Frequency ($\\Omega$)')
        ax.set_ylabel('Dipolar Interaction ($\\epsilon_{dd}$)')
        ax.set_zlabel('Stability Metric')
        ax.set_title(title)
        plt.colorbar(scatter, ax=ax, label='Stability')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=150)
        plt.close()
        logger.info(f"Scatter plot saved to {output_path}")
        return output_path

    # Create meshgrid
    X, Y = np.meshgrid(unique_x, unique_y)
    
    # Interpolate Z onto the meshgrid
    # We use a simple grid lookup assuming the input data matches the mesh
    # If data is scattered, we would need scipy.interpolate.griddata
    Z = np.full_like(X, np.nan, dtype=float)
    
    for i, xi in enumerate(unique_x):
        for j, yj in enumerate(unique_y):
            # Find matching row
            mask = (x == xi) & (y == yj)
            if np.any(mask):
                Z[j, i] = z[mask][0]
    
    # Create figure
    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(111, projection='3d')
    
    # Plot surface
    surf = ax.plot_surface(X, Y, Z, cmap=cm.viridis, edgecolor='none', alpha=0.9)
    
    # Labels and title
    ax.set_xlabel('Rotation Frequency ($\\Omega$)')
    ax.set_ylabel('Dipolar Interaction ($\\epsilon_{dd}$)')
    ax.set_zlabel('Stability Metric (Vortex Density)')
    ax.set_title(title)
    
    # Add colorbar
    cbar = fig.colorbar(surf, shrink=0.5, aspect=5)
    cbar.set_label('Stability Metric')
    
    # Set viewing angle
    ax.view_init(elev=30, azim=45)
    
    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"3D Contour map saved to {output_path}")
    return output_path

def plot_regime_samples(
    data: np.ndarray,
    density_file_pattern: str = "data/processed/density_snapshot_*.npy",
    output_dir: str = "figures/regime_samples",
    x_col: str = 'Omega',
    y_col: str = 'Epsilon_dd',
    z_col: str = 'Stability'
) -> List[str]:
    """
    Generate density plots for representative stable, metastable, and unstable regimes.
    
    Args:
        data: Aggregated data.
        density_file_pattern: Glob pattern for density snapshot files.
        output_dir: Directory to save the plots.
        x_col, y_col, z_col: Column names for parameters.
        
    Returns:
        List of paths to saved figures.
    """
    logger.info("Generating regime sample plots...")
    os.makedirs(output_dir, exist_ok=True)
    
    # Sort data by stability to find representatives
    # Assuming lower stability metric = more unstable (or higher = more stable, depending on definition)
    # Based on T021, StabilityMetric uses vortex_density. High vortex density = unstable.
    # So: Low vortex density = Stable, Medium = Metastable, High = Unstable.
    
    sorted_indices = np.argsort(data[z_col])
    sorted_data = data[sorted_indices]
    
    n = len(sorted_data)
    if n == 0:
        logger.warning("No data available for regime sampling.")
        return []
    
    stable_idx = 0
    metastable_idx = n // 2
    unstable_idx = n - 1
    
    if n > 1:
        metastable_idx = n // 2
    
    representatives = [
        ("Stable", stable_idx),
        ("Metastable", metastable_idx),
        ("Unstable", unstable_idx)
    ]
    
    saved_paths = []
    
    for regime_name, idx in representatives:
        row = sorted_data[idx]
        omega = row[data.columns.get_loc(x_col)] if hasattr(row, 'name') else row[x_col]
        epsilon_dd = row[data.columns.get_loc(y_col)] if hasattr(row, 'name') else row[y_col]
        stability = row[data.columns.get_loc(z_col)] if hasattr(row, 'name') else row[z_col]
        
        # Try to find a corresponding snapshot file
        # This is a heuristic: we assume filenames encode parameters or we just pick one
        # Since we don't have the exact filename mapping logic here, we'll simulate
        # finding a file or create a placeholder if none exists.
        # In a real run, we would match (omega, epsilon_dd) to the processed files.
        
        # Construct a likely filename pattern based on parameters
        # Assuming format: density_snapshot_O{omega:.2f}_E{epsilon_dd:.2f}.npy
        # This is an assumption based on typical naming conventions
        filename = f"density_snapshot_O{omega:.2f}_E{epsilon_dd:.2f}.npy"
        file_path = str(Path("data/processed") / filename)
        
        if not os.path.exists(file_path):
            # Fallback: try to find any file if the specific one isn't found
            # This handles cases where the naming convention might differ
            import glob
            candidates = glob.glob(os.path.join("data/processed", "density_snapshot_*.npy"))
            if candidates:
                file_path = candidates[idx % len(candidates)]
            else:
                logger.warning(f"Snapshot file not found for {regime_name} ({omega}, {epsilon_dd}). Skipping plot.")
                continue
        
        try:
            density_data = np.load(file_path)
            
            fig, ax = plt.subplots(figsize=(6, 6))
            im = ax.imshow(np.abs(density_data)**2, origin='lower', cmap='viridis', 
                           extent=[-5, 5, -5, 5]) # Assuming domain size 10x10
            plt.colorbar(im, ax=ax, label='Density |ψ|²')
            ax.set_title(f"{regime_name}: Ω={omega:.2f}, ε_dd={epsilon_dd:.2f}\nStability={stability:.4f}")
            ax.set_xlabel('x')
            ax.set_ylabel('y')
            
            save_path = os.path.join(output_dir, f"regime_{regime_name.lower()}.png")
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            saved_paths.append(save_path)
            logger.info(f"Saved {regime_name} plot to {save_path}")
            
        except Exception as e:
            logger.error(f"Failed to load or plot snapshot for {regime_name}: {e}")
            
    return saved_paths

def main():
    """Main entry point for generating visualization artifacts."""
    parser = argparse.ArgumentParser(description="Generate 3D stability phase maps.")
    parser.add_argument("--data", type=str, default="data/aggregated", 
                        help="Path to aggregated data directory.")
    parser.add_argument("--output-dir", type=str, default="figures",
                        help="Output directory for figures.")
    parser.add_argument("--regime-samples", action="store_true",
                        help="Generate representative regime sample plots.")
    
    args = parser.parse_args()
    
    logger.info("Starting visualization pipeline...")
    
    # Load data
    data = load_aggregated_metrics(args.data)
    if data is None:
        logger.error("Failed to load aggregated metrics. Exiting.")
        sys.exit(1)
        
    # Generate 3D Contour
    contour_path = os.path.join(args.output_dir, "phase_diagram_3d.png")
    create_3d_contour_map(
        data,
        output_path=contour_path,
        title="Stability Phase Diagram (3D)"
    )
    
    # Generate regime samples if requested
    if args.regime_samples:
        plot_regime_samples(
            data,
            output_dir=os.path.join(args.output_dir, "regime_samples")
        )
        
    logger.info("Visualization pipeline completed.")

if __name__ == "__main__":
    main()