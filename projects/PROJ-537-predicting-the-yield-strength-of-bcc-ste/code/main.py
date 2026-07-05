"""
Main orchestration skeleton for the llmXive BCC Steel Yield Strength pipeline.

This module provides the entry point for running the research pipeline stages:
1. Data Ingestion (US1)
2. Model Training & Evaluation (US2)
3. Interpretability & Stability Analysis (US3)

It includes error handling for specific pipeline failures, notably
ERR_INSUFFICIENT_DATA when the merged dataset has fewer than 20 valid rows.
"""

import sys
import argparse
import logging
from pathlib import Path

# Import local utilities and config
from config import CONFIG, ERR_INSUFFICIENT_DATA
from utils.logging import get_logger, log_provenance_event

# Setup logger
logger = get_logger(__name__)

def validate_dataset_min_rows(min_rows: int = 20) -> bool:
    """
    Validates that the intermediate merged dataset meets the minimum row requirement.
    
    Args:
        min_rows: Minimum required number of rows (default 20)
        
    Returns:
        True if dataset meets requirements, False otherwise
        
    Raises:
        SystemExit with ERR_INSUFFICIENT_DATA code if validation fails
    """
    import pandas as pd
    from config import CONFIG
    
    merged_path = Path(CONFIG.INTERMEDIATE_DATA_DIR) / "merged.csv"
    
    if not merged_path.exists():
        logger.error(f"Merged dataset not found at {merged_path}")
        log_provenance_event("validation_failed", "dataset_not_found", str(merged_path))
        print(f"ERROR: {ERR_INSUFFICIENT_DATA} - Merged dataset not found", file=sys.stderr)
        sys.exit(1)
    
    try:
        df = pd.read_csv(merged_path)
        row_count = len(df)
        
        logger.info(f"Merged dataset loaded: {row_count} rows")
        log_provenance_event("dataset_validated", "row_count", row_count)
        
        if row_count < min_rows:
            error_msg = f"{ERR_INSUFFICIENT_DATA}: Dataset has {row_count} rows, requires {min_rows}"
            logger.error(error_msg)
            log_provenance_event("validation_failed", ERR_INSUFFICIENT_DATA, f"rows={row_count}")
            print(f"ERROR: {error_msg}", file=sys.stderr)
            sys.exit(1)
        
        # Verify critical columns exist and are non-null
        required_cols = ["yield_strength_MPa", "shear_modulus_GPa"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            error_msg = f"Missing required columns: {missing_cols}"
            logger.error(error_msg)
            print(f"ERROR: {error_msg}", file=sys.stderr)
            sys.exit(1)
        
        null_counts = df[required_cols].isnull().sum()
        if null_counts.any():
            error_msg = f"Null values found in required columns: {null_counts[null_counts > 0].to_dict()}"
            logger.warning(error_msg)
            # Log warning but proceed (data cleaning should have handled this)
        
        logger.info(f"Dataset validation passed: {row_count} rows >= {min_rows}")
        return True
        
    except Exception as e:
        logger.error(f"Error validating dataset: {e}")
        print(f"ERROR: Failed to validate dataset: {e}", file=sys.stderr)
        sys.exit(1)

def run_ingestion_pipeline():
    """Execute the data ingestion pipeline (US1)."""
    logger.info("Starting data ingestion pipeline (US1)...")
    
    try:
        # Import and run ingestion modules
        from ingestion.fetch_experimental import fetch_experimental_data
        from ingestion.fetch_dft import fetch_dft_data
        from ingestion.merge_and_filter import merge_and_filter_data
        
        # Step 1: Fetch experimental data
        logger.info("Fetching experimental data...")
        fetch_experimental_data()
        
        # Step 2: Fetch DFT data
        logger.info("Fetching DFT data from Materials Project...")
        fetch_dft_data()
        
        # Step 3: Merge and filter
        logger.info("Merging and filtering datasets...")
        merge_and_filter_data()
        
        logger.info("Data ingestion pipeline completed successfully.")
        log_provenance_event("pipeline_stage", "ingestion", "completed")
        
    except ImportError as e:
        logger.error(f"Ingestion module import error: {e}")
        print(f"ERROR: Ingestion modules not found. Run T013-T017 first.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}")
        print(f"ERROR: Ingestion pipeline failed: {e}", file=sys.stderr)
        sys.exit(1)

def run_modeling_pipeline():
    """Execute the modeling pipeline (US2)."""
    logger.info("Starting modeling pipeline (US2)...")
    
    try:
        from modeling.features import prepare_features
        from modeling.train import train_models
        from modeling.evaluate import evaluate_models
        
        # Feature engineering
        logger.info("Preparing features...")
        prepare_features()
        
        # Model training
        logger.info("Training models...")
        train_models()
        
        # Model evaluation
        logger.info("Evaluating models...")
        evaluate_models()
        
        logger.info("Modeling pipeline completed successfully.")
        log_provenance_event("pipeline_stage", "modeling", "completed")
        
    except ImportError as e:
        logger.error(f"Modeling module import error: {e}")
        print(f"ERROR: Modeling modules not found. Run T024-T032 first.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Modeling pipeline failed: {e}")
        print(f"ERROR: Modeling pipeline failed: {e}", file=sys.stderr)
        sys.exit(1)

def run_interpretability_pipeline():
    """Execute the interpretability pipeline (US3)."""
    logger.info("Starting interpretability pipeline (US3)...")
    
    try:
        from interpretability.shap_analysis import run_shap_analysis
        from interpretability.bootstrap_stability import run_stability_analysis
        
        # SHAP analysis
        logger.info("Running SHAP analysis...")
        run_shap_analysis()
        
        # Bootstrap stability
        logger.info("Running bootstrap stability analysis...")
        run_stability_analysis()
        
        logger.info("Interpretability pipeline completed successfully.")
        log_provenance_event("pipeline_stage", "interpretability", "completed")
        
    except ImportError as e:
        logger.error(f"Interpretability module import error: {e}")
        print(f"ERROR: Interpretability modules not found. Run T035-T041 first.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Interpretability pipeline failed: {e}")
        print(f"ERROR: Interpretability pipeline failed: {e}", file=sys.stderr)
        sys.exit(1)

def run_full_pipeline():
    """Run the complete pipeline: Ingestion -> Modeling -> Interpretability."""
    logger.info("=== Starting Full Research Pipeline ===")
    
    # Validate dataset first
    validate_dataset_min_rows()
    
    run_ingestion_pipeline()
    run_modeling_pipeline()
    run_interpretability_pipeline()
    
    logger.info("=== Full Research Pipeline Completed Successfully ===")
    log_provenance_event("pipeline_complete", "status", "success")

def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="BCC Steel Yield Strength Prediction Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --stage ingestion
  python main.py --stage modeling
  python main.py --stage interpretability
  python main.py --full
  python main.py --validate-only
        """
    )
    
    parser.add_argument(
        "--stage",
        choices=["ingestion", "modeling", "interpretability"],
        help="Run a specific pipeline stage"
    )
    
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run the complete pipeline (all stages)"
    )
    
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate the dataset meets minimum requirements"
    )
    
    args = parser.parse_args()
    
    # Default to full pipeline if no arguments
    if not args.stage and not args.full and not args.validate_only:
        args.full = True
    
    try:
        if args.validate_only:
            validate_dataset_min_rows()
        elif args.stage:
            if args.stage == "ingestion":
                run_ingestion_pipeline()
            elif args.stage == "modeling":
                run_modeling_pipeline()
            elif args.stage == "interpretability":
                run_interpretability_pipeline()
        elif args.full:
            run_full_pipeline()
            
    except SystemExit as e:
        # Re-raise SystemExit from validation errors
        if e.code == 1:
            raise
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Pipeline execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()