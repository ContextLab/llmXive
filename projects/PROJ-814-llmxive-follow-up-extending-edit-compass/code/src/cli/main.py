import argparse
import sys
import logging
from pathlib import Path

# Ensure project root is in path for imports if running as script
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

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
    
    logger.info("Download and filter pipeline completed successfully.")


def run_score(args):
    """Execute the scoring pipeline stage.
    
    Reads filtered data from data/filtered/, computes Logic and Fidelity scores,
    and writes results to data/scores/.
    """
    logger.info("Starting scoring pipeline...")
    
    scoring_main()
    
    logger.info("Scoring pipeline completed successfully.")


def run_analyze(args):
    """Execute the analysis pipeline stage.
    
    Reads scores from data/scores/, performs statistical analysis,
    and writes reports to outputs/.
    """
    logger.info("Starting analysis pipeline...")
    
    analysis_main()
    
    logger.info("Analysis pipeline completed successfully.")


def run_all(args):
    """Execute the full pipeline: download, filter, score, analyze."""
    logger.info("Starting full pipeline...")
    
    run_download_filter(args)
    run_score(args)
    run_analyze(args)
    
    logger.info("Full pipeline completed successfully.")


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="llmXive Automated Science Pipeline CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Download-Filter command
    parser_download = subparsers.add_parser(
        "download-filter",
        help="Download raw dataset and filter by category"
    )
    parser_download.set_defaults(func=run_download_filter)
    
    # Score command
    parser_score = subparsers.add_parser(
        "score",
        help="Compute Logic and Fidelity scores for filtered instances"
    )
    parser_score.set_defaults(func=run_score)
    
    # Analyze command
    parser_analyze = subparsers.add_parser(
        "analyze",
        help="Perform statistical correlation analysis on scores"
    )
    parser_analyze.set_defaults(func=run_analyze)
    
    # All command
    parser_all = subparsers.add_parser(
        "all",
        help="Run the entire pipeline"
    )
    parser_all.set_defaults(func=run_all)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Setup logging
    setup_logging(level=logging.INFO)
    
    try:
        args.func(args)
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()