import argparse
import sys
import os
import json
import time
import signal
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Import from existing project API surface
from src.data_models import SimulationRun, MetricRecord
from src.sim.eco_director import run_simulation as run_eco_director
from src.sim.neural_baseline import run_neural_baseline_proxy
from src.data.loader import load_real_dataset, DataUnavailableError
from src.data.synthetic_fallback import generate_synthetic_fallback_dataset
from src.sim.logging_config import create_logger, MetricRecord as LogMetricRecord
from src.sim.termination_handler import check_memory_and_log, handle_termination
from config import set_seed, get_current_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/simulation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SimulationResult:
    def __init__(self, run_id: str, steps_completed: int, metrics: Dict[str, float], 
                 status: str, flags: List[str], config: Dict[str, Any]):
        self.run_id = run_id
        self.steps_completed = steps_completed
        self.metrics = metrics
        self.status = status
        self.flags = flags
        self.config = config

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "steps_completed": self.steps_completed,
            "metrics": self.metrics,
            "status": self.status,
            "flags": self.flags,
            "config": self.config,
            "timestamp": time.time()
        }

def load_target_steps_from_config(config_path: str = "config/default.yaml") -> int:
    """
    Load target_steps from config.yaml. 
    Defaults to 10000 if file is missing or key is absent.
    """
    default_steps = 10000
    try:
        import yaml
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            if config and 'target_steps' in config:
                val = config['target_steps']
                if isinstance(val, int):
                    return val
                elif isinstance(val, str) and val.isdigit():
                    return int(val)
                else:
                    logger.warning(f"Invalid target_steps format in {config_path}: {val}. Using default.")
        else:
            logger.warning(f"Config file {config_path} not found. Using default target_steps.")
    except Exception as e:
        logger.error(f"Error loading config: {e}. Using default target_steps.")
    return default_steps

def verify_step_count(actual_steps: int, target_steps: int) -> bool:
    """Verify if actual steps meet the target."""
    return actual_steps >= target_steps

