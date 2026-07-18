import sys
import time
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from config.loader import load_config
from generation.pipeline import run_pipeline
from analysis.metrics import run_metrics_pipeline
from analysis.stats import run_stats_pipeline
from analysis.reporter import run_reporter_pipeline
from hygiene.checksums import run_checksum_pipeline
from state.status_manager import update_execution_summary

logger = logging.getLogger(__name__)

def get_task_subset(config: Dict[str, Any]) -> List[int]:
    """
    Select a subset of tasks for the timing run.
    Uses the 'timing_subset_size' from config, defaulting to 10 if not present.
    """
    subset_size = config.get('timing_subset_size', 10)
    return list(range(subset_size))

def load_and_validate_config() -> Dict[str, Any]:
    """Load and validate the configuration."""
    config_path = Path('config/analysis.yaml')
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    config = load_config(config_path)
    return config

def run_timed_pipeline(config: Dict[str, Any], subset_ids: List[int]) -> float:
    """
    Run the full pipeline on the specified subset of tasks.
    Returns the total execution time in seconds.
    """
    start_time = time.time()
    
    logger.info(f"Starting timed pipeline run for {len(subset_ids)} tasks.")
    
    try:
        # Run Generation (US1)
        logger.info("Running Generation Pipeline...")
        run_pipeline(config)
        
        # Run Metrics (US2)
        logger.info("Running Metrics Pipeline...")
        run_metrics_pipeline(config)
        
        # Run Stats (US3)
        logger.info("Running Stats Pipeline...")
        run_stats_pipeline(config)
        
        # Run Reporter
        logger.info("Running Reporter Pipeline...")
        run_reporter_pipeline(config)
        
        # Checksums
        logger.info("Running Checksum Pipeline...")
        run_checksum_pipeline(config)
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        raise
        
    end_time = time.time()
    return end_time - start_time

def check_performance_threshold(duration: float, threshold_hours: float = 6.0) -> bool:
    """
    Check if the execution duration is within the threshold.
    """
    threshold_seconds = threshold_hours * 3600
    return duration <= threshold_seconds

def run_performance_verification(duration: float, subset_size: int):
    """
    Verify performance and log results.
    """
    threshold_hours = 6.0
    is_within_threshold = check_performance_threshold(duration, threshold_hours)
    
    log_path = Path('data/logs/timing.log')
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    status = "PASS" if is_within_threshold else "FAIL"
    
    with open(log_path, 'a') as f:
        f.write(f"{timestamp} | Verification: {status} | Duration: {duration:.2f}s | Threshold: {threshold_hours}h\n")
    
    logger.info(f"Performance Verification: {status}. Duration: {duration:.2f}s (Threshold: {threshold_hours}h)")
    
    if not is_within_threshold:
        logger.warning(f"Pipeline execution exceeded {threshold_hours} hours.")

def main():
    parser = argparse.ArgumentParser(description="Run pipeline subset and verify performance.")
    parser.add_argument('--config', type=str, default='config/analysis.yaml', help='Path to config file')
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('data/logs/pipeline.log')
        ]
    )
    
    config = load_and_validate_config()
    subset_size = config.get('timing_subset_size', 10)
    
    logger.info(f"Starting performance verification run. Subset size: {subset_size}.")
    
    duration = run_timed_pipeline(config, list(range(subset_size)))
    
    run_performance_verification(duration, subset_size)
    
    logger.info("Performance verification completed.")

if __name__ == '__main__':
    main()
