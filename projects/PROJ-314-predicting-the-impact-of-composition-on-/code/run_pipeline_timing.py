"""
Pipeline Timing and Execution Wrapper.

This script orchestrates the full pipeline execution with timing metrics.
It handles the ingestion, modeling, and reporting stages.
"""
import os
import sys
import time
import json
import logging
import traceback
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import modules using relative imports corrected for execution context
try:
    from ingestion import main as run_ingestion
    from modeling import main as run_modeling
    from report import main as run_reporting
    from diagnostics import main as run_diagnostics
    from generate_shap_plots import main as run_shap_plots
except ImportError as e:
    # Fallback for direct execution
    import ingestion
    import modeling
    import report
    import diagnostics
    import generate_shap_plots

    run_ingestion = ingestion.main
    run_modeling = modeling.main
    run_reporting = report.main
    run_diagnostics = diagnostics.main
    run_shap_plots = generate_shap_plots.main

from config import initialize_config, get_int_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / 'logs' / 'pipeline_timing.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize config
initialize_config()

def ensure_output_dir():
    """Ensure all required output directories exist."""
    dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "artifacts",
        project_root / "data" / "models",
        project_root / "data" / "results",
        project_root / "data" / "reports",
        project_root / "logs"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        logger.debug(f"Ensured directory: {d}")

def save_runtime_metrics(stage: str, duration: float, success: bool, error: str = None):
    """Save runtime metrics for a specific stage."""
    metrics_path = project_root / "data" / "results" / "pipeline_timing.json"
    metrics = {
        "stage": stage,
        "duration_seconds": duration,
        "success": success,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "error": error
    }

    # Load existing metrics if present
    if metrics_path.exists():
        with open(metrics_path, 'r') as f:
            existing = json.load(f)
        existing.append(metrics)
    else:
        existing = [metrics]

    with open(metrics_path, 'w') as f:
        json.dump(existing, f, indent=2)

def run_full_pipeline():
    """Execute the full pipeline with timing."""
    total_start = time.time()
    stages = [
        ("ingestion", run_ingestion),
        ("modeling", run_modeling),
        ("diagnostics", run_diagnostics),
        ("reporting", run_reporting),
        ("shap_plots", run_shap_plots)
    ]

    results = []
    overall_success = True

    for stage_name, stage_func in stages:
        logger.info(f"Starting stage: {stage_name}")
        stage_start = time.time()
        success = True
        error_msg = None

        try:
            # Call the stage function
            # Note: Some functions might need arguments or specific setup
            # We use a try-except block to catch any specific errors
            stage_func()
            logger.info(f"Stage {stage_name} completed successfully.")
        except SystemExit as e:
            # Some stages might exit with specific codes (e.g., data gap)
            if e.code != 0:
                success = False
                error_msg = f"Stage exited with code {e.code}"
                logger.warning(f"Stage {stage_name} exited with non-zero code: {e.code}")
            else:
                logger.info(f"Stage {stage_name} completed (exit code 0).")
        except Exception as e:
            success = False
            error_msg = str(e)
            logger.error(f"Stage {stage_name} failed: {traceback.format_exc()}")
            overall_success = False
            # Continue to next stage unless it's a critical failure
            if "critical" in error_msg.lower() or "fatal" in error_msg.lower():
                break

        duration = time.time() - stage_start
        results.append({
            "stage": stage_name,
            "duration": duration,
            "success": success,
            "error": error_msg
        })
        save_runtime_metrics(stage_name, duration, success, error_msg)

    total_duration = time.time() - total_start

    # Save overall summary
    summary = {
        "total_duration_seconds": total_duration,
        "stages": results,
        "overall_success": overall_success,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    summary_path = project_root / "data" / "results" / "pipeline_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Pipeline execution completed. Total time: {total_duration:.2f}s")
    logger.info(f"Summary saved to {summary_path}")

    return 0 if overall_success else 1

def main():
    """Main entry point."""
    logger.info("Pipeline Timing Wrapper Started")
    ensure_output_dir()
    return run_full_pipeline()

if __name__ == "__main__":
    sys.exit(main())
