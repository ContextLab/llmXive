import os
import sys
import time
import json
import logging
import traceback
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/pipeline_timing.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def ensure_output_dir():
    """Ensure output directory exists."""
    Path('data/results').mkdir(parents=True, exist_ok=True)

def save_runtime_metrics(start_time: float, end_time: float, status: str, error: Optional[str] = None):
    """Save runtime metrics to a JSON file."""
    metrics = {
        "start_time": start_time,
        "end_time": end_time,
        "duration_seconds": end_time - start_time,
        "status": status,
        "error": error
    }
    output_path = 'data/results/runtime_metrics.json'
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Runtime metrics saved to {output_path}")

def run_full_pipeline():
    """Run the full pipeline: ingestion, modeling, diagnostics."""
    logger.info("Starting full pipeline execution.")
    
    try:
        # Import and run ingestion
        logger.info("Running ingestion pipeline...")
        from ingestion import main as run_ingestion
        run_ingestion()
        logger.info("Ingestion pipeline completed.")
        
        # Import and run modeling
        logger.info("Running modeling pipeline...")
        from modeling import main as run_modeling
        run_modeling()
        logger.info("Modeling pipeline completed.")
        
        # Import and run diagnostics/reporting
        logger.info("Running diagnostics and reporting...")
        from diagnostics import main as run_diagnostics
        run_diagnostics()
        logger.info("Diagnostics completed.")
        
        from report import main as run_report
        run_report()
        logger.info("Reporting completed.")
        
        return True, None
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        logger.error(traceback.format_exc())
        return False, str(e)

def main():
    """Main entry point for pipeline timing."""
    start_time = time.time()
    ensure_output_dir()
    
    success, error = run_full_pipeline()
    
    end_time = time.time()
    status = "success" if success else "failure"
    
    save_runtime_metrics(start_time, end_time, status, error)
    
    if not success:
        logger.error("Pipeline failed. Check logs for details.")
        sys.exit(1)
    else:
        logger.info("Pipeline completed successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()
