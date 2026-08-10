"""
Orchestration skeleton for the molecular toxicity prediction pipeline.

This module provides the CLI entry point and high-level orchestration logic
for the pipeline: download -> preprocess -> features -> train -> evaluate.
"""
import argparse
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path('code/results/pipeline.log'))
    ]
)
logger = logging.getLogger(__name__)


def parse_args(args: Optional[list] = None) -> argparse.Namespace:
    """Parse command-line arguments for the pipeline."""
    parser = argparse.ArgumentParser(
        description='Orchestrate the molecular toxicity prediction pipeline',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Data arguments
    parser.add_argument(
        '--data-source',
        type=str,
        default='pubchem_ames',
        help='Data source identifier (e.g., pubchem_ames, toxcast)'
    )
    parser.add_argument(
        '--data-dir',
        type=str,
        default='code/data',
        help='Directory for data storage'
    )
    parser.add_argument(
        '--results-dir',
        type=str,
        default='code/results',
        help='Directory for results and metrics'
    )
    
    # Feature extraction arguments
    parser.add_argument(
        '--use-alerts',
        action='store_true',
        default=True,
        help='Enable structural alert feature extraction'
    )
    parser.add_argument(
        '--use-descriptors',
        action='store_true',
        default=True,
        help='Enable molecular descriptor feature extraction'
    )
    parser.add_argument(
        '--alert-config',
        type=str,
        default='code/config/structural_alerts.json',
        help='Path to structural alerts configuration file'
    )
    
    # Model training arguments
    parser.add_argument(
        '--n-folds',
        type=int,
        default=5,
        help='Number of CV folds'
    )
    parser.add_argument(
        '--n-repeats',
        type=int,
        default=3,
        help='Number of CV repeats'
    )
    parser.add_argument(
        '--random-seed',
        type=int,
        default=42,
        help='Random seed for reproducibility'
    )
    
    # Evaluation arguments
    parser.add_argument(
        '--metrics',
        type=str,
        nargs='+',
        default=['roc_auc', 'f1', 'recall'],
        help='Metrics to compute (roc_auc, f1, recall)'
    )
    
    # Execution flags
    parser.add_argument(
        '--skip-download',
        action='store_true',
        help='Skip data download step'
    )
    parser.add_argument(
        '--skip-preprocess',
        action='store_true',
        help='Skip data preprocessing step'
    )
    parser.add_argument(
        '--skip-features',
        action='store_true',
        help='Skip feature extraction step'
    )
    parser.add_argument(
        '--skip-training',
        action='store_true',
        help='Skip model training step'
    )
    parser.add_argument(
        '--skip-evaluation',
        action='store_true',
        help='Skip model evaluation step'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate configuration without executing'
    )
    
    return parser.parse_args(args)


def validate_paths(args: argparse.Namespace) -> bool:
    """Validate that all required paths exist or can be created."""
    logger.info("Validating paths...")
    
    data_dir = Path(args.data_dir)
    results_dir = Path(args.results_dir)
    alert_config = Path(args.alert_config)
    
    # Create directories if they don't exist
    for directory in [data_dir, results_dir]:
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {directory}")
    
    # Check alert config if using alerts
    if args.use_alerts and not alert_config.exists():
        logger.error(f"Alert configuration not found: {alert_config}")
        return False
    
    logger.info("Path validation complete")
    return True


def run_download(args: argparse.Namespace) -> bool:
    """Execute data download step."""
    logger.info("Starting data download...")
    
    try:
        # Import here to avoid circular dependencies and lazy load
        from src.data.download import main as download_main
        
        # Prepare args for download module
        download_args = argparse.Namespace(
            data_source=args.data_source,
            data_dir=args.data_dir,
            skip_download=args.skip_download
        )
        
        success = download_main(download_args)
        if success:
            logger.info("Data download completed successfully")
        else:
            logger.error("Data download failed")
        
        return success
    except ImportError as e:
        logger.error(f"Download module not available: {e}")
        return False
    except Exception as e:
        logger.error(f"Download step failed: {e}")
        return False


def run_preprocess(args: argparse.Namespace) -> bool:
    """Execute data preprocessing step."""
    logger.info("Starting data preprocessing...")
    
    try:
        from src.data.preprocess import main as preprocess_main
        
        preprocess_args = argparse.Namespace(
            data_dir=args.data_dir,
            results_dir=args.results_dir,
            skip_preprocess=args.skip_preprocess
        )
        
        success = preprocess_main(preprocess_args)
        if success:
            logger.info("Data preprocessing completed successfully")
        else:
            logger.error("Data preprocessing failed")
        
        return success
    except ImportError as e:
        logger.error(f"Preprocess module not available: {e}")
        return False
    except Exception as e:
        logger.error(f"Preprocess step failed: {e}")
        return False


def run_feature_extraction(args: argparse.Namespace) -> bool:
    """Execute feature extraction step."""
    logger.info("Starting feature extraction...")
    
    try:
        from src.features.alerts import main as alerts_main
        from src.features.descriptors import main as descriptors_main
        
        success = True
        
        if args.use_alerts:
            logger.info("Extracting structural alert features...")
            alerts_args = argparse.Namespace(
                data_dir=args.data_dir,
                results_dir=args.results_dir,
                alert_config=args.alert_config,
                skip_features=args.skip_features
            )
            success = success and alerts_main(alerts_args)
        
        if args.use_descriptors:
            logger.info("Extracting molecular descriptor features...")
            descriptors_args = argparse.Namespace(
                data_dir=args.data_dir,
                results_dir=args.results_dir,
                skip_features=args.skip_features
            )
            success = success and descriptors_main(descriptors_args)
        
        if success:
            logger.info("Feature extraction completed successfully")
        else:
            logger.error("Feature extraction failed")
        
        return success
    except ImportError as e:
        logger.error(f"Feature extraction module not available: {e}")
        return False
    except Exception as e:
        logger.error(f"Feature extraction step failed: {e}")
        return False


def run_training(args: argparse.Namespace) -> bool:
    """Execute model training step."""
    logger.info("Starting model training...")
    
    try:
        from src.models.rule_based import main as rule_based_main
        from src.models.logistic import main as logistic_main
        
        success = True
        
        logger.info("Training rule-based model...")
        rule_args = argparse.Namespace(
            data_dir=args.data_dir,
            results_dir=args.results_dir,
            n_folds=args.n_folds,
            n_repeats=args.n_repeats,
            random_seed=args.random_seed,
            skip_training=args.skip_training
        )
        success = success and rule_based_main(rule_args)
        
        logger.info("Training logistic regression model...")
        logistic_args = argparse.Namespace(
            data_dir=args.data_dir,
            results_dir=args.results_dir,
            n_folds=args.n_folds,
            n_repeats=args.n_repeats,
            random_seed=args.random_seed,
            skip_training=args.skip_training
        )
        success = success and logistic_main(logistic_args)
        
        if success:
            logger.info("Model training completed successfully")
        else:
            logger.error("Model training failed")
        
        return success
    except ImportError as e:
        logger.error(f"Training module not available: {e}")
        return False
    except Exception as e:
        logger.error(f"Training step failed: {e}")
        return False


def run_evaluation(args: argparse.Namespace) -> bool:
    """Execute model evaluation step."""
    logger.info("Starting model evaluation...")
    
    try:
        from src.evaluation.metrics import main as metrics_main
        
        metrics_args = argparse.Namespace(
            data_dir=args.data_dir,
            results_dir=args.results_dir,
            metrics=args.metrics,
            skip_evaluation=args.skip_evaluation
        )
        
        success = metrics_main(metrics_args)
        if success:
            logger.info("Model evaluation completed successfully")
        else:
            logger.error("Model evaluation failed")
        
        return success
    except ImportError as e:
        logger.error(f"Evaluation module not available: {e}")
        return False
    except Exception as e:
        logger.error(f"Evaluation step failed: {e}")
        return False


def main(args: Optional[list] = None) -> int:
    """
    Main orchestration function for the pipeline.
    
    Executes the pipeline steps in order:
    1. Download data
    2. Preprocess data
    3. Extract features
    4. Train models
    5. Evaluate models
    
    Args:
        args: Command-line arguments (uses sys.argv if None)
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parsed_args = parse_args(args)
    
    logger.info("=" * 60)
    logger.info("Molecular Toxicity Prediction Pipeline")
    logger.info("=" * 60)
    logger.info(f"Arguments: {vars(parsed_args)}")
    
    # Dry run mode - just validate configuration
    if parsed_args.dry_run:
        logger.info("Dry run mode - validating configuration only")
        if validate_paths(parsed_args):
            logger.info("Configuration valid")
            return 0
        else:
            logger.error("Configuration invalid")
            return 1
    
    # Validate paths
    if not validate_paths(parsed_args):
        logger.error("Path validation failed")
        return 1
    
    # Execute pipeline steps
    steps = [
        ("Download", run_download),
        ("Preprocess", run_preprocess),
        ("Feature Extraction", run_feature_extraction),
        ("Training", run_training),
        ("Evaluation", run_evaluation)
    ]
    
    for step_name, step_func in steps:
        logger.info(f"Executing {step_name} step...")
        if not step_func(parsed_args):
            logger.error(f"{step_name} step failed - aborting pipeline")
            return 1
        logger.info(f"{step_name} step completed")
    
    logger.info("=" * 60)
    logger.info("Pipeline completed successfully")
    logger.info("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())