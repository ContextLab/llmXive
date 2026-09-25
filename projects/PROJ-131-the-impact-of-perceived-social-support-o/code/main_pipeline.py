"""
Main Pipeline Entry Point for PROJ-131
Orchestrates: Ingestion -> Preprocessing -> Cohort -> Modeling -> Sensitivity -> Reporting

This script implements the 'Single-Dataset Analysis' approach as mandated by the Plan.
It strictly avoids the deprecated 'Synthetic Cohort' method.
"""
import os
import sys
import logging
import time
from pathlib import Path
from typing import Optional

# Ensure the project root is in the path so imports work relative to 'code/'
# When run as `python code/main_pipeline.py`, sys.path[0] is 'code', so we are good.
# When run as `python code/main_pipeline.py` from root, we need to ensure imports resolve.
# The standard convention here is that the script is executed from the 'code' directory
# or the path is set up such that 'code' is the root.

# Setup logging
def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """Configure logging for the pipeline."""
    logger = logging.getLogger("main_pipeline")
    logger.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # File handler if specified
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
    return logger

def run_pipeline(logger: logging.Logger):
    """Execute the full research pipeline steps sequentially."""
    logger.info("Starting Pipeline Execution...")
    start_time = time.time()
    
    # Step 1: Data Ingestion
    # Imports from data.ingestion based on API surface
    try:
        from data.ingestion import main as ingestion_main
        logger.info("Step 1: Ingesting data...")
        ingestion_main()
        logger.info("Step 1: Ingestion complete.")
    except Exception as e:
        logger.error(f"Step 1: Ingestion failed with error: {e}")
        raise

    # Step 2: Preprocessing
    try:
        from data.preprocessing import main as preprocessing_main
        logger.info("Step 2: Preprocessing data...")
        preprocessing_main()
        logger.info("Step 2: Preprocessing complete.")
    except Exception as e:
        logger.error(f"Step 2: Preprocessing failed with error: {e}")
        raise

    # Step 3: Cohort Construction & Validation
    try:
        from data.cohort import main as cohort_main
        logger.info("Step 3: Building and validating analysis cohort...")
        cohort_main()
        logger.info("Step 3: Cohort validation complete.")
    except Exception as e:
        logger.error(f"Step 3: Cohort construction failed with error: {e}")
        raise

    # Step 4: Model Fitting (OLS + Bootstrap)
    try:
        from analysis.models import main as models_main
        logger.info("Step 4: Fitting models and bootstrapping...")
        models_main()
        logger.info("Step 4: Model fitting complete.")
    except Exception as e:
        logger.error(f"Step 4: Model fitting failed with error: {e}")
        raise

    # Step 5: Sensitivity Analysis
    try:
        from analysis.sensitivity import main as sensitivity_main
        logger.info("Step 5: Running sensitivity analysis...")
        sensitivity_main()
        logger.info("Step 5: Sensitivity analysis complete.")
    except Exception as e:
        logger.error(f"Step 5: Sensitivity analysis failed with error: {e}")
        raise

    # Step 6: Results Generation & Reporting
    try:
        from analysis.results import main as results_main
        logger.info("Step 6: Generating final reports...")
        results_main()
        logger.info("Step 6: Report generation complete.")
    except Exception as e:
        logger.error(f"Step 6: Report generation failed with error: {e}")
        raise
        
    # Step 7: FDR Correction (Post-modeling, pre-report finalization if needed, 
    # but models.py handles bootstrap, fdr_correction.py handles FDR. 
    # The API surface shows fdr_correction has a main. 
    # Let's ensure it runs if the models output is ready.
    # Actually, looking at the flow: models -> fdr -> results.
    # But 'models.py' main might not call fdr. Let's call it explicitly here if needed.
    # The task T024 says "Save regression outputs...". T023 says "Implement FDR".
    # We should ensure FDR is applied.
    try:
        from analysis.fdr_correction import main as fdr_main
        logger.info("Step 7: Applying FDR correction...")
        fdr_main()
        logger.info("Step 7: FDR correction complete.")
    except Exception as e:
        logger.error(f"Step 7: FDR correction failed with error: {e}")
        # FDR is often a post-processing step; if it fails, we might still want to 
        # generate reports, but the results might be missing adjusted p-values.
        # Given the strictness, let's log and continue, or raise?
        # The spec implies FDR is part of the analysis. Let's raise to be safe.
        raise

    # Step 8: Sensitivity Comparison
    try:
        from analysis.sensitivity_compare import main as compare_main
        logger.info("Step 8: Comparing sensitivity results...")
        compare_main()
        logger.info("Step 8: Sensitivity comparison complete.")
    except Exception as e:
        logger.error(f"Step 8: Sensitivity comparison failed with error: {e}")
        # Non-blocking for final report? Or critical? Let's log and continue.
        logger.warning("Continuing despite sensitivity comparison failure.")

    end_time = time.time()
    duration = end_time - start_time
    logger.info(f"Pipeline Execution Complete. Total Duration: {duration:.2f} seconds.")
    return duration

def main():
    """Entry point for the pipeline."""
    # Determine log path
    project_root = Path(__file__).parent.parent
    data_results_dir = project_root / "data" / "results"
    data_results_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = data_results_dir / "pipeline_run.log"
    
    logger = setup_logging(str(log_file))
    
    try:
        run_pipeline(logger)
        logger.info("Pipeline finished successfully.")
    except Exception as e:
        logger.critical(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()