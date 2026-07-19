import argparse
import sys
import logging
from pathlib import Path

# Adjust imports to match project structure (src/ at root)
from src.utils.logging import get_logger, setup_logging
from src.services.download import main as download_main
from src.services.filter import main as filter_main
from src.services.scoring import main as scoring_main
from src.services.analysis import main as analysis_main

logger = get_logger(__name__)

def run_download_filter(args):
    """Execute the download and filter pipeline stages."""
    logger.info("Starting Download and Filter pipeline...")
    
    # Run download
    download_args = argparse.Namespace(
        output_dir=args.output_dir,
        force_download=args.force_download
    )
    download_main(download_args)
    
    # Run filter
    filter_args = argparse.Namespace(
        input_dir=args.output_dir,
        output_dir=args.output_dir,
        categories=args.categories or ["World Knowledge Reasoning", "Visual Reasoning"]
    )
    filter_main(filter_args)
    
    logger.info("Download and Filter pipeline completed successfully.")

def run_score(args):
    """Execute the scoring pipeline stage."""
    logger.info("Starting Scoring pipeline...")
    
    scoring_args = argparse.Namespace(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        batch_size=args.batch_size,
        max_workers=args.max_workers,
        memory_limit_gb=args.memory_limit_gb
    )
    scoring_main(scoring_args)
    
    logger.info(f"Scoring pipeline completed. Results saved to {args.output_dir}")

def run_analyze(args):
    """Execute the analysis pipeline stage."""
    logger.info("Starting Analysis pipeline...")
    
    analysis_args = argparse.Namespace(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        correlation_threshold=args.correlation_threshold
    )
    analysis_main(analysis_args)
    
    logger.info(f"Analysis pipeline completed. Reports saved to {args.output_dir}")

def run_all(args):
    """Execute the full pipeline: download -> filter -> score -> analyze."""
    logger.info("Starting Full Pipeline...")
    
    # Stage 1: Download & Filter
    logger.info("--- Stage 1: Download & Filter ---")
    run_download_filter(args)
    
    # Stage 2: Scoring
    logger.info("--- Stage 2: Scoring ---")
    filter_output = Path(args.output_dir) / "filtered"
    score_output = Path(args.output_dir) / "scores"
    score_args = argparse.Namespace(
        input_dir=str(filter_output),
        output_dir=str(score_output),
        batch_size=args.batch_size,
        max_workers=args.max_workers,
        memory_limit_gb=args.memory_limit_gb
    )
    scoring_main(score_args)
    
    # Stage 3: Analysis
    logger.info("--- Stage 3: Analysis ---")
    analysis_output = Path(args.output_dir) / "analysis"
    analysis_args = argparse.Namespace(
        input_dir=str(score_output),
        output_dir=str(analysis_output),
        correlation_threshold=args.correlation_threshold
    )
    analysis_main(analysis_args)
    
    logger.info("Full Pipeline completed successfully.")

def main():
    parser = argparse.ArgumentParser(
        description="llmXive Automated Science Pipeline CLI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Pipeline stages")
    
    # Common arguments
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=Path("data"),
        help="Base output directory for all artifacts"
    )
    
    # Download-Filter Stage
    sub_download = subparsers.add_parser(
        "download-filter",
        help="Download dataset and filter by categories"
    )
    sub_download.add_argument(
        "--categories", "-c",
        nargs="+",
        default=["World Knowledge Reasoning", "Visual Reasoning"],
        help="Categories to filter for"
    )
    sub_download.add_argument(
        "--force-download",
        action="store_true",
        help="Force re-download even if file exists"
    )
    sub_download.set_defaults(func=run_download_filter)
    
    # Score Stage
    sub_score = subparsers.add_parser(
        "score",
        help="Compute Logic and Fidelity scores"
    )
    sub_score.add_argument(
        "--input-dir", "-i",
        type=Path,
        default=Path("data/filtered"),
        help="Directory containing filtered instances"
    )
    sub_score.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/scores"),
        help="Directory to save score results"
    )
    sub_score.add_argument(
        "--batch-size",
        type=int,
        default=8,
        help="Initial batch size for processing"
    )
    sub_score.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="Maximum number of worker threads"
    )
    sub_score.add_argument(
        "--memory-limit-gb",
        type=float,
        default=6.5,
        help="Memory limit in GB for batch processing"
    )
    sub_score.set_defaults(func=run_score)
    
    # Analyze Stage
    sub_analyze = subparsers.add_parser(
        "analyze",
        help="Perform statistical correlation analysis"
    )
    sub_analyze.add_argument(
        "--input-dir", "-i",
        type=Path,
        default=Path("data/scores"),
        help="Directory containing score records"
    )
    sub_analyze.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs"),
        help="Directory to save analysis reports"
    )
    sub_analyze.add_argument(
        "--correlation-threshold",
        type=float,
        default=0.5,
        help="Threshold for circular validation risk"
    )
    sub_analyze.set_defaults(func=run_analyze)
    
    # Full Pipeline
    sub_full = subparsers.add_parser(
        "all",
        help="Run the complete pipeline"
    )
    sub_full.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data/raw"),
        help="Base input directory (used for raw data)"
    )
    sub_full.add_argument(
        "--categories", "-c",
        nargs="+",
        default=["World Knowledge Reasoning", "Visual Reasoning"],
        help="Categories to filter for"
    )
    sub_full.add_argument(
        "--force-download",
        action="store_true",
        help="Force re-download even if file exists"
    )
    sub_full.add_argument(
        "--batch-size",
        type=int,
        default=8,
        help="Initial batch size for scoring"
    )
    sub_full.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="Maximum number of worker threads for scoring"
    )
    sub_full.add_argument(
        "--memory-limit-gb",
        type=float,
        default=6.5,
        help="Memory limit in GB for scoring"
    )
    sub_full.add_argument(
        "--correlation-threshold",
        type=float,
        default=0.5,
        help="Threshold for circular validation risk"
    )
    sub_full.set_defaults(func=run_all)
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=logging.INFO)
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    try:
        args.func(args)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()