"""
Main orchestration script for the SN1 Rate Constant Prediction Pipeline.

This script coordinates the execution of the data ingestion, cleaning,
descriptor calculation, splitting, training, evaluation, and analysis stages.

Usage:
    python code/main.py --stage <stage_name>

Available stages:
    ingest      - Fetch and map raw data from external sources
    clean       - Canonicalize SMILES and filter substrates
    descriptors - Compute Gasteiger charges and topological indices
    finalize    - Aggregate logs, validate schema, and save final dataset
    split       - Stratified split into train/val/test sets
    train       - Train MPNN model with hyperparameter search
    evaluate    - Evaluate model and compare with linear baseline
    interpret   - Generate SHAP values and perturbation study
    sensitivity - Run sensitivity and collinearity analyses
    all         - Run the full pipeline sequentially
    validate    - Validate quickstart execution
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import ensure_dirs

# Import stage handlers
# Data Pipeline
from data.ingest import main as ingest_main
from data.clean import main as clean_main
from data.descriptors import main as descriptors_main
from data.finalize_dataset import main as finalize_main
from data.split import main as split_main

# Models
from models.train import main as train_main
from models.evaluate import main as evaluate_main
from models.save_artifacts import main as save_artifacts_main

# Analysis
from analysis.interpret import main as interpret_main
from analysis.sensitivity import main as sensitivity_main
from analysis.collinearity import main as collinearity_main
from analysis.consistency import main as consistency_main

# Validation
from validation.validate_quickstart import main as validate_main

# Setup logging
def setup_logging():
    """Configure logging for the pipeline."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(PROJECT_ROOT / 'logs' / 'pipeline.log')
        ]
    )
    return logging.getLogger('main')

def run_stage(stage_name, logger):
    """
    Execute a specific stage of the pipeline.
    
    Args:
        stage_name (str): Name of the stage to execute.
        logger (logging.Logger): Logger instance.
    """
    logger.info(f"Starting stage: {stage_name}")
    
    try:
        if stage_name == 'ingest':
            ingest_main()
        elif stage_name == 'clean':
            clean_main()
        elif stage_name == 'descriptors':
            descriptors_main()
        elif stage_name == 'finalize':
            finalize_main()
        elif stage_name == 'split':
            split_main()
        elif stage_name == 'train':
            train_main()
        elif stage_name == 'evaluate':
            evaluate_main()
        elif stage_name == 'save_artifacts':
            save_artifacts_main()
        elif stage_name == 'interpret':
            interpret_main()
        elif stage_name == 'sensitivity':
            sensitivity_main()
        elif stage_name == 'collinearity':
            collinearity_main()
        elif stage_name == 'consistency':
            consistency_main()
        elif stage_name == 'validate':
            validate_main()
        else:
            raise ValueError(f"Unknown stage: {stage_name}")
        
        logger.info(f"Stage {stage_name} completed successfully.")
        return True
        
    except Exception as e:
        logger.error(f"Stage {stage_name} failed with error: {str(e)}")
        raise

def run_full_pipeline(logger):
    """Execute the entire pipeline sequentially."""
    stages = [
        'ingest',
        'clean',
        'descriptors',
        'finalize',
        'split',
        'train',
        'evaluate',
        'save_artifacts',
        'interpret',
        'sensitivity',
        'collinearity',
        'consistency'
    ]
    
    for stage in stages:
        run_stage(stage, logger)
    
    logger.info("Full pipeline completed successfully.")

def main():
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(
        description="SN1 Rate Constant Prediction Pipeline Orchestration"
    )
    parser.add_argument(
        '--stage',
        type=str,
        required=True,
        choices=[
            'ingest', 'clean', 'descriptors', 'finalize', 'split',
            'train', 'evaluate', 'save_artifacts', 'interpret',
            'sensitivity', 'collinearity', 'consistency', 'all', 'validate'
        ],
        help='Stage to execute'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging()
    logger.setLevel(getattr(logging, args.log_level))
    
    # Ensure directories exist
    ensure_dirs()
    
    try:
        if args.stage == 'all':
            run_full_pipeline(logger)
        else:
            run_stage(args.stage, logger)
        
        print("Pipeline completed successfully.")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        print(f"Pipeline execution failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()