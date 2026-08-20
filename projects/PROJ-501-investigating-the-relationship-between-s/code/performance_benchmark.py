"""
Performance Benchmark for the Stellar Flare Analysis Pipeline.

This script verifies that the full pipeline (Ingestion -> Physics -> Analysis -> Visualization)
completes within the 60-second constraint defined in SC-004.

It times each stage and reports the total execution time.
"""
import time
import logging
import sys
from pathlib import Path
from typing import Dict, Tuple

# Configure logging to avoid cluttering stdout during benchmark, 
# but ensure logs are still written to file if needed.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import pipeline runners
from data_ingestion import run_ingestion_pipeline
from physics import run_physics_pipeline
from analysis import run_analysis_pipeline
from visualization import run_visualization_pipeline

MAX_DURATION_SECONDS = 60

def run_benchmark() -> Tuple[bool, Dict[str, float]]:
    """
    Executes the full pipeline and measures execution time.
    
    Returns:
        Tuple of (success: bool, timings: Dict[str, float])
        success is True if total time <= MAX_DURATION_SECONDS.
    """
    timings = {}
    total_start = time.time()
    
    logger.info(f"Starting full pipeline benchmark (Max allowed: {MAX_DURATION_SECONDS}s)...")

    # Stage 1: Data Ingestion
    try:
        logger.info("Stage 1: Running Data Ingestion...")
        t0 = time.time()
        run_ingestion_pipeline()
        timings['ingestion'] = time.time() - t0
        logger.info(f"Data Ingestion completed in {timings['ingestion']:.2f}s")
    except Exception as e:
        logger.error(f"Data Ingestion failed: {e}")
        return False, timings

    # Stage 2: Physics Modeling
    try:
        logger.info("Stage 2: Running Physics Modeling...")
        t0 = time.time()
        run_physics_pipeline()
        timings['physics'] = time.time() - t0
        logger.info(f"Physics Modeling completed in {timings['physics']:.2f}s")
    except Exception as e:
        logger.error(f"Physics Modeling failed: {e}")
        return False, timings

    # Stage 3: Statistical Analysis
    try:
        logger.info("Stage 3: Running Statistical Analysis...")
        t0 = time.time()
        run_analysis_pipeline()
        timings['analysis'] = time.time() - t0
        logger.info(f"Statistical Analysis completed in {timings['analysis']:.2f}s")
    except Exception as e:
        logger.error(f"Statistical Analysis failed: {e}")
        return False, timings

    # Stage 4: Visualization
    try:
        logger.info("Stage 4: Running Visualization...")
        t0 = time.time()
        run_visualization_pipeline()
        timings['visualization'] = time.time() - t0
        logger.info(f"Visualization completed in {timings['visualization']:.2f}s")
    except Exception as e:
        logger.error(f"Visualization failed: {e}")
        return False, timings

    total_end = time.time()
    total_duration = total_end - total_start
    timings['total'] = total_duration

    logger.info("-" * 40)
    logger.info(f"BENCHMARK RESULTS:")
    for stage, duration in timings.items():
        logger.info(f"  {stage}: {duration:.2f}s")
    logger.info(f"  TOTAL: {total_duration:.2f}s")
    logger.info("-" * 40)

    if total_duration <= MAX_DURATION_SECONDS:
        logger.info(f"SUCCESS: Pipeline completed in {total_duration:.2f}s (Limit: {MAX_DURATION_SECONDS}s)")
        return True, timings
    else:
        logger.warning(f"FAILURE: Pipeline took {total_duration:.2f}s, exceeding limit of {MAX_DURATION_SECONDS}s")
        return False, timings

if __name__ == "__main__":
    success, results = run_benchmark()
    sys.exit(0 if success else 1)