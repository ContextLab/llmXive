import argparse
import sys
import logging
from pathlib import Path

# Adjust import to match project structure (src/ is the package root in this context)
# Based on API surface: from src.utils.logging import get_logger, setup_logging
from src.utils.logging import get_logger, setup_logging
from src.services.download import main as download_main
from src.services.filter import main as filter_main
from src.services.scoring import main as scoring_main
from src.services.analysis import main as analysis_main

logger = get_logger(__name__)

def run_download_filter(args):
    """Execute the download and filter pipeline stages."""
    logger.info("Starting download and filter pipeline...")
    # Run download
    download_main()
    # Run filter
    filter_main()
    logger.info("Download and filter pipeline completed.")

def run_score(args):
    """Execute the scoring pipeline stage.
    
    Reads filtered data from data/filtered/, computes Logic and Fidelity scores,
    and writes results to data/scores/.
    """
    logger.info("Starting scoring pipeline...")
    scoring_main()
    logger.info("Scoring pipeline completed. Results written to data/scores/.")

def run_analyze(args):
    """Execute the analysis pipeline stage."""
    logger.info("Starting analysis pipeline...")
    analysis_main()
    logger.info("Analysis pipeline completed.")

def run_all(args):
    """Execute the full pipeline: download -> filter -> score -> analyze."""
    logger.info("Starting full pipeline...")
    run_download_filter(args)
    run_score(args)
    run_analyze(args)
    logger.info("Full pipeline completed.")

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="llmXive Automated Science Pipeline CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Download & Filter
    p_download = subparsers.add_parser('download-filter', help='Download and filter dataset')
    p_download.set_defaults(func=run_download_filter)
    
    # Scoring
    p_score = subparsers.add_parser('score', help='Compute Logic and Fidelity scores')
    p_score.set_defaults(func=run_score)
    
    # Analysis
    p_analyze = subparsers.add_parser('analyze', help='Perform statistical analysis')
    p_analyze.set_defaults(func=run_analyze)
    
    # Full Pipeline
    p_all = subparsers.add_parser('all', help='Run the entire pipeline')
    p_all.set_defaults(func=run_all)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    # Setup logging
    setup_logging(level=logging.INFO)
    
    try:
        args.func(args)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()