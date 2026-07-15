import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
import logging
import csv
import os

from thermal_solver import solve_kirchhoff_heat_flow, build_edge_resistances
import networkx as nx

logger = logging.getLogger(__name__)

# Sensitivity sweep parameters
SENSITIVITY_SCALE_RANGE = [0.9, 1.0, 1.1]  # 10% variation range
NUM_SWEEPS = 5  # Number of Monte Carlo samples per scale factor

def run_sensitivity_sweep(G: nx.Graph, edge_resistances: Dict, k_bulk: float,
                          diameter: float, length: float) -> Dict[str, float]:
    """
    Perform a sensitivity analysis by sweeping scaling factors on edge resistances.
    
    Args:
        G: The nanowire network graph
        edge_resistances: Dictionary of edge resistances
        k_bulk: Bulk thermal conductivity of the material
        diameter: Wire diameter
        length: Wire length
    
    Returns:
        Dictionary containing sensitivity metrics:
        - deviation: Normalized deviation (max-min)/mean
        - min_conductivity: Minimum conductivity observed
        - max_conductivity: Maximum conductivity observed
        - std_deviation: Standard deviation of conductivities
    """
    if not edge_resistances or not nx.is_connected(G):
        return {
            'deviation': 0.0,
            'min_conductivity': 0.0,
            'max_conductivity': 0.0,
            'std_deviation': 0.0
        }

    conductivities = []
    
    # Perform Monte Carlo sweep
    for scale_factor in SENSITIVITY_SCALE_RANGE:
        for _ in range(NUM_SWEEPS):
            # Perturb resistances
            perturbed_resistances = {}
            for edge, res in edge_resistances.items():
                # Add small random noise around the scale factor
                noise = np.random.normal(0, 0.02) # 2% noise
                perturbed_resistances[edge] = res * scale_factor * (1.0 + noise)
            
            try:
                cond = solve_kirchhoff_heat_flow(G, perturbed_resistances, diameter, length, k_bulk)
                if cond > 0:
                    conductivities.append(cond)
            except Exception as e:
                logger.warning(f"Solver failed during sensitivity sweep: {e}")
                continue

    if not conductivities:
        return {
            'deviation': 0.0,
            'min_conductivity': 0.0,
            'max_conductivity': 0.0,
            'std_deviation': 0.0
        }

    conductivities = np.array(conductivities)
    mean_cond = np.mean(conductivities)
    std_cond = np.std(conductivities)
    min_cond = np.min(conductivities)
    max_cond = np.max(conductivities)
    
    # Calculate normalized deviation (relative to mean)
    deviation = (max_cond - min_cond) / mean_cond if mean_cond > 0 else 0.0
    
    logger.debug(f"Sensitivity sweep: mean={mean_cond:.4f}, std={std_cond:.4f}, deviation={deviation:.4f}")
    
    return {
        'deviation': deviation,
        'min_conductivity': float(min_cond),
        'max_conductivity': float(max_cond),
        'std_deviation': float(std_cond)
    }

def calculate_deviation_report(conductivities: List[float]) -> Dict[str, float]:
    """
    Calculate a deviation report from a list of conductivity values.
    
    Returns:
        Dictionary with mean, std, min, max, and deviation_percent.
    """
    if not conductivities:
        return {
            'mean': 0.0,
            'std': 0.0,
            'min': 0.0,
            'max': 0.0,
            'deviation_percent': 0.0
        }

    arr = np.array(conductivities)
    mean_val = float(np.mean(arr))
    std_val = float(np.std(arr))
    min_val = float(np.min(arr))
    max_val = float(np.max(arr))
    
    deviation_percent = ((max_val - min_val) / mean_val * 100) if mean_val > 0 else 0.0
    
    return {
        'mean': mean_val,
        'std': std_val,
        'min': min_val,
        'max': max_val,
        'deviation_percent': deviation_percent
    }

def report_sensitivity_results(metrics: Dict[str, float], threshold: float = 0.10) -> str:
    """
    Generate a human-readable report of sensitivity results.
    
    Args:
        metrics: Output from run_sensitivity_sweep
        threshold: The acceptable deviation threshold (default 10%)
    
    Returns:
        Formatted string report
    """
    deviation = metrics.get('deviation', 0.0)
    status = "PASS" if deviation <= threshold else "FAIL"
    
    report = (
        f"Sensitivity Analysis Report:\n"
        f"  Deviation: {deviation:.4f} ({deviation*100:.2f}%)\n"
        f"  Threshold: {threshold*100:.2f}%\n"
        f"  Status: {status}\n"
        f"  Min Conductivity: {metrics.get('min_conductivity', 0):.4f}\n"
        f"  Max Conductivity: {metrics.get('max_conductivity', 0):.4f}\n"
        f"  Std Deviation: {metrics.get('std_deviation', 0):.4f}\n"
    )
    
    return report

def analyze_sensitivity(G: nx.Graph, edge_resistances: Dict, k_bulk: float,
                        diameter: float, length: float) -> Dict[str, Any]:
    """
    Full sensitivity analysis wrapper.
    
    Returns a dictionary with all metrics and the formatted report.
    """
    metrics = run_sensitivity_sweep(G, edge_resistances, k_bulk, diameter, length)
    report = report_sensitivity_results(metrics)
    
    return {
        'metrics': metrics,
        'report': report,
        'passed': metrics['deviation'] <= 0.10
    }
