import argparse
import sys
import logging
from pathlib import Path

# Ensure src is in path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.utils.logging import get_logger, setup_logging
from src.services.download import main as download_main
from src.services.filter import main as filter_main
from src.services.scoring import main as scoring_main
from src.services.analysis import main as analysis_main

logger = get_logger(__name__)

def run_download_filter(args):
    """Execute the download and filter pipeline stages."""
    logger.info("Starting download-filter stage")
    
    # Run download
    logger.info("Running download stage...")
    download_args = argparse.Namespace(
        output_dir=str(args.output_dir / "raw"),
        dataset_id=args.dataset_id,
        force=args.force
    )
    download_main(download_args)
    
    # Run filter
    logger.info("Running filter stage...")
    filter_args = argparse.Namespace(
        raw_dir=str(args.output_dir / "raw"),
        output_dir=str(args.output_dir / "filtered"),
        categories=args.categories
    )
    filter_main(filter_args)
    
    logger.info("Download-filter stage completed successfully")

def run_score(args):
    """Execute the scoring pipeline stage."""
    logger.info("Starting score stage")
    
    input_dir = args.input_dir or str(args.output_dir / "filtered")
    output_dir = args.output_dir / "scores"
    
    scoring_args = argparse.Namespace(
        input_dir=input_dir,
        output_dir=str(output_dir),
        batch_size=args.batch_size,
        vlm_model=args.vlm_model,
        embedding_model=args.embedding_model,
        force=args.force
    )
    
    scoring_main(scoring_args)
    logger.info("Score stage completed successfully")

def run_analyze(args):
    """Execute the analysis pipeline stage."""
    logger.info("Starting analyze stage")
    
    scores_dir = args.scores_dir or str(args.output_dir / "scores")
    filtered_dir = args.filtered_dir or str(args.output_dir / "filtered")
    output_dir = args.output_dir / "outputs"
    
    analysis_args = argparse.Namespace(
        scores_dir=scores_dir,
        filtered_dir=filtered_dir,
        output_dir=str(output_dir),
        threshold=args.threshold,
        fdr_alpha=args.fdr_alpha
    )
    
    analysis_main(analysis_args)
    logger.info("Analyze stage completed successfully")

def run_all(args):
    """Execute the full pipeline: download -> filter -> score -> analyze."""
    logger.info("Starting full pipeline")
    
    # 1. Download & Filter
    run_download_filter(args)
    
    # 2. Score
    run_score(args)
    
    # 3. Analyze
    run_analyze(args)
    
    logger.info("Full pipeline completed successfully")

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="llmXive Pipeline: Edit-Compass Benchmark Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Pipeline stages")
    
    # Common arguments
    parser.add_argument(
        "--output-dir", type=Path, default=Path("data"),
        help="Base output directory for all data (default: data/)"
    )
    parser.add_argument(
        "--dataset-id", type=str, default="llmXive/Edit-Compass",
        help="HuggingFace dataset ID to download"
    )
    parser.add_argument(
        "--categories", type=str, nargs="+",
        default=["World Knowledge Reasoning", "Visual Reasoning"],
        help="Categories to filter (default: World Knowledge Reasoning, Visual Reasoning)"
    )
    parser.add_argument(
        "--batch-size", type=int, default=8,
        help="Initial batch size for scoring (default: 8)"
    )
    parser.add_argument(
        "--vlm-model", type=str, default="Phi-3-mini-4k-instruct-GGUF",
        help="VLM model name for description generation"
    )
    parser.add_argument(
        "--embedding-model", type=str, default="all-MiniLM-L6-v2",
        help="Sentence transformer model for logic scoring"
    )
    parser.add_argument(
        "--threshold", type=float, default=0.5,
        help="Correlation threshold for independence check (default: 0.5)"
    )
    parser.add_argument(
        "--fdr-alpha", type=float, default=0.05,
        help="FDR correction alpha (default: 0.05)"
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Force re-download/re-computation even if outputs exist"
    )
    
    # download-filter subcommand
    subparsers.add_parser("download-filter", help="Download and filter dataset")
    
    # score subcommand
    subparsers.add_parser("score", help="Generate scores for filtered dataset")
    
    # analyze subcommand
    subparsers.add_parser("analyze", help="Perform statistical analysis")
    
    # all subcommand
    subparsers.add_parser("all", help="Run full pipeline")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Setup logging
    setup_logging(level=logging.INFO)
    
    try:
        if args.command == "download-filter":
            run_download_filter(args)
        elif args.command == "score":
            run_score(args)
        elif args.command == "analyze":
            run_analyze(args)
        elif args.command == "all":
            run_all(args)
        else:
            logger.error(f"Unknown command: {args.command}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()