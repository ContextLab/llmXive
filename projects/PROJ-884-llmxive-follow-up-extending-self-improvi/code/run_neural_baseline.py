"""
Execute Neural Subset Baseline (T030d).

Runs the BES loop with --mode neural_subset on a subset of N=50 puzzles
to generate neural_baseline_results.json.
"""
import os
import sys
import json
import time
import logging
import argparse
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from main import BESOrchestrator, BESRunResult
from config import load_config, initialize_experiment
from utils.logger import setup_logging
from utils.seed import set_seed

def main():
    parser = argparse.ArgumentParser(description="Execute Neural Subset Baseline")
    parser.add_argument("--n", type=int, default=50, help="Number of puzzles to process")
    parser.add_argument("--output", type=str, default="data/processed/neural_baseline_results.json",
                        help="Output file path for results")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    # Setup logging
    setup_logging(log_file="data/processed/neural_baseline.log")
    logger = logging.getLogger(__name__)

    logger.info(f"Starting Neural Subset Baseline with N={args.n}")
    logger.info(f"Output will be written to: {args.output}")

    # Initialize experiment
    initialize_experiment("neural_baseline")
    set_seed(args.seed)

    # Load configuration
    config = load_config()
    config["mode"] = "neural_subset"
    config["n_puzzles"] = args.n

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Run the BES orchestrator in neural_subset mode
        orchestrator = BESOrchestrator(config)
        result: BESRunResult = orchestrator.run()

        # Prepare results for serialization
        results_data = {
            "experiment_id": config.get("experiment_id", "neural_baseline"),
            "mode": "neural_subset",
            "n_puzzles_processed": result.total_puzzles,
            "successful_solutions": result.successful_solutions,
            "failed_solutions": result.failed_solutions,
            "success_rate": result.success_rate,
            "total_time_seconds": result.total_time,
            "avg_time_per_puzzle": result.avg_time_per_puzzle,
            "puzzle_details": []
        }

        # Add per-puzzle details if available
        if hasattr(result, 'puzzle_results') and result.puzzle_results:
            for puzzle_res in result.puzzle_results:
                results_data["puzzle_details"].append({
                    "puzzle_id": puzzle_res.get("puzzle_id", "unknown"),
                    "solved": puzzle_res.get("solved", False),
                    "time_seconds": puzzle_res.get("time_seconds", 0.0),
                    "complexity_n": puzzle_res.get("complexity_n", 0)
                })

        # Write results to file
        with open(output_path, 'w') as f:
            json.dump(results_data, f, indent=2)

        logger.info(f"Successfully wrote results to {args.output}")
        logger.info(f"Success rate: {result.success_rate:.2%}")
        logger.info(f"Total time: {result.total_time:.2f} seconds")

        return 0

    except Exception as e:
        logger.error(f"Neural Subset Baseline failed: {str(e)}", exc_info=True)
        # Re-raise to ensure the task fails loudly if execution fails
        raise

if __name__ == "__main__":
    sys.exit(main())
