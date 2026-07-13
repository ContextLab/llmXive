"""
Main orchestration script for the sleep quality prediction pipeline.
Coordinates download, preprocessing, feature engineering, and modeling steps.
"""
import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import List, Optional

# Add project root to path for imports
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_paths, ensure_dirs, set_all_seeds
from utils.logging import setup_logging, log_stage_start, log_stage_complete, log_stage_error
from data.download_hcp import filter_subjects, save_filtered_subjects, load_behavioral_data
from data.preprocess import main as preprocess_main
from data.feature_engineering import main as feature_main
from modeling.train import main as train_main
from modeling.evaluate import main as evaluate_main
from modeling.report_generator import main as report_main

def run_pipeline(subject_subset: Optional[List[str]] = None) -> bool:
    """
    Execute the full data pipeline.
    
    Args:
        subject_subset: Optional list of subject IDs to process. 
                        If None, uses all valid subjects from behavioral data.
                        
    Returns:
        True if the pipeline completed successfully, False otherwise.
    """
    paths = get_paths()
    
    # CRITICAL FIX: ensure_dirs is called here, but it might fail if a file exists where a dir is expected.
    # We handle this by catching the error and logging it, but the pipeline should fail if directories are not ready.
    try:
        ensure_dirs()
    except FileExistsError as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Configuration error: {e}")
        return False
    
    # Set random seeds for reproducibility
    set_all_seeds(42)
    
    logger = setup_logging(paths['log_file'])
    log_stage_start(logger, "Pipeline Execution")
    
    try:
        # 1. Download and Filter Data (T014a logic)
        log_stage_start(logger, "Step 1: Data Download and Filtering")
        try:
            # Load behavioral data (assumed downloaded by T005/T014a)
            behavioral_path = paths['raw_dir'] / "behavioral" / "hcp1200_behavioral_data.csv"
            if not behavioral_path.exists():
                raise FileNotFoundError(f"Behavioral data not found at {behavioral_path}")
            
            df = load_behavioral_data(str(behavioral_path))
            
            # Filter subjects if not provided
            if subject_subset is None:
                valid_subjects = filter_subjects(df)
                save_filtered_subjects(valid_subjects, paths['processed_dir'] / "filtered_subjects.txt")
            else:
                valid_subjects = subject_subset
                
            logger.info(f"Total subjects to process: {len(valid_subjects)}")
        except Exception as e:
            log_stage_error(logger, "Data Download and Filtering", str(e))
            return False
        log_stage_complete(logger, "Step 1: Data Download and Filtering")
        
        # 2. Preprocessing (T014b logic)
        log_stage_start(logger, "Step 2: Preprocessing")
        try:
            # Call preprocessing main with the filtered subjects
            # This will fail if real CIFTI data is not present, which is the correct behavior.
            preprocess_success = preprocess_main(valid_subjects)
            if not preprocess_success:
                raise RuntimeError("Preprocessing failed for some subjects")
        except Exception as e:
            log_stage_error(logger, "Preprocessing", str(e))
            return False
        log_stage_complete(logger, "Step 2: Preprocessing")
        
        # 3. Feature Engineering (T014c logic - THIS TASK)
        log_stage_start(logger, "Step 3: Feature Engineering")
        try:
            # Call feature engineering main with the filtered subjects
            # This invokes compute_pairwise_correlation, fisher_z_transform, etc.
            feature_success = feature_main(valid_subjects)
            if not feature_success:
                logger.warning("Feature engineering had failures, but continuing...")
        except Exception as e:
            log_stage_error(logger, "Feature Engineering", str(e))
            return False
        log_stage_complete(logger, "Step 3: Feature Engineering")
        
        # 4. Modeling (T020 logic)
        log_stage_start(logger, "Step 4: Training and Evaluation")
        try:
            # Train the model
            train_main()
            
            # Evaluate (permutation, bootstrap)
            evaluate_main()
        except Exception as e:
            log_stage_error(logger, "Modeling", str(e))
            return False
        log_stage_complete(logger, "Step 4: Training and Evaluation")
        
        # 5. Report Generation (T026 logic)
        log_stage_start(logger, "Step 5: Report Generation")
        try:
            report_main()
        except Exception as e:
            log_stage_error(logger, "Report Generation", str(e))
            return False
        log_stage_complete(logger, "Step 5: Report Generation")
        
        log_stage_complete(logger, "Pipeline Execution", extra={
            "status": "success",
            "subjects_processed": len(valid_subjects)
        })
        return True
            
    except Exception as e:
        log_stage_error(logger, "Pipeline Execution", str(e))
        return False

def main():
    """CLI entry point."""
    # Parse arguments if needed, currently defaults to full pipeline
    success = run_pipeline()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())