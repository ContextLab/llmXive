"""
Main script to run cross-validation on trained models.
Executes 5-fold CV and records metrics as per FR-004.
"""
import os
import sys
import logging
import json
import argparse
from typing import Dict, Any

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

from code.logging_config import setup_logging
from code.config import SEED, DATA_PATH
from code.data_loader import load_and_validate_target, apply_log_transformation
from code.scaffold_split import scaffold_split
from code.cross_validation import run_cross_validation, record_metrics_to_file, run_cv_for_multiple_models
from code.train_models import load_processed_data, prepare_features_and_target

# Setup logging
logger = setup_logging()


def main():
    """
    Main entry point for cross-validation pipeline.
    """
    parser = argparse.ArgumentParser(description="Run 5-fold cross-validation on molecular conductivity models")
    parser.add_argument("--input", type=str, default="data/processed/descriptors.csv",
                        help="Path to input descriptors CSV")
    parser.add_argument("--target", type=str, default="conductivity",
                        help="Target variable name")
    parser.add_argument("--output", type=str, default="data/processed/cv_results.json",
                        help="Path to output JSON file")
    parser.add_argument("--n-splits", type=int, default=5,
                        help="Number of CV folds")
    parser.add_argument("--seed", type=int, default=SEED,
                        help="Random seed")
    args = parser.parse_args()

    logger.info(f"Starting cross-validation pipeline with seed {args.seed}")
    logger.info(f"Input data: {args.input}")
    logger.info(f"Target variable: {args.target}")

    # Check if input file exists
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        logger.error("Please run the descriptor pipeline first to generate data/processed/descriptors.csv")
        sys.exit(1)

    # Load data
    try:
        logger.info("Loading processed data...")
        df = load_processed_data(args.input)

        # Prepare features and target
        X, y = prepare_features_and_target(df, args.target)

        logger.info(f"Loaded {len(X)} samples with {X.shape[1]} features")
        logger.info(f"Target range: [{y.min():.4f}, {y.max():.4f}]")

    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)

    # Define models
    models = {
        "random_forest": RandomForestRegressor(
            n_estimators=100,
            random_state=args.seed,
            n_jobs=-1
        ),
        "gradient_boosting": GradientBoostingRegressor(
            n_estimators=100,
            random_state=args.seed,
            max_depth=5
        )
    }

    logger.info(f"Running cross-validation for {len(models)} models")

    # Run CV for all models
    all_results = run_cv_for_multiple_models(X, y, models, n_splits=args.n_splits, seed=args.seed)

    # Save individual results
    for model_name, cv_data in all_results.items():
        output_file = args.output.replace('.json', f'_{model_name}.json')
        record_metrics_to_file(cv_data, output_file, model_name)

    # Save combined results
    combined_output = args.output
    with open(combined_output, 'w') as f:
        json.dump(all_results, f, indent=2)
    logger.info(f"Combined results saved to {combined_output}")

    # Generate comparison table
    comparison_df = compare_cv_results(all_results, output_path="data/processed/cv_comparison.csv")
    logger.info("Comparison table generated")

    # Print summary
    print("\n" + "="*60)
    print("CROSS-VALIDATION SUMMARY")
    print("="*60)
    print(comparison_df.to_string(index=False))
    print("="*60)

    logger.info("Cross-validation pipeline completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
