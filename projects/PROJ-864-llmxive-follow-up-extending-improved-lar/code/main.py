import argparse
import sys
import time
from pathlib import Path
from utils.setup_data_dirs import setup_data_directories
from utils.logging import setup_logging, get_logger, info, error, warning

def run_setup_stage():
    """Execute the setup stage: initialize directory structure."""
    logger = get_logger(__name__)
    info("Starting setup stage...")
    try:
        created_dirs = setup_data_directories()
        info(f"Setup stage completed. Created {len(created_dirs)} directories.")
        return True
    except Exception as e:
        error(f"Setup stage failed: {e}")
        return False

def run_data_stage():
    """Execute the data processing stage."""
    logger = get_logger(__name__)
    info("Starting data stage...")
    try:
        # Import here to avoid circular imports and ensure dependencies are ready
        from data.download_micro_corpus import main as download_corpus_main
        from data.tokenize_and_stream import main as tokenize_main
        from data.validate_corpus import main as validate_corpus_main
        from data.split_data import main as split_data_main

        # Execute pipeline steps
        info("Step 1: Download and balance micro-corpus")
        if not download_corpus_main():
            return False

        info("Step 2: Tokenize and stream corpus")
        if not tokenize_main():
            return False

        info("Step 3: Validate corpus")
        if not validate_corpus_main():
            return False

        info("Step 4: Split data into train/test")
        if not split_data_main():
            return False

        info("Data stage completed successfully.")
        return True
    except Exception as e:
        error(f"Data stage failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_train_stage():
    """Execute the training stage."""
    logger = get_logger(__name__)
    info("Starting training stage...")
    try:
        # Import here to avoid circular imports
        from training.run_experiment import main as run_experiment_main

        info("Executing training experiment...")
        if not run_experiment_main():
            return False

        info("Training stage completed successfully.")
        return True
    except Exception as e:
        error(f"Training stage failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_analyze_stage():
    """Execute the analysis stage."""
    logger = get_logger(__name__)
    info("Starting analysis stage...")
    try:
        # Import here to avoid circular imports
        from analysis.statistical_test import main as statistical_test_main
        from analysis.evaluate_human_eval import main as evaluate_human_eval_main
        from analysis.evaluate_wikitext2 import main as evaluate_wikitext2_main
        from analysis.compute_metrics import main as compute_metrics_main
        from analysis.report_generator import main as report_generator_main

        # Execute analysis pipeline
        info("Step 1: Run statistical analysis (ANOVA)")
        if not statistical_test_main():
            return False

        info("Step 2: Evaluate on HumanEval benchmark")
        if not evaluate_human_eval_main():
            return False

        info("Step 3: Evaluate on WikiText-2 for cross-domain validation")
        if not evaluate_wikitext2_main():
            return False

        info("Step 4: Compute metrics and correlations")
        if not compute_metrics_main():
            return False

        info("Step 5: Generate final report")
        if not report_generator_main():
            return False

        info("Analysis stage completed successfully.")
        return True
    except Exception as e:
        error(f"Analysis stage failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def parse_args():
    parser = argparse.ArgumentParser(description="llmXive Automated Science Pipeline")
    parser.add_argument(
        "stage",
        choices=["setup", "data", "train", "analyze"],
        help="Stage to execute"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Setup logging
    setup_logging(level=args.log_level)
    logger = get_logger(__name__)
    
    info(f"Starting stage: {args.stage}")
    start_time = time.time()
    
    success = False
    if args.stage == "setup":
        success = run_setup_stage()
    elif args.stage == "data":
        success = run_data_stage()
    elif args.stage == "train":
        success = run_train_stage()
    elif args.stage == "analyze":
        success = run_analyze_stage()
    
    elapsed = time.time() - start_time
    
    if success:
        info(f"Stage '{args.stage}' completed successfully in {elapsed:.2f}s")
        return 0
    else:
        error(f"Stage '{args.stage}' failed after {elapsed:.2f}s")
        return 1

if __name__ == "__main__":
    sys.exit(main())