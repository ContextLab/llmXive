"""
Stability Metrics Calculation Module.

Implements the calculation of stability metrics for Rotating Bose-Einstein Condensates:
- Vortex Density (vortices per unit area)
- Radial Variance (spread of density distribution)
- Structure Factor Sharpness (peakiness of the structure factor)

Dependencies:
- code/analysis/vortex_detector.py (for vortex detection)
- code/utils/io_helpers.py (for loading data)
- code/models/entities.py (for StabilityMetric dataclass)
- code/config/grid_config.py (for grid parameters)
"""

import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass

from models.entities import StabilityMetric
from analysis.vortex_detector import detect_vortices_phase_winding
from utils.io_helpers import load_array, load_simulation_snapshot
from config.grid_config import get_domain_size, get_grid_resolution
from utils.logger import get_logger

logger = get_logger(__name__)


def calculate_vortex_density(vortex_positions: List[Tuple[float, float]], 
                             grid_size: Tuple[int, int], 
                             domain_size: Tuple[float, float]) -> float:
    """
    Calculate vortex density (vortices per unit area).
    
    Args:
        vortex_positions: List of (x, y) coordinates of detected vortices.
        grid_size: Tuple (Nx, Ny) of grid dimensions.
        domain_size: Tuple (Lx, Ly) of physical domain size.
        
    Returns:
        Vortex density (number of vortices / area).
    """
    if not vortex_positions:
        return 0.0
    
    num_vortices = len(vortex_positions)
    area = domain_size[0] * domain_size[1]
    
    if area <= 0:
        logger.warning("Invalid domain size, returning 0 density")
        return 0.0
        
    return num_vortices / area


def calculate_radial_variance(density: np.ndarray, 
                              grid_size: Tuple[int, int], 
                              domain_size: Tuple[float, float]) -> float:
    """
    Calculate radial variance of the density distribution.
    
    This measures the spread of the density from the center of the trap.
    
    Args:
        density: 2D numpy array of density values |psi|^2.
        grid_size: Tuple (Nx, Ny) of grid dimensions.
        domain_size: Tuple (Lx, Ly) of physical domain size.
        
    Returns:
        Radial variance (mean squared distance from center weighted by density).
    """
    if density.size == 0:
        logger.warning("Empty density array, returning 0 variance")
        return 0.0
        
    Nx, Ny = grid_size
    Lx, Ly = domain_size
    
    # Create coordinate grids centered at (0, 0)
    x = np.linspace(-Lx/2, Lx/2, Nx)
    y = np.linspace(-Ly/2, Ly/2, Ny)
    X, Y = np.meshgrid(x, y, indexing='ij')
    
    # Calculate radial distance squared
    R2 = X**2 + Y**2
    
    # Normalize density to sum to 1 (probability distribution)
    total_mass = np.sum(density)
    if total_mass <= 0:
        logger.warning("Non-positive total mass, returning 0 variance")
        return 0.0
        
    prob_dist = density / total_mass
    
    # Calculate mean squared radius (variance)
    radial_variance = np.sum(R2 * prob_dist)
    
    return float(radial_variance)


