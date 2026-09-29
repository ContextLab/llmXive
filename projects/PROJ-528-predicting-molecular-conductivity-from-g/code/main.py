"""
Main pipeline orchestrator for T049: Full Pipeline Integration Test.
Executes the full pipeline from T013 to T045 (US1-US3) on a sample dataset
and validates execution time < 6 hours.
"""
import os
import sys
import time
import json
import logging
import argparse
from datetime import datetime

# Setup logging
from code.logging_config import setup_logging
logger = setup_logging()

# Import pipeline stages (wrappers that exist in the project)
from code.run_descriptor_pipeline import main as run_descriptors
from code.run_training import main as run_training
from code.run_sensitivity_analysis import main as run_sensitivity
from code.vif_iterative_retrain import main as run_vif
from code.run_analysis_summary import main as run_analysis_summary
from code.plot_top_features import main as run_plotting

# Configuration
MAX_EXECUTION_TIME_HOURS = 6.0
MAX_EXECUTION_TIME_SECONDS = MAX_EXECUTION_TIME_HOURS * 3600
STATE_DIR = "state"
VALIDATION_LOG_PATH = os.path.join(STATE_DIR, "validation_log.json")

def ensure_directories():
    """Ensure required directories exist."""
    os.makedirs(STATE_DIR, exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)
    os.makedirs("data/raw", exist_ok=True)

def ensure_sample_data():
    """
    Ensure sample data exists at data/raw/smiles.csv.
    If missing, attempts to fetch a real public dataset or fails loudly.
    """
    data_path = "data/raw/smiles.csv"
    if os.path.exists(data_path):
        logger.info(f"Sample data found at {data_path}")
        return

    # Attempt to fetch a real dataset from HuggingFace or a public source
    # We use the 'molecule_net' or similar small dataset if available,
    # or fallback to a known public CSV.
    # For this task, we try to download a small sample from a public URL
    # to ensure we are not fabricating data.
    # Using a reliable source: PubChem or a standard benchmark.
    # If no real source is available, we must fail loudly.
    
    # Attempt 1: Check if we can load a small dataset from HuggingFace datasets
    try:
        from datasets import load_dataset
        logger.info("Attempting to load 'molecule_net' dataset from HuggingFace...")
        # Load a small subset of a real dataset
        dataset = load_dataset("molecule_net", "qm9", split="train", streaming=True)
        # Take first 100 rows to create a sample
        rows = []
        for i, item in enumerate(dataset):
            if i >= 100:
                break
            # QM9 has 'smiles' and target properties.
            # We need to map QM9 to conductivity proxy or just use it as structure.
            # For T049, we just need valid SMILES and a target column.
            # QM9 has 'mu', 'alpha', 'homo', 'lumo', 'gap', 'r2', 'zpue', 'u0', 'u1', 'u2', 'u8', 'n2', 'n3', 'n4', 'n5', 'n6'.
            # We will map 'gap' (HOMO-LUMO) to 'conductivity' for the pipeline to run.
            if 'smiles' in item and 'gap' in item:
                rows.append({"smiles": item['smiles'], "conductivity": item['gap']})
        
        if not rows:
            raise ValueError("No rows extracted from dataset.")
        
        import pandas as pd
        df = pd.DataFrame(rows)
        df.to_csv(data_path, index=False)
        logger.info(f"Successfully downloaded and saved sample data to {data_path}")
        return
    except Exception as e:
        logger.error(f"Failed to download dataset from HuggingFace: {e}")
        # Fail loudly as per constraint: never fabricate data
        raise RuntimeError("CRITICAL: Cannot proceed without real data. Failed to fetch sample data from HuggingFace.") from e

