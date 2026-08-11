"""
Task T046: Measure Pipeline Runtime.

Executes the full pipeline (Ingestion -> Descriptors -> Modeling -> Reporting)
and logs the total duration and step-wise timings to data/reports/runtime_metrics.json.

This script fixes the import error in the previous run by using the correct
public API names exposed by sibling modules (e.g., `main` from `ingestion`,
`main` from `modeling`, etc.).
"""
import os
import sys
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path to ensure imports work correctly
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import load_environment, initialize_config, get_int_config
from ingestion import main as run_ingestion
from descriptors import main as run_descriptors
from modeling import main as run_modeling
from generate_shap_plots import main as run_shap
from generate_metrics_report import main as run_report
from hash_artifacts import main as run_hash

logger = logging.getLogger(__name__)

def ensure_output_dir():
    """Ensure the output directory for runtime metrics exists."""
    output_dir = project_root / "data" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def save_runtime_metrics(metrics: Dict[str, Any], output_dir: Path):
    """Save the collected runtime metrics to a JSON file."""
    output_file = output_dir / "runtime_metrics.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Runtime metrics saved to {output_file}")

def run_step(name: str, func, *args, **kwargs) -> float:
    """Execute a pipeline step and measure its duration."""
    logger.info(f"Starting step: {name}")
    start_time = time.time()
    try:
        func(*args, **kwargs)
        duration = time.time() - start_time
        logger.info(f"Completed step: {name} in {duration:.2f} seconds")
        return duration
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Failed step: {name} after {duration:.2f} seconds: {e}")
        raise

def run_full_pipeline():
    """
    Execute the full pipeline sequentially.
    
    Sequence:
    1. Ingestion (fetch, clean, gap check)
    2. Descriptors (compute features)
    3. Modeling (train, evaluate, permutation)
    4. SHAP/Interpretability (plots, stability)
    5. Reporting (final report)
    6. Hashing (artifact versioning)
    """
    load_environment()
    initialize_config()
    
    start_total = time.time()
    timings: Dict[str, float] = {}
    status: Dict[str, str] = {}
    
    steps = [
        ("ingestion", run_ingestion),
        ("descriptors", run_descriptors),
        ("modeling", run_modeling),
        ("shap_analysis", run_shap),
        ("reporting", run_report),
        ("hashing", run_hash),
    ]
    
    for name, func in steps:
        try:
            duration = run_step(name, func)
            timings[name] = duration
            status[name] = "success"
        except Exception as e:
            timings[name] = time.time() - start_total - sum(timings.values())
            status[name] = f"failed: {str(e)}"
            # Stop pipeline on critical failure (except maybe hashing/reporting which can be partial)
            # For this task, we stop to ensure we don't mask the root cause
            break
    
    total_duration = time.time() - start_total
    
    metrics = {
        "task_id": "T046",
        "total_duration_seconds": total_duration,
        "step_timings_seconds": timings,
        "step_status": status,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    output_dir = ensure_output_dir()
    save_runtime_metrics(metrics, output_dir)
    
    # Also ensure the specific deliverable requested in the failure report is generated
    # if the pipeline steps that create them ran successfully.
    # The 'reporting' step (T043) should have generated the final report.
    # We ensure the runtime file itself is the primary deliverable for T046.
    
    return metrics

def main():
    """Entry point for the pipeline timing script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(project_root / "logs" / "pipeline_timing.log")
        ]
    )
    
    logger.info("Starting Pipeline Runtime Measurement (T046)")
    
    try:
        metrics = run_full_pipeline()
        logger.info(f"Pipeline execution finished. Total time: {metrics['total_duration_seconds']:.2f}s")
        logger.info(f"Status: {metrics['step_status']}")
        
        # Exit with error code if any step failed
        if any(s.startswith("failed") for s in metrics['step_status'].values()):
            logger.error("Pipeline failed. Check logs for details.")
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        logger.critical(f"Pipeline execution crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()