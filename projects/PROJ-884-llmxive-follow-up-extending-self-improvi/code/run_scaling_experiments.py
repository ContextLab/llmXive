"""
Scaling Experiments Runner for llmXive BES.

Executes the BES loop across a range of puzzle complexities (N=10..500)
in symbolic mode to generate scaling_raw_logs.json.
"""
import os
import sys
import json
import time
import argparse
import logging
from pathlib import Path

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.main import BESOrchestrator, BESRunResult
from code.utils.seed import set_seed
from code.utils.logger import setup_logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / 'data' / 'processed' / 'scaling_experiments.log')
    ]
)
logger = logging.getLogger(__name__)

def run_scaling_experiment():
    """
    Run the BES loop across N=10, 50, 100, 200, 500 in symbolic mode.
    Outputs: data/processed/scaling_raw_logs.json
    """
    parser = argparse.ArgumentParser(description="Run BES Scaling Experiments")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["symbolic", "neural_subset"],
        default="symbolic",
        help="Execution mode (symbolic uses symbolic planner backward step)"
    )
    parser.add_argument(
        "--n_values",
        type=str,
        default="10,50,100,200,500",
        help="Comma-separated list of N values to test"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=5,
        help="Number of puzzles to test per N value"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    args = parser.parse_args()

    set_seed(args.seed)
    setup_logging()

    n_values = [int(x.strip()) for x in args.n_values.split(',')]
    output_path = PROJECT_ROOT / 'data' / 'processed' / 'scaling_raw_logs.json'
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting scaling experiments for N={n_values}, count={args.count}, mode={args.mode}")
    logger.info(f"Output will be written to: {output_path}")

    all_results = []

    for n in n_values:
        logger.info(f"--- Running experiment for N={n} ---")
        start_time = time.time()
        
        try:
            # Initialize orchestrator for this specific N
            # Note: In a real implementation, this would load puzzles of size N
            # For this task, we simulate the run structure matching the spec
            # The actual BESOrchestrator expects a dataset path or generation params.
            # We assume the dataset generation (T013b) created puzzles for these Ns.
            
            # Construct a temporary config for this run
            experiment_config = {
                "mode": args.mode,
                "n": n,
                "count": args.count,
                "population_size": 20,
                "generations": 5,
                "seed": args.seed,
                "puzzle_types": ["sudoku", "pathfinding"]
            }

            # Run the BES loop
            # We instantiate the orchestrator directly as per T024 implementation
            # Assuming T024 implemented BESOrchestrator.run_experiment correctly
            orchestrator = BESOrchestrator(experiment_config)
            result: BESRunResult = orchestrator.run_experiment()
            
            elapsed = time.time() - start_time
            
            run_record = {
                "n": n,
                "mode": args.mode,
                "count": args.count,
                "start_time": start_time,
                "end_time": time.time(),
                "elapsed_seconds": elapsed,
                "success_rate": result.success_rate,
                "total_successes": result.total_successes,
                "total_attempts": result.total_attempts,
                "avg_wall_clock": result.avg_wall_clock,
                "total_energy_joules": result.total_energy_joules,
                "population_stats": result.population_stats if result.population_stats else {},
                "status": "SUCCESS"
            }
            
            all_results.append(run_record)
            logger.info(f"Completed N={n}: Success Rate={result.success_rate:.2f}, Time={elapsed:.2f}s")

        except Exception as e:
            elapsed = time.time() - start_time
            error_record = {
                "n": n,
                "mode": args.mode,
                "count": args.count,
                "start_time": start_time,
                "end_time": time.time(),
                "elapsed_seconds": elapsed,
                "status": "FAILED",
                "error_message": str(e)
            }
            all_results.append(error_record)
            logger.error(f"Failed N={n}: {str(e)}", exc_info=True)

    # Write results to JSON
    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2)

    logger.info(f"Scaling experiments complete. Results written to {output_path}")
    return all_results

def main():
    run_scaling_experiment()

if __name__ == "__main__":
    main()
