"""
Convergence testing for oscillator simulations.

Task: T024
Goal: Verify simulation stability by running multiple seeds on a representative topology
      and ensuring the standard deviation of decay rates is < 1% of the mean.
"""
import os
import sys
import json
import logging
import argparse
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

# Import from existing project modules
from code.simulate_oscillators import simulate_graph, load_networks, set_seed
from code.utils.diagnostics import plot_convergence
from code.utils.checksums import generate_checksum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_NETWORKS_PATH = "data/raw/networks.csv"
DEFAULT_OUTPUT_DIR = "data/analysis"
DEFAULT_OUTPUT_PLOT = "convergence_plot.png"
DEFAULT_OUTPUT_METRICS = "convergence_metrics.json"
NUM_SEEDS = 10
SIMULATION_DURATION = 200.0
DRIVING_DURATION = 100.0
DAMPING_COEFF = 0.1
DRIVING_FREQ = 1.0
DRIVING_AMPLITUDE = 0.5
CONVERGENCE_THRESHOLD = 0.01  # std/mean < 1%

def select_median_degree_graph(networks_df: pd.DataFrame) -> Tuple[int, pd.Series]:
    """
    Select the graph with the median average degree from the networks dataset.

    Args:
        networks_df: DataFrame containing network metrics including 'avg_degree'.

    Returns:
        Tuple of (graph_id, row_data) for the median degree graph.
    """
    if 'avg_degree' not in networks_df.columns:
        raise ValueError("Input DataFrame must contain 'avg_degree' column.")
    
    median_degree = networks_df['avg_degree'].median()
    # Find the row closest to the median degree
    closest_idx = (networks_df['avg_degree'] - median_degree).abs().idxmin()
    selected_row = networks_df.loc[closest_idx]
    graph_id = int(selected_row['id'])
    
    logger.info(f"Selected graph ID {graph_id} with avg_degree {selected_row['avg_degree']:.2f} (median: {median_degree:.2f})")
    return graph_id, selected_row

def run_convergence_simulation(
    graph_id: int,
    num_seeds: int,
    duration: float,
    driving_duration: float,
    damping: float,
    driving_freq: float,
    driving_amp: float
) -> List[float]:
    """
    Run the oscillator simulation on a specific graph with multiple random seeds.

    Args:
        graph_id: ID of the graph to simulate.
        num_seeds: Number of random seeds to test.
        duration: Total simulation time.
        driving_duration: Duration of the driving force.
        damping: Damping coefficient.
        driving_freq: Driving frequency.
        driving_amp: Driving amplitude.

    Returns:
        List of decay rates extracted from each simulation.
    """
    decay_rates = []
    
    for seed in range(num_seeds):
        set_seed(seed)
        try:
            # Run simulation
            result = simulate_graph(
                graph_id=graph_id,
                duration=duration,
                driving_duration=driving_duration,
                damping=damping,
                driving_freq=driving_freq,
                driving_amp=driving_amp,
                seed=seed
            )
            
            if result and 'decay_rate' in result:
                decay_rates.append(result['decay_rate'])
                logger.info(f"Seed {seed}: Decay rate = {result['decay_rate']:.6f}, R² = {result.get('r_squared', 'N/A')}")
            else:
                logger.warning(f"Seed {seed}: Simulation failed to return valid decay rate.")
                
        except Exception as e:
            logger.error(f"Seed {seed}: Simulation failed with error: {e}")
            
    return decay_rates

def compute_convergence_metrics(decay_rates: List[float]) -> Dict[str, Any]:
    """
    Compute statistical metrics for convergence testing.

    Args:
        decay_rates: List of decay rates from multiple seeds.

    Returns:
        Dictionary containing mean, std, std/mean ratio, and pass/fail status.
    """
    if not decay_rates:
        raise ValueError("No decay rates computed for convergence analysis.")
    
    arr = np.array(decay_rates)
    mean_rate = np.mean(arr)
    std_rate = np.std(arr)
    cv = std_rate / mean_rate if mean_rate != 0 else float('inf')
    
    passed = cv < CONVERGENCE_THRESHOLD
    
    metrics = {
        "mean_decay_rate": float(mean_rate),
        "std_decay_rate": float(std_rate),
        "coefficient_of_variation": float(cv),
        "threshold": CONVERGENCE_THRESHOLD,
        "passed": passed,
        "num_samples": len(decay_rates),
        "min_decay_rate": float(np.min(arr)),
        "max_decay_rate": float(np.max(arr))
    }
    
    return metrics

