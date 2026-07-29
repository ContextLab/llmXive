import argparse
import sys
import logging
from pathlib import Path
from src.utils.logging import get_logger, setup_logging
from src.services.download import main as download_main
from src.services.filter import main as filter_main
from src.services.scoring import main as scoring_main
from src.services.analysis import main as analysis_main

logger = get_logger(__name__)

def run_download_filter(args):
    """Execute the download and filter pipeline stages."""
    logger.info("Starting download and filter pipeline...")
    
    # Run download stage
    logger.info("Executing download stage...")
    download_main()
    
    # Run filter stage
    logger.info("Executing filter stage...")
    filter_main()
    
    logger.info("Download and filter pipeline completed successfully.")

def run_score(args):
    """Execute the scoring pipeline stage."""
    logger.info("Starting scoring pipeline...")
    
    scoring_main()
    
    logger.info("Scoring pipeline completed successfully.")

def run_analyze(args):
    """Execute the analysis pipeline stage."""
    logger.info("Starting analysis pipeline...")
    
    analysis_main()
    
    logger.info("Analysis pipeline completed successfully.")

def run_all(args):
    """Execute the full pipeline: download -> filter -> score -> analyze."""
    logger.info("Starting full pipeline execution...")
    
    # Run download and filter
    logger.info("Phase 1: Download and Filter")
    run_download_filter(args)
    
    # Run scoring
    logger.info("Phase 2: Scoring")
    run_score(args)
    
    # Run analysis
    logger.info("Phase 3: Analysis")
    run_analyze(args)
    
    logger.info("Full pipeline completed successfully.")

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="llmXive automated science pipeline for Edit-Compass analysis"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Pipeline stages")
    
    # Download and Filter stage
    parser_download = subparsers.add_parser(
        "download-filter",
        help="Download raw dataset and filter by categories"
    )
    parser_download.set_defaults(func=run_download_filter)
    
    # Scoring stage
    parser_score = subparsers.add_parser(
        "score",
        help="Compute Logic and Fidelity scores for filtered instances"
    )
    parser_score.set_defaults(func=run_score)
    
    # Analysis stage
    parser_analyze = subparsers.add_parser(
        "analyze",
        help="Perform statistical correlation analysis"
    )
    parser_analyze.set_defaults(func=run_analyze)
    
    # Full pipeline
    parser_all = subparsers.add_parser(
        "all",
        help="Run the complete pipeline (download-filter -> score -> analyze)"
    )
    parser_all.set_defaults(func=run_all)
    
    # Validate docs command
    parser_validate = subparsers.add_parser(
        "validate-docs",
        help="Validate documentation and configuration"
    )
    parser_validate.set_defaults(func=lambda args: print("Documentation validation not yet implemented"))
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Setup logging
    setup_logging(level=logging.INFO)
    
    try:
        args.func(args)
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()