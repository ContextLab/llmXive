import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
import logging
import csv
import os

from config import SimulationConfig
from generate_networks import generate_nanowire_network, calculate_average_degree
from thermal_solver import assign_thermal_resistance, solve_kirchhoff_heat_flow
from material_db import get_material_conductivity

def run_sensitivity_sweep(config: SimulationConfig, factor_range: List[float]) -> List[Dict[str, Any]]:
    """Run sensitivity analysis by sweeping scaling factors."""
    logging.info(f"Running sensitivity sweep with factors: {factor_range}")
    
    results = []
    bulk_k = get_material_conductivity(config.material, config.bulk_conductivity)
    
    # Generate base network
    base_graph = generate_nanowire_network(
        N=config.N,
        p=config.p,
        seed=config.seed,
        target_degree=config.target_degree
    )
    
    for factor in factor_range:
        # Create modified config with scaled parameters
        scaled_config = SimulationConfig(
            N=config.N,
            p=config.p,
            d=config.d * factor,  # Scale diameter
            l=config.l,
            seed=config.seed,
            material=config.material,
            bulk_conductivity=config.bulk_conductivity,
            lambda_phonon=config.lambda_phonon,
            specularity=config.specularity,
            target_degree=config.target_degree
        )
        
        try:
            # Calculate thermal resistance with scaled parameters
            edge_resistances = assign_thermal_resistance(
                base_graph,
                bulk_k,
                scaled_config.d,
                scaled_config.l,
                scaled_config.lambda_phonon,
                scaled_config.specularity
            )
            
            # Solve for conductivity
            conductivity = solve_kirchhoff_heat_flow(
                base_graph,
                edge_resistances,
                scaled_config.d,
                scaled_config.l
            )
            
            # Calculate deviation from base
            base_conductivity = solve_kirchhoff_heat_flow(
                base_graph,
                assign_thermal_resistance(
                    base_graph,
                    bulk_k,
                    config.d,
                    config.l,
                    config.lambda_phonon,
                    config.specularity
                ),
                config.d,
                config.l
            )
            
            deviation = (conductivity - base_conductivity) / base_conductivity if base_conductivity > 0 else 0.0
            
            results.append({
                'factor': factor,
                'conductivity': conductivity,
                'deviation': deviation,
                'd_scaled': scaled_config.d
            })
            
        except Exception as e:
            logging.warning(f"Sensitivity sweep failed for factor {factor}: {e}")
            continue
    
    return results

def calculate_deviation_report(sweep_results: List[Dict[str, Any]]) -> pd.DataFrame:
    """Calculate deviation statistics from sensitivity sweep results."""
    if not sweep_results:
        return pd.DataFrame()
    
    df = pd.DataFrame(sweep_results)
    
    # Calculate statistics
    stats = {
        'mean_deviation': df['deviation'].mean(),
        'std_dev': df['deviation'].std(),
        'max_deviation': df['deviation'].abs().max(),
        'min_deviation': df['deviation'].min(),
        'count': len(df)
    }
    
    return pd.DataFrame([stats])

def report_sensitivity_results(sensitivity_metrics: Dict[str, float]) -> None:
    """Report sensitivity analysis results."""
    logging.info("Sensitivity Analysis Results:")
    logging.info(f"  Mean Deviation: {sensitivity_metrics.get('mean_deviation', 0):.4f}")
    logging.info(f"  Std Dev: {sensitivity_metrics.get('std_dev', 0):.4f}")
    logging.info(f"  Max Deviation: {sensitivity_metrics.get('max_deviation', 0):.4f}")
    
    # Check if within acceptable bounds (±10%)
    max_dev = sensitivity_metrics.get('max_deviation', 0)
    if abs(max_dev) <= 0.10:
        logging.info("  Status: Within acceptable bounds (±10%)")
    else:
        logging.warning(f"  Status: Exceeds acceptable bounds (±10%). Max deviation: {max_dev:.2%}")

def analyze_sensitivity(deviation_report: pd.DataFrame) -> Dict[str, float]:
    """Analyze sensitivity results and return metrics."""
    if deviation_report.empty:
        return {
            'mean_deviation': 0.0,
            'std_dev': 0.0,
            'max_deviation': 0.0
        }
    
    return {
        'mean_deviation': float(deviation_report['mean_deviation'].iloc[0]),
        'std_dev': float(deviation_report['std_dev'].iloc[0]),
        'max_deviation': float(deviation_report['max_deviation'].iloc[0])
    }
