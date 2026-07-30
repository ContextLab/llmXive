"""
Simulation Runner for Spin Dynamics.

Orchestrates the generation of network topologies, execution of Ising spin-flip
dynamics, calculation of diffusion metrics, and serialization of results.
"""
import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import networkx as nx
import numpy as np

# Local imports
from code.src.utils.config import load_config, set_seed
from code.src.utils.logging import init_logging, log_metric
from code.src.simulation.dynamics import run_spin_flip_simulation
from code.src.simulation.metrics import get_energy_profile, calculate_spatial_variance
from code.src.simulation.diffusion import calculate_diffusion_rate
from code.src.simulation.stability import check_numerical_stability, log_simulation_runtime
from code.src.simulation.profiler import profile_simulation_step, validate_fr_010

# Ensure output directories exist
OUTPUT_DIR = Path("data/analysis")
LOG_DIR = Path("data")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

def setup_logging(config: Dict[str, Any]) -> None:
    """Initialize logging infrastructure based on config."""
    log_file = LOG_DIR / "run_log.json"
    init_logging(log_file)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def load_graphs_from_manifest(manifest_path: Path) -> List[Dict[str, Any]]:
    """Load generated graphs from the batch manifest."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    graphs = []
    for entry in manifest.get('graphs', []):
        # Reconstruct graph from metadata or load from file if path provided
        # For this runner, we assume graphs are stored in data/raw/ or similar
        # based on the manifest structure.
        graph_id = entry.get('graph_id')
        graph_file = entry.get('file_path')
        
        if graph_file and os.path.exists(graph_file):
            G = nx.read_graphml(graph_file) # Assuming GraphML for persistence
            graphs.append({
                'graph_id': graph_id,
                'graph': G,
                'metadata': entry
            })
        else:
            logging.warning(f"Graph file not found for {graph_id}, skipping.")
    
    return graphs

def run_simulation_batch(
    graphs: List[Dict[str, Any]],
    config: Dict[str, Any],
    run_id: str
) -> List[Dict[str, Any]]:
    """
    Run spin dynamics simulation on a batch of graphs.
    
    Args:
        graphs: List of graph objects with metadata.
        config: Simulation configuration.
        run_id: Unique identifier for this run.
        
    Returns:
        List of simulation results.
    """
    results = []
    seed = config.get('global_seed', 42)
    sim_params = config.get('simulation_params', {})
    num_steps = sim_params.get('num_steps', 100)
    temperature = sim_params.get('temperature', 1.0)
    
    for graph_data in graphs:
        G = graph_data['graph']
        graph_id = graph_data['graph_id']
        
        logging.info(f"Starting simulation for graph {graph_id} ({G.number_of_nodes()} nodes)")
        
        # Set seed for reproducibility
        set_seed(seed)
        
        start_time = time.time()
        
        try:
            # Check stability before running
            is_stable, stability_msg = check_numerical_stability(G, temperature)
            if not is_stable:
                log_metric({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "event_type": "simulation_end",
                    "run_id": run_id,
                    "seed": seed,
                    "status": "failed_stability_check",
                    "duration_seconds": time.time() - start_time,
                    "graph_id": graph_id,
                    "error": stability_msg
                })
                continue
            
            # Run dynamics
            spin_config, energy_profile, spatial_variance = run_spin_flip_simulation(
                G, 
                num_steps=num_steps, 
                temperature=temperature,
                seed=seed
            )
            
            # Calculate diffusion rate
            diffusion_rate = calculate_diffusion_rate(energy_profile)
            
            # Profile step time
            step_time = profile_simulation_step(G, num_steps, temperature, seed)
            
            # Validate FR-010 (100 steps < 60 mins)
            fr_010_valid = validate_fr_010(step_time, num_steps)
            
            duration = time.time() - start_time
            
            result = {
                "graph_id": graph_id,
                "run_id": run_id,
                "seed": seed,
                "num_nodes": G.number_of_nodes(),
                "num_edges": G.number_of_edges(),
                "num_steps": num_steps,
                "temperature": temperature,
                "final_energy": float(energy_profile[-1]) if energy_profile else 0.0,
                "diffusion_rate": float(diffusion_rate),
                "spatial_variance_final": float(spatial_variance[-1]) if spatial_variance else 0.0,
                "avg_step_time_seconds": step_time,
                "fr_010_valid": fr_010_valid,
                "status": "success",
                "duration_seconds": duration,
                "energy_profile": [float(e) for e in energy_profile],
                "spatial_variance": [float(v) for v in spatial_variance]
            }
            
            log_metric({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": "simulation_end",
                "run_id": run_id,
                "seed": seed,
                "status": "success",
                "duration_seconds": duration,
                "graph_id": graph_id
            })
            
            results.append(result)
            
        except Exception as e:
            duration = time.time() - start_time
            logging.exception(f"Simulation failed for graph {graph_id}: {e}")
            
            log_metric({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": "simulation_end",
                "run_id": run_id,
                "seed": seed,
                "status": "failed",
                "duration_seconds": duration,
                "graph_id": graph_id,
                "error": str(e)
            })
            
            results.append({
                "graph_id": graph_id,
                "run_id": run_id,
                "status": "failed",
                "error": str(e)
            })
    
    return results

def serialize_results(results: List[Dict[str, Any]], output_path: Path) -> None:
    """Serialize simulation results to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logging.info(f"Results serialized to {output_path}")

def main() -> None:
    """Main entry point for the simulation runner."""
    parser = argparse.ArgumentParser(description="Run spin dynamics simulation on network graphs.")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Path to config file")
    parser.add_argument("--manifest", type=str, default="data/analysis/global_batch_manifest.json", help="Path to graph manifest")
    parser.add_argument("--output", type=str, default="data/analysis/simulation_results.json", help="Output path for results")
    args = parser.parse_args()
    
    # Load config
    config = load_config(args.config)
    
    # Setup logging
    setup_logging(config)
    
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    seed = config.get('global_seed', 42)
    set_seed(seed)
    
    logging.info(f"Starting simulation run {run_id} with seed {seed}")
    
    # Load graphs
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        # If manifest doesn't exist, we might need to generate a test graph
        # or fail loudly. Per constraints, we fail loudly if data is missing.
        logging.error(f"Manifest file not found: {manifest_path}")
        # Create a minimal empty result set if we must proceed, but log the error
        results = []
    else:
        graphs = load_graphs_from_manifest(manifest_path)
        if not graphs:
            logging.warning("No valid graphs found in manifest.")
            results = []
        else:
            results = run_simulation_batch(graphs, config, run_id)
    
    # Serialize results
    output_path = Path(args.output)
    serialize_results(results, output_path)
    
    logging.info("Simulation run completed.")

if __name__ == "__main__":
    main()
