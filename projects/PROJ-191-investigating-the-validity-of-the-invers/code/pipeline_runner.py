import os
import sys
import time
import logging
import json
import yaml
from pathlib import Path
from datetime import datetime

# Import project configuration and logging setup
from config import get_logger, ProjectConfig

# Import state management utilities
from data.state_manager import get_state_path, read_state, write_state, set_bootstrap_flag
from utils.versioning import atomic_update_json

# Import pipeline stage functions
from data.validator import validate_arxiv_id
from data.download import download_arxiv_source, extract_tarball, count_independent_runs
from data.parsers import parse_arxiv_2106_08611, parse_arxiv_2305_06325
from data.harmonize import harmonize_experiment, construct_covariance_matrix
from data.fallback_logic import check_and_set_bootstrap_flag, prepare_analysis_dataset
from inference.mcmc import run_mcmc
from inference.nested import run_nested_sampling
from robustness.cross_val import perform_leave_one_out, perform_bootstrap_resampling
from robustness.uncertainty import inflate_covariance, compute_bayes_factor
from robustness.metrics import calculate_robustness_metrics, save_metrics
from agents.sc002_verifier import compute_sc002_verification

# Configure logging
logger = get_logger("pipeline_runner")

def ensure_state_file(config: ProjectConfig) -> Path:
    """Ensure the state YAML file exists at the expected location."""
    state_path = get_state_path(config)
    if not state_path.exists():
        logger.info(f"Creating initial state file at {state_path}")
        initial_state = {
            "project_id": config.project_id,
            "version": "0.0.1",
            "started_at": datetime.now().isoformat(),
            "stages": {
                "setup": {"status": "pending", "started": None, "completed": None},
                "foundational": {"status": "pending", "started": None, "completed": None},
                "data_acquisition": {"status": "pending", "started": None, "completed": None},
                "harmonization": {"status": "pending", "started": None, "completed": None},
                "inference": {"status": "pending", "started": None, "completed": None},
                "robustness": {"status": "pending", "started": None, "completed": None},
                "verification": {"status": "pending", "started": None, "completed": None},
                "validation": {"status": "pending", "started": None, "completed": None}
            },
            "artifacts": [],
            "metrics": {}
        }
        with open(state_path, 'w') as f:
            yaml.dump(initial_state, f, default_flow_style=False)
    return state_path

def update_stage_status(config: ProjectConfig, stage_name: str, status: str, error: str = None):
    """Update the status of a specific stage in the state file."""
    state_path = get_state_path(config)
    state = read_state(config)
    
    if stage_name not in state["stages"]:
        raise ValueError(f"Unknown stage: {stage_name}")
    
    stage = state["stages"][stage_name]
    stage["status"] = status
    
    if status == "running" and not stage["started"]:
        stage["started"] = datetime.now().isoformat()
    elif status == "completed" and not stage["completed"]:
        stage["completed"] = datetime.now().isoformat()
    elif status == "failed":
        stage["error"] = error or "Unknown error"
        stage["completed"] = datetime.now().isoformat()
    
    write_state(config, state)
    logger.info(f"Stage '{stage_name}' status updated to: {status}")

def run_data_acquisition(config: ProjectConfig) -> bool:
    """Execute data acquisition stage: validate IDs, download, extract, parse."""
    logger.info("Starting data acquisition stage")
    update_stage_status(config, "data_acquisition", "running")
    
    try:
        # Validate arXiv IDs
        arxiv_ids = ["2106.08611", "2305.06325"]
        for arxiv_id in arxiv_ids:
            validate_arxiv_id(arxiv_id, config)
        logger.info("All arXiv IDs validated successfully")
        
        # Download and extract data
        raw_dir = config.data_dir / "raw"
        for arxiv_id in arxiv_ids:
            tarball_path = download_arxiv_source(arxiv_id, raw_dir, config)
            extract_tarball(tarball_path, raw_dir, config)
        
        # Count independent runs
        runs = count_independent_runs(raw_dir, config)
        logger.info(f"Found {runs} independent experimental runs")
        
        # Set bootstrap flag if needed
        if runs < 3:
            logger.warning(f"Insufficient runs ({runs} < 3) for leave-one-out cross-validation")
            set_bootstrap_flag(config, True)
        else:
            set_bootstrap_flag(config, False)
        
        update_stage_status(config, "data_acquisition", "completed")
        return True
    except Exception as e:
        logger.error(f"Data acquisition failed: {str(e)}")
        update_stage_status(config, "data_acquisition", "failed", str(e))
        return False

