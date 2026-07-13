"""
Main orchestration script for the sleep quality prediction pipeline.
Coordinates data download, preprocessing, feature engineering, and modeling.
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from config import get_paths, ensure_dirs
from utils.logging import log_stage_start, log_stage_complete, log_stage_error, setup_logging
from data.download_hcp import main as download_main
from data.preprocess import main as preprocess_main
from data.feature_engineering import main as feature_main
from modeling.train import main as train_main
from modeling.evaluate import main as evaluate_main
from modeling.report_generator import main as report_main
from modeling.interpret import main as interpret_main
from modeling.finalize_report import main as finalize_main

def run_pipeline():
    """Execute the complete sleep quality prediction pipeline."""
    paths = get_paths()
    
    # Ensure all required directories exist
    # ensure_dirs expects a dict of paths, not a list
    ensure_dirs(paths)
    
    log_file = os.path.join(paths["logs"], "pipeline_run.json")
    
    logger = setup_logging(log_file=log_file)
    logger.info("=== Starting Complete Sleep Quality Prediction Pipeline ===")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    
    try:
        # Step 1: Download raw data
        log_stage_start(logger, "Data Download")
        result = download_main()
        if result != 0:
            raise RuntimeError("Data download failed")
        log_stage_complete(logger, "Data Download", {"status": "success"})
        
        # Step 2: Preprocess data
        log_stage_start(logger, "Data Preprocessing")
        result = preprocess_main()
        if result != 0:
            raise RuntimeError("Data preprocessing failed")
        log_stage_complete(logger, "Data Preprocessing", {"status": "success"})
        
        # Step 3: Feature engineering (T014c)
        # Import and invoke the feature engineering function to process filtered subjects
        log_stage_start(logger, "Feature Engineering")
        result = feature_main()
        if result != 0:
            raise RuntimeError("Feature engineering failed")
        log_stage_complete(logger, "Feature Engineering", {"status": "success"})
        
        # Step 4: Train model
        log_stage_start(logger, "Model Training")
        result = train_main()
        if result != 0:
            raise RuntimeError("Model training failed")
        log_stage_complete(logger, "Model Training", {"status": "success"})
        
        # Step 5: Evaluate model
        log_stage_start(logger, "Model Evaluation")
        result = evaluate_main()
        if result != 0:
            raise RuntimeError("Model evaluation failed")
        log_stage_complete(logger, "Model Evaluation", {"status": "success"})
        
        # Step 6: Interpret model
        log_stage_start(logger, "Model Interpretation")
        result = interpret_main()
        if result != 0:
            logger.warning("Model interpretation completed with warnings")
        log_stage_complete(logger, "Model Interpretation", {"status": "success"})
        
        # Step 7: Generate report
        log_stage_start(logger, "Report Generation")
        result = report_main()
        if result != 0:
            raise RuntimeError("Report generation failed")
        log_stage_complete(logger, "Report Generation", {"status": "success"})
        
        # Step 8: Finalize report
        log_stage_start(logger, "Report Finalization")
        result = finalize_main()
        if result != 0:
            raise RuntimeError("Report finalization failed")
        log_stage_complete(logger, "Report Finalization", {"status": "success"})
        
        logger.info("=== Pipeline Complete ===")
        return 0
        
    except Exception as e:
        log_stage_error(logger, "Pipeline", str(e))
        logger.error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(run_pipeline())
