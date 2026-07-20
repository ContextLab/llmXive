"""
Main entry point for the project pipeline.

This script orchestrates the full pipeline execution as defined in the run-book.
It supports modes for generating synthetic data (for validation) and running
the full analysis pipeline.

Usage:
    python code/main.py --mode generate-synthetic --output data/processed/synthetic_dataset.csv
    python code/main.py --mode run-full --data data/processed/synthetic_dataset.csv
"""
import argparse
import logging
import sys
from pathlib import Path

from code.config import get_path, ensure_dirs, set_seed, load_config
from code.data_ingestion import run_ingestion_pipeline
from code.synthetic_data import run_synthetic_pipeline
from code.output_metrics import run_output_pipeline
from code.analysis import run_analysis_pipeline
from code.report_generator import run_report_pipeline
from code.validation_report import run_validation_pipeline

def main():
    parser = argparse.ArgumentParser(description="Main pipeline entry point")
    parser.add_argument('--mode', type=str, required=True,
                        choices=['generate-synthetic', 'run-full'],
                        help='Pipeline mode: generate-synthetic or run-full')
    parser.add_argument('--output', type=str, default=None,
                        help='Output path for synthetic data (mode: generate-synthetic)')
    parser.add_argument('--data', type=str, default=None,
                        help='Input data path for full run (mode: run-full)')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Set seed
    set_seed(args.seed)
    
    # Load config
    config = load_config()
    
    try:
        if args.mode == 'generate-synthetic':
            logger.info("Mode: generate-synthetic")
            output_path = args.output or str(Path(get_path('data_processed')) / 'synthetic_dataset.csv')
            ensure_dirs(Path(output_path).parent)
            
            # Generate synthetic data
            run_synthetic_pipeline(output_path=output_path)
            logger.info(f"Synthetic data generated at {output_path}")
            
        elif args.mode == 'run-full':
            logger.info("Mode: run-full")
            
            # Step 1: Output morphological metrics (T018)
            # If --data is provided, use it; otherwise run output pipeline
            if args.data:
                logger.info(f"Using provided data: {args.data}")
                # Note: In a real scenario, we'd load from args.data
                # For now, we assume the data is already in the expected format
                # and proceed to analysis
                metrics_path = args.data
            else:
                # Run T018 to generate metrics
                metrics_path = run_output_pipeline(use_synthetic=True)
            
            # Step 2: Run analysis (T023-T029)
            logger.info("Running analysis pipeline...")
            analysis_results = run_analysis_pipeline(input_path=str(metrics_path))
            
            # Step 3: Generate reports (T028-T029)
            logger.info("Generating reports...")
            run_report_pipeline()
            
            # Step 4: Validation (T033-T036)
            logger.info("Running validation pipeline...")
            run_validation_pipeline()
            
            logger.info("Full pipeline completed successfully.")
            
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
