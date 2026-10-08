import os
import sys
import time
import json
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "code"))

from training import run_training_pipeline
from evaluation import run_evaluation_pipeline
from utils import setup_logging, save_json, load_json, get_env_var

logger = logging.getLogger(__name__)

TIME_LIMIT_SECONDS = 6 * 3600  # 6 hours in seconds

def run_timed_training():
    """
    Executes the training pipeline and measures elapsed time.
    Returns (success, elapsed_time, error_message)
    """
    logger.info("Starting timed training execution...")
    start_time = time.time()
    
    try:
        # Run the actual training pipeline
        # This loads data from data/processed/train_set.parquet and trains the model
        run_training_pipeline()
        
        elapsed_time = time.time() - start_time
        logger.info(f"Training completed in {elapsed_time:.2f} seconds.")
        return True, elapsed_time, None
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Training failed after {elapsed_time:.2f} seconds: {e}")
        return False, elapsed_time, str(e)

def run_timed_evaluation():
    """
    Executes the evaluation pipeline and measures elapsed time.
    Returns (success, elapsed_time, error_message)
    """
    logger.info("Starting timed evaluation execution...")
    start_time = time.time()
    
    try:
        # Run the actual evaluation pipeline
        # This loads the model from results/artifacts/model.pkl and evaluates
        run_evaluation_pipeline()
        
        elapsed_time = time.time() - start_time
        logger.info(f"Evaluation completed in {elapsed_time:.2f} seconds.")
        return True, elapsed_time, None
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Evaluation failed after {elapsed_time:.2f} seconds: {e}")
        return False, elapsed_time, str(e)

def main():
    """
    Main entry point for T030b: Verify execution time <= 6 hours.
    Runs training and evaluation, checks timing, and writes results.
    """
    # Setup logging
    log_dir = Path(project_root) / "results" / "metrics"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "timing_verification.log"),
            logging.StreamHandler()
        ]
    )

    logger.info("=" * 50)
    logger.info("Starting T030b: Execution Time Verification")
    logger.info(f"Time limit: {TIME_LIMIT_SECONDS} seconds (6 hours)")
    logger.info("=" * 50)

    # Run Training
    train_success, train_time, train_error = run_timed_training()
    
    # Run Evaluation
    eval_success, eval_time, eval_error = run_timed_evaluation()

    total_time = train_time + eval_time
    passed = train_success and eval_success and (total_time <= TIME_LIMIT_SECONDS)

    # Prepare report
    report = {
        "task_id": "T030b",
        "time_limit_seconds": TIME_LIMIT_SECONDS,
        "total_execution_time_seconds": total_time,
        "training": {
            "success": train_success,
            "elapsed_seconds": train_time,
            "error": train_error
        },
        "evaluation": {
            "success": eval_success,
            "elapsed_seconds": eval_time,
            "error": eval_error
        },
        "verification_passed": passed,
        "message": "Execution time verification successful." if passed else "Execution time exceeded limit or pipeline failed."
    }

    # Save report
    output_path = log_dir / "timing_verification_report.json"
    save_json(report, output_path)

    logger.info("-" * 50)
    logger.info(f"Total Time: {total_time:.2f} seconds ({total_time/3600:.2f} hours)")
    logger.info(f"Limit: {TIME_LIMIT_SECONDS} seconds ({TIME_LIMIT_SECONDS/3600:.2f} hours)")
    logger.info(f"Status: {'PASSED' if passed else 'FAILED'}")
    logger.info(f"Report saved to: {output_path}")
    logger.info("-" * 50)

    if not passed:
        if not train_success or not eval_success:
            logger.error("Pipeline execution failed.")
        else:
            logger.error("Time limit exceeded.")
        sys.exit(1)
    else:
        logger.info("T030b verification completed successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()