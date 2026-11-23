"""
Seed Orchestrator for User Story 2.

Iterates over a fixed list of seeds [42, 43, 44], invoking the single-seed
runner (T016a) for each. Aggregates successful outputs into a single CSV.
"""
import os
import sys
import json
import logging
import argparse
import subprocess
import pandas as pd
from pathlib import Path
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/seeds_orchestrator.log')
    ]
)
logger = logging.getLogger(__name__)

# Configuration
SEEDS = [42, 43, 44]
SINGLE_SEED_SCRIPT = Path("code/models/run_single_seed.py")
RESULTS_DIR = Path("results")
OUTPUT_PATTERN = "uq_predictions_seed_{seed}.csv"
AGGREGATED_FILE = "uq_predictions_aggregated.csv"

def ensure_results_dir():
    """Ensure the results directory exists."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def run_single_seed(seed: int) -> bool:
    """
    Invoke the single-seed runner script for a specific seed.

    Args:
        seed: The random seed to use.

    Returns:
        True if the script completed successfully, False otherwise.
    """
    logger.info(f"Starting seed {seed}...")
    try:
        # Run the single seed script
        # We assume the script handles its own logging and file output
        result = subprocess.run(
            [sys.executable, str(SINGLE_SEED_SCRIPT), "--seed", str(seed)],
            capture_output=False, # Let it stream stdout/stderr for visibility
            check=True,
            timeout=3000 # 50 minutes timeout per seed to be safe within 5h total
        )
        
        # Verify the expected output file exists
        expected_output = RESULTS_DIR / OUTPUT_PATTERN.format(seed=seed)
        if not expected_output.exists():
            logger.error(f"Seed {seed} completed but output file {expected_output} not found.")
            return False

        logger.info(f"Seed {seed} completed successfully.")
        return True

    except subprocess.CalledProcessError as e:
        logger.warning(f"Seed {seed} failed with exit code {e.returncode}. Continuing to next seed.")
        return False
    except subprocess.TimeoutExpired as e:
        logger.warning(f"Seed {seed} timed out. Continuing to next seed.")
        return False
    except Exception as e:
        logger.warning(f"Seed {seed} encountered an unexpected error: {e}. Continuing to next seed.")
        return False

def aggregate_results(seeds: List[int]) -> Optional[pd.DataFrame]:
    """
    Load all successful seed outputs and aggregate them into a single DataFrame.

    Args:
        seeds: List of seeds that were attempted.

    Returns:
        Aggregated DataFrame or None if no seeds succeeded.
    """
    successful_outputs = []
    
    for seed in seeds:
        file_path = RESULTS_DIR / OUTPUT_PATTERN.format(seed=seed)
        if file_path.exists():
            try:
                df = pd.read_csv(file_path)
                # Add a column to track the seed if not present (for debugging/traceability)
                # The task description implies the file contains 'sample_id', 'method', etc.
                # We might want to tag the source seed if the single-seed script doesn't include it.
                # However, the single-seed script likely processes a specific test set.
                # If the test set is the same for all seeds, sample_id might be duplicated.
                # We assume the single-seed script outputs are distinct or we just concat.
                # To be safe and traceable, we'll rely on the file content.
                successful_outputs.append(df)
                logger.info(f"Loaded results for seed {seed}: {len(df)} rows.")
            except Exception as e:
                logger.error(f"Failed to load results for seed {seed}: {e}")
        else:
            logger.info(f"Skipping aggregation for seed {seed} (file not found).")

    if not successful_outputs:
        logger.warning("No successful seed outputs found to aggregate.")
        return None

    # Concatenate all DataFrames
    aggregated_df = pd.concat(successful_outputs, ignore_index=True)
    
    # Save to the aggregated file
    output_path = RESULTS_DIR / AGGREGATED_FILE
    aggregated_df.to_csv(output_path, index=False)
    logger.info(f"Aggregated {len(aggregated_df)} rows into {output_path}")
    
    return aggregated_df

def main(args=None):
    """Main entry point for the seed orchestrator."""
    parser = argparse.ArgumentParser(description="Run UQ inference for multiple seeds.")
    parser.add_argument(
        "--seeds", 
        type=int, 
        nargs="+", 
        default=SEEDS, 
        help=f"List of seeds to run (default: {SEEDS})"
    )
    args = parser.parse_args(args)

    ensure_results_dir()

    logger.info(f"Starting Seed Orchestrator with seeds: {args.seeds}")
    
    successful_seeds = []
    
    for seed in args.seeds:
        success = run_single_seed(seed)
        if success:
            successful_seeds.append(seed)

    if not successful_seeds:
        logger.error("No seeds completed successfully. Aborting aggregation.")
        sys.exit(1)

    logger.info(f"Successfully completed seeds: {successful_seeds}")
    
    aggregated_df = aggregate_results(args.seeds)
    
    if aggregated_df is None:
        logger.error("Aggregation failed or produced no data.")
        sys.exit(1)

    logger.info("Seed Orchestrator completed successfully.")

if __name__ == "__main__":
    main()