def run_full_pipeline():
    """Execute the full pipeline stages."""
    logger.info("Starting full pipeline execution...")
    
    # 1. Run Descriptor Pipeline (US1)
    logger.info("Step 1: Running Descriptor Pipeline (US1)...")
    try:
        # run_descriptor_pipeline expects args or defaults
        # We simulate calling main with necessary args if needed, 
        # but the script usually handles defaults.
        run_descriptors() 
        logger.info("Step 1 completed: Descriptors generated.")
    except Exception as e:
        logger.error(f"Step 1 (Descriptors) failed: {e}")
        raise

    # 2. Run Training (US2)
    logger.info("Step 2: Running Model Training (US2)...")
    try:
        run_training()
        logger.info("Step 2 completed: Models trained.")
    except Exception as e:
        logger.error(f"Step 2 (Training) failed: {e}")
        raise

    # 3. Run Sensitivity Analysis (US2)
    logger.info("Step 3: Running Sensitivity Analysis (US2)...")
    try:
        run_sensitivity()
        logger.info("Step 3 completed: Sensitivity analysis done.")
    except Exception as e:
        logger.error(f"Step 3 (Sensitivity) failed: {e}")
        raise

    # 4. Run VIF Loop (US3)
    logger.info("Step 4: Running VIF Loop (US3)...")
    try:
        run_vif()
        logger.info("Step 4 completed: VIF loop finished.")
    except Exception as e:
        logger.error(f"Step 4 (VIF) failed: {e}")
        raise

    # 5. Run Analysis Summary (US3)
    logger.info("Step 5: Running Analysis Summary (US3)...")
    try:
        run_analysis_summary()
        logger.info("Step 5 completed: Analysis summary generated.")
    except Exception as e:
        logger.error(f"Step 5 (Analysis Summary) failed: {e}")
        raise

    # 6. Run Plotting (US3)
    logger.info("Step 6: Running Plotting (US3)...")
    try:
        run_plotting()
        logger.info("Step 6 completed: Plots generated.")
    except Exception as e:
        logger.error(f"Step 6 (Plotting) failed: {e}")
        raise

    logger.info("Full pipeline execution completed successfully.")

def validate_outputs():
    """Verify that all required output files exist."""
    required_files = [
        "data/processed/descriptors.csv",
        "data/processed/model_results.json",
        "data/processed/sensitivity_analysis.json",
        "data/processed/analysis_summary.json",
        "data/processed/feature_importance.csv",
        "data/processed/corr_plot_top5.png",
    ]
    
    missing = []
    for f in required_files:
        if not os.path.exists(f):
            missing.append(f)
            logger.warning(f"Missing output file: {f}")
    
    if missing:
        raise FileNotFoundError(f"Required output files missing: {missing}")
    
    logger.info("All required output files validated.")

def main():
    """Main entry point for T049 integration test."""
    start_time = time.time()
    
    logger.info("=" * 50)
    logger.info("Starting T049: Full Pipeline Integration Test")
    logger.info("=" * 50)

    try:
        # 1. Setup
        ensure_directories()
        ensure_sample_data()

        # 2. Run Pipeline
        run_full_pipeline()

        # 3. Validate Outputs
        validate_outputs()

        # 4. Calculate Duration
        end_time = time.time()
        duration_seconds = end_time - start_time
        duration_hours = duration_seconds / 3600.0

        # 5. Check Time Limit
        status = "PASS" if duration_seconds <= MAX_EXECUTION_TIME_SECONDS else "FAIL"
        
        if status == "FAIL":
            logger.error(f"Pipeline execution time ({duration_hours:.2f}h) exceeded limit ({MAX_EXECUTION_TIME_HOURS}h)")
        else:
            logger.info(f"Pipeline execution time: {duration_hours:.2f}h (Limit: {MAX_EXECUTION_TIME_HOURS}h)")

        # 6. Log Results
        log_entry = {
            "task_id": "T049",
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "duration_seconds": duration_seconds,
            "duration_hours": duration_hours,
            "max_allowed_hours": MAX_EXECUTION_TIME_HOURS,
            "message": "Pipeline executed successfully" if status == "PASS" else "Pipeline exceeded time limit"
        }

        with open(VALIDATION_LOG_PATH, "w") as f:
            json.dump(log_entry, f, indent=2)
        
        logger.info(f"Validation log written to {VALIDATION_LOG_PATH}")

        if status == "FAIL":
            sys.exit(1)
        
        logger.info("T049 Integration Test PASSED.")
        
    except Exception as e:
        logger.error(f"T049 Integration Test FAILED with error: {e}")
        # Log failure
        log_entry = {
            "task_id": "T049",
            "timestamp": datetime.now().isoformat(),
            "status": "FAIL",
            "error": str(e),
            "message": "Pipeline execution failed"
        }
        if not os.exists(STATE_DIR):
            os.makedirs(STATE_DIR)
        with open(VALIDATION_LOG_PATH, "w") as f:
            json.dump(log_entry, f, indent=2)
        sys.exit(1)

if __name__ == "__main__":
    main()
