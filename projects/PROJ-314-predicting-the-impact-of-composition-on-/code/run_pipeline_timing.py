import os
import sys
import time
import json
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from ingestion import main as run_ingestion
from modeling import main as run_modeling
from generate_shap_plots import main as run_shap_plots
from report import main as run_report

logger = logging.getLogger(__name__)

def ensure_output_dir():
    """Ensure the data/results directory exists."""
    output_dir = project_root / "data" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def save_runtime_metrics(duration_seconds, output_dir):
    """Save runtime metrics to JSON file."""
    metrics = {
        "total_duration_seconds": duration_seconds,
        "total_duration_hours": duration_seconds / 3600.0,
        "limit_hours": 6.0,
        "passed_limit": duration_seconds < (6.0 * 3600),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    }
    output_path = output_dir / "runtime_metrics.json"
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Runtime metrics saved to {output_path}")
    return metrics

def run_full_pipeline():
    """
    Execute the full pipeline: Ingestion -> Modeling -> SHAP -> Report.
    Returns the total duration in seconds.
    """
    logger.info("Starting full pipeline execution for timing measurement.")
    
    start_time = time.time()
    
    # Step 1: Ingestion
    logger.info("Step 1: Running Ingestion Pipeline...")
    try:
        run_ingestion()
        logger.info("Ingestion pipeline completed successfully.")
    except SystemExit as e:
        if e.code != 0:
            logger.error("Ingestion pipeline failed with exit code: {}".format(e.code))
            raise
    except Exception as e:
        logger.error("Ingestion pipeline failed with exception: {}".format(str(e)))
        raise

    # Step 2: Modeling
    logger.info("Step 2: Running Modeling Pipeline...")
    try:
        run_modeling()
        logger.info("Modeling pipeline completed successfully.")
    except SystemExit as e:
        if e.code != 0:
            logger.error("Modeling pipeline failed with exit code: {}".format(e.code))
            raise
    except Exception as e:
        logger.error("Modeling pipeline failed with exception: {}".format(str(e)))
        raise

    # Step 3: SHAP Plots
    logger.info("Step 3: Running SHAP Analysis...")
    try:
        run_shap_plots()
        logger.info("SHAP analysis completed successfully.")
    except SystemExit as e:
        if e.code != 0:
            logger.error("SHAP analysis failed with exit code: {}".format(e.code))
            raise
    except Exception as e:
        logger.error("SHAP analysis failed with exception: {}".format(str(e)))
        raise

    # Step 4: Report Generation
    logger.info("Step 4: Running Report Generation...")
    try:
        run_report()
        logger.info("Report generation completed successfully.")
    except SystemExit as e:
        if e.code != 0:
            logger.error("Report generation failed with exit code: {}".format(e.code))
            raise
    except Exception as e:
        logger.error("Report generation failed with exception: {}".format(str(e)))
        raise

    end_time = time.time()
    duration = end_time - start_time
    
    logger.info(f"Full pipeline execution completed in {duration:.2f} seconds ({duration/3600:.2f} hours).")
    return duration

def main():
    """Main entry point for the timing script."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(project_root / "logs" / "pipeline_timing.log")
        ]
    )

    output_dir = ensure_output_dir()
    
    try:
        duration = run_full_pipeline()
        metrics = save_runtime_metrics(duration, output_dir)
        
        if not metrics["passed_limit"]:
            logger.warning("Pipeline exceeded the 6-hour limit!")
            return 1
        else:
            logger.info("Pipeline completed within the 6-hour limit.")
            return 0
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
