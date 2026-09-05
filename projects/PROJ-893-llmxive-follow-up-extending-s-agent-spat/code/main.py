"""
Orchestrator for the llmXive S-Agent Spatial Reasoning Pipeline.

Executes the full pipeline in strict order:
1. Download (S-Agent-300K subset)
2. Verify Checksum (Data Hygiene)
3. Validate Distribution (HARD BLOCK - Abort if KS-test fails)
4. Extract Geometry (Parse constraints)
5. Solve (CSP Engine)
6. Benchmark (Compare against VLM baseline & Ground Truth)
7. Failure Analysis (Classify errors and generate report)

Usage:
    python code/main.py
"""
import sys
import os
import argparse
from pathlib import Path

# Ensure code directory is in path for imports
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "code"))

from config import Config
from data.download import main as download_main
from data.verify_checksum import main as verify_checksum_main
from data.validate_distribution import main as validate_distribution_main
from data.extract_geometry import main as extract_geometry_main
from solver.run_solver import main as run_solver_main
from benchmark.metrics import main as benchmark_main
from benchmark.analyze_failures import main as analyze_failures_main
from hygiene import main as hygiene_main

def run_pipeline(args):
    """Execute the full pipeline steps sequentially."""
    config = Config()
    logger = config.logger
    
    logger.info("=" * 60)
    logger.info("Starting llmXive S-Agent Spatial Reasoning Pipeline")
    logger.info("=" * 60)

    # Step 1: Download
    logger.info("Step 1/7: Downloading dataset...")
    try:
        download_main()
    except Exception as e:
        logger.error(f"Download failed: {e}")
        sys.exit(1)

    # Step 2: Verify Checksum
    logger.info("Step 2/7: Verifying checksums...")
    try:
        verify_checksum_main()
    except Exception as e:
        logger.error(f"Checksum verification failed: {e}")
        sys.exit(1)

    # Step 3: Validate Distribution (HARD BLOCK)
    logger.info("Step 3/7: Validating data distribution (HARD BLOCK)...")
    try:
        # This function returns a boolean or raises if invalid based on spec
        # We assume the main() function handles the logic and exits if failed
        validate_distribution_main()
    except SystemExit as e:
        if e.code != 0:
            logger.error("Distribution validation failed. Pipeline ABORTED.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Distribution validation error: {e}")
        sys.exit(1)

    # Step 4: Extract Geometry
    logger.info("Step 4/7: Extracting geometric constraints...")
    try:
        extract_geometry_main()
    except Exception as e:
        logger.error(f"Geometry extraction failed: {e}")
        sys.exit(1)

    # Step 5: Solve
    logger.info("Step 5/7: Running CSP solver...")
    try:
        run_solver_main()
    except Exception as e:
        logger.error(f"Solver execution failed: {e}")
        sys.exit(1)

    # Step 6: Benchmark
    logger.info("Step 6/7: Running benchmarking metrics...")
    try:
        benchmark_main()
    except Exception as e:
        logger.error(f"Benchmarking failed: {e}")
        sys.exit(1)

    # Step 7: Failure Analysis (US3)
    logger.info("Step 7/7: Running failure analysis...")
    try:
        analyze_failures_main()
    except Exception as e:
        logger.error(f"Failure analysis failed: {e}")
        sys.exit(1)

    # Final Hygiene Check (Optional but recommended per Phase 6)
    if not args.skip_hygiene:
        logger.info("Running final data hygiene check...")
        try:
            hygiene_main()
        except Exception as e:
            logger.warning(f"Final hygiene check warning: {e}")
            # Non-fatal for the pipeline success, but logs the issue

    logger.info("=" * 60)
    logger.info("Pipeline completed successfully.")
    logger.info("=" * 60)

def main():
    parser = argparse.ArgumentParser(description="Orchestrator for S-Agent Spatial Reasoning Pipeline")
    parser.add_argument("--skip-hygiene", action="store_true", help="Skip final hygiene check")
    args = parser.parse_args()

    run_pipeline(args)

if __name__ == "__main__":
    main()