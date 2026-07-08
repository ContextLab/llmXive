import argparse
import logging
import sys
from pathlib import Path
from utils.logging import get_logger, get_manipulation_error_log_path
from config import (
    get_config, ensure_directories, get_log_level, get_log_file_path,
    get_error_log_file_path, get_manipulation_error_log_path as get_manip_log
)
from analysis.stats import main as run_power_analysis
from data.loader import main as run_loader
from stimuli.manipulator import main as run_manipulator
from stimuli.metadata import main as run_metadata
from participants.session import main as run_session
from analysis.viz import main as run_viz

def setup_logging():
    """Configure logging based on environment."""
    log_level = get_log_level()
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(get_log_file_path()),
            logging.StreamHandler(sys.stdout)
        ]
    )

def cmd_manipulate(args):
    """Run image manipulation pipeline."""
    setup_logging()
    run_manipulator()

def cmd_metadata(args):
    """Generate stimulus metadata."""
    setup_logging()
    run_metadata()

def cmd_simulate_session(args):
    """Run simulated participant session."""
    setup_logging()
    run_session()

def cmd_analyze(args):
    """Run statistical analysis."""
    setup_logging()
    if args.power:
        run_power_analysis()
    else:
        run_viz()

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="llmXive Research Pipeline")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Manipulate command
    p_manipulate = subparsers.add_parser("manipulate", help="Run image manipulation")
    p_manipulate.set_defaults(func=cmd_manipulate)

    # Metadata command
    p_metadata = subparsers.add_parser("metadata", help="Generate metadata")
    p_metadata.set_defaults(func=cmd_metadata)

    # Simulate command
    p_simulate = subparsers.add_parser("simulate", help="Run simulation")
    p_simulate.set_defaults(func=cmd_simulate_session)

    # Analyze command
    p_analyze = subparsers.add_parser("analyze", help="Run analysis")
    p_analyze.add_argument("--power", action="store_true", help="Run power analysis only")
    p_analyze.set_defaults(func=cmd_analyze)

    args = parser.parse_args()
    
    # Ensure directories exist
    ensure_directories()
    
    if args.command:
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()