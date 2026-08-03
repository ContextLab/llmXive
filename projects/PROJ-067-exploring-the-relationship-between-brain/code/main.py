import os
import sys
import json
import logging
import time
import traceback
from pathlib import Path
from datetime import datetime

# Import pipeline phases from existing modules
from data.validate_metadata import main as validate_metadata_main
from data.filter_subjects import main as filter_subjects_main
from data.download import main as download_main
from data.preprocess import main as preprocess_main
from data.cleanup import main as cleanup_main
from analysis.verify_atlas_labels import main as verify_atlas_labels_main
from analysis.metrics import main as metrics_main
from analysis.stats import main as stats_main
from analysis.generate_stats_json import main as generate_stats_json_main
from analysis.permutation_test import main as permutation_test_main
from analysis.power_analysis import main as power_analysis_main
from analysis.plot_results import main as plot_results_main
from analysis.ensure_null_reporting import main as ensure_null_reporting_main
from analysis.validate_results_schema import main as validate_results_schema_main
from utils.config import get_config_summary
from utils.memory_monitor import MemoryMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('results/pipeline.log')
    ]
)
logger = logging.getLogger('main')

# Runtime constraints
MAX_RUNTIME_SECONDS = 4 * 60 * 60  # 4 hours
START_TIME = None
PHASE_TIMERS = {}

def get_phase_timer(phase_name: str):
    """Get a timer function for a specific phase."""
    def timer():
        return time.time() - START_TIME
    return timer

def log_runtime_results():
    """Log runtime results to results/runtime_log.json."""
    end_time = time.time()
    total_runtime = end_time - START_TIME
    
    runtime_data = {
        "start_time": datetime.fromtimestamp(START_TIME).isoformat(),
        "end_time": datetime.fromtimestamp(end_time).isoformat(),
        "total_runtime_seconds": total_runtime,
        "total_runtime_formatted": f"{total_runtime/3600:.2f} hours",
        "phase_timings": {}
    }
    
    # Add phase timings
    for phase, timings in PHASE_TIMERS.items():
        duration = timings['end'] - timings['start']
        runtime_data["phase_timings"][phase] = {
            "duration_seconds": duration,
            "start_time": datetime.fromtimestamp(timings['start']).isoformat(),
            "end_time": datetime.fromtimestamp(timings['end']).isoformat()
        }
    
    # Ensure results directory exists
    results_dir = Path('results')
    results_dir.mkdir(exist_ok=True)
    
    # Write runtime log
    runtime_log_path = results_dir / 'runtime_log.json'
    with open(runtime_log_path, 'w') as f:
        json.dump(runtime_data, f, indent=2)
    
    logger.info(f"Runtime log written to {runtime_log_path}")
    logger.info(f"Total runtime: {total_runtime/3600:.2f} hours")
    
    return total_runtime

def run_pipeline():
    """Run the full pipeline with runtime verification."""
    global START_TIME
    START_TIME = time.time()
    
    logger.info("Starting pipeline execution")
    logger.info(f"Maximum allowed runtime: {MAX_RUNTIME_SECONDS} seconds (4 hours)")
    
    # Initialize memory monitor
    memory_monitor = MemoryMonitor(interval=10)  # Check every 10 seconds
    memory_monitor.start()
    
    phases = [
        ("validate_metadata", validate_metadata_main),
        ("filter_subjects", filter_subjects_main),
        ("download", download_main),
        ("preprocess", preprocess_main),
        ("cleanup_intermediates", cleanup_main),
        ("verify_atlas_labels", verify_atlas_labels_main),
        ("metrics", metrics_main),
        ("stats", stats_main),
        ("generate_stats_json", generate_stats_json_main),
        ("permutation_test", permutation_test_main),
        ("power_analysis", power_analysis_main),
        ("plot_results", plot_results_main),
        ("ensure_null_reporting", ensure_null_reporting_main),
        ("validate_results_schema", validate_results_schema_main)
    ]
    
    try:
        for phase_name, phase_func in phases:
            logger.info(f"Starting phase: {phase_name}")
            
            # Check runtime before each phase
            current_runtime = time.time() - START_TIME
            if current_runtime > MAX_RUNTIME_SECONDS:
                error_msg = f"Pipeline exceeded maximum runtime of {MAX_RUNTIME_SECONDS} seconds ({MAX_RUNTIME_SECONDS/3600} hours) at phase {phase_name}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            # Record phase start
            PHASE_TIMERS[phase_name] = {'start': time.time()}
            
            try:
                # Execute phase
                phase_func()
                
                # Record phase end
                PHASE_TIMERS[phase_name]['end'] = time.time()
                logger.info(f"Phase {phase_name} completed successfully")
                
            except Exception as e:
                logger.error(f"Phase {phase_name} failed with error: {str(e)}")
                logger.error(traceback.format_exc())
                raise
            
            # Check runtime after each phase
            current_runtime = time.time() - START_TIME
            if current_runtime > MAX_RUNTIME_SECONDS:
                error_msg = f"Pipeline exceeded maximum runtime of {MAX_RUNTIME_SECONDS} seconds ({MAX_RUNTIME_SECONDS/3600} hours) after phase {phase_name}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
        
        logger.info("All phases completed successfully")
        
    finally:
        # Stop memory monitor
        memory_monitor.stop()
        
        # Log final runtime results
        total_runtime = log_runtime_results()
        
        # Final runtime check
        if total_runtime > MAX_RUNTIME_SECONDS:
            error_msg = f"Pipeline exceeded maximum runtime of {MAX_RUNTIME_SECONDS} seconds ({MAX_RUNTIME_SECONDS/3600} hours)"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        logger.info("Pipeline execution completed within time limit")
    
    return True

def main():
    """Main entry point for the pipeline."""
    try:
        # Get configuration summary
        config_summary = get_config_summary()
        logger.info(f"Configuration: {config_summary}")
        
        # Run the pipeline
        run_pipeline()
        
        logger.info("Pipeline completed successfully")
        return 0
        
    except RuntimeError as e:
        logger.error(f"Runtime error: {str(e)}")
        # Re-raise to ensure CI failure
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())