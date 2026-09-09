"""
Main orchestration script for the Social Validation Impact Study.

This script implements the data acquisition and validation pipeline:
1. Attempts to load real data.
2. If real data fails, generates synthetic data.
3. Validates the data.
4. Processes the data (calculates Perceived Social Validation).
5. Writes a run log.
"""
import json
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path to ensure imports work when run as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import data modules
from data.loader import load_real_data
from data.generator import generate_synthetic_data, verify_association_recovery
from data.validator import validate_data
from data.processor import process_data

# Import utilities
from utils.exceptions import DataLoadError, DataGapError, InsufficientSampleError
from utils.logger import get_logger, log_pipeline_step, log_data_load_start, log_data_load_success, log_data_load_error
from utils.config import get_config

def main():
    """
    Orchestrates the data pipeline: Load -> Generate (if needed) -> Validate -> Process -> Log.
    """
    logger = get_logger(__name__)
    config = get_config()
    
    # Ensure output directory exists
    data_processed_dir = project_root / "data" / "processed"
    data_processed_dir.mkdir(parents=True, exist_ok=True)
    
    log_path = data_processed_dir / "pipeline_run_log.json"
    
    run_log = {
        "timestamp": datetime.now().isoformat(),
        "status": "started",
        "steps": []
    }

    try:
        # Step 1: Attempt Real Data Load
        log_pipeline_step(logger, "Attempting real data load...", "info")
        log_data_load_start(logger)
        
        try:
            real_data = load_real_data()
            if real_data is not None and not real_data.empty:
                log_data_load_success(logger, f"Loaded {len(real_data)} rows from real source.")
                run_log["steps"].append({
                    "step": "real_data_load",
                    "status": "success",
                    "rows": len(real_data)
                })
                df = real_data
            else:
                raise DataLoadError("Real data load returned empty or None.")
                
        except DataLoadError as e:
            logger.warning(f"Real data load failed: {e}. Switching to synthetic generation.")
            run_log["steps"].append({
                "step": "real_data_load",
                "status": "failed",
                "reason": str(e)
            })
            
            # Step 2: Generate Synthetic Data
            log_pipeline_step(logger, "Generating synthetic data...", "info")
            df = generate_synthetic_data()
            
            if df is None or df.empty:
                raise RuntimeError("Synthetic data generation failed to produce a DataFrame.")
            
            # Verify association recovery as per T011b
            verify_association_recovery(df)
            
            log_data_load_success(logger, f"Generated {len(df)} rows of synthetic data.")
            run_log["steps"].append({
                "step": "synthetic_data_generation",
                "status": "success",
                "rows": len(df)
            })
            
        except Exception as e:
            # Catch any other unexpected errors during load/generate
            log_data_load_error(logger, str(e))
            run_log["steps"].append({
                "step": "load_or_generate",
                "status": "failed",
                "reason": str(e)
            })
            raise

        # Step 3: Validate Data
        log_pipeline_step(logger, "Validating data...", "info")
        log_validation_start = lambda l: l.info("Validation started.")
        log_validation_start(logger)
        
        try:
            validation_result = validate_data(df)
            log_validation_success = lambda l: l.info("Validation passed.")
            log_validation_success(logger)
            
            run_log["steps"].append({
                "step": "validation",
                "status": "success",
                "details": validation_result
            })
            
        except DataGapError as e:
            logger.error(f"Validation failed: {e}")
            run_log["steps"].append({
                "step": "validation",
                "status": "failed",
                "error": "DataGapError",
                "reason": str(e)
            })
            raise
            
        except InsufficientSampleError as e:
            logger.error(f"Validation failed: {e}")
            run_log["steps"].append({
                "step": "validation",
                "status": "failed",
                "error": "InsufficientSampleError",
                "reason": str(e)
            })
            raise

        # Step 4: Process Data (Calculate Perceived Social Validation)
        log_pipeline_step(logger, "Processing data (calculating PSV)...", "info")
        df_processed = process_data(df)
        
        run_log["steps"].append({
            "step": "processing",
            "status": "success",
            "rows": len(df_processed)
        })
        
        # Optional: Save processed data for downstream tasks (US2)
        processed_csv_path = data_processed_dir / "validated_data.csv"
        df_processed.to_csv(processed_csv_path, index=False)
        logger.info(f"Processed data saved to {processed_csv_path}")

        # Final Success
        run_log["status"] = "completed"
        run_log["final_row_count"] = len(df_processed)
        log_pipeline_step(logger, "Pipeline completed successfully.", "info")

    except (DataGapError, InsufficientSampleError) as e:
        run_log["status"] = "failed"
        run_log["error_type"] = type(e).__name__
        run_log["error_message"] = str(e)
        log_pipeline_step(logger, f"Pipeline failed: {e}", "error")
        raise

    except Exception as e:
        run_log["status"] = "failed"
        run_log["error_type"] = type(e).__name__
        run_log["error_message"] = str(e)
        log_pipeline_step(logger, f"Pipeline failed with unexpected error: {e}", "error")
        raise

    finally:
        # Always write the log
        with open(log_path, 'w') as f:
            json.dump(run_log, f, indent=2)
        logger.info(f"Run log written to {log_path}")

    return df_processed

if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(1)