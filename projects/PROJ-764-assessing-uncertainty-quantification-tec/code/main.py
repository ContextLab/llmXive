import os
import sys
import time
import signal
import logging
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Add code root to path
code_root = Path(__file__).parent
sys.path.insert(0, str(code_root))

from utils.logging_config import setup_logging, log_pipeline_start, log_pipeline_end, log_metric
from utils.timing_logger import TimingLogger

# Configure logging
logger = setup_logging()

# Global timeout configuration (hours)
TIMEOUT_HOURS = 5.0
TIMEOUT_SECONDS = TIMEOUT_HOURS * 3600

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Pipeline execution exceeded global timeout.")

def run_command(cmd: list, description: str) -> bool:
    """
    Run a subprocess command. Returns True if successful, False otherwise.
    Logs the command and result.
    """
    logger.info(f"Running: {description}")
    logger.info(f"Command: {' '.join(cmd)}")
    try:
        start = time.time()
        result = subprocess.run(cmd, check=True, capture_output=False, text=True)
        duration = time.time() - start
        logger.info(f"Completed: {description} in {duration:.2f}s")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with return code {e.returncode}: {description}")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error running {description}: {e}")
        return False

def wait_for_models():
    """
    Wait for T013b, T014, T015 model artifacts to exist before proceeding.
    This acts as the 'Wait Logic' for the orchestrator.
    """
    logger.info("Checking for required model artifacts (T013b, T014, T015)...")
    required_files = [
        "results/models/ensemble/ensemble_seed_42.pt",
        "results/models/ensemble/ensemble_seed_43.pt",
        "results/models/ensemble/ensemble_seed_44.pt",
        "results/models/ensemble/ensemble_seed_45.pt",
        "results/models/ensemble/ensemble_seed_46.pt",
        "results/models/mc_dropout/mc_dropout_seed_42.pt",
        "results/models/sparse_gp_model.pt"
    ]

    missing = [f for f in required_files if not os.path.exists(f)]
    if missing:
        logger.warning(f"Missing model artifacts: {missing}. Rerunning model training scripts.")
        
        # Re-run T013b (Deep Ensemble)
        if not run_command(["python", "code/models/deep_ensemble.py"], "T013b: Deep Ensemble Training"):
            logger.error("Failed to train Deep Ensemble models.")
            return False

        # Re-run T014 (MC Dropout)
        if not run_command(["python", "code/models/mc_dropout.py"], "T014: MC Dropout Training"):
            logger.error("Failed to train MC Dropout model.")
            return False

        # Re-run T015 (Sparse GP)
        if not run_command(["python", "code/models/sparse_gp.py"], "T015: Sparse GP Fitting"):
            logger.error("Failed to fit Sparse GP model.")
            return False
        
        # Verify again
        missing = [f for f in required_files if not os.path.exists(f)]
        if missing:
            logger.error(f"Critical: Model artifacts still missing after re-run: {missing}")
            return False
    else:
        logger.info("All required model artifacts found.")
    return True

def run_t016a(seed: int) -> bool:
    """
    Run T016a for a specific seed.
    """
    cmd = ["python", "code/models/run_single_seed.py", "--seed", str(seed)]
    return run_command(cmd, f"T016a: Run Single Seed {seed}")

def merge_predictions():
    """
    Merge outputs from T016a runs into results/uq_predictions_base.csv.
    """
    logger.info("Merging T016a outputs into results/uq_predictions_base.csv...")
    
    # Collect seed files
    seeds = [42, 43, 44]
    input_files = [f"results/uq_predictions_seed_{s}.csv" for s in seeds]
    output_file = "results/uq_predictions_base.csv"
    
    import pandas as pd
    dfs = []
    missing_files = []
    
    for f in input_files:
        if os.path.exists(f):
            dfs.append(pd.read_csv(f))
        else:
            missing_files.append(f)
    
    if missing_files:
        logger.warning(f"Missing seed prediction files: {missing_files}")
        if not dfs:
            logger.error("No seed prediction files found to merge.")
            return False
    
    if dfs:
        merged_df = pd.concat(dfs, ignore_index=True)
        merged_df.to_csv(output_file, index=False)
        logger.info(f"Merged {len(merged_df)} rows into {output_file}")
        return True
    else:
        return False