def plot_convergence_results(
    decay_rates: List[float],
    metrics: Dict[str, Any],
    output_path: str
):
    """
    Generate a convergence plot showing decay rates across seeds.

    Args:
        decay_rates: List of decay rates.
        metrics: Computed convergence metrics.
        output_path: Path to save the plot.
    """
    seeds = list(range(len(decay_rates)))
    
    plt.figure(figsize=(10, 6))
    plt.errorbar(seeds, decay_rates, yerr=[0]*len(decay_rates), fmt='o', capsize=5, 
                 label='Simulated Decay Rates', color='blue', alpha=0.6)
    
    mean_line = [metrics['mean_decay_rate']] * len(seeds)
    plt.axhline(y=metrics['mean_decay_rate'], color='red', linestyle='--', label=f'Mean: {metrics["mean_decay_rate"]:.4f}')
    
    plt.axhline(y=metrics['mean_decay_rate'] * (1 - CONVERGENCE_THRESHOLD), color='green', linestyle=':', 
                label=f'Tolerance (±1%)')
    plt.axhline(y=metrics['mean_decay_rate'] * (1 + CONVERGENCE_THRESHOLD), color='green', linestyle=':')
    
    plt.xlabel('Random Seed')
    plt.ylabel('Decay Rate (λ)')
    plt.title(f'Convergence Test: Decay Rate Stability\nCV = {metrics["coefficient_of_variation"]:.4f} ({"PASS" if metrics["passed"] else "FAIL"})')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Convergence plot saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Run convergence test on oscillator simulations.")
    parser.add_argument("--networks", type=str, default=DEFAULT_NETWORKS_PATH,
                        help="Path to networks CSV file")
    parser.add_argument("--output-dir", type=str, default=DEFAULT_OUTPUT_DIR,
                        help="Output directory for results")
    parser.add_argument("--seeds", type=int, default=NUM_SEEDS,
                        help="Number of random seeds to test")
    args = parser.parse_args()

    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    plot_path = os.path.join(args.output_dir, DEFAULT_OUTPUT_PLOT)
    metrics_path = os.path.join(args.output_dir, DEFAULT_OUTPUT_METRICS)

    logger.info(f"Loading networks from {args.networks}")
    if not os.path.exists(args.networks):
        logger.error(f"Networks file not found: {args.networks}")
        sys.exit(1)

    networks_df = load_networks(args.networks)
    
    if networks_df.empty:
        logger.error("No networks found in the input file.")
        sys.exit(1)

    # Select representative topology
    graph_id, row_data = select_median_degree_graph(networks_df)
    
    logger.info(f"Running convergence simulation on graph {graph_id} with {args.seeds} seeds...")
    decay_rates = run_convergence_simulation(
        graph_id=graph_id,
        num_seeds=args.seeds,
        duration=SIMULATION_DURATION,
        driving_duration=DRIVING_DURATION,
        damping=DAMPING_COEFF,
        driving_freq=DRIVING_FREQ,
        driving_amp=DRIVING_AMPLITUDE
    )

    if not decay_rates:
        logger.error("No valid decay rates were computed. Aborting.")
        sys.exit(1)

    # Compute metrics
    metrics = compute_convergence_metrics(decay_rates)
    
    # Plot results
    plot_convergence_results(decay_rates, metrics, plot_path)

    # Save metrics
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Convergence metrics saved to {metrics_path}")
    logger.info(f"Result: {'PASS' if metrics['passed'] else 'FAIL'} (CV={metrics['coefficient_of_variation']:.4f})")

    # Generate checksum for the metrics file
    checksum = generate_checksum(metrics_path)
    logger.info(f"Checksum for {metrics_path}: {checksum}")

    if not metrics['passed']:
        logger.warning("Convergence test FAILED. The simulation results vary by more than 1% across seeds.")
        sys.exit(1)
    else:
        logger.info("Convergence test PASSED.")

if __name__ == "__main__":
    main()
