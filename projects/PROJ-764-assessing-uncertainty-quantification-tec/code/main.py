"""
Main orchestrator for the UQ pipeline.
Chains data loading, model training, and UQ inference with a global 5-hour timeout.
"""
import os
import sys
import time
import signal
import logging
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Add project root to path to ensure imports work
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.logging_config import setup_logging, log_pipeline_start, log_pipeline_end, log_metric
from data.preprocess import main as preprocess_main
from models.baseline_nn import main as baseline_nn_main
from models.deep_ensemble import main as deep_ensemble_main
from models.mc_dropout import main as mc_dropout_main
from models.sparse_gp import main as sparse_gp_main
from models.run_single_seed import main as run_single_seed_main

# Configuration
GLOBAL_TIMEOUT_HOURS = 5.0
SEEDS_TO_RUN = [42, 43, 44]  # Based on T025a requirements
OUTPUT_FILE = "results/uq_predictions_base.csv"

logger = logging.getLogger(__name__)

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Pipeline execution exceeded the 5-hour global timeout.")

def run_command(cmd_list, description):
    """Run a subprocess command and wait for completion."""
    logger.info(f"Starting: {description}")
    start_time = time.time()
    try:
        # Run the script as a subprocess to isolate execution and handle exit codes cleanly
        result = subprocess.run(
            [sys.executable] + cmd_list,
            check=True,
            capture_output=False,
            text=True
        )
        elapsed = time.time() - start_time
        logger.info(f"Completed: {description} in {elapsed:.2f}s")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed: {description} with exit code {e.returncode}")
        raise e
    except Exception as e:
        logger.error(f"Error running {description}: {e}")
        raise e

def merge_predictions(seed_files, output_path):
    """Merge individual seed prediction files into a single base CSV."""
    import pandas as pd
    import glob

    all_dfs = []
    # Pattern: results/uq_predictions_seed_<seed>.csv
    for seed in SEEDS_TO_RUN:
        file_path = f"results/uq_predictions_seed_{seed}.csv"
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            all_dfs.append(df)
        else:
            logger.warning(f"Predictions file for seed {seed} not found: {file_path}")

    if not all_dfs:
        logger.error("No prediction files found to merge.")
        raise FileNotFoundError("No prediction files found to merge.")

    combined_df = pd.concat(all_dfs, ignore_index=True)
    combined_df.to_csv(output_path, index=False)
    logger.info(f"Merged predictions saved to {output_path}")
    return combined_df

def run_pipeline():
    """Orchestrate the full pipeline steps."""
    log_pipeline_start("UQ Pipeline")

    # Step 1: Preprocessing (T006a, T006b1, T006b2, T006b3)
    # This generates the processed data and PCA artifacts needed for models
    run_command(
        ["data/preprocess.py"],
        "Preprocessing (Split, Binning, PCA, Exclusion)"
    )

    # Step 2: Train Models (T012, T013, T014, T015)
    # These must complete before inference (T016a) can start
    logger.info("Waiting for model training to complete...")

    # Train Baseline (T012)
    run_command(
        ["models/baseline_nn.py"],
        "Training Baseline NN"
    )

    # Train Deep Ensemble (T013)
    run_command(
        ["models/deep_ensemble.py"],
        "Training Deep Ensemble"
    )

    # Train MC Dropout (T014)
    run_command(
        ["models/mc_dropout.py"],
        "Training MC Dropout"
    )

    # Train Sparse GP (T015)
    run_command(
        ["models/sparse_gp.py"],
        "Training Sparse GP"
    )

    # Step 3: Run Inference for each seed (T016a)
    # This consumes the trained models and generates per-seed predictions
    for seed in SEEDS_TO_RUN:
        run_command(
            ["models/run_single_seed.py", "--seed", str(seed)],
            f"Running Inference for Seed {seed}"
        )

    # Step 4: Merge Results
    merge_predictions(SEEDS_TO_RUN, OUTPUT_FILE)

    log_pipeline_end("UQ Pipeline")
    logger.info("Pipeline completed successfully.")

def main():
    """Entry point with global timeout enforcement."""
    # Setup logging
    setup_logging()
    logger.info("Starting UQ Pipeline Orchestrator")

    # Set global timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(int(GLOBAL_TIMEOUT_HOURS * 3600))

    try:
        run_pipeline()
    except TimeoutError as e:
        logger.critical(f"Pipeline terminated: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Pipeline failed unexpectedly: {e}")
        sys.exit(1)
    finally:
        # Cancel the alarm
        signal.alarm(0)

if __name__ == "__main__":
    main()