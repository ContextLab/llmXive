import argparse
import logging
import sys
from pathlib import Path
import os
import json

from code.config import get_path, ensure_dirs, set_seed, load_config
from code.synthetic_data import run_synthetic_pipeline as run_synthetic_pipeline_func
from code.analysis import run_analysis_pipeline
from code.output_metrics import run_output_pipeline
from code.report_generator import run_report_pipeline
from code.validation_report import run_validation_pipeline

logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Main pipeline runner.")
    parser.add_argument('--mode', type=str, required=True, 
                      choices=['generate-synthetic', 'run-full', 'run-analysis', 'run-report', 'run-validation'],
                      help="Pipeline mode")
    parser.add_argument('--data', type=str, help="Input data path (for run-full)")
    parser.add_argument('--output', type=str, help="Output path (for generate-synthetic)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    
    try:
        if args.mode == 'generate-synthetic':
            logger.info("Mode: generate-synthetic")
            path = run_synthetic_pipeline_func(output_path=args.output)
            logger.info(f"Synthetic data generated at {path}")
        
        elif args.mode == 'run-full':
            logger.info("Mode: run-full")
            input_path = args.data
            if not input_path:
                # Try default
                input_path = get_path("data/processed/synthetic_dataset.csv")
                if not os.path.exists(input_path):
                    # Try morphological_metrics.csv if synthetic not found
                    input_path = get_path("data/processed/morphological_metrics.csv")
            
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Input data not found at {input_path}")
            
            logger.info(f"Using provided data: {input_path}")
            
            # Run analysis
            analysis_results = run_analysis_pipeline(input_path=input_path)
            
            # Run output metrics (T018 logic)
            # The run_output_pipeline expects to read from intermediates or processed
            # We assume run_analysis_pipeline writes to intermediates, and run_output_pipeline reads from there.
            # But T018 says "Output structured CSV logic in code/main.py".
            # Let's call run_output_pipeline to ensure the CSV is written.
            run_output_pipeline()
            
            # Run report
            run_report_pipeline()
            
            # Run validation
            run_validation_pipeline()
            
            logger.info("Full pipeline completed.")
        
        elif args.mode == 'run-analysis':
            logger.info("Mode: run-analysis")
            path = args.data or get_path("data/processed/morphological_metrics.csv")
            run_analysis_pipeline(input_path=path)
        
        elif args.mode == 'run-report':
            logger.info("Mode: run-report")
            run_report_pipeline()
        
        elif args.mode == 'run-validation':
            logger.info("Mode: run-validation")
            run_validation_pipeline()

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
