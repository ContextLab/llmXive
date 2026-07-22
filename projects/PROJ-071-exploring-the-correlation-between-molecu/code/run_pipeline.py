"""
Full Pipeline Execution Script for PROJ-071.

Executes the complete research pipeline:
1. Data Ingestion & Merging (US1)
2. Descriptor Calculation (US1)
3. Data Standardization & Stratification (US2)
4. Correlation & Regression Analysis (US2)
5. Visualization & Reporting (US3)
6. Reproducibility Logging & Verification (US3)

Output Artifacts:
- data/processed/merged_drugs.csv
- data/processed/analysis_results.json
- results_report.md
- reproducibility_log.json
- data/gate_status.json
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from logging_config import setup_logging, get_logger, log_pipeline_start, log_pipeline_complete, log_pipeline_failure
from ingest import main as run_ingest
from descriptors import main as run_descriptors
from standardize import main as run_standardize
from analysis import main as run_analysis
from viz import main as run_viz
from report import main as run_report
from reproducibility_audit import main as run_reproducibility_audit

# Setup logging
setup_logging()
logger = get_logger(__name__)

def run_pipeline():
    """Execute the full pipeline end-to-end."""
    start_time = time.time()
    status = "success"
    error_msg = None
    
    log_pipeline_start(logger, "T055_Full_Pipeline_Smoke_Test")
    
    try:
        # Stage 1: Ingestion & Merging (US1)
        logger.info("Stage 1: Running Data Ingestion and Merging...")
        run_ingest()
        logger.info("Stage 1: Complete.")
        
        # Stage 2: Descriptor Calculation (US1)
        logger.info("Stage 2: Calculating Molecular Descriptors...")
        run_descriptors()
        logger.info("Stage 2: Complete.")
        
        # Stage 3: Standardization & Stratification (US2)
        logger.info("Stage 3: Standardizing Data and Stratifying...")
        run_standardize()
        logger.info("Stage 3: Complete.")
        
        # Stage 4: Analysis (US2)
        logger.info("Stage 4: Running Correlation and Regression Analysis...")
        run_analysis()
        logger.info("Stage 4: Complete.")
        
        # Stage 5: Visualization (US3)
        logger.info("Stage 5: Generating Visualizations...")
        run_viz()
        logger.info("Stage 5: Complete.")
        
        # Stage 6: Reporting (US3)
        logger.info("Stage 6: Generating Final Report and Reproducibility Logs...")
        run_report()
        logger.info("Stage 6: Complete.")
        
        # Stage 7: Reproducibility Audit (US3)
        logger.info("Stage 7: Running Reproducibility Audit...")
        run_reproducibility_audit()
        logger.info("Stage 7: Complete.")
        
    except Exception as e:
        status = "failed"
        error_msg = str(e)
        logger.error(f"Pipeline failed at stage: {e}", exc_info=True)
        log_pipeline_failure(logger, "T055_Full_Pipeline_Smoke_Test", str(e))
    
    end_time = time.time()
    total_duration = end_time - start_time
    
    # Save metrics
    metrics = {
        "task_id": "T055",
        "start_time": datetime.fromtimestamp(start_time).isoformat(),
        "end_time": datetime.fromtimestamp(end_time).isoformat(),
        "total_duration_seconds": total_duration,
        "status": status,
        "error": error_msg
    }
    
    metrics_path = DATA_DIR / "output" / "pipeline_metrics.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Pipeline execution metrics saved to {metrics_path}")
    
    if status == "success":
        log_pipeline_complete(logger, "T055_Full_Pipeline_Smoke_Test", total_duration)
        logger.info("Full Pipeline Smoke Test Completed Successfully.")
        
        # Final verification of required artifacts
        required_artifacts = [
            DATA_DIR / "processed" / "merged_drugs.csv",
            DATA_DIR / "processed" / "analysis_results.json",
            PROJECT_ROOT / "results_report.md",
            PROJECT_ROOT / "reproducibility_log.json"
        ]
        
        missing = []
        for artifact in required_artifacts:
            if not artifact.exists():
                missing.append(str(artifact))
            elif artifact.stat().st_size == 0:
                missing.append(f"{artifact} (empty)")
        
        if missing:
            logger.error(f"Missing or empty required artifacts: {missing}")
            return False
        else:
            logger.info("All required artifacts verified successfully.")
            return True
    else:
        return False

def main():
    """Entry point."""
    success = run_pipeline()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()