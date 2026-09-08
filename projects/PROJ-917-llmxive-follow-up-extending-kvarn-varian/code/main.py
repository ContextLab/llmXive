"""
Unified Entry Point for the KVarN Research Pipeline.

This script orchestrates the full workflow:
1. Data Generation (T017c)
2. Model Training (T023)
3. Batch Simulation (T030b)
4. Report Generation (T033)

Usage:
    python code/main.py [--seed SEED] [--task TASK_NAME]
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_config, set_config, reset_config
from data_generation.synthetic_attention import main as generate_data_main
from model_training.train import main as train_model_main
from simulation.batch_runner import main as run_simulation_main
from analysis.stats import main as analyze_results_main
from utils.seed_manager import set_seed

def setup_logging(log_file: Optional[Path] = None):
    """Setup logging configuration."""
    if log_file is None:
        log_file = project_root / "data" / "metrics" / "main_execution.log"
    
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Configure logging to write to both file and stdout
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def run_phase(phase_name: str, logger: logging.Logger):
    """Execute a specific phase of the pipeline."""
    logger.info(f"--- Starting Phase: {phase_name} ---")
    try:
        if phase_name == "generate_data":
            logger.info("Executing Data Generation (T017c)...")
            generate_data_main()
            logger.info("Data generation completed.")
        elif phase_name == "train_model":
            logger.info("Executing Model Training (T023)...")
            train_model_main()
            logger.info("Model training completed.")
        elif phase_name == "run_simulation":
            logger.info("Executing Batch Simulation (T030b)...")
            run_simulation_main()
            logger.info("Batch simulation completed.")
        elif phase_name == "analyze_results":
            logger.info("Executing Report Generation & Analysis (T033)...")
            analyze_results_main()
            logger.info("Analysis and report generation completed.")
        else:
            raise ValueError(f"Unknown phase: {phase_name}")
        logger.info(f"--- Phase {phase_name} completed successfully ---")
    except Exception as e:
        logger.error(f"--- Phase {phase_name} failed: {e} ---", exc_info=True)
        raise

def main():
    parser = argparse.ArgumentParser(description="KVarN Research Pipeline Entry Point")
    parser.add_argument("--seed", type=int, default=None, help="Override random seed")
    parser.add_argument("--task", type=str, default="all", 
                        choices=["all", "generate_data", "train_model", "run_simulation", "analyze_results"],
                        help="Specific task to run. Default: all")
    args = parser.parse_args()

    logger = setup_logging()
    logger.info("Starting KVarN Pipeline")
    logger.info(f"Project Root: {project_root}")

    # Set seed if provided
    if args.seed is not None:
        current_config = get_config()
        current_config.RANDOM_SEED = args.seed
        set_config(current_config)
        set_seed(args.seed)
        logger.info(f"Set global seed to {args.seed}")

    try:
        if args.task == "all":
            # Run full pipeline in strict sequential order
            run_phase("generate_data", logger)
            run_phase("train_model", logger)
            run_phase("run_simulation", logger)
            run_phase("analyze_results", logger)
        else:
            run_phase(args.task, logger)
        
        logger.info("Pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()