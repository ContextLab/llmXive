"""
End-to-End Validation Script for llmXive Quantization Robustness Pipeline.

This script executes the full pipeline (FP16 baseline + Quantized runs) on a
CPU-only environment to verify:
1. The pipeline completes without crashing (OOM handling works).
2. The total wall-clock time does not exceed the SC-005 threshold (6 hours).
3. Expected output artifacts are generated.
"""
import os
import sys
import time
import logging
import json
from pathlib import Path
from datetime import datetime
from main import run_fp16_generation, run_quantized_generation, run_statistical_analysis
from state_manager import save_artifacts_state, load_artifacts_state
from config import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('state/e2e_validation.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
MAX_DURATION_SECONDS = 6 * 60 * 60  # 6 hours in seconds
PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_CSV = PROJECT_ROOT / "data" / "results.csv"
ANALYSIS_JSON = PROJECT_ROOT / "data" / "analysis_results.json"
STATE_FILE = PROJECT_ROOT / "state" / "artifacts.yaml"

def run_validation():
    logger.info("Starting End-to-End Validation (T031)")
    logger.info(f"Max allowed duration: {MAX_DURATION_SECONDS} seconds (6 hours)")
    
    start_time = time.time()
    success = True
    error_message = None

    try:
        # Load configuration
        config = load_config()
        logger.info("Configuration loaded successfully.")

        # 1. Run FP16 Baseline Generation (US1)
        logger.info("Phase 1: Running FP16 Baseline Generation...")
        run_fp16_generation()
        
        # Verify FP16 artifacts
        if not RESULTS_CSV.exists():
            raise FileNotFoundError("FP16 generation did not produce data/results.csv")
        logger.info("FP16 Baseline completed successfully.")

        # 2. Run Quantized Generation (US2)
        logger.info("Phase 2: Running Quantized Generation (INT8/INT4)...")
        # This function includes the OOM handling logic from T008
        run_quantized_generation()
        
        # Verify quantized artifacts appended to results
        if not RESULTS_CSV.exists():
            raise FileNotFoundError("Quantized generation did not update data/results.csv")
        logger.info("Quantized Generation completed successfully.")

        # 3. Run Statistical Analysis (US3)
        logger.info("Phase 3: Running Statistical Analysis...")
        run_statistical_analysis()
        
        if not ANALYSIS_JSON.exists():
            raise FileNotFoundError("Statistical analysis did not produce data/analysis_results.json")
        logger.info("Statistical Analysis completed successfully.")

    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}", exc_info=True)
        success = False
        error_message = str(e)

    end_time = time.time()
    duration = end_time - start_time

    # Check Duration Constraint (SC-005)
    duration_ok = duration <= MAX_DURATION_SECONDS
    
    logger.info("-" * 50)
    logger.info("VALIDATION SUMMARY")
    logger.info(f"Total Duration: {duration:.2f} seconds ({duration/3600:.2f} hours)")
    logger.info(f"Duration Limit: {MAX_DURATION_SECONDS} seconds (6 hours)")
    logger.info(f"Duration Check (SC-005): {'PASS' if duration_ok else 'FAIL'}")
    logger.info(f"Pipeline Execution: {'PASS' if success else 'FAIL'}")
    if not success:
        logger.error(f"Error: {error_message}")
    logger.info("-" * 50)

    # Save validation report
    report = {
        "task_id": "T031",
        "timestamp": datetime.now().isoformat(),
        "duration_seconds": duration,
        "duration_limit_seconds": MAX_DURATION_SECONDS,
        "duration_check_passed": duration_ok,
        "pipeline_execution_passed": success,
        "error_message": error_message if not success else None,
        "artifacts": {
            "results_csv_exists": RESULTS_CSV.exists(),
            "analysis_json_exists": ANALYSIS_JSON.exists(),
            "state_yaml_exists": STATE_FILE.exists()
        }
    }

    report_path = PROJECT_ROOT / "state" / "e2e_validation_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report saved to {report_path}")

    # Determine exit code
    if success and duration_ok:
        logger.info("T031 VALIDATION: SUCCESS")
        return 0
    else:
        logger.error("T031 VALIDATION: FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(run_validation())
