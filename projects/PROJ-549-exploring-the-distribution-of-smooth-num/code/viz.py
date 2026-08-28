import argparse
import json
import logging
import os
import sys
from typing import Dict, List, Optional, Tuple, Any

import matplotlib.pyplot as plt
import numpy as np

from utils import setup_logging

logger = logging.getLogger(__name__)

def load_and_group_data(data_path: str) -> Dict[str, List[Dict[str, Any]]]:
    """Load density data and group by y-value."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    data = []
    with open(data_path, 'r') as f:
        # Skip header
        next(f)
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 5:
                try:
                    row = {
                        'x': int(parts[0]),
                        'y': int(parts[1]),
                        'h': int(parts[2]),
                        'density': float(parts[3]),
                        'rho_dickman': float(parts[4]),
                        'deviation_ratio': float(parts[5]) if len(parts) > 5 else 0.0
                    }
                    data.append(row)
                except (ValueError, IndexError) as e:
                    logger.warning(f"Skipping malformed line: {line.strip()} - {e}")
    
    grouped = {}
    for row in data:
        y = row['y']
        if y not in grouped:
            grouped[y] = []
        grouped[y].append(row)
    
    return grouped

def calculate_confidence_intervals(data: List[Dict[str, Any]]) -> Tuple[List[float], List[float]]:
    """Calculate 95% confidence intervals for density values."""
    if not data:
        return [], []
    
    densities = [d['density'] for d in data]
    n = len(densities)
    if n < 2:
        mean = densities[0] if densities else 0.0
        return [mean], [mean]
    
    mean = np.mean(densities)
    std_err = np.std(densities, ddof=1) / np.sqrt(n)
    margin = 1.96 * std_err
    
    return [mean - margin], [mean + margin]

def plot_spec_grid(data_path: str, output_path: str, model_fits: Optional[Dict] = None) -> None:
    """Plot density vs interval length for the Spec-defined grid."""
    grouped = load_and_group_data(data_path)
    
    plt.figure(figsize=(12, 8))
    colors = plt.cm.viridis(np.linspace(0, 1, len(grouped)))
    
    for idx, (y, rows) in enumerate(sorted(grouped.items())):
        h_values = [r['h'] for r in rows]
        density_values = [r['density'] for r in rows]
        dickman_values = [r['rho_dickman'] for r in rows]
        
        plt.scatter(h_values, density_values, color=colors[idx], label=f'y={y}', alpha=0.6, edgecolors='k')
        plt.plot(h_values, dickman_values, '--', color=colors[idx], alpha=0.4)
        
        # Calculate and plot confidence intervals
        ci_lower, ci_upper = calculate_confidence_intervals(rows)
        if ci_lower:
            plt.fill_between(h_values, [ci_lower[0]] * len(h_values), [ci_upper[0]] * len(h_values), 
                             color=colors[idx], alpha=0.1)
    
    plt.xscale('log')
    plt.yscale('log')
    plt.xlabel('Interval Length (h)', fontsize=12)
    plt.ylabel('Observed Density (ρ)', fontsize=12)
    plt.title('Snapshot of Prime Density: Spec-Defined Grid (Comparative Analysis)', fontsize=14)
    plt.legend(title='y-smoothness threshold')
    plt.grid(True, which='both', ls='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved Spec grid plot to {output_path}")

def plot_plan_grid(data_path: str, output_path: str, model_fits: Optional[Dict] = None) -> None:
    """Plot deviation ratio vs interval length for the Plan-defined grid."""
    grouped = load_and_group_data(data_path)
    
    plt.figure(figsize=(12, 8))
    colors = plt.cm.plasma(np.linspace(0, 1, len(grouped)))
    
    for idx, (y, rows) in enumerate(sorted(grouped.items())):
        h_values = [r['h'] for r in rows]
        deviation_values = [r['deviation_ratio'] for r in rows]
        
        plt.scatter(h_values, deviation_values, color=colors[idx], label=f'y={y}', alpha=0.6, edgecolors='k')
        
        # Fit and plot trend line if model fits available
        if model_fits and 'plan_beta' is not None:
            # Simple linear fit in log-log space for visualization
            log_h = np.log10(h_values)
            log_dev = np.log10([max(d, 1e-10) for d in deviation_values])
            if len(log_h) > 1:
                coeffs = np.polyfit(log_h, log_dev, 1)
                trend_h = np.logspace(np.min(log_h), np.max(log_h), 100)
                trend_dev = 10**(np.polyval(coeffs, trend_h))
                plt.plot(trend_h, trend_dev, '-', color=colors[idx], alpha=0.5, linewidth=2)
    
    plt.xscale('log')
    plt.yscale('log')
    plt.xlabel('Interval Length (h)', fontsize=12)
    plt.ylabel('Deviation Ratio (R = ρ_obs / ρ_Dickman)', fontsize=12)
    plt.title('Snapshot of Prime Density: Plan-Defined Grid (Primary Experiment)', fontsize=14)
    plt.legend(title='y-smoothness threshold')
    plt.grid(True, which='both', ls='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved Plan grid plot to {output_path}")

def main() -> None:
    """Main entry point for visualization generation."""
    parser = argparse.ArgumentParser(description="Generate density distribution visualizations")
    parser.add_argument("--spec-data", default="data/density_measurements_spec.csv",
                      help="Path to Spec-defined grid data")
    parser.add_argument("--plan-data", default="data/density_measurements_plan.csv",
                      help="Path to Plan-defined grid data")
    parser.add_argument("--model-fits", default="data/model_fits.json",
                      help="Path to model fits JSON for annotations")
    parser.add_argument("--output-dir", default="data",
                      help="Output directory for plots")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        setup_logging(level=logging.DEBUG)
    else:
        setup_logging(level=logging.INFO)
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Load model fits if available
    model_fits = None
    if os.path.exists(args.model_fits):
        with open(args.model_fits, 'r') as f:
            model_fits = json.load(f)
        logger.info(f"Loaded model fits from {args.model_fits}")
    
    # Generate Spec grid plot
    spec_output = os.path.join(args.output_dir, "spec_grid_density.png")
    if os.path.exists(args.spec_data):
        plot_spec_grid(args.spec_data, spec_output, model_fits)
    else:
        logger.warning(f"Spec data file not found: {args.spec_data}, skipping plot")
    
    # Generate Plan grid plot
    plan_output = os.path.join(args.output_dir, "plan_grid_deviation.png")
    if os.path.exists(args.plan_data):
        plot_plan_grid(args.plan_data, plan_output, model_fits)
    else:
        logger.warning(f"Plan data file not found: {args.plan_data}, skipping plot")
    
    logger.info("Visualization generation complete")

if __name__ == "__main__":
    main()
