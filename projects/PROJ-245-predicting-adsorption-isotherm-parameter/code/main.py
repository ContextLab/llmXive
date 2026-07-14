import argparse
import logging
import sys
import json
from pathlib import Path
from datetime import datetime

# Importing from project modules
from data.synthetic_gen import generate_synthetic_data, main as gen_main
from data.validate_schema import validate_dataframe, main as validate_main
from data.preprocess import preprocess_pipeline, main as preprocess_main
from data.download import attempt_nist_fetch, write_verification_log, main as download_main
from data.load_external import load_external_data, validate_external_data, run_load_external_pipeline, main as external_main
from models.train import run_training_pipeline, main as train_main
from models.evaluate import run_evaluation_pipeline, main as eval_main
from interpret.shap_analysis import run_shap_analysis_pipeline, main as shap_main, validate_consensus, retrain_top_features
from interpret.diagnostics import run_diagnostic_pipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_dirs():
    """Create necessary directories for the project."""
    dirs = [
        "data/raw", "data/processed", "data/external", "data/validation",
        "data/models", "figures", "logs"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def run_download_phase():
    logger.info("Running download phase...")
    # Attempt to fetch real data, log failure if it happens
    success = attempt_nist_fetch()
    if not success:
        write_verification_log(status="failed", reason="NIST fetch failed")
    else:
        write_verification_log(status="success", reason="NIST fetch succeeded")

def run_synthetic_gen_phase():
    logger.info("Running synthetic data generation...")
    generate_synthetic_data(n_samples=5000)

def run_preprocess_phase():
    logger.info("Running preprocessing...")
    preprocess_pipeline()

def run_train_phase():
    logger.info("Running model training...")
    run_training_pipeline()

def run_evaluation_phase():
    logger.info("Running model evaluation...")
    eval_results = run_evaluation_pipeline()
    return eval_results

def run_shap_phase():
    logger.info("Running SHAP analysis...")
    run_shap_analysis_pipeline()

def run_diagnostic_phase():
    logger.info("Running diagnostic analysis for low R2...")
    # Check if evaluation results indicate low R2 before running
    eval_file = Path("data/models/evaluation_results.json")
    if eval_file.exists():
        with open(eval_file, 'r') as f:
            data = json.load(f)
            best_r2 = data.get('best_model', {}).get('r2', 1.0)
            if best_r2 < 0.5:
                logger.warning(f"R2 ({best_r2}) is below 0.5. Triggering diagnostic phase.")
                run_diagnostic_pipeline()
            else:
                logger.info(f"R2 ({best_r2}) is acceptable. Skipping diagnostic phase.")
    else:
        logger.warning("Evaluation results not found. Skipping diagnostic phase.")

def run_full_pipeline(mode="synthetic"):
    ensure_dirs()
    
    if mode == "synthetic":
        logger.info("Starting full pipeline in SYNTHETIC mode.")
        run_synthetic_gen_phase()
        run_preprocess_phase()
        run_train_phase()
        run_evaluation_phase()
        run_shap_phase()
        # Only run diagnostics if R2 is low
        run_diagnostic_phase()
    elif mode == "external":
        logger.info("Starting full pipeline in EXTERNAL mode.")
        # Download/Load external data
        run_load_external_pipeline()
        
        # CRITICAL: Trigger T032 and T033 logic ONLY when external data is present
        # These tasks implement the validation logic in shap_analysis.py
        # The orchestrator must call the specific functions to generate the reports
        logger.info("External data detected. Triggering consensus validation (T032) and re-training (T033).")
        
        try:
            # Call the specific validation logic implemented in T032
            validate_consensus()
            logger.info("Consensus validation (T032) completed successfully.")
        except Exception as e:
            logger.error(f"Consensus validation (T032) failed: {e}")
            # Do not stop the pipeline, just log the error
        
        try:
            # Call the specific re-training logic implemented in T033
            retrain_top_features()
            logger.info("Top-3 re-training (T033) completed successfully.")
        except Exception as e:
            logger.error(f"Top-3 re-training (T033) failed: {e}")
            # Do not stop the pipeline, just log the error

        run_preprocess_phase()
        run_train_phase()
        run_evaluation_phase()
        run_shap_phase()
        run_diagnostic_phase()
    else:
        logger.error(f"Unknown mode: {mode}")
        sys.exit(1)

def run_synthetic_flow():
    run_full_pipeline(mode="synthetic")

def run_external_flow():
    run_full_pipeline(mode="external")

def main():
    parser = argparse.ArgumentParser(description="llmXive Adsorption Isotherm Pipeline")
    parser.add_argument("--mode", type=str, choices=["synthetic", "external"], default="synthetic",
                        help="Data source mode: synthetic or external")
    parser.add_argument("--full", action="store_true", help="Run the full pipeline")
    
    args = parser.parse_args()
    
    if args.full:
        run_full_pipeline(mode=args.mode)
    else:
        # Default to just synthetic gen for quick testing if no flag
        run_synthetic_gen_phase()

if __name__ == "__main__":
    main()