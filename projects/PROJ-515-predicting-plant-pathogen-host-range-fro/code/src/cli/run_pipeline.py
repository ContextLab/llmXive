import os
import sys
import argparse
import time
from pathlib import Path
from typing import Optional

# Import local modules
from src.utils.logging import setup_logging, get_logger
from src.config import load_config_from_json, validate_paths, get_default_config
from src.data.preprocess import run_preprocessing_pipeline
from src.data.feature_extractor import extract_batch_features
from src.models.train import train_model_fold, save_model
from src.models.evaluate import run_nested_cv, compare_primary_sensitivity_models
from src.models.interpret import run_shap_analysis, generate_bias_awareness_report

logger = get_logger()

def check_ci_limits(start_time: float) -> bool:
    """
    Check if the pipeline is approaching CI time limits (5 hours).
    
    Args:
        start_time: Pipeline start timestamp
        
    Returns:
        True if within limits, False otherwise
    """
    elapsed = time.time() - start_time
    limit_seconds = 5 * 3600  # 5 hours
    if elapsed > limit_seconds * 0.9:
        logger.warning("Pipeline approaching CI time limit (90%)")
        return False
    return True

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run the plant pathogen host-range prediction pipeline"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="./data",
        help="Path to the data directory containing raw and processed data"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["primary", "sensitivity"],
        default="primary",
        help="Run mode: primary (standard) or sensitivity (with imputed negatives)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    return parser.parse_args()

def main():
    """Main pipeline orchestration function."""
    args = parse_args()
    start_time = time.time()
    
    # Setup logging first to ensure all steps are logged
    log_path = Path(args.data_dir) / "reports" / "pipeline.log"
    setup_logging(log_path=log_path, level=args.log_level)
    logger.info("Pipeline execution started")
    logger.info(f"Configuration: mode={args.mode}, seed={args.seed}")
    
    # Validate paths
    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        logger.error(f"Data directory does not exist: {data_dir}")
        sys.exit(1)
    
    # Step 1: Preprocessing
    logger.info("Starting data preprocessing step")
    try:
        run_preprocessing_pipeline(
            data_dir=data_dir,
            mode=args.mode,
            seed=args.seed
        )
        logger.info("Data preprocessing completed successfully")
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        sys.exit(1)
    
    if not check_ci_limits(start_time):
        logger.warning("Stopping early due to CI time limits")
        sys.exit(0)
    
    # Step 2: Feature Extraction
    logger.info("Starting genomic feature extraction step")
    try:
        extract_batch_features(
            genomes_path=data_dir / "raw" / "genomes.fasta",
            output_path=data_dir / "processed" / "features_matrix.csv",
            seed=args.seed
        )
        logger.info("Feature extraction completed successfully")
    except Exception as e:
        logger.error(f"Feature extraction failed: {e}")
        sys.exit(1)
    
    if not check_ci_limits(start_time):
        logger.warning("Stopping early due to CI time limits")
        sys.exit(0)
    
    # Step 3: Model Training and Evaluation
    logger.info("Starting model training and evaluation step")
    try:
        if args.mode == "sensitivity":
            # Run sensitivity analysis comparison
            compare_primary_sensitivity_models(
                data_dir=data_dir,
                seed=args.seed
            )
            logger.info("Sensitivity analysis comparison completed")
        else:
            # Run nested cross-validation
            run_nested_cv(
                data_dir=data_dir,
                seed=args.seed,
                output_dir=data_dir / "models"
            )
            logger.info("Nested cross-validation completed successfully")
    except Exception as e:
        logger.error(f"Model training/evaluation failed: {e}")
        sys.exit(1)
    
    if not check_ci_limits(start_time):
        logger.warning("Stopping early due to CI time limits")
        sys.exit(0)
    
    # Step 4: Interpretation and Reporting
    logger.info("Starting model interpretation and reporting step")
    try:
        run_shap_analysis(
            data_dir=data_dir,
            output_dir=data_dir / "reports"
        )
        generate_bias_awareness_report(
            data_dir=data_dir,
            output_dir=data_dir / "reports"
        )
        logger.info("Model interpretation completed successfully")
    except Exception as e:
        logger.error(f"Model interpretation failed: {e}")
        sys.exit(1)
    
    logger.info("Pipeline execution completed successfully")
    logger.info(f"Total execution time: {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    main()
