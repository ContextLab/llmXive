"""
Main entry point for the llmXive automated science pipeline.

Orchestrates the execution of the following stages:
1. Setup: Initialize directory structures and configuration.
2. Data: Download, tokenize, and validate the micro-corpus.
3. Train: Execute comparative training loops for AR and Diffusion models.
4. Analyze: Perform statistical analysis and benchmark evaluation.
"""
import argparse
import sys
import time
from pathlib import Path

# Add the project root to the path to ensure imports work regardless of CWD
# The script is expected to be run from the project root (code/)
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from utils.setup_data_dirs import setup_data_directories
from utils.logging import setup_logging, get_logger, info, error, warning
from utils.config import get_project_root, reset_config, get_config

# Import stage-specific modules (placeholders for future implementation if not yet created,
# but we assume the pipeline structure expects these functions to exist or be defined here if small)
# Since T002 is just initialization, we define the orchestration logic.

def run_setup_stage(args):
    """
    Initialize project directory structure and configuration.
    Corresponds to Phase 1: Setup.
    """
    info("Starting Setup Stage...")
    try:
        # Initialize logging first if not already done
        if not args.no_setup_logging:
            setup_logging(level=args.log_level)
        
        # Setup data directories
        setup_data_directories()
        
        # Initialize config
        reset_config()
        get_config() # Trigger config load/initialization
        
        info("Setup Stage completed successfully.")
        return True
    except Exception as e:
        error(f"Setup Stage failed: {e}")
        return False

def run_data_stage(args):
    """
    Download, tokenize, and validate the micro-corpus.
    Corresponds to Phase 3: User Story 1.
    """
    info("Starting Data Stage...")
    try:
        # Import data processing modules
        from data.download_micro_corpus import main as download_main
        from data.tokenize_and_stream import main as tokenize_main
        from data.validate_corpus import main as validate_main
        from data.split_data import main as split_main

        info("Downloading micro-corpus...")
        # We pass args to allow configuration overrides if needed
        download_main() 

        info("Tokenizing and streaming corpus...")
        tokenize_main()

        info("Validating corpus...")
        validate_main()

        info("Splitting data...")
        split_main()

        info("Data Stage completed successfully.")
        return True
    except Exception as e:
        error(f"Data Stage failed: {e}")
        return False

def run_train_stage(args):
    """
    Execute comparative training loops for AR and Diffusion models.
    Corresponds to Phase 4: User Story 2.
    """
    info("Starting Training Stage...")
    try:
        from training.run_experiment import main as experiment_main
        
        info("Running training experiment...")
        experiment_main()

        info("Training Stage completed successfully.")
        return True
    except Exception as e:
        error(f"Training Stage failed: {e}")
        return False

def run_analyze_stage(args):
    """
    Perform statistical analysis and benchmark evaluation.
    Corresponds to Phase 5: User Story 3.
    """
    info("Starting Analysis Stage...")
    try:
        from analysis.statistical_test import main as stat_test_main
        from analysis.evaluate_human_eval import main as human_eval_main
        from analysis.compute_metrics import main as compute_metrics_main
        from analysis.evaluate_wikitext2 import main as wikitext2_main
        from analysis.power_analysis import main as power_analysis_main
        from analysis.report_generator import main as report_main

        info("Running statistical test...")
        stat_test_main()

        info("Evaluating HumanEval...")
        human_eval_main()

        info("Computing metrics...")
        compute_metrics_main()

        info("Evaluating WikiText-2...")
        wikitext2_main()

        info("Running power analysis...")
        power_analysis_main()

        info("Generating report...")
        report_main()

        info("Analysis Stage completed successfully.")
        return True
    except Exception as e:
        error(f"Analysis Stage failed: {e}")
        return False

def parse_args():
    parser = argparse.ArgumentParser(
        description="llmXive Automated Science Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
          python main.py --stage setup
          python main.py --stage data
          python main.py --stage train
          python main.py --stage analyze
          python main.py --stage all
        """
    )
    
    parser.add_argument(
        "--stage",
        type=str,
        choices=["setup", "data", "train", "analyze", "all"],
        default="all",
        help="Which stage of the pipeline to run. Default: all"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level. Default: INFO"
    )

    parser.add_argument(
        "--no-setup-logging",
        action="store_true",
        help="Do not setup logging in this stage (useful if already done)"
    )

    return parser.parse_args()

def main():
    args = parse_args()
    
    # Ensure project root is set
    project_root = get_project_root()
    info(f"Project Root: {project_root}")

    success = True
    
    if args.stage in ["setup", "all"]:
        if not run_setup_stage(args):
            success = False
            if args.stage == "all":
                error("Stopping pipeline due to Setup failure.")
                sys.exit(1)

    if args.stage in ["data", "all"] and success:
        if not run_data_stage(args):
            success = False
            if args.stage == "all":
                error("Stopping pipeline due to Data failure.")
                sys.exit(1)

    if args.stage in ["train", "all"] and success:
        if not run_train_stage(args):
            success = False
            if args.stage == "all":
                error("Stopping pipeline due to Training failure.")
                sys.exit(1)

    if args.stage in ["analyze", "all"] and success:
        if not run_analyze_stage(args):
            success = False
            if args.stage == "all":
                error("Stopping pipeline due to Analysis failure.")
                sys.exit(1)

    if success:
        info("Pipeline completed successfully.")
        sys.exit(0)
    else:
        # This point is reached if a non-all stage failed
        sys.exit(1)

if __name__ == "__main__":
    main()