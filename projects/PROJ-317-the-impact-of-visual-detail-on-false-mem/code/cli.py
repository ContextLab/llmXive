import argparse
import logging
import sys
from pathlib import Path
from utils.logging import get_logger, get_manipulation_error_log_path
from config import (
    get_project_root, get_stimuli_dir, get_stimuli_metadata_dir,
    get_responses_dir, get_processed_dir, get_figures_dir
)
from stimuli.manipulator import main as manipulator_main
from stimuli.metadata import main as metadata_main
from participants.interface import main as interface_main
from analysis.stats import main as stats_main
from analysis.viz import main as viz_main

def setup_logging():
    """Configure root logger for CLI operations."""
    logger = get_logger("cli")
    logger.setLevel(logging.INFO)
    return logger

def cmd_manipulate(args):
    """Run the image manipulation pipeline."""
    logger = get_logger("manipulator")
    logger.info(f"Processing stimuli from: {get_stimuli_dir()}")
    # Pass arguments to the manipulator's main function
    manipulator_main()

def cmd_metadata(args):
    """Generate metadata for processed stimuli."""
    logger = get_logger("metadata")
    logger.info(f"Generating metadata for: {get_stimuli_dir()}")
    metadata_main()

def cmd_simulate_session(args):
    """Run the simulated participant interface."""
    logger = get_logger("session")
    logger.info("Starting simulated participant session")
    interface_main()

def cmd_analyze(args):
    """Run statistical analysis and generate visualizations."""
    logger = get_logger("analysis")
    logger.info("Starting statistical analysis pipeline")
    # Run stats analysis (ANOVA, power, etc.)
    stats_main()
    # Run visualization generation
    viz_main()
    logger.info("Analysis pipeline completed")

def main():
    """CLI entry point for the llmXive research pipeline."""
    parser = argparse.ArgumentParser(
        description="llmXive Automated Science Pipeline CLI"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Manipulate command
    parser_manipulate = subparsers.add_parser(
        "manipulate", help="Run image manipulation pipeline"
    )
    parser_manipulate.set_defaults(func=cmd_manipulate)

    # Metadata command
    parser_metadata = subparsers.add_parser(
        "metadata", help="Generate stimulus metadata"
    )
    parser_metadata.set_defaults(func=cmd_metadata)

    # Simulate command
    parser_simulate = subparsers.add_parser(
        "simulate", help="Run simulated participant session"
    )
    parser_simulate.set_defaults(func=cmd_simulate_session)

    # Analyze command
    parser_analyze = subparsers.add_parser(
        "analyze", help="Run statistical analysis and generate visualizations"
    )
    parser_analyze.set_defaults(func=cmd_analyze)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    setup_logging()
    args.func(args)

if __name__ == "__main__":
    main()