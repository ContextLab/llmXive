import argparse
import logging
import sys
from pathlib import Path
import os
import json
from code.config import get_path, ensure_dirs, set_seed, load_config
from code.synthetic_data import run_synthetic_pipeline
from code.analysis import run_analysis_pipeline
from code.output_metrics import run_output_pipeline
from code.report_generator import run_report_pipeline
from code.validation_report import run_validation_pipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Microglial Morphology Analysis Pipeline')
    parser.add_argument('--mode', type=str, choices=['generate-synthetic', 'run-full', 'run-analysis', 'run-output', 'run-report', 'run-validation'],
                      help='Pipeline mode')
    parser.add_argument('--data', type=str, help='Input data path (for run-full mode)')
    parser.add_argument('--output', type=str, help='Output path (for generate-synthetic mode)')
    
    args = parser.parse_args()
    
    # Set random seed
    set_seed(42)
    
    try:
        if args.mode == 'generate-synthetic':
            logger.info("Mode: generate-synthetic")
            output_path = args.output or get_path('processed', 'synthetic_dataset.csv')
            ensure_dirs(output_path)
            run_synthetic_pipeline(output_path=output_path)
            logger.info(f"Synthetic data generated at {output_path}")
        
        elif args.mode == 'run-full':
            logger.info("Mode: run-full")
            input_path = args.data or get_path('processed', 'synthetic_dataset.csv')
            if not os.path.exists(input_path):
                # Try to generate synthetic data first
                logger.info("Input data not found. Generating synthetic data...")
                synthetic_path = get_path('processed', 'synthetic_dataset.csv')
                run_synthetic_pipeline(output_path=synthetic_path)
                input_path = synthetic_path
            
            logger.info(f"Using provided data: {input_path}")
            logger.info("Running analysis pipeline...")
            
            # Run analysis pipeline
            analysis_results = run_analysis_pipeline(input_path=input_path)
            
            # Run output pipeline
            logger.info("Running output pipeline...")
            run_output_pipeline()
            
            # Run report pipeline
            logger.info("Running report pipeline...")
            run_report_pipeline()
            
            # Run validation pipeline
            logger.info("Running validation pipeline...")
            run_validation_pipeline()
            
            logger.info("Full pipeline completed successfully.")
        
        elif args.mode == 'run-analysis':
            logger.info("Mode: run-analysis")
            input_path = args.data or get_path('processed', 'morphological_metrics.csv')
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Input data not found: {input_path}")
            
            run_analysis_pipeline(input_path=input_path)
            logger.info("Analysis pipeline completed.")
        
        elif args.mode == 'run-output':
            logger.info("Mode: run-output")
            run_output_pipeline()
            logger.info("Output pipeline completed.")
        
        elif args.mode == 'run-report':
            logger.info("Mode: run-report")
            run_report_pipeline()
            logger.info("Report pipeline completed.")
        
        elif args.mode == 'run-validation':
            logger.info("Mode: run-validation")
            run_validation_pipeline()
            logger.info("Validation pipeline completed.")
        
        else:
            parser.print_help()
            
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
