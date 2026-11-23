"""
Main pipeline orchestrator for the llmXive automated science pipeline.
Implements runtime monitoring and enforcement of the 6-hour limit.
"""
import argparse
import logging
import signal
import sys
import time
from pathlib import Path

# Import from existing API surface
from config import Config, RuntimeLimitExceededError, enforce_runtime_limit, cancel_runtime_limit
from services.data_ingestion import run_data_ingestion_pipeline
from services.anxiety_scoring import run_full_scoring_pipeline_from_config as run_stage_2
from services.proxy_extractor import run_full_proxy_pipeline
from services.merge_and_save import run_merge_and_save_pipeline
from analysis.statistical_test import run_statistical_analysis_pipeline
from viz.save_visualization import run_visualization_pipeline

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def setup_runtime_monitor():
    """
    Sets up the runtime monitor to log elapsed time and enforce the 6-hour limit.
    This implements T004b: Integrate runtime monitor into code/main.py.
    """
    start_time = time.time()
    
    def signal_handler(signum, frame):
        elapsed = time.time() - start_time
        logger.error(f"Runtime limit exceeded after {elapsed:.2f} seconds ({elapsed/3600:.2f} hours).")
        cancel_runtime_limit()
        raise RuntimeLimitExceededError(f"Pipeline exceeded maximum runtime of {Config.RUNTIME_LIMIT_HOURS} hours.")

    # Set up the signal handler for the runtime limit
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(Config.RUNTIME_LIMIT_SECONDS)
    
    logger.info(f"Runtime monitor initialized. Limit: {Config.RUNTIME_LIMIT_HOURS} hours ({Config.RUNTIME_LIMIT_SECONDS} seconds).")
    return start_time

def stage_01_data_ingestion():
    """Stage 1: Data Ingestion"""
    logger.info("Starting Stage 1: Data Ingestion")
    try:
        run_data_ingestion_pipeline()
        logger.info("Stage 1 completed successfully.")
    except Exception as e:
        logger.error(f"Stage 1 failed: {e}")
        raise

def stage_02_preprocessing():
    """Stage 2: Preprocessing (Language & Gibberish filtering)"""
    logger.info("Starting Stage 2: Preprocessing")
    # This stage is handled within the anxiety scoring pipeline in current implementation
    # or can be extracted if needed. For now, we assume it runs as part of stage 3
    # or is a no-op if integrated.
    # Based on task list, T014b/T014c are completed, so we assume data is preprocessed.
    # We log the start of the next logical block which includes scoring.
    logger.info("Stage 2 (Preprocessing) assumed complete or integrated into Stage 3.")

def stage_03_anxiety_scoring():
    """Stage 3: Anxiety Scoring"""
    logger.info("Starting Stage 3: Anxiety Scoring")
    try:
        run_stage_2()
        logger.info("Stage 3 completed successfully.")
    except Exception as e:
        logger.error(f"Stage 3 failed: {e}")
        raise

def stage_04_proxy_extraction():
    """Stage 4: Proxy Extraction"""
    logger.info("Starting Stage 4: Proxy Extraction")
    try:
        run_full_proxy_pipeline()
        logger.info("Stage 4 completed successfully.")
    except Exception as e:
        logger.error(f"Stage 4 failed: {e}")
        raise

def stage_05_merge_and_validate():
    """Stage 5: Merge and Validate"""
    logger.info("Starting Stage 5: Merge and Validate")
    try:
        run_merge_and_save_pipeline()
        logger.info("Stage 5 completed successfully.")
    except Exception as e:
        logger.error(f"Stage 5 failed: {e}")
        raise

def stage_06_statistical_analysis():
    """Stage 6: Statistical Analysis"""
    logger.info("Starting Stage 6: Statistical Analysis")
    try:
        run_statistical_analysis_pipeline()
        logger.info("Stage 6 completed successfully.")
    except Exception as e:
        logger.error(f"Stage 6 failed: {e}")
        raise

def stage_07_visualization():
    """Stage 7: Visualization"""
    logger.info("Starting Stage 7: Visualization")
    try:
        run_visualization_pipeline()
        logger.info("Stage 7 completed successfully.")
    except Exception as e:
        logger.error(f"Stage 7 failed: {e}")
        raise

def run_pipeline():
    """
    Orchestrates the full pipeline with runtime monitoring.
    """
    start_time = setup_runtime_monitor()
    
    try:
        logger.info("Pipeline started.")
        
        # Execute stages sequentially
        stage_01_data_ingestion()
        stage_02_preprocessing()
        stage_03_anxiety_scoring()
        stage_04_proxy_extraction()
        stage_05_merge_and_validate()
        stage_06_statistical_analysis()
        stage_07_visualization()
        
        elapsed = time.time() - start_time
        logger.info(f"Pipeline completed successfully in {elapsed:.2f} seconds.")
        
    except RuntimeLimitExceededError:
        logger.error("Pipeline terminated due to runtime limit.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        sys.exit(1)
    finally:
        cancel_runtime_limit()

def main():
    parser = argparse.ArgumentParser(description="Run the full research pipeline.")
    parser.add_argument("--stage", type=int, choices=[1, 2, 3, 4, 5, 6, 7], 
                        help="Run a specific stage only (default: all stages)")
    args = parser.parse_args()

    if args.stage:
        logger.warning("Running specific stage only. Runtime limit still enforced.")
        start_time = setup_runtime_monitor()
        try:
            if args.stage == 1:
                stage_01_data_ingestion()
            elif args.stage == 2:
                stage_02_preprocessing()
            elif args.stage == 3:
                stage_03_anxiety_scoring()
            elif args.stage == 4:
                stage_04_proxy_extraction()
            elif args.stage == 5:
                stage_05_merge_and_validate()
            elif args.stage == 6:
                stage_06_statistical_analysis()
            elif args.stage == 7:
                stage_07_visualization()
            logger.info(f"Stage {args.stage} completed.")
        finally:
            cancel_runtime_limit()
    else:
        run_pipeline()

if __name__ == "__main__":
    main()