def calculate_structure_factor_sharpness(density: np.ndarray, 
                                         grid_size: Tuple[int, int], 
                                         threshold: float = 0.1) -> float:
    """
    Calculate the sharpness of the structure factor peak.
    
    The structure factor is the Fourier transform of the density.
    Sharpness is defined as the ratio of the peak value to the mean of the 
    non-peak region (excluding the zero-frequency component).
    
    Args:
        density: 2D numpy array of density values.
        grid_size: Tuple (Nx, Ny) of grid dimensions.
        threshold: Threshold to exclude low values from the mean calculation.
        
    Returns:
        Structure factor sharpness ratio.
    """
    if density.size == 0:
        logger.warning("Empty density array, returning 0 sharpness")
        return 0.0
        
    # Compute 2D FFT
    fft_result = np.fft.fft2(density)
    structure_factor = np.abs(fft_result)**2
    
    # Shift zero-frequency component to center
    structure_factor_shifted = np.fft.fftshift(structure_factor)
    
    Nx, Ny = grid_size
    center_x, center_y = Nx // 2, Ny // 2
    
    # Define a small region around the center to exclude (peak region)
    exclude_radius = max(2, min(Nx, Ny) // 8)
    
    # Create mask for non-peak region
    Y_idx, X_idx = np.ogrid[:Ny, :Nx]
    dist_from_center = np.sqrt((X_idx - center_x)**2 + (Y_idx - center_y)**2)
    mask = dist_from_center > exclude_radius
    
    # Calculate peak value (at center)
    peak_value = structure_factor_shifted[center_y, center_x]
    
    # Calculate mean of non-peak region
    non_peak_values = structure_factor_shifted[mask]
    
    if len(non_peak_values) == 0:
        logger.warning("No non-peak values found, returning 0 sharpness")
        return 0.0
        
    mean_non_peak = np.mean(non_peak_values)
    
    if mean_non_peak <= 0:
        logger.warning("Non-positive mean non-peak value, returning 0 sharpness")
        return 0.0
        
    sharpness = peak_value / mean_non_peak
    
    return float(sharpness)


def calculate_all_metrics(snapshot_data: Dict[str, Any], 
                          grid_config: Optional[Dict[str, Any]] = None) -> StabilityMetric:
    """
    Calculate all stability metrics from a simulation snapshot.
    
    Args:
        snapshot_data: Dictionary containing 'density' (2D array) and optionally 'phase' (2D array).
        grid_config: Optional dictionary with grid configuration parameters. 
                     If None, defaults from grid_config.py are used.
                     
    Returns:
        StabilityMetric dataclass instance with calculated metrics.
    """
    logger.info("Calculating stability metrics from snapshot")
    
    if 'density' not in snapshot_data:
        raise ValueError("Snapshot data must contain 'density' key")
        
    density = snapshot_data['density']
    phase = snapshot_data.get('phase', None)
    
    # Get grid parameters
    if grid_config is None:
        grid_size = get_grid_resolution()
        domain_size = get_domain_size()
    else:
        grid_size = (grid_config.get('Nx', 64), grid_config.get('Ny', 64))
        domain_size = (grid_config.get('Lx', 20.0), grid_config.get('Ly', 20.0))
        
    # Detect vortices if phase is available
    vortex_positions = []
    if phase is not None:
        logger.debug("Detecting vortices from phase winding")
        try:
            vortex_positions = detect_vortices_phase_winding(phase, grid_size)
            logger.info(f"Detected {len(vortex_positions)} vortices")
        except Exception as e:
            logger.warning(f"Vortex detection failed: {e}. Setting vortex density to 0.")
    else:
        logger.warning("Phase data not available, skipping vortex detection")
        
    # Calculate metrics
    vortex_density = calculate_vortex_density(vortex_positions, grid_size, domain_size)
    radial_variance = calculate_radial_variance(density, grid_size, domain_size)
    structure_factor_sharpness = calculate_structure_factor_sharpness(density, grid_size)
    
    logger.info(f"Metrics calculated - Vortex Density: {vortex_density:.4f}, "
               f"Radial Variance: {radial_variance:.4f}, "
               f"Structure Factor Sharpness: {structure_factor_sharpness:.4f}")
               
    return StabilityMetric(
        vortex_density=vortex_density,
        radial_variance=radial_variance,
        structure_factor_sharpness=structure_factor_sharpness
    )


def process_snapshot_file(snapshot_path: str, 
                          output_path: Optional[str] = None) -> StabilityMetric:
    """
    Load a simulation snapshot from file and calculate stability metrics.
    
    Args:
        snapshot_path: Path to the snapshot file (.npy or .npz).
        output_path: Optional path to save the metrics as a JSON file.
                    
    Returns:
        StabilityMetric dataclass instance.
    """
    logger.info(f"Processing snapshot file: {snapshot_path}")
    
    # Load snapshot
    snapshot_data = load_simulation_snapshot(snapshot_path)
    
    # Calculate metrics
    metrics = calculate_all_metrics(snapshot_data)
    
    # Save if output path provided
    if output_path:
        logger.info(f"Saving metrics to: {output_path}")
        import json
        with open(output_path, 'w') as f:
            json.dump({
                'vortex_density': float(metrics.vortex_density),
                'radial_variance': float(metrics.radial_variance),
                'structure_factor_sharpness': float(metrics.structure_factor_sharpness)
            }, f, indent=2)
            
    return metrics


def main():
    """
    Main entry point for running metrics calculation on a provided snapshot.
    Usage: python -m analysis.metrics --snapshot <path> [--output <path>]
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Calculate stability metrics from simulation snapshot')
    parser.add_argument('--snapshot', required=True, help='Path to snapshot file (.npy or .npz)')
    parser.add_argument('--output', help='Optional path to save metrics JSON')
    parser.add_argument('--Nx', type=int, default=None, help='Grid size X (overrides default)')
    parser.add_argument('--Ny', type=int, default=None, help='Grid size Y (overrides default)')
    parser.add_argument('--Lx', type=float, default=None, help='Domain size X (overrides default)')
    parser.add_argument('--Ly', type=float, default=None, help='Domain size Y (overrides default)')
    
    args = parser.parse_args()
    
    grid_config = {}
    if args.Nx: grid_config['Nx'] = args.Nx
    if args.Ny: grid_config['Ny'] = args.Ny
    if args.Lx: grid_config['Lx'] = args.Lx
    if args.Ly: grid_config['Ly'] = args.Ly
    
    metrics = process_snapshot_file(args.snapshot, args.output)
    
    print(f"Stability Metrics:")
    print(f"  Vortex Density: {metrics.vortex_density:.6f}")
    print(f"  Radial Variance: {metrics.radial_variance:.6f}")
    print(f"  Structure Factor Sharpness: {metrics.structure_factor_sharpness:.6f}")
    
    return metrics


if __name__ == '__main__':
    main()