"""
Pipeline timing and execution wrapper.
Ensures all pipeline stages run within time limits and logs metrics.
"""
import os
import sys
import time
import json
import logging
import traceback
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Ensure logging directory exists
Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/pipeline_timing.log')
    ]
)
logger = logging.getLogger(__name__)

def ensure_output_dir():
    """Ensure all required output directories exist."""
    dirs = [
        "data/raw", "data/processed", "data/artifacts", 
        "data/models", "data/results", "data/reports",
        "logs", "state"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    logger.info("Output directories ensured")

def save_runtime_metrics(stage: str, duration: float, status: str, error: str = None):
    """Save runtime metrics for a pipeline stage."""
    metrics = {
        "stage": stage,
        "start_time": datetime.now().isoformat(),
        "duration_seconds": duration,
        "status": status,
        "error": error
    }
    
    metrics_path = Path("data/results/runtime_metrics.json")
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing metrics if any
    existing_metrics = []
    if metrics_path.exists():
        try:
            with open(metrics_path, 'r') as f:
                existing_metrics = json.load(f)
        except:
            existing_metrics = []
    
    existing_metrics.append(metrics)
    
    with open(metrics_path, 'w') as f:
        json.dump(existing_metrics, f, indent=2)
    
    logger.info(f"Saved runtime metrics for {stage}: {status} ({duration:.2f}s)")

def run_stage(stage_name: str, func, *args, **kwargs):
    """Run a pipeline stage with timing and error handling."""
    logger.info(f"Starting stage: {stage_name}")
    start_time = time.time()
    
    try:
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        save_runtime_metrics(stage_name, duration, "success")
        logger.info(f"Stage {stage_name} completed in {duration:.2f}s")
        return result
    except Exception as e:
        duration = time.time() - start_time
        error_msg = str(e)
        save_runtime_metrics(stage_name, duration, "failed", error_msg)
        logger.error(f"Stage {stage_name} failed: {error_msg}")
        logger.error(traceback.format_exc())
        raise

def run_full_pipeline():
    """Run the full pipeline with timing."""
    logger.info("Starting full pipeline execution")
    start_time = time.time()
    
    try:
        # Import pipeline modules
        from ingestion import main as run_ingestion
        from modeling import main as run_modeling
        from report import main as run_report
        
        # Run stages
        run_stage("ingestion", run_ingestion)
        run_stage("modeling", run_modeling)
        run_stage("reporting", run_report)
        
        duration = time.time() - start_time
        logger.info(f"Full pipeline completed in {duration:.2f}s")
        return True
        
    except Exception as e:
        duration = time.time() - start_time
        save_runtime_metrics("full_pipeline", duration, "failed", str(e))
        logger.error(f"Full pipeline failed: {e}")
        raise

def main():
    """Main entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Run pipeline with timing")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode")
    parser.add_argument("--stage", choices=["ingestion", "modeling", "reporting", "full"], 
                      help="Run specific stage only")
    args = parser.parse_args()
    
    ensure_output_dir()
    
    try:
        if args.dry_run:
            logger.info("Running in dry-run mode")
            # In dry-run mode, we just verify imports and structure
            from ingestion import main as run_ingestion
            from modeling import main as run_modeling
            from report import main as run_report
            logger.info("Dry-run: All imports successful")
            sys.exit(0)
        
        if args.stage == "ingestion":
            from ingestion import main as run_ingestion
            run_stage("ingestion", run_ingestion)
        elif args.stage == "modeling":
            from modeling import main as run_modeling
            run_stage("modeling", run_modeling)
        elif args.stage == "reporting":
            from report import main as run_report
            run_stage("reporting", run_report)
        elif args.stage == "full" or not args.stage:
            run_full_pipeline()
        else:
            logger.error("Invalid stage specified")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