def run_harmonization(config: ProjectConfig) -> bool:
    """Execute harmonization stage: parse, convert units, align grid, construct covariance."""
    logger.info("Starting harmonization stage")
    update_stage_status(config, "harmonization", "running")
    
    try:
        raw_dir = config.data_dir / "raw"
        processed_dir = config.data_dir / "processed"
        
        # Parse raw data
        dataset_1 = parse_arxiv_2106_08611(raw_dir, config)
        dataset_2 = parse_arxiv_2305_06325(raw_dir, config)
        
        # Harmonize experiments
        harmonized_1 = harmonize_experiment(dataset_1, config)
        harmonized_2 = harmonize_experiment(dataset_2, config)
        
        # Construct covariance matrices
        cov_diag = construct_covariance_matrix(harmonized_1, harmonized_2, method="diagonal", config=config)
        cov_banded = construct_covariance_matrix(harmonized_1, harmonized_2, method="banded", bandwidth=20, config=config)
        
        # Save outputs
        import numpy as np
        np.save(processed_dir / "covariance_matrix.npy", cov_diag)
        np.save(processed_dir / "covariance_banded.npy", cov_banded)
        
        update_stage_status(config, "harmonization", "completed")
        return True
    except Exception as e:
        logger.error(f"Harmonization failed: {str(e)}")
        update_stage_status(config, "harmonization", "failed", str(e))
        return False

def run_inference(config: ProjectConfig) -> bool:
    """Execute inference stage: MCMC and nested sampling."""
    logger.info("Starting inference stage")
    update_stage_status(config, "inference", "running")
    
    try:
        processed_dir = config.data_dir / "processed"
        results_dir = config.data_dir / "results"
        
        # Check if bootstrap mode is active
        use_bootstrap = check_and_set_bootstrap_flag(config)
        
        # Run MCMC
        chains = run_mcmc(processed_dir, results_dir, config)
        
        # Run nested sampling for model comparison
        bayes_factor = run_nested_sampling(processed_dir, results_dir, config)
        
        update_stage_status(config, "inference", "completed")
        return True
    except Exception as e:
        logger.error(f"Inference failed: {str(e)}")
        update_stage_status(config, "inference", "failed", str(e))
        return False

def run_robustness(config: ProjectConfig) -> bool:
    """Execute robustness stage: cross-validation and uncertainty inflation."""
    logger.info("Starting robustness stage")
    update_stage_status(config, "robustness", "running")
    
    try:
        processed_dir = config.data_dir / "processed"
        results_dir = config.data_dir / "results"
        
        # Check bootstrap mode
        use_bootstrap = check_and_set_bootstrap_flag(config)
        
        if use_bootstrap:
            logger.info("Running bootstrap resampling for robustness")
            bootstrap_results = perform_bootstrap_resampling(processed_dir, results_dir, config)
        else:
            logger.info("Running leave-one-out cross-validation")
            cv_results = perform_leave_one_out(processed_dir, results_dir, config)
        
        # Uncertainty inflation test
        inflation_factor = 1.1  # Default, can be read from config
        inflate_covariance(processed_dir, results_dir, inflation_factor, config)
        
        # Calculate metrics
        metrics = calculate_robustness_metrics(results_dir, config)
        save_metrics(metrics, results_dir, config)
        
        update_stage_status(config, "robustness", "completed")
        return True
    except Exception as e:
        logger.error(f"Robustness analysis failed: {str(e)}")
        update_stage_status(config, "robustness", "failed", str(e))
        return False

def run_verification(config: ProjectConfig) -> bool:
    """Execute verification stage: SC-002 validation and report generation."""
    logger.info("Starting verification stage")
    update_stage_status(config, "verification", "running")
    
    try:
        results_dir = config.data_dir / "results"
        
        # Compute SC-002 verification
        verification_result = compute_sc002_verification(results_dir, config)
        
        # Generate validity report
        validity_report = {
            "sc002_pass": verification_result.get("pass", False),
            "bayes_factor": verification_result.get("bayes_factor", None),
            "p_value": verification_result.get("p_value", None),
            "timestamp": datetime.now().isoformat()
        }
        
        with open(results_dir / "validity_report.json", 'w') as f:
            json.dump(validity_report, f, indent=2)
        
        update_stage_status(config, "verification", "completed")
        return True
    except Exception as e:
        logger.error(f"Verification failed: {str(e)}")
        update_stage_status(config, "verification", "failed", str(e))
        return False

def run_full_pipeline(config: ProjectConfig) -> bool:
    """Execute the complete pipeline end-to-end."""
    logger.info("Starting full pipeline execution")
    
    stages = [
        ("data_acquisition", run_data_acquisition),
        ("harmonization", run_harmonization),
        ("inference", run_inference),
        ("robustness", run_robustness),
        ("verification", run_verification)
    ]
    
    for stage_name, stage_func in stages:
        if not stage_func(config):
            logger.error(f"Pipeline failed at stage: {stage_name}")
            return False
    
    logger.info("Pipeline completed successfully")
    return True

def main():
    """Main entry point for pipeline execution."""
    config = ProjectConfig()
    logger = get_logger("pipeline_runner")
    
    try:
        # Ensure state file exists
        state_path = ensure_state_file(config)
        logger.info(f"State file initialized at: {state_path}")
        
        # Run full pipeline
        success = run_full_pipeline(config)
        
        if success:
            logger.info("Full pipeline validation completed successfully")
            print("Pipeline execution: SUCCESS")
            return 0
        else:
            logger.error("Full pipeline validation failed")
            print("Pipeline execution: FAILED")
            return 1
            
    except Exception as e:
        logger.error(f"Pipeline execution failed with exception: {str(e)}")
        print(f"Pipeline execution: FAILED - {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
