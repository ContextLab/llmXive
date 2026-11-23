"""
Performance benchmark and optimization driver for the gut microbiome circadian rhythm pipeline.

This script executes the full pipeline (Ingestion -> Diversity -> Analysis -> Validation)
on the processed cohort, utilizing parallel execution strategies defined in
`performance_optimizer` to ensure the total runtime remains under 6 hours for N=200.

It logs detailed timing metrics to `data/outputs/performance_report.json` and
verifies that execution completes within the target budget.
"""
import os
import sys
import time
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "projects" / "PROJ-037-investigating-the-correlation-between-gu"))

from code.performance_optimizer import (
    run_performance_benchmark,
    optimize_dataframe_memory,
    configure_parallelism,
    estimate_runtime
)
from code.performance_config import get_performance_config, set_performance_config
from code.utils.logging_utils import setup_logging, get_logger
from code.utils.seeding import set_seed
from code.ingestion import main as run_ingestion
from code.diversity import main as run_diversity
from code.analysis import main as run_analysis
from code.validation import main as run_validation
from code.report import main as run_report

# Constants
TARGET_RUNTIME_SECONDS = 6 * 3600  # 6 hours
COHORT_SIZE_TARGET = 200

def log_metrics(metrics: Dict[str, Any], logger: logging.Logger, output_path: Path):
    """Log metrics to console and save to JSON file."""
    logger.info("=" * 60)
    logger.info("PERFORMANCE BENCHMARK RESULTS")
    logger.info("=" * 60)
    
    for key, value in metrics.items():
        logger.info(f"{key}: {value}")
    
    # Save to JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2, default=str)
    logger.info(f"Metrics saved to {output_path}")

def run_full_pipeline_with_profiling(logger: logging.Logger) -> Dict[str, Any]:
    """
    Execute the full pipeline stages with timing and optimization.
    Returns a dictionary of timing metrics.
    """
    metrics = {
        "start_time": datetime.now().isoformat(),
        "target_cohort_size": COHORT_SIZE_TARGET,
        "target_runtime_seconds": TARGET_RUNTIME_SECONDS,
        "stages": {}
    }

    # 1. Configuration
    logger.info("Configuring parallelism and memory optimization...")
    config = get_performance_config()
    configure_parallelism(max_workers=config.max_workers)
    
    # 2. Ingestion Stage
    logger.info("Starting Ingestion Stage (T011-T017)...")
    start = time.time()
    try:
        # Run ingestion with profiling hook if available, otherwise just time it
        run_ingestion() 
        elapsed = time.time() - start
        metrics["stages"]["ingestion"] = {
            "status": "completed",
            "duration_seconds": round(elapsed, 2)
        }
        logger.info(f"Ingestion completed in {elapsed:.2f}s")
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        metrics["stages"]["ingestion"] = {"status": "failed", "error": str(e)}
        return metrics

    # 3. Diversity Stage
    logger.info("Starting Diversity Stage (T020)...")
    start = time.time()
    try:
        # Apply memory optimization before heavy computation
        optimize_dataframe_memory()
        run_diversity()
        elapsed = time.time() - start
        metrics["stages"]["diversity"] = {
            "status": "completed",
            "duration_seconds": round(elapsed, 2)
        }
        logger.info(f"Diversity completed in {elapsed:.2f}s")
    except Exception as e:
        logger.error(f"Diversity failed: {e}")
        metrics["stages"]["diversity"] = {"status": "failed", "error": str(e)}
        return metrics

    # 4. Analysis Stage
    logger.info("Starting Analysis Stage (T021-T025)...")
    start = time.time()
    try:
        run_analysis()
        elapsed = time.time() - start
        metrics["stages"]["analysis"] = {
            "status": "completed",
            "duration_seconds": round(elapsed, 2)
        }
        logger.info(f"Analysis completed in {elapsed:.2f}s")
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        metrics["stages"]["analysis"] = {"status": "failed", "error": str(e)}
        return metrics

    # 5. Validation Stage
    logger.info("Starting Validation Stage (T032-T035)...")
    start = time.time()
    try:
        run_validation()
        elapsed = time.time() - start
        metrics["stages"]["validation"] = {
            "status": "completed",
            "duration_seconds": round(elapsed, 2)
        }
        logger.info(f"Validation completed in {elapsed:.2f}s")
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        metrics["stages"]["validation"] = {"status": "failed", "error": str(e)}
        return metrics

    # 6. Report Stage
    logger.info("Starting Report Generation (T029, T036)...")
    start = time.time()
    try:
        run_report()
        elapsed = time.time() - start
        metrics["stages"]["report"] = {
            "status": "completed",
            "duration_seconds": round(elapsed, 2)
        }
        logger.info(f"Report completed in {elapsed:.2f}s")
    except Exception as e:
        logger.error(f"Report failed: {e}")
        metrics["stages"]["report"] = {"status": "failed", "error": str(e)}
        return metrics

    # Final Totals
    total_time = sum(
        m["duration_seconds"] for m in metrics["stages"].values() 
        if isinstance(m, dict) and m.get("status") == "completed"
    )
    metrics["total_duration_seconds"] = round(total_time, 2)
    metrics["end_time"] = datetime.now().isoformat()
    
    # Pass/Fail Check
    metrics["within_budget"] = total_time <= TARGET_RUNTIME_SECONDS
    metrics["budget_status"] = "PASS" if metrics["within_budget"] else "FAIL"
    
    # Estimated runtime for N=200 (if current N differs, scale linearly as a rough estimate)
    # Note: This assumes linear scaling which is an approximation for O(N^2) operations like distance matrices
    # For a true N=200 benchmark, the pipeline should run on a dataset of that size.
    estimated_n = metrics.get("actual_cohort_size", COHORT_SIZE_TARGET) 
    if estimated_n != COHORT_SIZE_TARGET:
        # Simple scaling factor (linear for IO, quadratic for distance matrices - using conservative linear for now)
        scaling_factor = COHORT_SIZE_TARGET / estimated_n
        metrics["estimated_runtime_at_n_200"] = round(total_time * scaling_factor, 2)
    
    return metrics

def main():
    parser = argparse.ArgumentParser(description="Run performance benchmark for PROJ-037")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    parser.add_argument("--output-dir", type=Path, default=Path("data/outputs"), help="Output directory for reports")
    args = parser.parse_args()

    # Setup logging
    log_path = Path("logs")
    log_path.mkdir(parents=True, exist_ok=True)
    logger = setup_logging(
        level=getattr(logging, args.log_level.upper()),
        log_file=log_path / "performance_benchmark.log",
        name="performance_benchmark"
    )

    logger.info("Starting Performance Benchmark for Gut Microbiome Circadian Rhythm Pipeline")
    logger.info(f"Target Runtime: {TARGET_RUNTIME_SECONDS/3600:.1f} hours")
    logger.info(f"Target Cohort Size: {COHORT_SIZE_TARGET}")

    # Set random seed for reproducibility
    set_seed(42)

    # Run the pipeline
    metrics = run_full_pipeline_with_profiling(logger)

    # Output results
    output_path = args.output_dir / "performance_report.json"
    log_metrics(metrics, logger, output_path)

    if not metrics["within_budget"]:
        logger.warning("WARNING: Pipeline exceeded the 6-hour runtime budget.")
        logger.warning("Optimization strategies (parallelism, memory mapping) should be reviewed.")
        sys.exit(1)
    else:
        logger.info("SUCCESS: Pipeline completed within the 6-hour runtime budget.")
        sys.exit(0)

if __name__ == "__main__":
    main()
