"""
Script to demonstrate transient metrics extraction.
This script is primarily for testing the metrics module logic independently
or as a helper if the main simulation runner needs to be invoked specifically for this.

However, per T027b, the extraction is integrated into the simulation runner.
This script serves as a standalone validator if needed.
"""
import argparse
import json
import logging
import sys
from pathlib import Path
import numpy as np
import networkx as nx

from code.src.simulation.metrics import extract_transient_metrics, save_transient_metrics, compute_energy_density_profile, compute_spatial_variance
from code.src.utils.config import load_config, get_global_config
from code.src.utils.io import ensure_data_directory

logger = logging.getLogger(__name__)


def generate_dummy_history(steps: int, nodes: int = 10) -> list:
    """
    Generates a dummy history list for testing purposes.
    In a real scenario, this data comes from the simulation loop.
    """
    history = []
    # Create a dummy graph
    graph = nx.erdos_renyi_graph(nodes, 0.3)
    
    for step in range(steps):
        # Simulate some spin state (random for dummy)
        spins = np.random.choice([-1, 1], size=nodes)
        energy_density = compute_energy_density_profile(spins, graph)
        variance = compute_spatial_variance(energy_density)
        
        history.append({
            "step": step,
            "spatial_variance": variance,
            "energy_density_profile": energy_density.tolist()
        })
    
    return history


def main():
    parser = argparse.ArgumentParser(description="Run transient metrics extraction test.")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Path to config file")
    parser.add_argument("--steps", type=int, default=None, help="Override transient steps from config")
    parser.add_argument("--output", type=str, default="data/analysis/transient_metrics.json", help="Output file path")
    args = parser.parse_args()

    # Load config
    config = load_config(args.config)
    transient_steps = args.steps if args.steps is not None else config.get("simulation_params", {}).get("transient_steps", 10)

    logger.info(f"Extracting transient metrics for {transient_steps} steps...")

    # Generate dummy history (in real flow, this is passed from simulation)
    # We simulate a longer run to ensure we have data beyond transient
    total_steps = transient_steps + 20
    history = generate_dummy_history(total_steps)

    # Extract metrics
    result = extract_transient_metrics(history, transient_steps)

    # Save
    output_path = Path(args.output)
    ensure_data_directory(output_path)
    save_transient_metrics(result, str(output_path))

    logger.info(f"Transient metrics extraction complete. Saved to {output_path}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
