"""
CLI entry point for the llmXive statistical analysis pipeline.

Usage:
    python -m src.code.run_pipeline [--stage <stage_name>]

Stages available:
    - ingestion: Run MPD ingestion and MusicBrainz matching (T010-T012)
    - embeddings: Train Word2Vec and aggregate yearly embeddings (T013-T014)
    - similarity: Compute pairwise similarities and save results (T019-T020)
    - viz: Generate visualization plots (T021-T022)
    - regression: Fit linear regression and robustness checks (T026-T036b)
    - full: Run the entire pipeline from ingestion to regression
"""

import argparse
import logging
import sys
import os
from pathlib import Path

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils import setup_logging, get_logger, set_deterministic_seed
from memory_utils import check_memory_checkpoint, trigger_garbage_collection
from ingest import main as run_ingestion
from embeddings import main as run_embeddings
from similarity import main as run_similarity
from viz import main as run_viz
from regression import main as run_regression

def setup_cli_logging():
    """Configure logging for the CLI entry point."""
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "cli_pipeline.log"
    
    # Setup logging
    setup_logging(log_file=log_file, level=logging.INFO)
    return get_logger("cli_pipeline")

def run_stage(logger, stage_name: str):
    """
    Execute a specific stage of the pipeline.
    
    Args:
        logger: Logger instance
        stage_name: Name of the stage to run
    """
    logger.info(f"Starting stage: {stage_name}")
    
    try:
        if stage_name == "ingestion":
            run_ingestion()
        elif stage_name == "embeddings":
            run_embeddings()
        elif stage_name == "similarity":
            run_similarity()
        elif stage_name == "viz":
            run_viz()
        elif stage_name == "regression":
            run_regression()
        elif stage_name == "full":
            logger.info("Running full pipeline...")
            stages = ["ingestion", "embeddings", "similarity", "viz", "regression"]
            for stage in stages:
                logger.info(f"--- Executing stage: {stage} ---")
                run_stage(logger, stage)
                # Memory checkpoint between major stages
                check_memory_checkpoint(logger)
                trigger_garbage_collection()
            logger.info("Full pipeline completed successfully.")
        else:
            logger.error(f"Unknown stage: {stage_name}")
            return False
        
        logger.info(f"Stage {stage_name} completed successfully.")
        return True
        
    except Exception as e:
        logger.exception(f"Error during stage {stage_name}: {str(e)}")
        return False

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="llmXive Music Genre Evolution Analysis Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Run full pipeline:
    python -m src.code.run_pipeline

  Run only regression stage:
    python -m src.code.run_pipeline --stage regression

  Run only ingestion stage:
    python -m src.code.run_pipeline --stage ingestion
        """
    )
    
    parser.add_argument(
        "--stage",
        type=str,
        choices=["ingestion", "embeddings", "similarity", "viz", "regression", "full"],
        default="full",
        help="Specific stage to run (default: full pipeline)"
    )
    
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)"
    )
    
    args = parser.parse_args()
    
    # Setup deterministic seeding
    set_deterministic_seed(args.seed)
    
    # Setup logging
    logger = setup_cli_logging()
    
    logger.info("=" * 60)
    logger.info("llmXive Pipeline CLI Starting")
    logger.info(f"Stage: {args.stage}")
    logger.info(f"Random Seed: {args.seed}")
    logger.info("=" * 60)
    
    success = run_stage(logger, args.stage)
    
    if success:
        logger.info("Pipeline execution finished successfully.")
        sys.exit(0)
    else:
        logger.error("Pipeline execution failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()