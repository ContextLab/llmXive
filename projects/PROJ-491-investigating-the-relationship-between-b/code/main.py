"""
Main orchestration entry point for the Brain Network Dynamics and Anticipatory Reward Processing pipeline.

This script executes the pipeline phases in order:
1. Setup: Create directory structure
2. Contract Generation: Create JSON contracts for atlas and ROI
3. Data Ingestion: Download and validate HCP data
4. Preprocessing: Extract BOLD time series and VS activation
5. Connectivity: Calculate dynamic functional connectivity and flexibility scores
6. Analysis: Correlate flexibility with VS activation
7. Reporting: Generate final markdown report
"""

import sys
import logging
import os
from pathlib import Path

# Add project root to path if needed
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_stage(module_name: str, stage_name: str):
    """Import and run the main function of a pipeline stage module."""
    logger.info(f"--- Starting {stage_name} ---")
    try:
        # Dynamically import the module
        module = __import__(module_name, fromlist=['main'])
        if hasattr(module, 'main'):
            module.main()
            logger.info(f"--- {stage_name} completed successfully ---")
        else:
            logger.error(f"Module {module_name} does not have a main() function")
            sys.exit(1)
    except Exception as e:
        logger.error(f"--- {stage_name} failed: {e} ---")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

def main():
    """Orchestrate the full pipeline execution."""
    logger.info("Starting Brain Network Dynamics Pipeline")

    # Phase 1: Setup
    run_stage('setup_directories', "Phase 1: Setup Directories")

    # Phase 2: Contract Generation
    # Fix: Use explicit coordinate definition instead of nilearn fetch to avoid import error
    # Ensure we are in the project root directory before generating contracts
    os.chdir(project_root)
    
    run_stage('create_atlas_power264_json', "Phase 2: Generate Power264 Atlas Contract")
    run_stage('create_roi_ventral_striatum_json', "Phase 2: Generate VS ROI Contract")
    run_stage('create_power_excl_vs_json', "Phase 2: Generate Exclusion Contract")

    # Phase 3: Data Ingestion & Validation
    run_stage('data_ingestion', "Phase 3: Download HCP Data")
    run_stage('session_validation_metrics', "Phase 3: Calculate Session Validation Metrics")
    run_stage('write_excluded_session_ids', "Phase 3: Write Excluded Session IDs")
    run_stage('verify_session_validation_metrics', "Phase 3: Verify Session Metrics")
    run_stage('verify_tr', "Phase 3: Verify TR Values")

    # Phase 4: Preprocessing
    run_stage('preprocessing', "Phase 4: Extract BOLD Time Series")
    run_stage('aggregate_vs_activation', "Phase 4: Aggregate VS Activation")
    run_stage('verify_vs_activation', "Phase 4: Verify VS Activation")

    # Phase 5: Connectivity & Flexibility
    # Note: Assuming connectivity.py is the module for US2
    run_stage('connectivity', "Phase 5: Calculate dFC and Flexibility")

    # Phase 6: Analysis
    run_stage('analysis', "Phase 6: Correlation Analysis")

    # Phase 7: Reporting
    run_stage('reporting', "Phase 7: Generate Final Report")

    logger.info("Pipeline execution completed successfully.")

if __name__ == "__main__":
    main()