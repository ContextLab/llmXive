"""
T029c: Execute Full Symbolic Experiments.

Runs the BES loop in 'symbolic' mode across the full dataset to generate
symbolic_results.json. This script orchestrates the execution defined in T024.
"""
import os
import sys
import json
import time
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Ensure code directory is in path for imports
code_root = Path(__file__).resolve().parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from main import BESOrchestrator, BESRunResult
from config import load_config, initialize_experiment
from utils.logger import setup_logging
from utils.seed import set_seed
from exceptions import BaseResearchException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("T029c_SymbolicExperiments")

def run_symbolic_experiments(output_path: Path, dataset_dir: Path, config_path: Path):
    """
    Executes the full symbolic experiment loop.

    Args:
        output_path: Path to write symbolic_results.json
        dataset_dir: Path to the directory containing generated puzzles
        config_path: Path to the experiment configuration file
    """
    logger.info(f"Starting Full Symbolic Experiments (T029c)")
    logger.info(f"Dataset directory: {dataset_dir}")
    logger.info(f"Output file: {output_path}")

    # Initialize environment
    set_seed(42)
    setup_logging(log_file=str(output_path.with_suffix('.log')))

    # Load configuration
    if not config_path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        raise FileNotFoundError(f"Config file missing: {config_path}")
    
    config = load_config(config_path)
    experiment_id = initialize_experiment(config)
    
    logger.info(f"Experiment ID: {experiment_id}")

    # Initialize Orchestrator
    try:
        orchestrator = BESOrchestrator(
            config=config,
            mode="symbolic",
            dataset_dir=dataset_dir,
            output_dir=output_path.parent
        )
    except Exception as e:
        logger.error(f"Failed to initialize BESOrchestrator: {e}")
        raise

    results = []
    start_time = time.time()

    try:
        # Run the full experiment loop
        logger.info("Executing BES loop in symbolic mode...")
        run_result: BESRunResult = orchestrator.run()
        
        if run_result.success:
            logger.info(f"Experiment completed successfully.")
            # Collect results
            results = run_result.results
            logger.info(f"Processed {len(results)} puzzle instances.")
        else:
            logger.warning(f"Experiment finished with warnings or partial success.")
            results = run_result.results or []
            logger.info(f"Processed {len(results)} puzzle instances.")

    except BaseResearchException as e:
        logger.error(f"Research exception during execution: {e}")
        # Even if an exception occurred, we may have partial results to save
        # depending on where it failed.
        raise
    except Exception as e:
        logger.error(f"Unexpected error during execution: {e}")
        raise
    finally:
        end_time = time.time()
        elapsed = end_time - start_time
        logger.info(f"Total execution time: {elapsed:.2f} seconds")

    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report = {
        "experiment_id": experiment_id,
        "mode": "symbolic",
        "total_instances": len(results),
        "execution_time_seconds": elapsed,
        "results": results
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Results saved to {output_path}")
    return report

def main():
    parser = argparse.ArgumentParser(description="Execute Full Symbolic Experiments (T029c)")
    parser.add_argument(
        "--dataset-dir",
        type=str,
        default="data/raw",
        help="Path to the directory containing puzzle instances"
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default="data/processed/symbolic_results.json",
        help="Path to the output results file"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="code/bes/config.yaml",
        help="Path to the experiment configuration file"
    )

    args = parser.parse_args()

    dataset_dir = Path(args.dataset_dir)
    output_path = Path(args.output_file)
    config_path = Path(args.config)

    if not dataset_dir.exists():
        logger.error(f"Dataset directory does not exist: {dataset_dir}")
        sys.exit(1)

    try:
        run_symbolic_experiments(output_path, dataset_dir, config_path)
        logger.info("T029c Execution Complete.")
    except Exception as e:
        logger.error(f"T029c Execution Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()