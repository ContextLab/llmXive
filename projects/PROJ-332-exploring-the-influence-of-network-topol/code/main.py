import os
import sys
import csv
import logging
import time
import argparse
from typing import List, Dict, Any, Optional

from config import SimulationConfig, load_config, get_simulation_parameters
from material_db import get_material_conductivity
from generate_networks import generate_nanowire_network, calculate_average_degree
from thermal_solver import solve_kirchhoff_heat_flow, calculate_effective_conductivity
from regression_analysis import run_ols_regression, detect_percolation_threshold, update_csv_with_percolation_threshold
from sensitivity_analysis import run_sensitivity_sweep
from utils import setup_logging, write_csv_row, format_error

# Global timer for T016a/T016b
_SIMULATION_START_TIME: Optional[float] = None
_TIMEOUT_SECONDS: float = 6 * 3600  # 6 hours

def check_runtime_limit() -> bool:
    """
    T016a: Check if elapsed time exceeds the limit.
    Returns True if limit exceeded, False otherwise.
    """
    if _SIMULATION_START_TIME is None:
        return False
    elapsed = time.time() - _SIMULATION_START_TIME
    if elapsed > _TIMEOUT_SECONDS:
        return True
    return False

def abort_on_timeout() -> None:
    """
    T016b: Abort execution if timeout exceeded.
    """
    if check_runtime_limit():
        logger = logging.getLogger(__name__)
        logger.error("Runtime ceiling (6h) exceeded. Aborting grid.")
        sys.exit(1)

def load_existing_results(csv_path: str) -> List[Dict[str, Any]]:
    """Load existing results from CSV if it exists."""
    results = []
    if os.path.exists(csv_path):
        with open(csv_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numeric strings to floats/int
                converted = {}
                for k, v in row.items():
                    try:
                        if '.' in v:
                            converted[k] = float(v)
                        else:
                            converted[k] = int(v)
                    except (ValueError, TypeError):
                        converted[k] = v
                results.append(converted)
        logger = logging.getLogger(__name__)
        logger.info(f"Loaded {len(results)} existing results")
    return results

def append_results_to_csv(csv_path: str, results: List[Dict[str, Any]]) -> None:
    """Append results to the CSV file."""
    if not results:
        return

    fieldnames = ["seed", "N", "p", "avg_degree", "conductivity", "percolation_flag", "scaling_factor"]
    # Check if file exists to determine if header is needed
    file_exists = os.path.exists(csv_path) and os.path.getsize(csv_path) > 0

    with open(csv_path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for row in results:
            # Ensure all keys exist, fill missing with None
            complete_row = {k: row.get(k, "") for k in fieldnames}
            writer.writerow(complete_row)

def run_single_simulation(config: SimulationConfig, seed: int) -> Dict[str, Any]:
    """Run a single simulation iteration."""
    logger = logging.getLogger(__name__)
    logger.info(f"Running simulation: N={config.N}, p={config.p}, seed={seed}")

    # Generate network
    graph = generate_nanowire_network(config.N, config.p, seed=seed)
    avg_degree = calculate_average_degree(graph)

    # Check connectivity
    is_connected = nx.is_connected(graph) if nx.is_directed(graph) == False else nx.is_strongly_connected(graph)
    percolation_flag = 1 if is_connected else 0

    if not is_connected:
        logger.warning("Graph disconnected; conductivity set to 0.0")
        conductivity = 0.0
    else:
        # Get material conductivity
        bulk_k = get_material_conductivity(config.material, config.bulk_conductivity)

        # Solve thermal problem
        conductivity = calculate_effective_conductivity(
            graph, bulk_k, config.d, config.l
        )

    return {
        "seed": seed,
        "N": config.N,
        "p": config.p,
        "avg_degree": avg_degree,
        "conductivity": conductivity,
        "percolation_flag": percolation_flag,
        "scaling_factor": 1.0  # Default for non-sensitivity runs
    }

def run_grid_simulation(config: SimulationConfig) -> List[Dict[str, Any]]:
    """Run simulations over a grid of parameters."""
    logger = logging.getLogger(__name__)
    results = []
    seeds = range(config.seed, config.seed + 10)  # Example grid size

    for seed in seeds:
        # T016a: Check timeout at start of every iteration
        if check_runtime_limit():
            abort_on_timeout()

        try:
            result = run_single_simulation(config, seed)
            results.append(result)
        except Exception as e:
            logger.error(f"Simulation failed for seed {seed}: {format_error(e)}")
            continue

    return results

def run_sensitivity_analysis(config: SimulationConfig, existing_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Run sensitivity analysis and append to results."""
    logger = logging.getLogger(__name__)
    logger.info("Starting sensitivity analysis")
    logger.info(f"Running sensitivity sweep with factors: {config.sensitivity_factors}")

    # Run sensitivity sweep using existing results as baseline
    sensitivity_results = run_sensitivity_sweep(config, existing_results)

    # Append results to CSV
    if sensitivity_results:
        append_results_to_csv("data/processed/simulation_results.csv", sensitivity_results)

    return sensitivity_results

def run_regression_analysis(config: SimulationConfig, existing_results: List[Dict[str, Any]]) -> None:
    """Run regression analysis on existing results."""
    logger = logging.getLogger(__name__)
    logger.info("Running regression analysis")

    if not existing_results:
        logger.warning("No results available for regression analysis")
        return

    # Detect percolation threshold
    percolation_threshold = detect_percolation_threshold(existing_results)

    # Update CSV with percolation threshold
    update_csv_with_percolation_threshold("data/processed/simulation_results.csv", percolation_threshold)

    # Run OLS regression
    run_ols_regression(existing_results)

def main():
    """Main entry point for the pipeline."""
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting thermal conductivity simulation pipeline")

    # Initialize global timer (T016a)
    global _SIMULATION_START_TIME
    _SIMULATION_START_TIME = time.time()

    parser = argparse.ArgumentParser(description="Thermal Conductivity Simulation")
    parser.add_argument("--sensitivity-only", action="store_true", help="Run only sensitivity analysis")
    parser.add_argument("--config", type=str, help="Path to config YAML")
    args = parser.parse_args()

    config = load_config(args.config) if args.config else SimulationConfig()

    csv_path = "data/processed/simulation_results.csv"
    existing_results = load_existing_results(csv_path)

    if args.sensitivity_only:
        run_sensitivity_analysis(config, existing_results)
    else:
        # Run grid simulation
        new_results = run_grid_simulation(config)
        if new_results:
            append_results_to_csv(csv_path, new_results)
            existing_results.extend(new_results)

        # Run regression analysis
        run_regression_analysis(config, existing_results)

        # Run sensitivity analysis
        run_sensitivity_analysis(config, existing_results)

    logger.info("Pipeline completed successfully")

if __name__ == "__main__":
    import networkx as nx  # Ensure networkx is imported for run_single_simulation
    main()
