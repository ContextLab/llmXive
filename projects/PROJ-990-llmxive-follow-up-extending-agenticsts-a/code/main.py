"""
Main entry point for the llmXive pipeline.
Orchestrates the full execution flow from parsing to statistical analysis.
"""
import os
import sys
import argparse
import logging
import json
from pathlib import Path

# Import pipeline modules
from parser import main as run_parser
from splitter import main as run_splitter
from ablation import main as run_ablation
from validator import main as run_validator
from classifier import main as run_classifier
from simulator import main as run_simulator
from stats import main as run_stats
from generate_baseline_comparison import main as run_baseline_comparison
from token_reduction_verifier import main as run_token_reduction
from token_consistency_checker import main as run_token_consistency
from generate_statistical_report import main as run_statistical_report
from generate_analysis_config import main as run_analysis_config
from benchmark import main as run_benchmark
from optimization_report import main as run_optimization_report
from config import load_config_from_file, ensure_directories, validate_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_dry_run_pipeline(config: dict):
    """Run the pipeline on a small subset for validation."""
    logger.info("Running DRY-RUN pipeline on subset...")
    # Implement dry-run logic here if needed
    logger.info("Dry-run complete.")

def run_full_pipeline(config: dict):
    """Execute the full pipeline."""
    logger.info("Starting FULL pipeline execution.")

    # 1. Parse data
    logger.info("Step 1: Parsing data...")
    run_parser()

    # 2. Split data
    logger.info("Step 2: Splitting data...")
    run_splitter()

    # 3. Extract static proxy (validation set)
    logger.info("Step 3: Extracting static proxy...")
    # Parser with --extract-static-proxy flag
    os.system("python code/parser.py --extract-static-proxy")

    # 4. Ablation study (train)
    logger.info("Step 4: Running ablation study (train)...")
    os.system("python code/ablation.py --dataset train_set")

    # 5. Ablation study (validation)
    logger.info("Step 5: Running ablation study (validation)...")
    os.system("python code/ablation.py --dataset validation_set")

    # 6. Validate sample count
    logger.info("Step 6: Validating sample count...")
    run_validator()

    # 7. Train classifier
    logger.info("Step 7: Training classifier...")
    run_classifier()

    # 8. Run simulations
    logger.info("Step 8: Running simulations...")
    run_simulator()  # This should handle all policies or be called multiple times

    # 9. Aggregate baselines
    logger.info("Step 9: Aggregating baselines...")
    run_baseline_comparison()

    # 10. Verify token reduction
    logger.info("Step 10: Verifying token reduction...")
    run_token_reduction()

    # 11. Check token consistency
    logger.info("Step 11: Checking token consistency...")
    run_token_consistency()

    # 12. Detect divergence
    logger.info("Step 12: Detecting trajectory divergence...")
    os.system("python code/stats.py --detect-divergence")

    # 13. Run statistical tests
    logger.info("Step 13: Running statistical tests...")
    os.system("python code/stats.py --test")

    # 14. Generate statistical report
    logger.info("Step 14: Generating statistical report...")
    run_statistical_report()

    # 15. Generate analysis config
    logger.info("Step 15: Generating analysis config snapshot...")
    run_analysis_config()

    # 16. Run benchmark
    logger.info("Step 16: Running benchmark...")
    run_benchmark()

    # 17. Generate optimization report
    logger.info("Step 17: Generating optimization report...")
    run_optimization_report()

    logger.info("FULL pipeline execution complete.")

def main():
    parser = argparse.ArgumentParser(description="llmXive Pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Run on a small subset")
    parser.add_argument("--config", type=str, default="config.json", help="Path to config file")
    args = parser.parse_args()

    # Load config
    config = load_config_from_file(args.config)
    ensure_directories(config)
    validate_config(config)

    if args.dry_run:
        run_dry_run_pipeline(config)
    else:
        run_full_pipeline(config)

if __name__ == "__main__":
    main()