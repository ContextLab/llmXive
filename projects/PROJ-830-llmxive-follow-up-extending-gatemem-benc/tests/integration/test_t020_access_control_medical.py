"""
Integration test for Task T020: Access Control Evaluation on Medical Domain.

This script executes the Gatekeeper and Baseline pipelines on the "medical" domain
subset of the GateMem dataset and calculates the Access Control score.

It verifies that:
1. The pipeline runs successfully on real data.
2. Results are written to disk in the expected format.
3. An Access Control score is calculated and is a valid float between 0.0 and 1.0.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Project root adjustment for execution context
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.logging_config import setup_logging, pin_random_seed
from code.data.loader import fetch_gatemem, validate_fields, run_validation_pipeline
from code.gatekeeper.pipeline import run_gatekeeper_pipeline, load_prompt_templates
from code.gatekeeper.metrics import calculate_access_control_score, load_json_file
from code.utils.config import get_llm_singleton
from code.utils.profiling import profile_execution

logger = setup_logging(__name__)

def run_t020_medical_domain():
    """
    Executes the T020 task: Run pipeline on 'medical' domain and verify Access Control score.
    """
    logger.info("Starting T020: Medical Domain Access Control Evaluation")
    
    # 1. Setup and Configuration
    pin_random_seed(42)
    llm_instance = get_llm_singleton()
    logger.info(f"Using LLM Instance ID: {llm_instance.instance_id}")
    
    prompt_templates = load_prompt_templates()
    
    # 2. Data Loading (Real Data Only)
    # Fetch dataset, filtering for 'medical' domain if possible, or load all and filter
    logger.info("Fetching GateMem dataset...")
    try:
        raw_data = run_validation_pipeline(domains=["medical"])
    except Exception as e:
        logger.error(f"Data loading failed: {e}")
        raise

    if not raw_data:
        raise ValueError("No data found for 'medical' domain. Aborting T020.")
    
    logger.info(f"Loaded {len(raw_data)} episodes for 'medical' domain.")

    # 3. Run Gatekeeper Pipeline
    logger.info("Running Gatekeeper pipeline on medical domain...")
    gatekeeper_results_path = PROJECT_ROOT / "data" / "processed" / "gatekeeper_results_medical.json"
    
    # Ensure directory exists
    gatekeeper_results_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        gatekeeper_scores = run_gatekeeper_pipeline(
            episodes=raw_data,
            prompt_templates=prompt_templates,
            output_path=str(gatekeeper_results_path),
            method="gatekeeper"
        )
    except Exception as e:
        logger.error(f"Gatekeeper pipeline failed: {e}")
        raise

    if not gatekeeper_scores:
        raise ValueError("Gatekeeper pipeline produced no results.")
    
    logger.info(f"Gatekeeper pipeline completed. Results saved to {gatekeeper_results_path}")

    # 4. Run Baseline Pipeline (Long Context)
    logger.info("Running Baseline (Long Context) pipeline on medical domain...")
    baseline_results_path = PROJECT_ROOT / "data" / "processed" / "baseline_longcontext_results_medical.json"
    baseline_results_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        baseline_scores = run_gatekeeper_pipeline(
            episodes=raw_data,
            prompt_templates=prompt_templates,
            output_path=str(baseline_results_path),
            method="baseline_longcontext"
        )
    except Exception as e:
        logger.error(f"Baseline pipeline failed: {e}")
        raise

    if not baseline_scores:
        raise ValueError("Baseline pipeline produced no results.")
    
    logger.info(f"Baseline pipeline completed. Results saved to {baseline_results_path}")

    # 5. Calculate Access Control Score
    logger.info("Calculating Access Control score...")
    
    # Load results back to calculate metrics against ground truth
    gatekeeper_data = load_json_file(gatekeeper_results_path)
    baseline_data = load_json_file(baseline_results_path)
    
    # Calculate Access Control for Gatekeeper
    # The metric function expects the raw results and ground truth logic
    # We assume calculate_access_control_score handles the comparison internally
    # based on the 'outcome' field in the original episode data.
    
    # Re-load raw data with ground truth for metric calculation
    # (Assuming run_validation_pipeline returns episodes with 'outcome' and 'leak-target')
    ac_score = calculate_access_control_score(gatekeeper_data, raw_data)
    
    logger.info(f"Access Control Score (Gatekeeper) on Medical Domain: {ac_score:.4f}")
    
    # 6. Verification and Output
    assert isinstance(ac_score, float), "Access Control score must be a float."
    assert 0.0 <= ac_score <= 1.0, f"Access Control score {ac_score} must be between 0.0 and 1.0."
    
    # Write final report to disk as evidence
    report_path = PROJECT_ROOT / "data" / "processed" / "t020_medical_access_control_report.json"
    report_data = {
        "task_id": "T020",
        "domain": "medical",
        "gatekeeper_ac_score": ac_score,
        "gatekeeper_results_file": str(gatekeeper_results_path),
        "baseline_results_file": str(baseline_results_path),
        "episode_count": len(raw_data),
        "status": "completed"
    }
    
    with open(report_path, "w") as f:
        json.dump(report_data, f, indent=2)
    
    logger.info(f"Final report written to {report_path}")
    print(f"T020 SUCCESS: Medical Domain Access Control Score = {ac_score:.4f}")
    
    return ac_score

def main():
    try:
        run_t020_medical_domain()
    except Exception as e:
        logger.error(f"T020 FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
