"""
Orchestrator for the llmXive S-Agent Spatial Reasoning Pipeline.

Executes the full pipeline in strict order:
1. Download (S-AgentK subset)
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
from benchmark.generate_benchmark_results import main as benchmark_main
from benchmark.analyze_failures import main as analyze_failures_main
from hygiene import main as hygiene_main
from benchmark.sensitivity import main as sensitivity_main

def run_pipeline(args):
    """Execute the full pipeline steps sequentially."""
    config = Config()
    # Use a simple logger fallback if Config.logger is not fully implemented
    logger = getattr(config, 'logger', None)
    if not logger:
        class SimpleLogger:
            def info(self, msg): print(f"INFO: {msg}")
            def error(self, msg): print(f"ERROR: {msg}")
            def warning(self, msg): print(f"WARNING: {msg}")
        logger = SimpleLogger()

    logger.info("=" * 60)
    logger.info("Starting llmXive S-Agent Spatial Reasoning Pipeline")
    logger.info("=" * 60)

    # Step 1: Download
    logger.info("Step 1/8: Downloading dataset...")
    try:
        download_main()
    except SystemExit as e:
        if e.code != 0:
            logger.error("Download failed. Pipeline ABORTED.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Download failed: {e}")
        sys.exit(1)

    # Step 2: Verify Checksum
    logger.info("Step 2/8: Verifying checksums...")
    try:
        verify_checksum_main()
    except SystemExit as e:
        if e.code != 0:
            logger.error("Checksum verification failed. Pipeline ABORTED.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Checksum verification failed: {e}")
        sys.exit(1)

    # Step 3: Validate Distribution (HARD BLOCK)
    logger.info("Step 3/8: Validating data distribution (HARD BLOCK)...")
    try:
        validate_distribution_main()
    except SystemExit as e:
        if e.code != 0:
            logger.error("Distribution validation failed. Pipeline ABORTED.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Distribution validation error: {e}")
        sys.exit(1)

    # Step 4: Extract Geometry
    logger.info("Step 4/8: Extracting geometric constraints...")
    try:
        extract_geometry_main()
    except SystemExit as e:
        if e.code != 0:
            logger.error("Geometry extraction failed. Pipeline ABORTED.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Geometry extraction failed: {e}")
        sys.exit(1)

    # Step 5: Solve
    logger.info("Step 5/8: Running CSP solver...")
    try:
        run_solver_main()
    except SystemExit as e:
        if e.code != 0:
            logger.error("Solver execution failed. Pipeline ABORTED.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Solver execution failed: {e}")
        sys.exit(1)

    # Step 6: Benchmark
    logger.info("Step 6/8: Running benchmarking metrics...")
    try:
        benchmark_main()
    except SystemExit as e:
        if e.code != 0:
            logger.error("Benchmarking failed. Pipeline ABORTED.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Benchmarking failed: {e}")
        sys.exit(1)

    # Step 7: Sensitivity Analysis
    logger.info("Step 7/8: Running sensitivity analysis...")
    try:
        sensitivity_main()
    except SystemExit as e:
        if e.code != 0:
            logger.error("Sensitivity analysis failed. Pipeline ABORTED.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        sys.exit(1)

    # Step 8: Failure Analysis (US3)
    logger.info("Step 8/8: Running failure analysis...")
    try:
        analyze_failures_main()
    except SystemExit as e:
        if e.code != 0:
            logger.error("Failure analysis failed. Pipeline ABORTED.")
            sys.exit(1)
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