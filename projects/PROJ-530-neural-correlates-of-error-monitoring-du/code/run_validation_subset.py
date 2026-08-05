"""
Validation Script for Task T036: Run full pipeline on N=5 subset.

This script orchestrates the full pipeline (Download -> Preprocess -> Analysis -> Viz)
on a subset of 5 participants to verify runtime < 10 minutes.

It imports and executes the main functions from existing modules:
- code/download.py
- code/preprocess.py
- code/analysis.py
- code/viz.py

It measures execution time and memory usage, writing a feasibility report to
results/diagnostics/feasibility_report.json.
"""
import os
import sys
import time
import json
import psutil
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))

from code.download import main as download_main
from code.preprocess import main as preprocess_main
from code.analysis import main as analysis_main
from code.viz import main as viz_main
from code.utils import set_global_seed
from code.logging_config import initialize_logging, get_logger

# Configuration
SUBSET_SIZE = 5
MAX_RUNTIME_SECONDS = 600  # 10 minutes
MAX_MEMORY_MB = 7168       # 7 GB
OUTPUT_DIR = Path("results/diagnostics")
REPORT_FILE = OUTPUT_DIR / "feasibility_report.json"

def get_memory_usage_mb():
    """Get current process memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def run_pipeline_subset():
    """Run the full pipeline on a subset of N=5 participants."""
    logger = get_logger(__name__)
    logger.info(f"Starting validation pipeline with subset size: {SUBSET_SIZE}")
    
    start_time = time.time()
    peak_memory = get_memory_usage_mb()
    
    try:
        # 1. Download (or verify existing data)
        logger.info("Step 1: Data Download/Verification")
        # Pass subset size via environment variable or config if supported
        # For now, we assume download.py handles its own logic or we rely on existing data
        # We set a flag to indicate subset processing if the module supports it
        os.environ['PIPELINE_SUBSET_SIZE'] = str(SUBSET_SIZE)
        download_main()
        
        current_memory = get_memory_usage_mb()
        if current_memory > peak_memory:
            peak_memory = current_memory

        # 2. Preprocessing
        logger.info("Step 2: Preprocessing (Filtering, ICA, Feature Extraction)")
        preprocess_main()
        
        current_memory = get_memory_usage_mb()
        if current_memory > peak_memory:
            peak_memory = current_memory

        # 3. Analysis (Model Fitting)
        logger.info("Step 3: Analysis (Model Fitting, Validation)")
        analysis_main()
        
        current_memory = get_memory_usage_mb()
        if current_memory > peak_memory:
            peak_memory = current_memory

        # 4. Visualization
        logger.info("Step 4: Visualization")
        viz_main()
        
        current_memory = get_memory_usage_mb()
        if current_memory > peak_memory:
            peak_memory = current_memory

    except Exception as e:
        logger.error(f"Pipeline failed during execution: {str(e)}")
        raise

    end_time = time.time()
    runtime_seconds = end_time - start_time

    # Generate Report
    report = {
        "timestamp": datetime.now().isoformat(),
        "subset_size": SUBSET_SIZE,
        "runtime_seconds": round(runtime_seconds, 2),
        "peak_memory_mb": round(peak_memory, 2),
        "status": "success" if runtime_seconds <= MAX_RUNTIME_SECONDS and peak_memory <= MAX_MEMORY_MB else "exceeded_limits",
        "limits": {
            "max_runtime_seconds": MAX_RUNTIME_SECONDS,
            "max_memory_mb": MAX_MEMORY_MB
        }
    }

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(REPORT_FILE, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Feasibility report saved to: {REPORT_FILE}")
    logger.info(f"Runtime: {runtime_seconds:.2f}s (Limit: {MAX_RUNTIME_SECONDS}s)")
    logger.info(f"Peak Memory: {peak_memory:.2f}MB (Limit: {MAX_MEMORY_MB}MB)")

    if runtime_seconds > MAX_RUNTIME_SECONDS:
        logger.warning(f"Runtime exceeded limit by {runtime_seconds - MAX_RUNTIME_SECONDS:.2f}s")
    if peak_memory > MAX_MEMORY_MB:
        logger.warning(f"Memory exceeded limit by {peak_memory - MAX_MEMORY_MB:.2f}MB")

    return report

if __name__ == "__main__":
    # Initialize logging
    initialize_logging(log_level=logging.INFO)
    
    # Set seed for reproducibility
    set_global_seed(42)
    
    # Run the validation
    report = run_pipeline_subset()
    
    # Exit with error code if limits exceeded
    if report["status"] == "exceeded_limits":
        sys.exit(1)
    else:
        sys.exit(0)