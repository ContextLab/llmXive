"""
Simulation Runner Script for User Story 2.

Loads graphs from data/raw/, executes Ising spin-flip dynamics,
calculates diffusion rates, and serializes results to data/analysis/simulation_results.json.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx
import numpy as np

# Project imports
from code.src.simulation.dynamics import IsingDynamics, create_dynamics
from code.src.simulation.diffusion import compute_diffusion_from_simulation
from code.src.simulation.metrics import compute_spatial_variance, track_metrics_history
from code.src.simulation.schema import save_results, validate_results_file
from code.src.simulation.stability import run_full_stability_check, StabilityError
from code.src.utils.config import load_config, get_config_value
from code.src.utils.io import load_graph_gpickle, load_graph_json
from code.src.utils.reproducibility import generate_run_id, ensure_data_directory


logger = logging.getLogger(__name__)


def load_graph_from_raw(graph_path: Path) -> Tuple[nx.Graph, str]:
    """
    Load a graph from data/raw/ supporting both gpickle and json formats.
    Returns the graph and the topology class inferred from the filename.
    """
    suffix = graph_path.suffix.lower()
    if suffix == ".gpickle":
        G = load_graph_gpickle(graph_path)
    elif suffix in [".json", ".graphml"]:
        G = load_graph_json(graph_path)
    else:
        raise ValueError(f"Unsupported graph format: {suffix}")

    if G is None or not nx.is_connected(G):
        raise ValueError(f"Graph {graph_path} is not connected or could not be loaded.")

    # Infer topology class from filename (e.g., er_100_0.5.graphml -> er)
    stem = graph_path.stem
    parts = stem.split("_")
    topology_class = parts[0].lower() if parts else "unknown"

    return G, topology_class


def run_single_simulation(
    graph: nx.Graph,
    topology_class: str,
    run_id: str,
    seed: int,
    num_steps: int,
    temperature: float,
    initial_energy: float = 1.0,
) -> Dict[str, Any]:
    """
    Execute the Ising dynamics on a single graph for num_steps.
    Returns a dictionary containing the simulation results.
    """
    logger.info(f"Starting simulation for {run_id}, topology={topology_class}, steps={num_steps}")

    # Initialize dynamics
    dynamics = create_dynamics(graph, temperature=temperature, seed=seed)

    # Initial state
    initial_spins = dynamics.spins
    initial_energy_density = np.mean(initial_spins)
    
    # History tracking
    energy_history = [initial_energy_density]
    variance_history = [compute_spatial_variance(graph, initial_spins)]

    # Run simulation loop
    divergence_detected = False
    try:
        for t in range(num_steps):
            # Perform one step of dynamics
            new_spins = dynamics.step()
            current_energy_density = np.mean(new_spins)
            current_variance = compute_spatial_variance(graph, new_spins)

            # Stability check
            stability_result = run_full_stability_check(
                graph, new_spins, current_energy_density, current_variance
            )
            if not stability_result["is_stable"]:
                logger.warning(f"Stability check failed at step {t}: {stability_result['reason']}")
                divergence_detected = True
                break

            energy_history.append(current_energy_density)
            variance_history.append(current_variance)
            dynamics.spins = new_spins

    except Exception as e:
        logger.error(f"Simulation failed at step {t} due to: {e}")
        divergence_detected = True
        raise

    # Calculate diffusion rate
    diffusion_rate = compute_diffusion_from_simulation(variance_history)

    # Compile results
    result = {
        "run_id": run_id,
        "network_id": topology_class, # Using topology class as network ID per spec
        "topology_class": topology_class,
        "seed": seed,
        "num_nodes": graph.number_of_nodes(),
        "num_edges": graph.number_of_edges(),
        "temperature": temperature,
        "num_steps": num_steps,
        "initial_energy_density": float(initial_energy_density),
        "final_energy_density": float(energy_history[-1]),
        "spatial_variance_initial": float(variance_history[0]),
        "spatial_variance_final": float(variance_history[-1]),
        "diffusion_rate": float(diffusion_rate),
        "divergence_detected": divergence_detected,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    return result


def run_batch_simulation(
    raw_data_dir: Path,
    output_file: Path,
    config: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Iterate over all graphs in raw_data_dir, run simulations, and aggregate results.
    """
    ensure_data_directory(output_file.parent)

    # Configuration parameters
    num_steps = get_config_value(config, "simulation", "num_steps", default=100)
    temperature = get_config_value(config, "simulation", "temperature", default=1.0)
    base_seed = get_config_value(config, "simulation", "base_seed", default=42)

    run_id = generate_run_id()
    results = []

    # Find all graph files
    graph_files = list(raw_data_dir.glob("*"))
    if not graph_files:
        logger.warning(f"No graph files found in {raw_data_dir}")
        return results

    logger.info(f"Found {len(graph_files)} graphs to process.")

    for i, graph_path in enumerate(graph_files):
        if not graph_path.is_file():
            continue

        # Skip non-graph files (e.g., manifest.json)
        if graph_path.suffix.lower() not in [".gpickle", ".json", ".graphml"]:
            continue

        try:
            G, topology_class = load_graph_from_raw(graph_path)
            seed = base_seed + i  # Deterministic seed per graph in batch

            result = run_single_simulation(
                graph=G,
                topology_class=topology_class,
                run_id=run_id,
                seed=seed,
                num_steps=num_steps,
                temperature=temperature,
            )
            results.append(result)
            logger.info(f"Completed {i+1}/{len(graph_files)}: {graph_path.name}")

        except Exception as e:
            logger.error(f"Failed to process {graph_path}: {e}")
            # Continue with next graph rather than failing the whole batch
            continue

    # Validate and save results
    if results:
        # Validate schema
        for res in results:
            validate_results_file(res) # Validates single record against schema structure

        # Save to JSON
        save_results(results, output_file)
        logger.info(f"Saved {len(results)} results to {output_file}")
    else:
        logger.warning("No results to save.")

    return results


def main():
    """
    Entry point for the simulation runner script.
    """
    parser = argparse.ArgumentParser(description="Run Ising spin dynamics on generated graphs.")
    parser.add_argument(
        "--config",
        type=str,
        default="code/config.yaml",
        help="Path to the configuration file.",
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/raw",
        help="Directory containing input graphs.",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default="data/analysis/simulation_results.json",
        help="Path to the output results JSON file.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging.",
    )
    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Load config
    config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)

    config = load_config(config_path)

    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        logger.error(f"Input directory not found: {input_dir}")
        sys.exit(1)

    output_path = Path(args.output_file)

    try:
        results = run_batch_simulation(input_dir, output_path, config)
        if not results:
            logger.warning("Simulation run completed but produced no results.")
            sys.exit(1)
        logger.info("Simulation run completed successfully.")
    except Exception as e:
        logger.error(f"Simulation run failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()