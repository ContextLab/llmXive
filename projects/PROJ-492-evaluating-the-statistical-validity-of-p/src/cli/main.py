"""
CLI interface skeleton for the A/B Test Validity Audit Pipeline.

This module provides the entry point for the command-line interface.
It is designed to be extended with subcommands for each pipeline stage.
"""

import argparse
import sys
from typing import Optional

# Version information
__version__ = "0.1.0"

def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="abtest-audit",
        description="Evaluate the statistical validity of public A/B test summaries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  abtest-audit --help              Show this help message
  abtest-audit --version           Show version information
  abtest-audit run                 Run the full audit pipeline
        """
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show program version and exit"
    )
    
    # Subparsers for future commands
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands"
    )
    
    # 'run' command - will be implemented in T032
    run_parser = subparsers.add_parser(
        "run",
        help="Run the full audit pipeline"
    )
    run_parser.add_argument(
        "--input",
        type=str,
        default="input/urls.csv",
        help="Path to input URLs CSV file (default: input/urls.csv)"
    )
    run_parser.add_argument(
        "--output",
        type=str,
        default="output",
        help="Output directory for audit artifacts (default: output)"
    )
    run_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser

def main(args: Optional[list[str]] = None) -> int:
    """
    Main entry point for the CLI.
    
    Args:
        args: Command-line arguments (defaults to sys.argv[1:])
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args)
    
    if parsed_args.command is None:
        parser.print_help()
        return 0
    
    if parsed_args.command == "run":
        # Placeholder for T032 implementation
        print("Audit pipeline runner - implementation in progress")
        print(f"Input: {parsed_args.input}")
        print(f"Output: {parsed_args.output}")
        if parsed_args.verbose:
            print("Verbose mode enabled")
        return 0
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
