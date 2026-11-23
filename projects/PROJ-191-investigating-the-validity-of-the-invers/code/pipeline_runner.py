import os
import sys
import time
import logging
import json
import yaml
from pathlib import Path
from config import get_logger, setup_logging
from data.download import download_arxiv_source, extract_tarball, count_independent_runs, main as download_main
from data.parsers import parse_raw_data, parse_arxiv_2106_08611, parse_arxiv_2305_06325, main as parse_main
from data.harmonize import harmonize_experiment, construct_covariance_matrix, main as harmonize_main
from inference.mcmc import run_mcmc, main as mcmc_main
from inference.nested import run_nested_sampling, main as nested_main
from robustness.cross_val import perform_leave_one_out, perform_bootstrap_resampling, main as cv_main
from robustness.uncertainty import run_inflation_test, main as unc_main
from robustness.metrics import calculate_robustness_metrics, save_metrics, main as metrics_main
from agents.sc002_verifier import compute_sc002_verification, main as sc002_main
from data.state_manager import read_state, write_state, get_state_path, set_bootstrap_flag
from utils.versioning import atomic_update_json

# Configure logging
logger = get_logger("pipeline_runner")

def ensure_state_file():
    """Ensure the state YAML file exists at the expected path."""
    state_path = get_state_path()
    if not state_path.exists():
        state_path.parent.mkdir(parents=True, exist_ok=True)
        initial_state = {
            "project_id": "PROJ-191-investigating-the-validity-of-the-invers",
            "stages": {
                "data_acquisition": "pending",
                "harmonization": "pending",
                "inference": "pending",
                "robustness": "pending",
                "verification": "pending"
            },
            "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        with open(state_path, 'w') as f:
            yaml.dump(initial_state, f)
        logger.info(f"Created initial state file at {state_path}")
    else:
        logger.info(f"State file already exists at {state_path}")

def update_stage_status(stage_name: str, status: str, details: dict = None):
    """Update the status of a specific stage in the state file."""
    state_path = get_state_path()
    state = read_state()
    if "stages" not in state:
        state["stages"] = {}
    
    state["stages"][stage_name] = {
        "status": status,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "details": details or {}
    }
    state["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    
    # Atomic update
    atomic_update_json(state_path, state)
    logger.info(f"Updated stage '{stage_name}' to '{status}'")

def run_data_acquisition():
    """Execute the data acquisition phase (T013)."""
    logger.info("Starting data acquisition...")
    try:
        # Validate IDs (T013-VALIDATE-IDS)
        from data.validator import validate_arxiv_id
        arxiv_ids = ["2106.08611", "2305.06325"]
        for aid in arxiv_ids:
            validate_arxiv_id(aid)
        
        # Download data (T013-DATA)
        download_arxiv_source("2106.08611")
        download_arxiv_source("2305.06325")
        
        # Extract and count runs
        extract_tarball("2106.08611")
        extract_tarball("2305.06325")
        run_count = count_independent_runs()
        
        # Save run count
        run_count_path = Path("data/processed/run_count.json")
        run_count_path.parent.mkdir(parents=True, exist_ok=True)
        with open(run_count_path, 'w') as f:
            json.dump({"run_count": run_count}, f)
        
        # Parse data (T013-PARSE)
        parse_arxiv_2106_08611()
        parse_arxiv_2305_06325()
        
        update_stage_status("data_acquisition", "completed", {"run_count": run_count})
        return True
    except Exception as e:
        logger.error(f"Data acquisition failed: {e}")
        update_stage_status("data_acquisition", "failed", {"error": str(e)})
        return False

def run_harmonization():
    """Execute the harmonization phase (T014, T015)."""
    logger.info("Starting harmonization...")
    try:
        # Load parsed data and harmonize
        harmonize_experiment()
        
        # Construct covariance matrices
        construct_covariance_matrix()
        
        # Verify covariance (T015-C-VERIFY)
        # (Verification logic assumed to be inside construct_covariance_matrix or called here)
        
        update_stage_status("harmonization", "completed")
        return True
    except Exception as e:
        logger.error(f"Harmonization failed: {e}")
        update_stage_status("harmonization", "failed", {"error": str(e)})
        return False

def run_inference():
    """Execute the inference phase (T023, T024)."""
    logger.info("Starting inference...")
    try:
        # Run MCMC (T023-MCMC)
        run_mcmc()
        
        # Run Nested Sampling (T024)
        run_nested_sampling()
        
        # Save Bayes factor for later verification
        # (Assumed to be saved by nested.py)
        
        update_stage_status("inference", "completed")
        return True
    except Exception as e:
        logger.error(f"Inference failed: {e}")
        update_stage_status("inference", "failed", {"error": str(e)})
        return False

def run_robustness():
    """Execute the robustness phase (T030, T031, T033)."""
    logger.info("Starting robustness analysis...")
    try:
        # Cross-validation (T030)
        perform_leave_one_out()
        
        # Uncertainty inflation (T031)
        run_inflation_test()
        
        # Calculate metrics (T033)
        calculate_robustness_metrics()
        
        update_stage_status("robustness", "completed")
        return True
    except Exception as e:
        logger.error(f"Robustness analysis failed: {e}")
        update_stage_status("robustness", "failed", {"error": str(e)})
        return False

def run_verification():
    """Execute the verification phase (T038, T036)."""
    logger.info("Starting verification...")
    try:
        # Run SC-002 verification (T038)
        sc002_result = compute_sc002_verification()
        
        # Check validity report
        validity_report_path = Path("data/results/validity_report.json")
        if not validity_report_path.exists():
            raise FileNotFoundError("Validity report not found. Pipeline may have failed earlier.")
        
        with open(validity_report_path, 'r') as f:
            report = json.load(f)
        
        is_passed = report.get("pass", False) or report.get("SC002_KASS_RAFTERY_PASS", False)
        
        update_stage_status("verification", "completed", {"passed": is_passed})
        return is_passed
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        update_stage_status("verification", "failed", {"error": str(e)})
        return False

def run_full_pipeline():
    """Run the entire pipeline end-to-end."""
    logger.info("Starting full pipeline execution...")
    ensure_state_file()
    
    stages = [
        ("data_acquisition", run_data_acquisition),
        ("harmonization", run_harmonization),
        ("inference", run_inference),
        ("robustness", run_robustness),
        ("verification", run_verification)
    ]
    
    success = True
    for stage_name, stage_func in stages:
        if not stage_func():
            success = False
            logger.error(f"Pipeline stopped at stage: {stage_name}")
            break
    
    if success:
        logger.info("Pipeline completed successfully.")
    else:
        logger.error("Pipeline failed.")
    
    return success

def main():
    """Entry point for the pipeline runner."""
    setup_logging()
    run_full_pipeline()

if __name__ == "__main__":
    main()
