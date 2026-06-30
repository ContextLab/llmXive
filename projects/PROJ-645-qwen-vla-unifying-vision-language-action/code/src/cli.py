"""
Main CLI entry point for the Qwen-VLA Cross-Embodiment Transfer Study.
Orchestrates the full pipeline: Training (US1 & US2) -> Evaluation -> Statistical Analysis.
"""
import os
import sys
import logging
import argparse
import time
from pathlib import Path
from typing import Optional

# Import core pipeline components
from src.utils.logging_config import setup_logging, get_logger
from src.utils.reproducibility import load_seeds
from src.training.train_loop import main as train_main
from src.training.train_baseline import main as train_baseline_main
from src.evaluation.libero_eval import main as eval_main
from src.statistics.wilcoxon_test import main as stat_main
from src.reporting.stat_report import main as report_main

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Qwen-VLA Cross-Embodiment Transfer Study CLI"
    )
    
    parser.add_argument(
        "--mode",
        type=str,
        choices=["full", "train", "eval", "stats", "report"],
        default="full",
        help="Execution mode: 'full' runs train+eval+stats+report, others run specific steps."
    )
    
    parser.add_argument(
        "--ratio",
        type=float,
        default=1.0,
        help="Data composition ratio for training (0.0 to 1.0). Used for US1. US2 uses single-platform."
    )
    
    parser.add_argument(
        "--epochs",
        type=int,
        default=5,
        help="Number of training epochs."
    )
    
    parser.add_argument(
        "--skip-baseline",
        action="store_true",
        help="If set, skip US2 baseline training and statistical comparison."
    )
    
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data",
        help="Root directory for data artifacts."
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level."
    )
    
    return parser.parse_args()

def run_training_pipeline(args, logger):
    """Execute US1 (Cross-Embodiment) and US2 (Baseline) training."""
    logger.info("Starting Training Pipeline...")
    
    # Ensure seeds are available
    seeds_path = Path(args.data_dir) / "seeds.json"
    if not seeds_path.exists():
        logger.warning(f"Seeds file {seeds_path} not found. Running reproducibility init.")
        # We assume T018 has run or will be run by the training scripts if needed.
        # If strict dependency, we might call reproducibility.main() here, but 
        # T018 is completed, so we assume seeds exist or training script generates them.
    
    # 1. Run US1: Cross-Embodiment Training
    logger.info("=== Starting US1: Cross-Embodiment Training ===")
    # Construct args for train_loop
    train_args = argparse.Namespace(
        epochs=args.epochs,
        ratio=args.ratio,
        data_dir=args.data_dir,
        log_level=args.log_level,
        mode="train" # Internal mode for train_loop
    )
    try:
        train_main(train_args)
        logger.info("US1 Training completed successfully.")
    except Exception as e:
        logger.error(f"US1 Training failed: {e}")
        raise

    if not args.skip_baseline:
        # 2. Run US2: Baseline Training (Single Platform)
        logger.info("=== Starting US2: Baseline Training ===")
        baseline_args = argparse.Namespace(
            epochs=args.epochs,
            data_dir=args.data_dir,
            log_level=args.log_level,
            mode="train"
        )
        try:
            train_baseline_main(baseline_args)
            logger.info("US2 Baseline Training completed successfully.")
        except Exception as e:
            logger.error(f"US2 Baseline Training failed: {e}")
            raise
    else:
        logger.info("Skipping US2 Baseline Training (flag set).")

def run_evaluation_pipeline(args, logger):
    """Execute Zero-Shot Evaluation (US1)."""
    logger.info("=== Starting Evaluation Pipeline ===")
    eval_args = argparse.Namespace(
        data_dir=args.data_dir,
        log_level=args.log_level,
        mode="eval"
    )
    try:
        eval_main(eval_args)
        logger.info("Evaluation completed successfully.")
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise

def run_statistical_pipeline(args, logger):
    """Execute Statistical Analysis (US2) and Report Generation."""
    logger.info("=== Starting Statistical Analysis Pipeline ===")
    
    # 1. Wilcoxon Test
    stat_args = argparse.Namespace(
        data_dir=args.data_dir,
        log_level=args.log_level,
        mode="stats"
    )
    try:
        stat_main(stat_args)
        logger.info("Statistical test completed successfully.")
    except Exception as e:
        logger.error(f"Statistical test failed: {e}")
        raise

    # 2. Report Generation
    report_args = argparse.Namespace(
        data_dir=args.data_dir,
        log_level=args.log_level,
        mode="report"
    )
    try:
        report_main(report_args)
        logger.info("Statistical report generated successfully.")
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise

def main():
    args = parse_args()
    
    # Setup logging
    log_file = Path(args.data_dir) / "cli_run.log"
    log_dir = log_file.parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    setup_logging(level=args.log_level, log_file=str(log_file))
    logger = get_logger(__name__)
    
    logger.info(f"CLI started with mode: {args.mode}, ratio: {args.ratio}")
    
    start_time = time.time()
    
    try:
        if args.mode == "full":
            # 1. Train (US1 & optionally US2)
            run_training_pipeline(args, logger)
            
            # 2. Evaluate (US1)
            run_evaluation_pipeline(args, logger)
            
            # 3. Stats & Report (US2) - only if baseline was run
            if not args.skip_baseline:
                run_statistical_pipeline(args, logger)
            else:
                logger.warning("Skipping statistical analysis because --skip-baseline was set.")
                
        elif args.mode == "train":
            run_training_pipeline(args, logger)
            
        elif args.mode == "eval":
            run_evaluation_pipeline(args, logger)
            
        elif args.mode == "stats":
            # Assumes training and eval already done
            run_statistical_pipeline(args, logger)
            
        elif args.mode == "report":
            # Assumes stats already done
            report_args = argparse.Namespace(
                data_dir=args.data_dir,
                log_level=args.log_level,
                mode="report"
            )
            report_main(report_args)
            
    except Exception as e:
        logger.critical(f"Pipeline execution failed: {e}")
        sys.exit(1)
        
    elapsed = time.time() - start_time
    logger.info(f"Pipeline completed in {elapsed:.2f} seconds.")

if __name__ == "__main__":
    main()