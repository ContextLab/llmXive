"""
Orchestration script for the Steel Yield Strength Prediction Pipeline.

This script provides CLI entry points for each major stage of the research pipeline:
1. Ingestion: Fetch and clean raw data.
2. Feature Engineering: Calculate ratios, interactions, and orthogonalize features.
3. Training: Train GAM, Linear, RF, and XGBoost models.
4. Evaluation: Compute SHAP values, permutation tests, and model comparison.
5. Sensitivity: Analyze threshold stability.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import PROJECT_ROOT, DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_RESULTS_DIR
from src.data.ingest import run_ingestion
from src.data.features import engineer_features
from src.models.train import run_training_pipeline
from src.models.evaluate import run_evaluation_pipeline
from src.models.sensitivity import run_sensitivity_pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(PROJECT_ROOT, 'logs', 'pipeline.log')),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure all required directories exist."""
    for dir_path in [DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_RESULTS_DIR]:
        os.makedirs(dir_path, exist_ok=True)
        logger.info(f"Verified directory: {dir_path}")

def run_stage_ingest(args):
    """Run the data ingestion stage."""
    logger.info("Starting Data Ingestion Stage...")
    ensure_directories()
    
    # Run ingestion
    try:
        df = run_ingestion(
            sources=args.sources.split(',') if args.sources else None,
            output_path=args.output if args.output else None
        )
        logger.info(f"Ingestion complete. Rows: {len(df)}")
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)

def run_stage_features(args):
    """Run the feature engineering stage."""
    logger.info("Starting Feature Engineering Stage...")
    ensure_directories()
    
    input_path = args.input if args.input else os.path.join(DATA_RAW_DIR, 'cleaned_data.csv')
    output_path = args.output if args.output else os.path.join(DATA_PROCESSED_DIR, 'engineered_features.csv')
    
    try:
        df = engineer_features(
            input_path=input_path,
            output_path=output_path
        )
        logger.info(f"Feature engineering complete. Output: {output_path}")
    except Exception as e:
        logger.error(f"Feature engineering failed: {e}")
        sys.exit(1)

def run_stage_train(args):
    """Run the model training stage."""
    logger.info("Starting Model Training Stage...")
    ensure_directories()
    
    input_path = args.input if args.input else os.path.join(DATA_PROCESSED_DIR, 'engineered_features.csv')
    
    try:
        results = run_training_pipeline(
            input_path=input_path,
            cv_folds=args.cv_folds,
            use_repeated=args.use_repeated
        )
        logger.info(f"Training complete. Models trained: {list(results.keys())}")
    except Exception as e:
        logger.error(f"Training failed: {e}")
        sys.exit(1)

def run_stage_evaluate(args):
    """Run the model evaluation stage."""
    logger.info("Starting Model Evaluation Stage...")
    ensure_directories()
    
    input_path = args.input if args.input else os.path.join(DATA_PROCESSED_DIR, 'engineered_features.csv')
    model_results_path = args.model_results if args.model_results else os.path.join(DATA_RESULTS_DIR, 'model_results.json')
    
    try:
        results = run_evaluation_pipeline(
            input_path=input_path,
            model_results_path=model_results_path
        )
        logger.info(f"Evaluation complete. Metrics saved to {model_results_path}")
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        sys.exit(1)

def run_stage_sensitivity(args):
    """Run the sensitivity analysis stage."""
    logger.info("Starting Sensitivity Analysis Stage...")
    ensure_directories()
    
    input_path = args.input if args.input else os.path.join(DATA_PROCESSED_DIR, 'engineered_features.csv')
    output_path = args.output if args.output else os.path.join(DATA_RESULTS_DIR, 'sensitivity_report.md')
    
    try:
        results = run_sensitivity_pipeline(
            input_path=input_path,
            thresholds=[0.01, 0.05, 0.10],
            output_path=output_path
        )
        logger.info(f"Sensitivity analysis complete. Report saved to {output_path}")
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        sys.exit(1)

def run_full_pipeline(args):
    """Run the entire pipeline sequentially."""
    logger.info("Starting Full Pipeline Execution...")
    ensure_directories()
    
    # 1. Ingest
    logger.info("--- Stage 1: Ingestion ---")
    run_stage_ingest(args)
    
    # 2. Features
    logger.info("--- Stage 2: Feature Engineering ---")
    run_stage_features(args)
    
    # 3. Train
    logger.info("--- Stage 3: Training ---")
    run_stage_train(args)
    
    # 4. Evaluate
    logger.info("--- Stage 4: Evaluation ---")
    run_stage_evaluate(args)
    
    # 5. Sensitivity
    logger.info("--- Stage 5: Sensitivity Analysis ---")
    run_stage_sensitivity(args)
    
    logger.info("Full Pipeline completed successfully.")

def main():
    parser = argparse.ArgumentParser(description="Steel Yield Strength Prediction Pipeline")
    subparsers = parser.add_subparsers(dest='command', help='Pipeline stages')

    # Ingest Command
    ingest_parser = subparsers.add_parser('ingest', help='Run data ingestion')
    ingest_parser.add_argument('--sources', type=str, help='Comma-separated list of data sources')
    ingest_parser.add_argument('--output', type=str, help='Output path for cleaned data')
    ingest_parser.set_defaults(func=run_stage_ingest)

    # Features Command
    features_parser = subparsers.add_parser('features', help='Run feature engineering')
    features_parser.add_argument('--input', type=str, help='Input path for raw data')
    features_parser.add_argument('--output', type=str, help='Output path for engineered features')
    features_parser.set_defaults(func=run_stage_features)

    # Train Command
    train_parser = subparsers.add_parser('train', help='Run model training')
    train_parser.add_argument('--input', type=str, help='Input path for processed data')
    train_parser.add_argument('--cv-folds', type=int, default=3, help='Number of CV folds')
    train_parser.add_argument('--use-repeated', action='store_true', help='Use RepeatedKFold for small datasets')
    train_parser.set_defaults(func=run_stage_train)

    # Evaluate Command
    eval_parser = subparsers.add_parser('evaluate', help='Run model evaluation')
    eval_parser.add_argument('--input', type=str, help='Input path for processed data')
    eval_parser.add_argument('--model-results', type=str, help='Path to save model results')
    eval_parser.set_defaults(func=run_stage_evaluate)

    # Sensitivity Command
    sens_parser = subparsers.add_parser('sensitivity', help='Run sensitivity analysis')
    sens_parser.add_argument('--input', type=str, help='Input path for processed data')
    sens_parser.add_argument('--output', type=str, help='Output path for sensitivity report')
    sens_parser.set_defaults(func=run_stage_sensitivity)

    # Full Pipeline Command
    full_parser = subparsers.add_parser('all', help='Run the full pipeline')
    full_parser.add_argument('--sources', type=str, help='Comma-separated list of data sources')
    full_parser.add_argument('--output', type=str, help='Output path for cleaned data (ingest)')
    full_parser.add_argument('--input', type=str, help='Input path for processed data (features/train/eval)')
    full_parser.add_argument('--cv-folds', type=int, default=3, help='Number of CV folds (train)')
    full_parser.add_argument('--use-repeated', action='store_true', help='Use RepeatedKFold (train)')
    full_parser.add_argument('--model-results', type=str, help='Path to save model results (eval)')
    full_parser.set_defaults(func=run_full_pipeline)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    args.func(args)

if __name__ == '__main__':
    main()