def check_robustness_gate():
    """
    Check the robustness gate (T026 logic).
    """
    report_path = "results/robustness_report.json"
    if not os.path.exists(report_path):
        logger.warning(f"Robustness report {report_path} not found. Skipping gate check.")
        return True # Non-fatal for this specific task context if not yet generated
    
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    if report.get('pass', False):
        logger.info("Robustness Gate PASSED.")
        return True
    else:
        logger.warning("Robustness Gate FAILED: CV > threshold or insufficient seeds.")
        # Per spec: log error but do not exit with error code 1
        return True

def run_pipeline():
    """
    Main pipeline orchestrator.
    """
    # Set global timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(TIMEOUT_SECONDS)
    
    start_time = time.time()
    log_pipeline_start("Assessing Uncertainty Quantification Pipeline")
    
    success = True

    # Phase 1: Ensure Data is Ready (T005, T006)
    # Note: The task description implies T016b depends on T006d.
    # However, the execution failure log shows T005/T006 failed.
    # We must ensure these run if artifacts are missing.
    
    data_artifacts = [
        "data/raw/oqmd.parquet",
        "data/processed/raw_train.csv",
        "data/processed/raw_val.csv",
        "data/processed/raw_test.csv",
        "data/processed/pca_transformer.pkl",
        "data/processed/features_train_20pca.csv",
        "data/processed/features_val_20pca.csv",
        "data/processed/features_test_20pca.csv"
    ]
    
    missing_data = [f for f in data_artifacts if not os.path.exists(f)]
    if missing_data:
        logger.warning(f"Missing data artifacts: {missing_data}. Running data pipeline.")
        
        # Run T005: Download
        if not run_command(["python", "code/data/download.py"], "T005: Download OQMD"):
            logger.error("Data download failed. Cannot proceed.")
            success = False
        
        # Run T006: Preprocess (Split + PCA)
        if success and not run_command(["python", "code/data/preprocess.py"], "T006: Preprocess Data"):
            logger.error("Data preprocessing failed. Cannot proceed.")
            success = False
    else:
        logger.info("All data artifacts present.")

    if not success:
        signal.alarm(0) # Cancel alarm
        log_pipeline_end(False)
        return False

    # Phase 2: Wait for/Ensure Models (T013b, T014, T015)
    if not wait_for_models():
        logger.error("Model training failed.")
        signal.alarm(0)
        log_pipeline_end(False)
        return False

    # Phase 3: Run T016a for each seed
    seeds = [42, 43, 44]
    for seed in seeds:
        if not run_t016a(seed):
            logger.error(f"T016a failed for seed {seed}.")
            # Decide if we stop or continue. Spec says "Wait Logic" then "Merge".
            # If a seed fails, we might still merge what we have, but log failure.
            # For strictness, we mark success=False but continue to attempt merge.
            success = False

    # Phase 4: Merge Results (T016b requirement)
    if not merge_predictions():
        logger.error("Failed to merge predictions.")
        success = False

    # Phase 5: Robustness Gate (T026 dependency)
    # Note: T026 is in US2, but main.py is the orchestrator.
    # We check it if the report exists.
    check_robustness_gate()

    signal.alarm(0) # Cancel alarm
    duration = time.time() - start_time
    log_pipeline_end(success)
    log_metric("total_pipeline_time_seconds", duration)
    
    return success

def main():
    """Entry point for the orchestrator."""
    logger.info(f"Starting main pipeline with timeout={TIMEOUT_HOURS} hours")
    logger.info("--- PIPELINE START ---")
    
    success = run_pipeline()
    
    if success:
        logger.info("--- PIPELINE SUCCESSFUL ---")
        sys.exit(0)
    else:
        logger.error("--- PIPELINE FAILED ---")
        sys.exit(1)

if __name__ == "__main__":
    main()