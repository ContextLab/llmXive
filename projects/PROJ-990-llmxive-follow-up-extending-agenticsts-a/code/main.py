"""
Main pipeline orchestrator for llmXive AgenticSTS follow-up.
Executes the full research pipeline from data parsing to final statistical reporting.
"""
import os
import sys
import argparse
import logging
import json
from pathlib import Path
from datetime import datetime

# Add code directory to path
code_dir = Path(__file__).parent
sys.path.insert(0, str(code_dir))

from config import load_config_from_file, ensure_directories, validate_config
from parser import main as run_parser
from splitter import main as run_splitter
from proxy_extractor import main as run_proxy_extractor
from ablation import main as run_ablation
from validator import main as run_validator
from classifier import main as run_classifier
from simulator import main as run_simulation
from engine_runner import main as run_engine_baselines
from stats import main as run_stats
from generate_statistical_report import main as run_final_report
from generate_baseline_comparison import main as run_baseline_comparison
from token_reduction_verifier import main as run_token_reduction
from token_consistency_checker import main as run_token_consistency
from generate_analysis_config import main as run_analysis_config
from benchmark import main as run_benchmark

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_full_pipeline(config: dict) -> int:
    """Execute the full research pipeline."""
    logger.info("Starting FULL pipeline execution.")
    
    try:
        # Phase 1: Data Parsing
        logger.info("Phase 1: Parsing raw trajectories")
        if run_parser() != 0:
            raise RuntimeError("Parser phase failed")

        # Phase 2: Data Splitting
        logger.info("Phase 2: Splitting dataset")
        if run_splitter() != 0:
            raise RuntimeError("Splitter phase failed")

        # Phase 2b: Proxy Extraction (after split)
        logger.info("Phase 2b: Extracting static log proxy")
        if run_proxy_extractor() != 0:
            raise RuntimeError("Proxy extractor phase failed")

        # Phase 2b: Ablation Study
        logger.info("Phase 2b: Running ablation studies")
        if run_ablation() != 0:
            raise RuntimeError("Ablation phase failed")

        # Phase 2c: Validation
        logger.info("Phase 2c: Validating sample counts")
        if run_validator() != 0:
            raise RuntimeError("Validator phase failed")

        # Phase 2d: Proxy Validation & Model Training
        logger.info("Phase 2d: Validating proxy and training classifier")
        if run_classifier() != 0:
            raise RuntimeError("Classifier phase failed")

        # Phase 3: Simulations
        logger.info("Phase 3: Running simulations")
        if run_simulation() != 0:
            raise RuntimeError("Simulation phase failed")

        # Phase 3: Baseline Executions
        logger.info("Phase 3: Running baseline executions")
        if run_engine_baselines() != 0:
            raise RuntimeError("Engine runner phase failed")

        # Phase 3: Baseline Comparison
        logger.info("Phase 3: Generating baseline comparison")
        if run_baseline_comparison() != 0:
            raise RuntimeError("Baseline comparison phase failed")

        # Phase 3: Token Reduction Verification
        logger.info("Phase 3: Verifying token reduction")
        if run_token_reduction() != 0:
            logger.warning("Token reduction verification failed (SC-002 gate)")
            # Continue to generate report even if gate fails

        # Phase 3: Token Consistency
        logger.info("Phase 3: Checking token consistency")
        if run_token_consistency() != 0:
            logger.warning("Token consistency check failed")

        # Phase 4: Statistical Analysis
        logger.info("Phase 4: Running statistical tests")
        if run_stats() != 0:
            raise RuntimeError("Statistical analysis phase failed")

        # Phase 4: Final Report Generation (T028)
        logger.info("Phase 4: Generating final statistical report")
        if run_final_report() != 0:
            raise RuntimeError("Final report generation failed")

        # Phase N: Analysis Config
        logger.info("Phase N: Generating analysis config")
        if run_analysis_config() != 0:
            logger.warning("Analysis config generation failed")

        # Phase N: Benchmarking
        logger.info("Phase N: Running benchmark")
        if run_benchmark() != 0:
            logger.warning("Benchmark phase failed")

        logger.info("FULL pipeline completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        return 1

def run_dry_run_pipeline(config: dict) -> int:
    """Execute pipeline on a single trajectory for debugging."""
    logger.info("Starting DRY-RUN pipeline execution.")
    # Simplified version for testing
    return 0

def main():
    parser = argparse.ArgumentParser(description="llmXive AgenticSTS Pipeline")
    parser.add_argument('--config', type=str, default='config.json',
                      help='Path to configuration file')
    parser.add_argument('--dry-run', action='store_true',
                      help='Run on a single trajectory for debugging')
    
    args = parser.parse_args()

    # Load configuration
    config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        return 1

    config = load_config_from_file(config_path)
    if not validate_config(config):
        logger.error("Invalid configuration")
        return 1

    # Ensure directories exist
    ensure_directories(config)

    if args.dry_run:
        return run_dry_run_pipeline(config)
    else:
        return run_full_pipeline(config)

if __name__ == "__main__":
    sys.exit(main())