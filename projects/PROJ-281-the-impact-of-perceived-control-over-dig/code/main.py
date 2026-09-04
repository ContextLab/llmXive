"""
Main pipeline orchestrator for the llmXive automated science pipeline.

This module coordinates the execution of all stages:
1. Data ingestion (T013)
2. Preprocessing (T014a)
3. Anxiety scoring (T015, T016)
4. Proxy extraction (T021-T025)
5. Merge and save (T032)
6. Statistical analysis (T033, T034)
7. Visualization (T035, T036)
"""
import argparse
import logging
import sys
from pathlib import Path

from code.config import (
    CONFIG,
    setup_logging
)
from code.services.data_ingestion import run_data_ingestion_pipeline
from code.services.anxiety_scoring import run_full_scoring_pipeline
from code.services.proxy_extractor import run_full_proxy_pipeline
from code.services.merge_and_save import run_merge_and_save_pipeline
from code.analysis.statistical_test import run_statistical_analysis_pipeline
from code.viz.plot_results import run_visualization_pipeline
from code.viz.save_visualization import save_visualization
from code.services.coverage_validation import run_coverage_validation

logger = logging.getLogger(__name__)


def stage_01_data_ingestion():
    """Execute Stage 1: Data ingestion (T013)."""
    logger.info("Starting Stage 1: Data Ingestion")
    run_data_ingestion_pipeline()
    logger.info("Stage 1 completed successfully")


def stage_02_preprocessing():
    """Execute Stage 2: Text preprocessing (T014a)."""
    logger.info("Starting Stage 2: Text Preprocessing")
    # Preprocessing is integrated into the anxiety scoring pipeline
    # This stage is handled by run_full_scoring_pipeline
    logger.info("Stage 2 completed (integrated with scoring)")


def stage_03_anxiety_scoring():
    """Execute Stage 3: Anxiety scoring (T015, T016, T017)."""
    logger.info("Starting Stage 3: Anxiety Scoring")
    run_full_scoring_pipeline()
    logger.info("Stage 3 completed successfully")


def stage_04_proxy_extraction():
    """Execute Stage 4: Proxy extraction (T021-T026)."""
    logger.info("Starting Stage 4: Proxy Extraction")
    run_full_proxy_pipeline()
    logger.info("Stage 4 completed successfully")


def stage_05_merge_and_validate():
    """Execute Stage 5: Merge and save (T032)."""
    logger.info("Starting Stage 5: Merge and Save")
    run_merge_and_save_pipeline()
    
    # Also run coverage validation (T018a)
    logger.info("Running coverage validation")
    run_coverage_validation()
    
    logger.info("Stage 5 completed successfully")


def stage_06_statistical_analysis():
    """Execute Stage 6: Statistical analysis (T033, T034)."""
    logger.info("Starting Stage 6: Statistical Analysis")
    run_statistical_analysis_pipeline()
    logger.info("Stage 6 completed successfully")


def stage_07_visualization():
    """Execute Stage 7: Visualization (T035, T036)."""
    logger.info("Starting Stage 7: Visualization")
    run_visualization_pipeline()
    save_visualization()
    logger.info("Stage 7 completed successfully")


def run_pipeline(stages=None):
    """
    Run the full analysis pipeline.
    
    Args:
        stages: List of stage numbers to run. If None, runs all stages.
               Stages: 1=ingestion, 2=preprocessing, 3=scoring, 4=proxy,
                      5=merge, 6=analysis, 7=visualization
    """
    if stages is None:
        stages = [1, 2, 3, 4, 5, 6, 7]
    
    stage_functions = {
        1: stage_01_data_ingestion,
        2: stage_02_preprocessing,
        3: stage_03_anxiety_scoring,
        4: stage_04_proxy_extraction,
        5: stage_05_merge_and_validate,
        6: stage_06_statistical_analysis,
        7: stage_07_visualization
    }
    
    for stage_num in sorted(stages):
        if stage_num not in stage_functions:
            logger.warning(f"Unknown stage number: {stage_num}")
            continue
        
        logger.info(f"{'='*60}")
        logger.info(f"Running Stage {stage_num}")
        logger.info(f"{'='*60}")
        
        try:
            stage_functions[stage_num]()
        except Exception as e:
            logger.error(f"Stage {stage_num} failed: {e}")
            raise
    
    logger.info(f"{'='*60}")
    logger.info("Pipeline completed successfully!")
    logger.info(f"{'='*60}")


def main():
    """CLI entry point for the pipeline."""
    parser = argparse.ArgumentParser(
        description="Run the llmXive automated science pipeline for anxiety and control analysis."
    )
    parser.add_argument(
        "--stages",
        type=str,
        default=None,
        help="Comma-separated list of stages to run (e.g., '1,3,5'). Runs all if not specified."
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        default=None,
        help="Path to log file"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    if args.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    
    setup_logging(level, args.log_file)
    
    # Parse stages
    stages = None
    if args.stages:
        stages = [int(s.strip()) for s in args.stages.split(",")]
    
    try:
        run_pipeline(stages)
        sys.exit(0)
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()