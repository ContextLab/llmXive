"""
Main entry point for running the full code cleanup, formatting, and refactoring pipeline.

This script orchestrates the three main cleanup phases:
1. Cleanup: Remove unused imports, standardize logging, normalize docstrings
2. Format: Enforce PEP 8, normalize whitespace, fix indentation
3. Refactor: Simplify expressions, add type hints, identify patterns

Usage:
    python code/run_cleanup.py [--directory <path>] [--verbose]
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from time import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.cleanup import cleanup_directory, CleanupReport
from utils.formatting import format_directory, FormattingReport
from utils.refactor import refactor_directory, RefactorReport


def setup_logging(verbose: bool = False):
    """Configure logging for the cleanup pipeline."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def run_pipeline(directory: str, exclude_patterns: list, verbose: bool) -> dict:
    """
    Run the full cleanup pipeline on a directory.

    Args:
        directory: Path to the directory to process
        exclude_patterns: List of patterns to exclude
        verbose: Enable verbose output

    Returns:
        Dictionary with pipeline results
    """
    results = {
        'cleanup': [],
        'format': [],
        'refactor': [],
        'summary': {}
    }

    logger = logging.getLogger(__name__)
    logger.info(f"Starting cleanup pipeline for: {directory}")
    logger.info(f"Excluding: {', '.join(exclude_patterns)}")

    start_time = time()

    # Phase 1: Cleanup
    logger.info("\n" + "=" * 60)
    logger.info("PHASE 1: CODE CLEANUP")
    logger.info("=" * 60)
    results['cleanup'] = cleanup_directory(directory, exclude_patterns)

    # Phase 2: Formatting
    logger.info("\n" + "=" * 60)
    logger.info("PHASE 2: CODE FORMATTING")
    logger.info("=" * 60)
    results['format'] = format_directory(directory, exclude_patterns)

    # Phase 3: Refactoring
    logger.info("\n" + "=" * 60)
    logger.info("PHASE 3: CODE REFACTORING")
    logger.info("=" * 60)
    results['refactor'] = refactor_directory(directory, exclude_patterns)

    end_time = time()
    duration = end_time - start_time

    # Generate summary
    total_files = len(set(
        r.file_path for r in results['cleanup'] + results['format'] + results['refactor']
    ))
    total_issues = (
        sum(r.issues_found for r in results['cleanup']) +
        sum(r.changes_made for r in results['format']) +
        sum(r.improvements_made for r in results['refactor'])
    )
    total_fixed = (
        sum(r.issues_fixed for r in results['cleanup']) +
        sum(r.changes_made for r in results['format']) +
        sum(r.improvements_made for r in results['refactor'])
    )

    results['summary'] = {
        'total_files': total_files,
        'total_issues': total_issues,
        'total_fixed': total_fixed,
        'duration_seconds': duration
    }

    return results


def print_summary(results: dict):
    """Print a formatted summary of the pipeline results."""
    summary = results['summary']

    print("\n" + "=" * 70)
    print("                    CLEANUP PIPELINE SUMMARY")
    print("=" * 70)
    print(f"Directory processed: {results.get('directory', 'N/A')}")
    print(f"Total files processed: {summary['total_files']}")
    print(f"Total issues identified: {summary['total_issues']}")
    print(f"Total issues fixed: {summary['total_fixed']}")
    print(f"Pipeline duration: {summary['duration_seconds']:.2f} seconds")
    print("=" * 70)

    # Breakdown by phase
    print("\nPhase Breakdown:")
    print(f"  Cleanup:    {len(results['cleanup'])} files, {sum(r.issues_fixed for r in results['cleanup'])} fixes")
    print(f"  Formatting: {len(results['format'])} files, {sum(r.changes_made for r in results['format'])} changes")
    print(f"  Refactoring: {len(results['refactor'])} files, {sum(r.improvements_made for r in results['refactor'])} improvements")

    # Files with changes
    changed_files = set()
    for r in results['cleanup']:
        if r.issues_fixed > 0:
            changed_files.add(r.file_path)
    for r in results['format']:
        if r.changes_made > 0:
            changed_files.add(r.file_path)
    for r in results['refactor']:
        if r.improvements_made > 0:
            changed_files.add(r.file_path)

    if changed_files:
        print("\nFiles Modified:")
        for f in sorted(changed_files):
            print(f"  - {f}")
    else:
        print("\nNo files were modified. Code is already clean!")

    print("=" * 70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run the full code cleanup, formatting, and refactoring pipeline"
    )
    parser.add_argument(
        '--directory',
        type=str,
        default='code',
        help='Directory to process (default: code)'
    )
    parser.add_argument(
        '--exclude',
        nargs='+',
        default=['__pycache__', 'venv', '.git', 'build', 'dist'],
        help='Patterns to exclude'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    if not os.path.isdir(args.directory):
        logger.error(f"Directory not found: {args.directory}")
        return 1

    results = run_pipeline(args.directory, args.exclude, args.verbose)
    print_summary(results)

    # Return 0 if all issues were fixed, 1 otherwise
    return 0 if results['summary']['total_issues'] == results['summary']['total_fixed'] else 1


if __name__ == '__main__':
    sys.exit(main())