import argparse
import logging
import sys
from pathlib import Path

from utils.logging import get_logger, get_manipulation_error_log_path
from config import (
    get_project_root,
    get_data_dir,
    get_stimuli_dir,
    get_stimuli_metadata_dir,
    get_responses_dir,
    get_processed_dir,
    get_logs_dir,
    get_log_level,
    get_log_file_path,
    get_error_log_file_path,
    get_manipulation_error_log_path as get_manipulation_log,
    get_dataset_source,
    get_alpha_level,
    get_power_target,
    get_effect_size
)
from stimuli.manipulator import main as cmd_manipulate_main
from stimuli.metadata import main as cmd_metadata_main
from participants.session import main as cmd_simulate_session_main
from analysis.anova import main as cmd_analyze_main

logger = get_logger(__name__)

def setup_logging():
    """Configure logging for the CLI."""
    log_level = get_log_level()
    log_file = get_log_file_path()
    error_log = get_error_log_file_path()
    manipulation_log = get_manipulation_log()

    handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)

    # File handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    # Error log handler
    if error_log:
        error_log.parent.mkdir(parents=True, exist_ok=True)
        error_handler = logging.FileHandler(error_log)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        handlers.append(error_handler)

    # Manipulation error log handler
    if manipulation_log:
        manipulation_log.parent.mkdir(parents=True, exist_ok=True)
        manip_handler = logging.FileHandler(manipulation_log)
        manip_handler.setLevel(logging.ERROR)
        manip_handler.setFormatter(formatter)
        handlers.append(manip_handler)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    for handler in handlers:
        root_logger.addHandler(handler)

def cmd_manipulate(args):
    """Command to run the stimulus manipulation pipeline."""
    logger.info("Starting stimulus manipulation pipeline...")
    # Delegate to the manipulator module's main function
    return cmd_manipulate_main()

def cmd_metadata(args):
    """Command to generate stimulus metadata."""
    logger.info("Generating stimulus metadata...")
    # Build arguments for the metadata module
    metadata_args = argparse.Namespace(
        baseline=args.baseline,
        enhanced=args.enhanced,
        reduced=args.reduced,
        log=args.log,
        output_dir=args.output_dir
    )
    return cmd_metadata_main()

def cmd_simulate_session(args):
    """Command to run simulated participant sessions."""
    logger.info("Starting simulated participant sessions...")
    return cmd_simulate_session_main()

def cmd_analyze(args):
    """Command to run statistical analysis."""
    logger.info("Starting statistical analysis...")
    return cmd_analyze_main()

def main():
    """Main CLI entry point."""
    setup_logging()

    parser = argparse.ArgumentParser(description="llmXive Research Pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Manipulate command
    manipulate_parser = subparsers.add_parser("manipulate", help="Run stimulus manipulation")
    manipulate_parser.set_defaults(func=cmd_manipulate)

    # Metadata command
    metadata_parser = subparsers.add_parser("metadata", help="Generate stimulus metadata")
    metadata_parser.add_argument('--baseline', nargs='+', help='Baseline image IDs')
    metadata_parser.add_argument('--enhanced', nargs='+', help='Enhanced image IDs')
    metadata_parser.add_argument('--reduced', nargs='+', help='Reduced image IDs')
    metadata_parser.add_argument('--log', type=str, help='Path to generation log')
    metadata_parser.add_argument('--output-dir', type=str, help='Output directory')
    metadata_parser.set_defaults(func=cmd_metadata)

    # Simulate session command
    simulate_parser = subparsers.add_parser("simulate", help="Run simulated participant sessions")
    simulate_parser.add_argument('--count', type=int, default=10, help='Number of sessions')
    simulate_parser.add_argument('--seed', type=int, default=42, help='Random seed')
    simulate_parser.set_defaults(func=cmd_simulate_session)

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Run statistical analysis")
    analyze_parser.add_argument('--input', type=str, help='Input data file')
    analyze_parser.add_argument('--output', type=str, help='Output results file')
    analyze_parser.set_defaults(func=cmd_analyze)

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate project structure")
    validate_parser.add_argument('--quickstart', action='store_true', help='Run quickstart validation')
    validate_parser.set_defaults(func=lambda args: 0)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    return args.func(args)

if __name__ == "__main__":
    sys.exit(main())
