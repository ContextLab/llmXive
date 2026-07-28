"""
T020: Run "No-Store Random" baseline execution.

Logic:
1. Invoke `code/engine_runner.py` with policy="Random" on the test set.
2. The engine selects k layers uniformly at random for each turn with NO memory of past layers.
3. k is defined as `config.K_RANDOM_BASELINE`.
4. Output: `data/processed/simulation_logs_random.json`.

Dependencies:
- T018 (engine_runner.py)
- T014a (test_set.csv)
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from engine_runner import load_test_set_ids, run_random_baseline
from config import load_config_from_file

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Run Random Baseline Simulation (T020)")
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/test_set.csv",
        help="Path to the test set CSV"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/simulation_logs_random.json",
        help="Path to the output JSON"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="code/config.py",
        help="Path to config file (for K_RANDOM_BASELINE)"
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting Random Baseline simulation on {input_path}")
    
    try:
        # Load config to get K_RANDOM_BASELINE if needed, though engine_runner handles policy="random"
        config = load_config_from_file(args.config)
        k_baseline = config.get('K_RANDOM_BASELINE', 2)
        logger.info(f"Using K_RANDOM_BASELINE = {k_baseline}")

        # Run the random baseline
        # The engine_runner.run_random_baseline function handles the logic:
        # - Loads test set IDs
        # - For each turn, selects k layers uniformly at random (no-store)
        # - Executes the engine and collects results
        results = run_random_baseline(
            input_file=str(input_path),
            output_file=str(output_path),
            k=k_baseline
        )

        if results is None:
            logger.error("Random baseline simulation failed to produce results.")
            sys.exit(1)

        logger.info(f"Random baseline simulation completed. Output written to {output_path}")
        logger.info(f"Processed {len(results) if isinstance(results, list) else 'unknown'} trajectories")

    except Exception as e:
        logger.error(f"Error during random baseline simulation: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()