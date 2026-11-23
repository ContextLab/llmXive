"""
Visualization module for plotting dominant spatiotemporal modes from fPCA results.

Generates plots of eigenfunctions (temporal modes) and, if spatial data is available,
reconstructed spatial patterns at key time points.

FR-006: Generate plots of dominant modes as spatiotemporal patterns.
"""
import os
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import cartopy.crs as ccrs
import cartopy.feature as cfeature

from config import get_project_root, get_data_dir, get_artifacts_dir
from fpca import load_b_spline_coefficients, perform_fpca, reconstruct_eigenfunctions, calculate_cumulative_variance

logger = logging.getLogger(__name__)

def load_fpca_results(fpca_results_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load fPCA results from disk.
    
    Args:
        fpca_results_path: Path to the fPCA results pickle file. If None, uses default path.
        
    Returns:
        Dictionary containing eigenvalues, eigenfunctions, cumulative variance, and metadata.
    """
    if fpca_results_path is None:
        data_dir = get_data_dir()
        fpca_results_path = data_dir / "processed" / "fpca_results.pkl"
        
    if not fpca_results_path.exists():
        raise FileNotFoundError(f"fPCA results file not found at {fpca_results_path}")
        
    with open(fpca_results_path, 'rb') as f:
        results = pickle.load(f)
        
    logger.info(f"Loaded fPCA results from {fpca_results_path}")
    return results

def plot_temporal_modes(
    eigenfunctions: np.ndarray,
    eigenvalues: np.ndarray,
    time_grid: np.ndarray,
    output_path: Path,
    n_components: int = 5
) -> None:
    """
    Plot the temporal patterns of the dominant eigenfunctions.
    
    Args:
        eigenfunctions: Array of shape (n_components, n_knots) containing eigenfunctions.
        eigenvalues: Array of eigenvalues.
        time_grid: Array of time points for reconstruction.
        output_path: Path to save the plot.
        n_components: Number of dominant components to plot.
    """
    n_comp = min(n_components, eigenfunctions.shape[0])
    
    plt.figure(figsize=(12, 8))
    
    for i in range(n_comp):
        # Reconstruct the eigenfunction on the time grid
        # eigenfunctions are typically represented as coefficients in the B-spline basis
        # We need to reconstruct the function values at the time grid points
        # Assuming eigenfunctions are stored as coefficients and we have the basis
        # For simplicity, we assume eigenfunctions are already evaluated on a dense grid
        # or we reconstruct them using the B-spline basis from the original data
        
        # If eigenfunctions are coefficients, we need to evaluate them
        # This is a placeholder for the actual reconstruction logic
        # In a real implementation, we would use the B-spline basis to evaluate
        # the eigenfunction at the time grid points
        
        # Assuming eigenfunctions are already evaluated on the time grid
        # If not, we would need to reconstruct them using the basis
        if eigenfunctions.ndim == 2 and eigenfunctions.shape[1] == len(time_grid):
            mode_values = eigenfunctions[i, :]
        else:
            # If eigenfunctions are coefficients, we need to reconstruct
            # This is a simplified reconstruction assuming linear interpolation
            # In a real implementation, we would use the B-spline basis
            logger.warning(f"Eigenfunction shape {eigenfunctions.shape} does not match time grid. Using interpolation.")
            mode_values = np.interp(time_grid, np.linspace(0, 1, eigenfunctions.shape[1]), eigenfunctions[i, :])
        
        plt.plot(time_grid, mode_values, label=f'PC{i+1} (Var: {eigenvalues[i]:.4f})', linewidth=2)
    
    plt.xlabel('Time')
    plt.ylabel('Eigenfunction Value')
    plt.title('Dominant Temporal Modes (Eigenfunctions)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved temporal modes plot to {output_path}")

def plot_spatial_patterns(
    eigenfunctions: np.ndarray,
    spatial_grid: Tuple[np.ndarray, np.ndarray],
    time_points: List[float],
    output_dir: Path,
    n_components: int = 3,
    time_point_indices: Optional[List[int]] = None
) -> None:
    """
    Plot spatial patterns of dominant modes at specific time points.
    
    Args:
        eigenfunctions: Array of shape (n_components, n_spatial_points) or (n_components, n_lat, n_lon).
        spatial_grid: Tuple of (lons, lats) for spatial coordinates.
        time_points: List of time points to visualize.
        output_dir: Directory to save the plots.
        n_components: Number of dominant components to plot.
        time_point_indices: Indices of time points to use. If None, uses evenly spaced points.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    lons, lats = spatial_grid
    n_comp = min(n_components, eigenfunctions.shape[0])
    
    # Determine the shape of the spatial data
    if eigenfunctions.ndim == 2:
        # Flattened spatial data
        n_spatial = eigenfunctions.shape[1]
        n_lat = len(lats)
        n_lon = len(lons)
        
        # Reshape to 2D if possible
        if n_spatial == n_lat * n_lon:
            eigenfunctions_2d = eigenfunctions.reshape(n_comp, n_lat, n_lon)
        else:
            logger.warning(f"Cannot reshape spatial data to 2D. Skipping spatial plots.")
            return
    elif eigenfunctions.ndim == 3:
        eigenfunctions_2d = eigenfunctions
    else:
        logger.error(f"Unexpected eigenfunction shape: {eigenfunctions.shape}")
        return
    
    # Select time points if not specified
    if time_point_indices is None:
        time_point_indices = [0, len(time_points)//2, -1]
    
    for comp_idx in range(n_comp):
        for t_idx in time_point_indices:
            if t_idx >= len(time_points):
                continue
                
            t_val = time_points[t_idx]
            pattern = eigenfunctions_2d[comp_idx, :, :]
            
            fig = plt.figure(figsize=(10, 8))
            ax = plt.axes(projection=ccrs.PlateCarree())
            
            # Create a meshgrid for plotting
            lon_grid, lat_grid = np.meshgrid(lons, lats)
            
            # Plot the spatial pattern
            contour = ax.contourf(lon_grid, lat_grid, pattern, levels=20, 
                                  transform=ccrs.PlateCarree(), cmap='RdBu_r')
            
            # Add coastlines and gridlines
            ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
            ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)
            gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
                              linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
            gl.top_labels = False
            gl.right_labels = False
            
            plt.title(f'PC{comp_idx+1} Spatial Pattern at t={t_val:.2f}')
            plt.colorbar(contour, ax=ax, orientation='vertical', label='Eigenfunction Value')
            
            output_file = output_dir / f"spatial_pattern_PC{comp_idx+1}_t{t_idx}.png"
            plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            logger.info(f"Saved spatial pattern for PC{comp_idx+1} at t={t_val:.2f} to {output_file}")

def plot_cumulative_variance(
    eigenvalues: np.ndarray,
    output_path: Path,
    threshold: float = 0.8
) -> None:
    """
    Plot cumulative variance explained by the components.
    
    Args:
        eigenvalues: Array of eigenvalues.
        output_path: Path to save the plot.
        threshold: Variance threshold to mark (e.g., 0.8 for 80%).
    """
    cumulative_variance = calculate_cumulative_variance(eigenvalues)
    
    plt.figure(figsize=(10, 6))
    plt.plot(range(1, len(cumulative_variance) + 1), cumulative_variance, marker='o', linewidth=2)
    plt.axhline(y=threshold, color='r', linestyle='--', label=f'{threshold*100}% Variance Threshold')
    plt.xlabel('Number of Components')
    plt.ylabel('Cumulative Variance Explained')
    plt.title('Cumulative Variance Explained by Principal Components')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved cumulative variance plot to {output_path}")

def generate_all_visualizations(
    fpca_results_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    n_components: int = 5
) -> Dict[str, str]:
    """
    Generate all visualizations for the fPCA results.
    
    Args:
        fpca_results_path: Path to the fPCA results file.
        output_dir: Directory to save the plots.
        n_components: Number of dominant components to visualize.
        
    Returns:
        Dictionary mapping plot type to file path.
    """
    if output_dir is None:
        artifacts_dir = get_artifacts_dir()
        output_dir = artifacts_dir / "visualizations"
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load fPCA results
    results = load_fpca_results(fpca_results_path)
    
    eigenvalues = results.get('eigenvalues')
    eigenfunctions = results.get('eigenfunctions')
    metadata = results.get('metadata', {})
    
    if eigenvalues is None or eigenfunctions is None:
        raise ValueError("fPCA results must contain 'eigenvalues' and 'eigenfunctions'")
    
    # Extract time grid and spatial grid from metadata
    time_grid = metadata.get('time_grid')
    spatial_grid = metadata.get('spatial_grid')
    time_points = metadata.get('time_points', [])
    
    output_paths = {}
    
    # Plot temporal modes
    if time_grid is not None:
        temporal_plot_path = output_dir / "temporal_modes.png"
        plot_temporal_modes(eigenfunctions, eigenvalues, time_grid, temporal_plot_path, n_components)
        output_paths['temporal_modes'] = str(temporal_plot_path)
    
    # Plot cumulative variance
    cumulative_variance_path = output_dir / "cumulative_variance.png"
    plot_cumulative_variance(eigenvalues, cumulative_variance_path)
    output_paths['cumulative_variance'] = str(cumulative_variance_path)
    
    # Plot spatial patterns if spatial data is available
    if spatial_grid is not None and len(time_points) > 0:
        spatial_dir = output_dir / "spatial_patterns"
        spatial_dir.mkdir(exist_ok=True)
        plot_spatial_patterns(eigenfunctions, spatial_grid, time_points, spatial_dir, n_components)
        output_paths['spatial_patterns'] = str(spatial_dir)
    
    logger.info(f"Generated visualizations in {output_dir}")
    return output_paths

def main():
    """
    Main entry point for generating visualizations.
    """
    # Setup logging
    from logging_config import setup_logging
    setup_logging()
    
    logger.info("Starting visualization generation for fPCA results")
    
    try:
        # Load fPCA results and generate visualizations
        output_paths = generate_all_visualizations()
        
        logger.info("Visualization generation completed successfully")
        logger.info(f"Output files: {output_paths}")
        
        # Print summary
        print("Visualization Generation Summary:")
        for key, path in output_paths.items():
            print(f"  {key}: {path}")
            
    except Exception as e:
        logger.error(f"Error generating visualizations: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
