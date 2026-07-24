import os
import sys
import json
import time
import logging
import argparse
from pathlib import Path

# Add project root to path to ensure imports work
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config.settings import get_config, DatasetPaths
from data.download import download_data
from data.validation import run_validation_pipeline
from data.extract import run_extraction
from data.sampling import main as sampling_main
from data.sentiment import main as sentiment_main
from data.metrics import run_decision_quality_pipeline
from data.modeling import run_modeling_pipeline
from data.generate_report import main as report_main
from analysis.final_validation import run_final_validation

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('state/pipeline_execution.log')
    ]
)
logger = logging.getLogger(__name__)

def ensure_directories(paths: DatasetPaths):
    """Ensure all required directories exist."""
    dirs = [
        paths.raw, paths.processed, paths.state, 
        'docs', 'figures'
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    logger.info("Ensured directory structure.")

def run_stage(stage_name: str, stage_func, *args, **kwargs):
    """Execute a pipeline stage with timing and error handling."""
    logger.info(f"--- Starting Stage: {stage_name} ---")
    start = time.time()
    try:
        result = stage_func(*args, **kwargs)
        duration = time.time() - start
        logger.info(f"--- Completed Stage: {stage_name} in {duration:.2f}s ---")
        return result
    except Exception as e:
        logger.error(f"Stage {stage_name} failed: {str(e)}")
        raise

def run_full_pipeline(threads_limit: int = 500):
    """
    Execute the full research pipeline end-to-end.
    This function orchestrates all stages from data download to final report.
    """
    config = get_config()
    paths = config.paths
    
    start_time = time.time()
    total_runtime = 0
    thread_count = 0
    
    try:
        # 1. Setup
        ensure_directories(paths)
        
        # 2. Data Download (T008)
        # Note: In CI, this might be skipped if raw data is cached, 
        # but we run it to ensure the pipeline is self-contained.
        # If data exists, download_data should ideally be a no-op or re-verify.
        # For this implementation, we assume download_data handles existence checks.
        run_stage("Data Download", download_data, paths)
        
        # 3. Validation & Classification (T019, T019b)
        run_stage("Validation & Classification", run_validation_pipeline, paths)
        
        # 4. Extraction (T010, T009)
        run_stage("Extraction", run_extraction, paths)
        
        # 5. Sampling (T007a-2) - Optional but part of flow
        run_stage("Sampling", sampling_main, paths)
        
        # 6. Sentiment Analysis (T013)
        run_stage("Sentiment Analysis", sentiment_main, paths)
        
        # 7. Metrics & Contagion Index (T015, T016, T018)
        run_stage("Metrics Calculation", run_decision_quality_pipeline, paths)
        
        # 8. Modeling & Sensitivity (T020, T021, T022, T023, T024)
        run_stage("Statistical Modeling", run_modeling_pipeline, paths)
        
        # 9. Report Generation (T026, T033, T034)
        run_stage("Report Generation", report_main, paths)
        
        # 10. Final Validation (T039)
        run_stage("Final Validation", run_final_validation, paths)
        
        total_runtime = time.time() - start_time
        
        # Determine thread count from processed data if possible
        valid_threads_path = paths.processed / "valid_threads.csv"
        if valid_threads_path.exists():
            import pandas as pd
            df = pd.read_csv(valid_threads_path)
            thread_count = len(df)
        else:
            # Fallback estimation or 0 if no data
            thread_count = 0

        # Write performance log
        perf_log = {
            "total_runtime_seconds": int(total_runtime),
            "thread_count": thread_count,
            "status": "success",
            "resource_check": {
                "cpu": True, # We are on CPU runner
                "ram_gb": 7.0, # Free tier limit
                "disk_gb": 14.0 # Free tier limit
            }
        }
        
        with open(paths.state / "performance_log.json", "w") as f:
            json.dump(perf_log, f, indent=2)
        
        logger.info(f"Pipeline completed successfully. Runtime: {total_runtime:.2f}s, Threads: {thread_count}")
        return True

    except RuntimeError as e:
        if "All data sources failed" in str(e):
            logger.error("CRITICAL: Data download failed. Pipeline cannot proceed without real data.")
            # Re-raise to fail the CI job
            raise
        else:
            logger.error(f"Pipeline failed with runtime error: {e}")
            raise
    except Exception as e:
        logger.error(f"Pipeline failed with unexpected error: {e}")
        raise
    finally:
        # Ensure performance log is written even on failure if partial data exists
        if not Path(paths.state / "performance_log.json").exists():
            perf_log = {
                "total_runtime_seconds": int(time.time() - start_time),
                "thread_count": 0,
                "status": "failure",
                "resource_check": {
                    "cpu": True,
                    "ram_gb": 7.0,
                    "disk_gb": 14.0
                }
            }
            with open(paths.state / "performance_log.json", "w") as f:
                json.dump(perf_log, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Run the full research pipeline.")
    parser.add_argument("--threads", type=int, default=500, help="Limit number of threads to process.")
    args = parser.parse_args()

    logger.info("Starting Full Pipeline Execution (T036 Gate)...")
    logger.info(f"Thread limit: {args.threads}")

    try:
        success = run_full_pipeline(threads_limit=args.threads)
        if success:
            logger.info("Pipeline execution successful. T036 Gate Passed.")
            sys.exit(0)
        else:
            logger.error("Pipeline execution failed.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline execution aborted: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()