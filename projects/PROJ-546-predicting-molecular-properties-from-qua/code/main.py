"""
Main CLI entry point for the molecular property prediction pipeline.
Orchestrates pipeline phases: Fetch -> Optimize -> DFT -> Train -> Evaluate.

Usage:
    python code/main.py run           # Run full pipeline
    python code/main.py fetch         # Fetch and normalize data only
    python code/main.py optimize      # Run semi-empirical optimization only
    python code/main.py dft           # Run DFT subset selection and calculation
    python code/main.py train         # Train models only
    python code/main.py evaluate      # Evaluate models only
    python code/main.py --help        # Show help
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Import pipeline components
# T004c: Fetch and normalize data
from fetch_data import main as fetch_data_main
# T011: Confound analysis
from confounds import main as confounds_main
# T013c: Semi-empirical descriptor generation
from descriptor_pipeline import main as descriptor_pipeline_main
# T020a/b: DFT subset selection and calculation
from dft_calculator import main as dft_main
# T021: Model training
from train_models import main as train_models_main
# T022: Model evaluation
from evaluate_models import main as evaluate_models_main

def setup_logging():
    """Setup logging for the main pipeline."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "pipeline.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger("main_pipeline")

def run_full_pipeline(logger):
    """Execute the full pipeline end-to-end."""
    logger.info("Starting full pipeline execution")
    
    try:
        # Step 1: Fetch data (T004c)
        logger.info("Step 1: Fetching data")
        fetch_data_main()
        
        # Step 2: Confound analysis (T011)
        logger.info("Step 2: Running confound analysis")
        confounds_main()
        
        # Step 3: Generate semi-empirical descriptors (T013c)
        logger.info("Step 3: Generating semi-empirical descriptors")
        descriptor_pipeline_main()
        
        # Step 4: Select subset and run DFT calculations (T020a/b)
        logger.info("Step 4: Running DFT calculations on subset")
        dft_main()
        
        # Step 5: Train models (T021)
        logger.info("Step 5: Training models")
        train_models_main()
        
        # Step 6: Evaluate models (T022)
        logger.info("Step 6: Evaluating models")
        evaluate_models_main()
        
        logger.info("Pipeline execution complete")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise

def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Molecular Property Prediction Pipeline CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  run       Execute the full pipeline (fetch -> optimize -> dft -> train -> evaluate)
  fetch     Fetch and normalize raw data only
  optimize  Run semi-empirical geometry optimization and descriptor generation only
  dft       Run DFT subset selection and calculation only
  train     Train models only (requires prior descriptor generation)
  evaluate  Evaluate models only (requires prior model training)

Options:
  --skip-fetch  Skip data fetching step (useful for re-running downstream steps)
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Run command
    subparsers.add_parser('run', help='Execute full pipeline')
    
    # Fetch command
    subparsers.add_parser('fetch', help='Fetch and normalize data only')
    
    # Optimize command
    subparsers.add_parser('optimize', help='Run semi-empirical optimization only')
    
    # DFT command
    subparsers.add_parser('dft', help='Run DFT subset selection and calculation')
    
    # Train command
    subparsers.add_parser('train', help='Train models only')
    
    # Evaluate command
    subparsers.add_parser('evaluate', help='Evaluate models only')
    
    parser.add_argument('--skip-fetch', action='store_true', 
                      help='Skip data fetching step')
    
    args = parser.parse_args()
    
    logger = setup_logging()
    
    if args.command is None:
        parser.print_help()
        sys.exit(0)
    
    try:
        if args.command == 'run':
            run_full_pipeline(logger)
        elif args.command == 'fetch':
            logger.info("Running fetch step only")
            fetch_data_main()
        elif args.command == 'optimize':
            logger.info("Running optimization step only")
            # Ensure data is fetched if not skipped
            if not args.skip_fetch:
                fetch_data_main()
            confounds_main()
            descriptor_pipeline_main()
        elif args.command == 'dft':
            logger.info("Running DFT step only")
            dft_main()
        elif args.command == 'train':
            logger.info("Running training step only")
            train_models_main()
        elif args.command == 'evaluate':
            logger.info("Running evaluation step only")
            evaluate_models_main()
        else:
            logger.error(f"Unknown command: {args.command}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Command failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()