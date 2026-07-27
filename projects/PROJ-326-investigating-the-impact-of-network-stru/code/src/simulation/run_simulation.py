"""
Simulation Runner Script for Energy Propagation on Spin Networks.

This script orchestrates the full simulation pipeline:
1. Loads configuration and generated graph batches.
2. Runs the Ising spin-flip dynamics on each graph.
3. Measures diffusion rates and spatial variance.
4. Enforces runtime limits and numerical stability checks.
5. Profiles CPU time per step.
6. Serializes results to `data/analysis/simulation_results.json`.
"""

import argparse
import json
import logging
import os
import sys
import time
import signal
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import local project modules
from code.src.utils.config import load_config
from code.src.utils.logging import log_metric, log_run, get_run_log
from code.src.simulation.dynamics import run_spin_flip_simulation
from code.src.simulation.metrics import calculate_spatial_variance, get_energy_profile
from code.src.simulation.stability import enforce_runtime_limit, check_numerical_stability
from code.src.simulation.diffusion import calculate_diffusion_rate
from code.src.simulation.profiler import measure_cpu_time

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "code" / "config.yaml"
MANIFEST_PATH = PROJECT_ROOT / "data" / "raw" / "global_batch_manifest.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "analysis" / "simulation_results.json"
LOG_PATH = PROJECT_ROOT / "data" / "run_log.json"

def setup_logging(log_path: Optional[Path] = None) -> logging.Logger:
    """Initialize logging infrastructure."""
    logger = logging.getLogger("simulation_runner")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    
    # Ensure log file exists
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        if not log_path.exists():
            log_path.write_text("[]")
    
    return logger

def load_graph_batch(manifest_path: Path) -> List[Dict[str, Any]]:
    """Load graph batch metadata from the global batch manifest."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    # Extract graph metadata entries
    graphs = manifest.get("graphs", [])
    if not graphs:
        raise ValueError("No graphs found in manifest")
    
    return graphs

def run_simulation_on_graph(
    graph_meta: Dict[str, Any],
    config: Dict[str, Any],
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Run the full simulation pipeline on a single graph.
    
    Returns a dictionary containing simulation results for this graph.
    """
    start_time = time.time()
    run_id = graph_meta.get("id", "unknown")
    seed = graph_meta.get("seed", 0)
    topology = graph_meta.get("topology", "unknown")
    
    # Log simulation start
    log_metric(
        run_id=run_id,
        event_type="simulation_start",
        seed=seed,
        status="running",
        duration_seconds=0.0,
        logger=logger
    )
    
    try:
        # Enforce runtime limit
        timeout_seconds = config.get("simulation_params", {}).get("timeout_seconds", 3600)
        enforce_runtime_limit(timeout_seconds, logger)
        
        # Run dynamics
        dynamics_config = config.get("simulation_params", {})
        profile_data = measure_cpu_time(
            run_spin_flip_simulation,
            graph_meta,
            dynamics_config,
            logger=logger
        )
        
        # Extract metrics
        energy_profile = get_energy_profile(profile_data["dynamics_result"])
        spatial_variance = calculate_spatial_variance(profile_data["dynamics_result"])
        diffusion_rate = calculate_diffusion_rate(spatial_variance)
        
        # Check numerical stability
        stability_status = check_numerical_stability(energy_profile, logger)
        
        end_time = time.time()
        duration_seconds = end_time - start_time
        
        # Log simulation end
        log_metric(
            run_id=run_id,
            event_type="simulation_end",
            seed=seed,
            status="completed",
            duration_seconds=duration_seconds,
            logger=logger
        )
        
        return {
            "run_id": run_id,
            "topology": topology,
            "seed": seed,
            "runtime_duration_seconds": duration_seconds,
            "diffusion_rate": diffusion_rate,
            "spatial_variance_final": spatial_variance[-1] if spatial_variance else None,
            "energy_conservation": stability_status.get("conserved", False),
            "stability_status": stability_status.get("status", "unknown"),
            "time_per_step": profile_data.get("avg_time_per_step", 0.0),
            "total_steps": profile_data.get("total_steps", 0)
        }
        
    except Exception as e:
        end_time = time.time()
        duration_seconds = end_time - start_time
        
        # Log divergence or error
        log_metric(
            run_id=run_id,
            event_type="divergence_detected" if "divergence" in str(e).lower() else "simulation_end",
            seed=seed,
            status="failed",
            duration_seconds=duration_seconds,
            logger=logger
        )
        
        logger.error(f"Simulation failed for {run_id}: {e}")
        return {
            "run_id": run_id,
            "topology": topology,
            "seed": seed,
            "runtime_duration_seconds": duration_seconds,
            "status": "failed",
            "error": str(e)
        }

def main():
    """Main entry point for the simulation runner."""
    parser = argparse.ArgumentParser(description="Run energy propagation simulations on generated graphs.")
    parser.add_argument("--config", type=str, default=str(CONFIG_PATH), help="Path to config.yaml")
    parser.add_argument("--manifest", type=str, default=str(MANIFEST_PATH), help="Path to global batch manifest")
    parser.add_argument("--output", type=str, default=str(OUTPUT_PATH), help="Path to output results JSON")
    parser.add_argument("--log", type=str, default=str(LOG_PATH), help="Path to run log JSON")
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(Path(args.log))
    logger.info("Starting simulation pipeline")
    
    # Load configuration
    try:
        config = load_config(args.config)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)
    
    # Load graph batch
    try:
        graphs = load_graph_batch(Path(args.manifest))
    except Exception as e:
        logger.error(f"Failed to load graph batch: {e}")
        sys.exit(1)
    
    logger.info(f"Loaded {len(graphs)} graphs from manifest")
    
    # Run simulations
    results = []
    for i, graph_meta in enumerate(graphs):
        logger.info(f"Processing graph {i+1}/{len(graphs)}: {graph_meta.get('id', 'unknown')}")
        result = run_simulation_on_graph(graph_meta, config, logger)
        results.append(result)
    
    # Serialize results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config_path": args.config,
        "manifest_path": args.manifest,
        "total_graphs": len(graphs),
        "successful_runs": sum(1 for r in results if r.get("status") != "failed"),
        "failed_runs": sum(1 for r in results if r.get("status") == "failed"),
        "results": results
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Simulation pipeline complete. Results written to {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