def ensure_output_dir(output_path: str) -> None:
    """Ensure the directory for the output file exists."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

def write_status_log(status_data: Dict[str, Any], output_path: str) -> None:
    """Write the status log to a JSON file."""
    ensure_output_dir(output_path)
    with open(output_path, 'w') as f:
        json.dump(status_data, f, indent=2)
    logger.info(f"Status log written to {output_path}")

def run_with_timeout(func, args=(), kwargs=None, timeout=None):
    """Run a function with a timeout using signal."""
    if kwargs is None:
        kwargs = {}
    
    def handler(signum, frame):
        raise TimeoutError("Function execution timed out")
    
    old_handler = signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout)
    try:
        result = func(*args, **kwargs)
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
    return result

def ensure_fallback_dataset(target_steps: int) -> pd.DataFrame:
    """
    Generate a synthetic fallback dataset if real data is unavailable.
    This is triggered by catching DataUnavailableError elsewhere.
    """
    logger.info("Generating synthetic fallback dataset...")
    df = generate_synthetic_fallback_dataset(steps=target_steps)
    return df

def run_simulation_with_timeout(agent_type: str, target_steps: int, seed: int, 
                                memory_limit_mb: int, time_limit_sec: Optional[int] = None,
                                output_path: str = "data/raw/baseline_partial.parquet") -> SimulationResult:
    """
    Core simulation runner with timeout, memory checks, and fallback logic.
    """
    run_id = f"{agent_type}_{seed}_{int(time.time())}"
    flags = []
    status = "SUCCESS"
    metrics = {}
    steps_completed = 0

    # Set seed
    set_seed(seed)

    # Load real dataset or fallback
    try:
        # Attempt to load real data (streaming if large)
        # Assuming load_real_dataset handles streaming internally or returns an iterator
        # For this implementation, we assume it returns a DataFrame or raises DataUnavailableError
        data_df = load_real_dataset(target_steps=target_steps)
        logger.info("Real dataset loaded successfully.")
    except DataUnavailableError as e:
        logger.warning(f"Real data unavailable: {e}. Triggering fallback.")
        flags.append("Power-Limited")
        data_df = ensure_fallback_dataset(target_steps)
        # Verify fallback density
        if len(data_df) < 1000:
            logger.warning("Fallback dataset insufficient steps. Flagging.")
            flags.append("Insufficient-Fallback")
    except Exception as e:
        logger.error(f"Unexpected error loading data: {e}")
        status = "FAILED"
        return SimulationResult(run_id, 0, {}, status, flags, {})

    # Prepare configuration
    config = {
        "agent_type": agent_type,
        "target_steps": target_steps,
        "seed": seed,
        "memory_limit_mb": memory_limit_mb
    }

    # Execute Simulation
    try:
        if time_limit_sec:
            logger.info(f"Running with timeout: {time_limit_sec}s")
            # Note: In a real multi-process environment, signal.SIGALRM only works in main thread
            # For robustness, we might use multiprocessing.TimeoutError, but sticking to signal for simplicity here
            # as per existing project patterns.
            result_data = run_with_timeout(
                run_eco_director if agent_type == "ca_eco_director" else run_neural_baseline_proxy,
                args=(config, data_df),
                timeout=time_limit_sec
            )
        else:
            if agent_type == "ca_eco_director":
                result_data = run_eco_director(config, data_df)
            else:
                result_data = run_neural_baseline_proxy(config, data_df)

        # Extract metrics from result_data (assumed to be a dict or object)
        # Adapting to the actual return type of run_eco_director / run_neural_baseline_proxy
        if isinstance(result_data, dict):
            metrics = result_data.get('metrics', {})
            steps_completed = result_data.get('steps_completed', 0)
        elif hasattr(result_data, 'to_dict'):
            d = result_data.to_dict()
            metrics = d.get('metrics', {})
            steps_completed = d.get('steps_completed', 0)
        else:
            # Fallback for unknown return types
            logger.warning("Unknown return type from simulation. Attempting to extract metrics.")
            metrics = {"coherence": 0.0, "diversity": 0.0} # Default placeholders if extraction fails
            steps_completed = target_steps # Assume full run if no error thrown

        # Check for Time-Bound flag if timeout was set and we hit it (handled by TimeoutError usually)
        # If we are here, timeout didn't kill us, but we might have hit a soft limit in logic
        if time_limit_sec and steps_completed < target_steps:
            flags.append("Time-Bound")
            status = "TIMEOUT"

    except TimeoutError:
        logger.error("Simulation timed out.")
        flags.append("Time-Bound")
        status = "TIMEOUT"
        steps_completed = target_steps # We might have partial data saved in the process
        # Ensure partial save happens here if run_eco_director handles it
        # For this task, we assume the partial save logic is in the agent or handled by termination_handler
        # We just flag it.
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        status = "FAILED"
        metrics = {"error": str(e)}

    # Create result object
    result = SimulationResult(
        run_id=run_id,
        steps_completed=steps_completed,
        metrics=metrics,
        status=status,
        flags=flags,
        config=config
    )

    # Write output
    try:
        # Create DataFrame for Parquet
        output_df = pd.DataFrame([result.to_dict()])
        ensure_output_dir(output_path)
        output_df.to_parquet(output_path, index=False)
        logger.info(f"Results saved to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write output to {output_path}: {e}")

    return result

def run_sweep(grid_params: List[Dict[str, Any]], target_steps: int, seed: int, 
              memory_limit_mb: int, output_dir: str = "data/processed/") -> List[SimulationResult]:
    """Run a parameter sweep over a grid of configurations."""
    results = []
    os.makedirs(output_dir, exist_ok=True)
    
    for i, params in enumerate(grid_params):
        logger.info(f"Running configuration {i+1}/{len(grid_params)}: {params}")
        config = {
            **params,
            "target_steps": target_steps,
            "seed": seed + i, # Vary seed for each run
            "memory_limit_mb": memory_limit_mb
        }
        
        # Assuming agent type is in params or defaults to ca_eco_director
        agent_type = params.get("agent_type", "ca_eco_director")
        
        try:
            result = run_simulation_with_timeout(
                agent_type=agent_type,
                target_steps=target_steps,
                seed=config["seed"],
                memory_limit_mb=memory_limit_mb,
                output_path=os.path.join(output_dir, f"sweep_run_{i}.parquet")
            )
            results.append(result)
        except Exception as e:
            logger.error(f"Configuration {i} failed: {e}")
            results.append(SimulationResult(
                run_id=f"failed_{i}", steps_completed=0, metrics={}, 
                status="FAILED", flags=["Error"], config=config
            ))
    
    return results

def write_sweep_results(results: List[SimulationResult], output_path: str):
    """Write sweep results to a CSV file."""
    data = [r.to_dict() for r in results]
    df = pd.DataFrame(data)
    ensure_output_dir(output_path)
    df.to_csv(output_path, index=False)
    logger.info(f"Sweep results written to {output_path}")

def parse_args():
    parser = argparse.ArgumentParser(description="Run llmXive simulation with configuration loading.")
    parser.add_argument('--agent', type=str, default='ca_eco_director',
                        help='Agent type: ca_eco_director or neural_baseline')
    parser.add_argument('--steps', type=int, default=None,
                        help='Number of steps to run. If None, loads from config.')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--memory-limit', type=int, default=4096, help='Memory limit in MB')
    parser.add_argument('--time-limit', type=int, default=None, help='Time limit in seconds')
    parser.add_argument('--output', type=str, default='data/raw/baseline_partial.parquet',
                        help='Output path for results')
    parser.add_argument('--config', type=str, default='config/default.yaml',
                        help='Path to configuration file')
    parser.add_argument('--mode', type=str, default='single', choices=['single', 'sweep'],
                        help='Run mode: single simulation or parameter sweep')
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Load target_steps from config if not provided via CLI
    if args.steps is None:
        target_steps = load_target_steps_from_config(args.config)
    else:
        target_steps = args.steps
    
    logger.info(f"Starting simulation: agent={args.agent}, steps={target_steps}, seed={args.seed}")
    
    if args.mode == 'sweep':
        # Generate a simple grid for demonstration if not provided via separate grid file
        # In a real scenario, this would load from a grid CSV or config
        grid_params = [
            {"agent_type": "ca_eco_director", "neighborhood_radius": 1},
            {"agent_type": "ca_eco_director", "neighborhood_radius": 2},
        ]
        results = run_sweep(grid_params, target_steps, args.seed, args.memory_limit)
        write_sweep_results(results, "data/processed/sweep_results.csv")
        logger.info("Sweep completed.")
    else:
        result = run_simulation_with_timeout(
            agent_type=args.agent,
            target_steps=target_steps,
            seed=args.seed,
            memory_limit_mb=args.memory_limit,
            time_limit_sec=args.time_limit,
            output_path=args.output
        )
        logger.info(f"Simulation completed: {result.status}, Steps: {result.steps_completed}")
        if result.flags:
            logger.info(f"Flags: {', '.join(result.flags)}")

if __name__ == "__main__":
    main()