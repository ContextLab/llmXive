import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, field
import os
import json
from models.entities import StabilityMetric

@dataclass
class MetricResult:
    vortex_density: float = 0.0
    radial_variance: float = 0.0
    structure_factor_sharpness: float = 0.0

def calculate_vortex_density(density_map: np.ndarray) -> float:
    """Calculates the vortex density from a density map.
    """
    return np.sum(density_map < 0.1) / density_map.size

def calculate_radial_variance(density_map: np.ndarray) -> float:
    """Calculates the radial variance of the density map.
    """
    center_x, center_y = density_map.shape[0] // 2, density_map.shape[1] // 2
    distances = np.sqrt((np.arange(density_map.shape[0]) - center_x)**2 + (np.arange(density_map.shape[1]) - center_y)**2)
    return np.var(density_map[distances < density_map.shape[0] / 2])

def calculate_structure_factor_sharpness(density_map: np.ndarray) -> float:
    """Calculates the sharpness of the structure factor.
    """
    # Placeholder implementation - replace with actual structure factor calculation
    return np.std(density_map)

def classify_metastability(vortex_density: float, condensate_density: float) -> str:
    """Classifies the stability of the condensate based on vortex density and condensate density.
    """
    if condensate_density < 0.3:
        return "unstable"
    elif vortex_density > 0.05:
        return "metastable"
    else:
        return "stable"

def calculate_false_positive_rate(predictions: List[str], ground_truth: List[str]) -> float:
    """Calculates the false positive rate.
    """
    fp = sum([1 for i in range(len(predictions)) if predictions[i] == 'stable' and ground_truth[i] != 'stable'])
    return fp / len(ground_truth) if len(ground_truth) > 0 else 0.0

def calculate_false_negative_rate(predictions: List[str], ground_truth: List[str]) -> float:
    """Calculates the false negative rate.
    """
    fn = sum([1 for i in range(len(predictions)) if predictions[i] != 'stable' and ground_truth[i] == 'stable'])
    return fn / len(ground_truth) if len(ground_truth) > 0 else 0.0

def process_snapshot_file(file_path: str) -> MetricResult:
    """Processes a snapshot file and calculates the stability metrics.
    """
    # Load the density map from the file
    density_map = np.load(file_path)

    # Calculate the metrics
    vortex_density = calculate_vortex_density(density_map)
    radial_variance = calculate_radial_variance(density_map)
    structure_factor_sharpness = calculate_structure_factor_sharpness(density_map)

    # Create the metric result
    metric_result = MetricResult(
        vortex_density=vortex_density,
        radial_variance=radial_variance,
        structure_factor_sharpness=structure_factor_sharpness
    )

    return metric_result

def calculate_all_metrics(density_map: np.ndarray) -> MetricResult:
    """Calculates all stability metrics for a given density map."""
    vortex_density = calculate_vortex_density(density_map)
    radial_variance = calculate_radial_variance(density_map)
    structure_factor_sharpness = calculate_structure_factor_sharpness(density_map)

    return MetricResult(
        vortex_density=vortex_density,
        radial_variance=radial_variance,
        structure_factor_sharpness=structure_factor_sharpness
    )

def main():
    """Main function for testing."""
    # Example usage
    density_map = np.random.rand(64, 64)
    metric_result = calculate_all_metrics(density_map)
    print(f"Vortex Density: {metric_result.vortex_density}")
    print(f"Radial Variance: {metric_result.radial_variance}")
    print(f"Structure Factor Sharpness: {metric_result.structure_factor_sharpness}")
