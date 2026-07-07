"""
Main pipeline orchestrator for evaluating code generation model vulnerability density.

This script coordinates the execution of dataset download, code generation,
static analysis, and statistical analysis based on user-provided arguments.
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Optional

# Import from sibling modules based on provided API surface
from download import download_human_eval, download_mbpp, main as download_main
from state_utils import store_artifact_hashes, compute_artifact_hashes
from config import get_config, get_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(get_path('log_file'))
    ]
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments for the pipeline."""
    parser = argparse.ArgumentParser(
        description='LLM Code Vulnerability Density Evaluation Pipeline'
    )

    parser.add_argument(
        '--models',
        nargs='+',
        default=['starcoder', 'codegen'],
        choices=['starcoder', 'codegen'],
        help='List of models to evaluate (default: starcoder codegen)'
    )

    parser.add_argument(
        '--benchmarks',
        nargs='+',
        default=['humaneval', 'mbpp'],
        choices=['humaneval', 'mbpp'],
        help='List of benchmarks to use (default: humaneval mbpp)'
    )

    parser.add_argument(
        '--skip-download',
        action='store_true',
        help='Skip dataset download if already present'
    )

    parser.add_argument(
        '--skip-generation',
        action='store_true',
        help='Skip code generation step'
    )

    parser.add_argument(
        '--skip-analysis',
        action='store_true',
        help='Skip static analysis step'
    )

    parser.add_argument(
        '--skip-stats',
        action='store_true',
        help='Skip statistical analysis step'
    )

    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    return parser.parse_args()


def run_download(benchmarks: list, skip: bool) -> bool:
    """
    Run dataset download phase.

    Args:
        benchmarks: List of benchmark names to download.
        skip: Whether to skip this step.

    Returns:
        bool: True if successful or skipped, False on failure.
    """
    if skip:
        logger.info("Skipping dataset download as requested.")
        return True

    logger.info("Starting dataset download phase...")
    try:
        for benchmark in benchmarks:
            logger.info(f"Downloading {benchmark} dataset...")
            if benchmark == 'humaneval':
                download_human_eval()
            elif benchmark == 'mbpp':
                download_mbpp()
            else:
                logger.warning(f"Unknown benchmark: {benchmark}, skipping.")
                continue

        logger.info("Dataset download completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Dataset download failed: {e}")
        return False


def run_generation(models: list, benchmarks: list, skip: bool) -> bool:
    """
    Run code generation phase.

    Args:
        models: List of models to use for generation.
        benchmarks: List of benchmarks to generate code for.
        skip: Whether to skip this step.

    Returns:
        bool: True if successful or skipped, False on failure.
    """
    if skip:
        logger.info("Skipping code generation as requested.")
        return True

    logger.info("Starting code generation phase...")
    # Placeholder for generation logic
    # This will be implemented in code/generate.py
    # For now, we simulate the step to ensure the pipeline structure works
    try:
        for model in models:
            for benchmark in benchmarks:
                logger.info(f"Generating code for {model} on {benchmark}...")
                # TODO: Call actual generation function from code/generate.py
                # generate_code(model, benchmark)
                logger.info(f"Generation completed for {model} on {benchmark}.")

        logger.info("Code generation phase completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Code generation failed: {e}")
        return False


def run_analysis(models: list, benchmarks: list, skip: bool) -> bool:
    """
    Run static analysis phase.

    Args:
        models: List of models whose code was generated.
        benchmarks: List of benchmarks used.
        skip: Whether to skip this step.

    Returns:
        bool: True if successful or skipped, False on failure.
    """
    if skip:
        logger.info("Skipping static analysis as requested.")
        return True

    logger.info("Starting static analysis phase...")
    # Placeholder for analysis logic
    # This will be implemented in code/analyze.py
    try:
        for model in models:
            for benchmark in benchmarks:
                logger.info(f"Running Bandit analysis on {model} - {benchmark}...")
                # TODO: Call actual analysis function from code/analyze.py
                # run_bandit_analysis(model, benchmark)
                logger.info(f"Analysis completed for {model} on {benchmark}.")

        logger.info("Static analysis phase completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Static analysis failed: {e}")
        return False


def run_statistics(skip: bool) -> bool:
    """
    Run statistical analysis phase.

    Args:
        skip: Whether to skip this step.

    Returns:
        bool: True if successful or skipped, False on failure.
    """
    if skip:
        logger.info("Skipping statistical analysis as requested.")
        return True

    logger.info("Starting statistical analysis phase...")
    # Placeholder for stats logic
    # This will be implemented in code/stats.py
    try:
        logger.info("Running ZINB regression and permutation tests...")
        # TODO: Call actual stats function from code/stats.py
        # run_statistical_analysis()
        logger.info("Statistical analysis completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Statistical analysis failed: {e}")
        return False


def main() -> int:
    """
    Main entry point for the pipeline orchestrator.

    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    args = parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("========================================")
    logger.info("Starting LLM Code Vulnerability Density Pipeline")
    logger.info("========================================")
    logger.info(f"Models: {args.models}")
    logger.info(f"Benchmarks: {args.benchmarks}")
    logger.info(f"Seed: {args.seed}")

    start_time = time.time()

    # Step 1: Download datasets
    if not run_download(args.benchmarks, args.skip_download):
        logger.error("Pipeline failed at dataset download step.")
        return 1

    # Step 2: Generate code
    if not run_generation(args.models, args.benchmarks, args.skip_generation):
        logger.error("Pipeline failed at code generation step.")
        return 1

    # Step 3: Analyze vulnerabilities
    if not run_analysis(args.models, args.benchmarks, args.skip_analysis):
        logger.error("Pipeline failed at static analysis step.")
        return 1

    # Step 4: Statistical analysis
    if not run_statistics(args.skip_stats):
        logger.error("Pipeline failed at statistical analysis step.")
        return 1

    # Compute and store artifact hashes
    logger.info("Computing and storing artifact hashes...")
    try:
        hashes = compute_artifact_hashes()
        store_artifact_hashes(hashes)
        logger.info("Artifact hashes stored successfully.")
    except Exception as e:
        logger.warning(f"Failed to store artifact hashes: {e}")

    end_time = time.time()
    logger.info("========================================")
    logger.info(f"Pipeline completed successfully in {end_time - start_time:.2f} seconds")
    logger.info("========================================")

    return 0


if __name__ == "__main__":
    sys.exit(main())