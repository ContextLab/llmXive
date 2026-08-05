import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, field
import os
import json

from models.entities import StabilityMetric
from analysis.vortex_detector import detect_vortices_phase_winding
from utils.io_helpers import load_array, load_simulation_snapshot
from utils.logger import get_logger

logger = get_logger(__name__)

# Metastability threshold constants
METASTABLE_VORTEX_DROP_THRESHOLD = 0.30  # 30% drop defines metastable boundary

def calculate_vortex_density(vortices: List[Tuple[float, float]], area: float) -> float:
    """
    Calculate vortex density (vortices per unit area).
    
    Args:
        vortices: List of (x, y) coordinates of detected vortices.
        area: Total area of the simulation domain.
        
    Returns:
        Vortex density (float). Returns 0.0 if area is zero or no vortices.
    """
    if area <= 0.0:
        logger.warning("Area is zero or negative, returning 0.0 for vortex density.")
        return 0.0
    if not vortices:
        return 0.0
    return len(vortices) / area

def calculate_radial_variance(density_grid: np.ndarray, coords: np.ndarray) -> float:
    """
    Calculate radial variance of the density distribution.
    
    Measures how spread out the density is radially from the center.
    
    Args:
        density_grid: 2D array of density values.
        coords: 2D array of coordinates (x, y) for each grid point.
        
    Returns:
        Radial variance (float).
    """
    if density_grid.size == 0:
        return 0.0
    
    # Calculate center of mass
    total_mass = np.sum(density_grid)
    if total_mass == 0:
        return 0.0
        
    x_coords = coords[:, 0]
    y_coords = coords[:, 1]
    
    cx = np.sum(density_grid * x_coords) / total_mass
    cy = np.sum(density_grid * y_coords) / total_mass
    
    # Calculate radial distance from center of mass for each point
    r_sq = (x_coords - cx)**2 + (y_coords - cy)**2
    
    # Weighted variance
    variance = np.sum(density_grid * r_sq) / total_mass
    return variance

def calculate_structure_factor_sharpness(density_grid: np.ndarray) -> float:
    """
    Calculate the sharpness of the structure factor.
    
    This is a proxy for order: higher sharpness indicates more structured
    vortex arrangements (e.g., lattice-like).
    
    Args:
        density_grid: 2D array of density values.
        
    Returns:
        Sharpness metric (float).
    """
    if density_grid.size == 0:
        return 0.0
        
    # Compute 2D FFT
    fft_result = np.fft.fft2(density_grid)
    spectrum = np.abs(fft_result)**2
    
    # Shift zero frequency to center
    spectrum_shifted = np.fft.fftshift(spectrum)
    
    # Calculate sharpness as the ratio of peak intensity to mean intensity
    # excluding the central peak (zero frequency)
    h, w = spectrum_shifted.shape
    center_h, center_w = h // 2, w // 2
    
    # Mask out the central region to avoid DC component dominance
    mask = np.ones((h, w), dtype=bool)
    mask[center_h-5:center_h+5, center_w-5:center_w+5] = False
    
    if np.sum(mask) == 0:
        return 0.0
        
    peak_intensity = np.max(spectrum_shifted)
    mean_intensity = np.mean(spectrum_shifted[mask])
    
    if mean_intensity == 0:
        return 0.0
        
    return peak_intensity / mean_intensity

def calculate_all_metrics(
    density_grid: np.ndarray,
    phase_grid: np.ndarray,
    coords: np.ndarray,
    area: float
) -> Dict[str, float]:
    """
    Calculate all stability metrics for a given snapshot.
    
    Args:
        density_grid: 2D array of density values.
        phase_grid: 2D array of phase values.
        coords: 2D array of coordinates (x, y) for each grid point.
        area: Total area of the simulation domain.
        
    Returns:
        Dictionary containing all calculated metrics.
    """
    # Detect vortices
    vortices = detect_vortices_phase_winding(phase_grid, coords)
    
    # Calculate metrics
    vortex_density = calculate_vortex_density(vortices, area)
    radial_variance = calculate_radial_variance(density_grid, coords)
    structure_sharpness = calculate_structure_factor_sharpness(density_grid)
    
    return {
        'vortex_density': vortex_density,
        'radial_variance': radial_variance,
        'structure_factor_sharpness': structure_sharpness,
        'vortex_count': len(vortices)
    }

def process_snapshot_file(
    snapshot_path: str,
    initial_vortex_count: Optional[int] = None
) -> StabilityMetric:
    """
    Process a single simulation snapshot file and calculate stability metrics.
    
    Args:
        snapshot_path: Path to the snapshot file (.npy or .csv).
        initial_vortex_count: Optional count of vortices at t=0 for metastability analysis.
        
    Returns:
        StabilityMetric dataclass with calculated metrics.
    """
    logger.info(f"Processing snapshot: {snapshot_path}")
    
    # Load data
    try:
        snapshot_data = load_simulation_snapshot(snapshot_path)
        density_grid = snapshot_data['density']
        phase_grid = snapshot_data['phase']
        coords = snapshot_data['coords']
        area = snapshot_data.get('area', 1.0)
    except Exception as e:
        logger.error(f"Failed to load snapshot {snapshot_path}: {e}")
        raise
    
    # Calculate metrics
    metrics_dict = calculate_all_metrics(density_grid, phase_grid, coords, area)
    
    # Handle metastability boundary logic
    current_vortex_count = metrics_dict['vortex_count']
    metastable_drop_percent = None
    is_metastable = False
    
    if initial_vortex_count is not None and initial_vortex_count > 0:
        if current_vortex_count < initial_vortex_count:
            drop_ratio = (initial_vortex_count - current_vortex_count) / initial_vortex_count
            metastable_drop_percent = drop_ratio * 100.0
            
            # Check if drop > 30%
            if drop_ratio > METASTABLE_VORTEX_DROP_THRESHOLD:
                is_metastable = True
                logger.info(
                    f"Metastable boundary detected: {drop_ratio*100:.2f}% vortex loss "
                    f"(threshold: {METASTABLE_VORTEX_DROP_THRESHOLD*100:.0f}%)"
                )
    
    # Create StabilityMetric object
    metric = StabilityMetric(
        vortex_density=metrics_dict['vortex_density'],
        radial_variance=metrics_dict['radial_variance'],
        structure_factor_sharpness=metrics_dict['structure_factor_sharpness'],
        vortex_count=current_vortex_count,
        is_metastable=is_metastable,
        metastable_drop_percent=metastable_drop_percent
    )
    
    return metric

def main():
    """
    Main entry point for metrics calculation script.
    Processes a snapshot file and prints metrics to stdout.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Calculate stability metrics from snapshot")
    parser.add_argument("snapshot_path", help="Path to snapshot file")
    parser.add_argument("--initial-vortices", type=int, default=None,
                      help="Initial vortex count for metastability analysis")
    parser.add_argument("--output", type=str, default=None,
                      help="Output JSON file path")
    
    args = parser.parse_args()
    
    try:
        metric = process_snapshot_file(args.snapshot_path, args.initial_vortices)
        
        # Convert to dict for output
        result = {
            'vortex_density': metric.vortex_density,
            'radial_variance': metric.radial_variance,
            'structure_factor_sharpness': metric.structure_factor_sharpness,
            'vortex_count': metric.vortex_count,
            'is_metastable': metric.is_metastable,
            'metastable_drop_percent': metric.metastable_drop_percent
        }
        
        print(json.dumps(result, indent=2))
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            logger.info(f"Results saved to {args.output}")
            
    except Exception as e:
        logger.error(f"Error processing snapshot: {e}")
        raise

if __name__ == "__main__":
    main()