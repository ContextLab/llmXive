"""
CLI entry point for running the simulation with timeout and fallback handling.
Implements T008a, T008b, T008c, T018, T015b, and T016 logic.
"""
import argparse
import sys
import os
import json
import time
import signal
import logging
from datetime import datetime
from typing import Optional, Dict, Any

# Import from project modules based on API surface
from src.data_models import SimulationRun, MetricRecord
from src.sim.eco_director import run_simulation as run_eco_simulation, load_and_inject_config
from src.sim.neural_baseline import run_neural_baseline_proxy
from src.data.loader import DataUnavailableError, load_simulation_dataset
from src.data.synthetic_fallback import generate_synthetic_fallback_dataset
from src.logging_config import create_logger, SimulationLogger
from config import initialize_reproducibility, get_current_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/simulation_run.log')
    ]
)
logger = logging.getLogger(__name__)

class TimeoutError(Exception):
    """Custom timeout exception."""
    pass

def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError("Simulation timed out after 6 hours.")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run simulation with timeout and fallback handling.")
    parser.add_argument("--config", type=str, default="default.yaml", help="Path to config file")
    parser.add_argument("--steps", type=int, default=10000, help="Number of steps to run")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    parser.add_argument("--timeout", type=int, default=21600, help="Timeout in seconds (default: 6 hours)")
    parser.add_argument("--mode", type=str, default="eco", choices=["eco", "neural", "both"], help="Simulation mode")
    return parser.parse_args()

def ensure_output_dir():
    """Ensure output directories exist."""
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    os.makedirs("state", exist_ok=True)

def write_status_log(status: Dict[str, Any], output_path: str = "data/raw/status.json"):
    """Write structured status log to JSON."""
    with open(output_path, 'w') as f:
        json.dump(status, f, indent=2)
    logger.info(f"Status log written to {output_path}")

def run_simulation_with_timeout(sim_func, args, timeout_seconds: int):
    """Run simulation with timeout enforcement."""
    # Set up signal handler for timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    
    try:
        start_time = time.time()
        result = sim_func(args)
        end_time = time.time()
        signal.alarm(0)  # Cancel alarm
        
        result['execution_time'] = end_time - start_time
        result['timed_out'] = False
        return result
    except TimeoutError:
        signal.alarm(0)  # Cancel alarm
        logger.warning("Simulation timed out!")
        return {
            'timed_out': True,
            'execution_time': timeout_seconds,
            'error': 'Time-Bound Baseline',
            'partial_results': True
        }
    finally:
        signal.alarm(0)  # Ensure alarm is cancelled

def ensure_fallback_dataset(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure dataset is available. If real data fails, generate fallback and flag as 'Power-Limited'.
    This implements T015b logic.
    """
    try:
        # Attempt to load real simulation dataset
        dataset = load_simulation_dataset(config.get('dataset_path', None))
        logger.info("Real dataset loaded successfully.")
        config['dataset_available'] = True
        config['power_limited'] = False
        return config
    except DataUnavailableError as e:
        logger.warning(f"Real dataset unavailable: {e}. Falling back to synthetic data.")
        # Generate fallback dataset
        fallback_data = generate_synthetic_fallback_dataset(steps=config.get('steps', 10000))
        # Save fallback data
        fallback_path = "data/raw/fallback_dataset.parquet"
        fallback_data.to_parquet(fallback_path, index=False)
        logger.info(f"Synthetic fallback dataset saved to {fallback_path}")
        
        # Flag as power-limited
        config['dataset_available'] = False
        config['power_limited'] = True
        config['fallback_dataset_path'] = fallback_path
        return config

def run_simulation_with_fallback(args):
    """
    Main simulation runner with fallback handling.
    Implements T016: Execute minimum 10,000 time-steps with timeout and fallback.
    """
    ensure_output_dir()
    initialize_reproducibility(args.seed)
    
    # Load config
    config = load_and_inject_config(args.config, args)
    config['steps'] = args.steps
    config['seed'] = get_current_seed()
    
    # Ensure dataset availability (T018 + T015b)
    config = ensure_fallback_dataset(config)
    
    # Initialize logger
    sim_logger = create_logger("simulation", "logs/simulation.log")
    
    # Prepare result structure
    result = {
        'run_id': str(datetime.now().strftime("%Y%m%d_%H%M%S")),
        'config': config,
        'steps_requested': args.steps,
        'steps_completed': 0,
        'status': 'running',
        'flags': []
    }
    
    # Run based on mode
    if args.mode == "eco":
        logger.info("Running Eco-Director simulation...")
        sim_result = run_eco_simulation(config, sim_logger)
        result.update(sim_result)
    elif args.mode == "neural":
        logger.info("Running Neural Baseline simulation...")
        sim_result = run_neural_baseline_proxy(config, sim_logger)
        result.update(sim_result)
    elif args.mode == "both":
        logger.info("Running both simulations...")
        eco_result = run_eco_simulation(config, sim_logger)
        neural_result = run_neural_baseline_proxy(config, sim_logger)
        result['eco_results'] = eco_result
        result['neural_results'] = neural_result
    
    # Check for timeout and set flags
    if result.get('timed_out', False):
        result['flags'].append('Time-Bound Baseline')
        # Save partial results
        if 'partial_results' in result:
            partial_path = f"data/raw/baseline_partial.parquet"
            # Convert results to DataFrame and save
            import pandas as pd
            if isinstance(result.get('metrics'), list):
                df = pd.DataFrame(result['metrics'])
                df.to_parquet(partial_path, index=False)
                logger.info(f"Partial results saved to {partial_path}")
    
    # Check for power-limited flag
    if config.get('power_limited', False):
        result['flags'].append('Power-Limited')
    
    # Finalize result
    result['status'] = 'completed' if not result.get('timed_out', False) else 'timeout'
    
    # Save results
    output_path = f"data/raw/{result['run_id']}_results.json"
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    logger.info(f"Results saved to {output_path}")
    
    # Write status log
    status_log = {
        'run_id': result['run_id'],
        'status': result['status'],
        'flags': result['flags'],
        'steps_completed': result['steps_completed'],
        'steps_requested': result['steps_requested'],
        'execution_time': result.get('execution_time', 0)
    }
    write_status_log(status_log, "data/raw/status.json")
    
    return result

def main():
    """Main entry point."""
    args = parse_args()
    
    # Run simulation with timeout
    result = run_simulation_with_timeout(
        run_simulation_with_fallback,
        args,
        timeout_seconds=args.timeout
    )
    
    # Print summary
    print(json.dumps(result, indent=2, default=str))
    
    # Exit with appropriate code
    if result.get('timed_out', False):
        sys.exit(1)  # Timeout exit code
    elif result.get('status') == 'completed':
        sys.exit(0)
    else:
        sys.exit(2)  # Other error

if __name__ == "__main__":
    main()
