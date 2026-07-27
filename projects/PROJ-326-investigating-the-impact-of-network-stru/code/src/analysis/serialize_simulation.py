"""
Task T029: Implement result serialization to data/analysis/simulation_results.json.

This module handles the serialization of simulation results, including
diffusion rates, runtime metrics, and topology information, into a
structured JSON file as defined by the schema in T029a.
"""
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure we can import from code/src
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.src.simulation.run_simulation import run_simulation
from code.src.utils.logging import log_metric, get_run_log
from code.src.utils.config import load_config

logger = logging.getLogger(__name__)

SIMULATION_RESULTS_PATH = Path("data/analysis/simulation_results.json")

def load_simulation_results() -> List[Dict[str, Any]]:
    """
    Load existing simulation results if they exist, otherwise return empty list.
    This is used to append new results or validate existing data.
    """
    if SIMULATION_RESULTS_PATH.exists():
        try:
            with open(SIMULATION_RESULTS_PATH, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not load existing simulation results: {e}")
            return []
    return []

def save_simulation_results(results: List[Dict[str, Any]]) -> None:
    """
    Save the list of simulation results to the designated JSON file.
    
    Args:
        results: List of dictionaries containing simulation results.
    """
    # Ensure directory exists
    SIMULATION_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(SIMULATION_RESULTS_PATH, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Saved {len(results)} simulation results to {SIMULATION_RESULTS_PATH}")

def serialize_single_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure a single result dictionary conforms to the expected schema.
    
    Expected schema (from T029a):
    {
        "run_id": str,
        "timestamp": str (ISO 8601),
        "generation_algorithm": str,
        "topology_type": str,
        "diffusion_rate": float,
        "spatial_variance_initial": float,
        "spatial_variance_final": float,
        "runtime_duration_seconds": float,
        "status": str,
        "seed": int
    }
    """
    serialized = {
        "run_id": result.get("run_id", "unknown"),
        "timestamp": result.get("timestamp", datetime.now(timezone.utc).isoformat()),
        "generation_algorithm": result.get("generation_algorithm", "unknown"),
        "topology_type": result.get("topology_type", "unknown"),
        "diffusion_rate": float(result.get("diffusion_rate", 0.0)),
        "spatial_variance_initial": float(result.get("spatial_variance_initial", 0.0)),
        "spatial_variance_final": float(result.get("spatial_variance_final", 0.0)),
        "runtime_duration_seconds": float(result.get("runtime_duration_seconds", 0.0)),
        "status": result.get("status", "unknown"),
        "seed": int(result.get("seed", 0))
    }
    return serialized

def run_and_serialize_simulation(config_path: str = "code/config.yaml") -> List[Dict[str, Any]]:
    """
    Run a simulation using the provided config and serialize the results.
    
    This function:
    1. Loads the configuration
    2. Runs the simulation (which should handle graph generation and dynamics)
    3. Collects the results
    4. Serializes them to data/analysis/simulation_results.json
    
    Args:
        config_path: Path to the configuration file.
        
    Returns:
        List of serialized simulation results.
    """
    logger.info(f"Starting simulation run and serialization with config: {config_path}")
    
    # Load config
    config = load_config(config_path)
    
    # Get global seed
    seed = config.get("global_seed", 42)
    
    # Run simulation
    # Note: run_simulation is expected to return a list of result dictionaries
    # or a single result dictionary. We handle both cases.
    try:
        simulation_output = run_simulation(config)
        
        # Normalize output to a list
        if isinstance(simulation_output, dict):
            results = [simulation_output]
        elif isinstance(simulation_output, list):
            results = simulation_output
        else:
            logger.error(f"Unexpected simulation output type: {type(simulation_output)}")
            return []
        
        # Serialize each result
        serialized_results = []
        for result in results:
            if isinstance(result, dict):
                serialized = serialize_single_result(result)
                serialized_results.append(serialized)
                
                # Log the result
                log_metric(
                    event_type="simulation_end",
                    run_id=serialized["run_id"],
                    seed=serialized["seed"],
                    status=serialized["status"],
                    duration_seconds=serialized["runtime_duration_seconds"]
                )
            else:
                logger.warning(f"Skipping non-dict result: {result}")
        
        # Save to file
        save_simulation_results(serialized_results)
        
        return serialized_results
        
    except Exception as e:
        logger.error(f"Error during simulation run or serialization: {e}")
        # Log the error
        log_metric(
            event_type="simulation_end",
            run_id="error",
            seed=seed,
            status="error",
            duration_seconds=0.0
        )
        raise

def main(config_path: str = "code/config.yaml", output_path: str = None) -> None:
    """
    Main entry point for the serialization script.
    
    Args:
        config_path: Path to the configuration file.
        output_path: Optional override for the output file path.
    """
    setup_logging()
    
    if output_path:
        global SIMULATION_RESULTS_PATH
        SIMULATION_RESULTS_PATH = Path(output_path)
    
    try:
        results = run_and_serialize_simulation(config_path)
        logger.info(f"Successfully serialized {len(results)} simulation results.")
    except Exception as e:
        logger.error(f"Failed to serialize simulation results: {e}")
        sys.exit(1)

def setup_logging():
    """Initialize logging for this script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Serialize simulation results to JSON.")
    parser.add_argument(
        "--config",
        type=str,
        default="code/config.yaml",
        help="Path to the configuration file."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Override the default output file path."
    )
    
    args = parser.parse_args()
    main(args.config, args.output)
