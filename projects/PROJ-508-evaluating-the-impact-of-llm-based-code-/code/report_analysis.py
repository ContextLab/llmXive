"""
Script to generate analysis_results.json from the statistical models.
This task implements T040: Generate analysis results JSON.
"""
import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Import from existing project modules
from utils.metrics import calculate_diff_complexity_score, is_ai_noise_flag
# Note: The main analysis logic (GLMM, ZINB, VIF, Bonferroni) is in code/analyze.py
# We assume the analysis has been run and results are available or can be re-run.
# Since T033-T039 are marked complete, we expect analyze.py to have the functions.
# However, to keep this script standalone and robust, we will re-run the analysis
# pipeline if the output file doesn't exist, or load existing results if they do.

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DERIVED_DIR = PROJECT_ROOT / "data" / "derived"
ANALYSIS_RESULTS_PATH = DATA_DERIVED_DIR / "analysis_results.json"
MASTER_DATASET_PATH = DATA_DERIVED_DIR / "master_dataset.csv"

def ensure_directories():
    """Ensure output directories exist."""
    DATA_DERIVED_DIR.mkdir(parents=True, exist_ok=True)

def run_analysis_pipeline():
    """
    Run the full analysis pipeline if results don't exist.
    Imports and executes functions from code/analyze.py.
    """
    logger.info("Running analysis pipeline to generate results...")
    
    # Dynamically import from code/analyze.py
    # We need to add the code directory to sys.path for relative imports to work
    import sys
    code_dir = PROJECT_ROOT / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    
    try:
        from analyze import (
            load_master_dataset, 
            clean_data, 
            calculate_vif, 
            flag_high_vif, 
            run_glmm, 
            run_zinb_model, 
            apply_bonferroni_correction,
            run_analysis
        )
    except ImportError as e:
        logger.error(f"Failed to import analysis functions: {e}")
        logger.error("Ensure code/analyze.py exists and implements the required functions.")
        raise

    # Load and clean data
    df = load_master_dataset(str(MASTER_DATASET_PATH))
    if df is None or df.empty:
        raise ValueError("Master dataset is empty or could not be loaded.")
    
    df_clean = clean_data(df)
    
    # Calculate VIF and flag
    vif_results = calculate_vif(df_clean)
    high_vif_flags = flag_high_vif(vif_results)
    
    # Run GLMM
    glmm_results = run_glmm(df_clean)
    
    # Run ZINB
    zinb_results = run_zinb_model(df_clean)
    
    # Apply Bonferroni correction
    corrected_pvalues = apply_bonferroni_correction(glmm_results, zinb_results)
    
    # Compile results
    results = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "dataset_path": str(MASTER_DATASET_PATH),
            "vif_check": {
                "results": vif_results.to_dict() if hasattr(vif_results, 'to_dict') else vif_results,
                "high_vif_flags": high_vif_flags
            },
            "model_types": ["GLMM", "ZINB"]
        },
        "glmm_results": glmm_results,
        "zinb_results": zinb_results,
        "corrected_pvalues": corrected_pvalues
    }
    
    return results

def load_existing_results():
    """Load existing results if they exist."""
    if ANALYSIS_RESULTS_PATH.exists():
        logger.info(f"Loading existing results from {ANALYSIS_RESULTS_PATH}")
        with open(ANALYSIS_RESULTS_PATH, 'r') as f:
            return json.load(f)
    return None

def write_results(results):
    """Write results to JSON file."""
    ensure_directories()
    with open(ANALYSIS_RESULTS_PATH, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Results written to {ANALYSIS_RESULTS_PATH}")

def main():
    """Main entry point."""
    logger.info("Starting T040: Generate analysis_results.json")
    
    # Check if results already exist
    existing = load_existing_results()
    if existing:
        logger.info("Results already exist. Skipping analysis run.")
        # Verify the structure contains required fields
        required_keys = ["glmm_results", "zinb_results", "corrected_pvalues"]
        missing = [k for k in required_keys if k not in existing]
        if missing:
            logger.warning(f"Existing results missing keys: {missing}. Re-running analysis.")
            results = run_analysis_pipeline()
        else:
            results = existing
    else:
        results = run_analysis_pipeline()
    
    write_results(results)
    logger.info("T040 completed successfully.")

if __name__ == "__main__":
    main()
