"""
Script to evaluate models and save metrics to data/results/model_metrics.json.

This script:
1. Loads processed data from data/processed/
2. Trains models (Random Forest, Gradient Boosting)
3. Evaluates against test set and baseline
4. Saves metrics to data/results/model_metrics.json
"""
import pandas as pd
import numpy as np
import json
import logging
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.modeling import prepare_splits, train_models, evaluate_models
from code.config import initialize_config, get_data_source_url
from code import logger

def main():
    """Main execution function."""
    initialize_config()
    logger.info("Starting model evaluation and metric saving")
    
    # Define paths
    processed_data_path = project_root / "data" / "processed" / "ceramic_dataset_processed.csv"
    output_dir = project_root / "data" / "results"
    output_file = output_dir / "model_metrics.json"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load processed data
    if not processed_data_path.exists():
        logger.error(f"Processed data not found at {processed_data_path}")
        logger.error("Please run the ingestion pipeline first to generate processed data.")
        sys.exit(1)
    
    logger.info(f"Loading data from {processed_data_path}")
    df = pd.read_csv(processed_data_path)
    
    # Identify feature columns (exclude known non-feature columns)
    exclude_cols = ['composition', 'weibull_modulus', 'is_range_flag', 'range_original', 
                   'range_uncertainty', 'is_imputed', 'primary_anion_cation_group']
    
    # Ensure target exists
    if 'weibull_modulus' not in df.columns:
        logger.error("Target column 'weibull_modulus' not found in data")
        sys.exit(1)
    
    # Select feature columns
    feature_cols = [col for col in df.columns if col not in exclude_cols and df[col].dtype in ['int64', 'float64']]
    
    if len(feature_cols) < 2:
        logger.error(f"Insufficient feature columns found: {feature_cols}")
        sys.exit(1)
    
    logger.info(f"Using {len(feature_cols)} features for modeling")
    
    # Prepare splits
    X_train, X_test, y_train, y_test, split_info = prepare_splits(
        df, 
        target_col='weibull_modulus',
        stratify_col='primary_anion_cation_group'
    )
    
    logger.info(f"Split info: {split_info}")
    
    # Train models
    models_cv_results = train_models(X_train, y_train, cv_folds=5)
    
    # Evaluate models
    evaluation_results = evaluate_models(models_cv_results, X_test, y_test)
    
    # Add split information to results
    evaluation_results['split_info'] = split_info
    evaluation_results['n_train'] = len(X_train)
    evaluation_results['n_test'] = len(X_test)
    evaluation_results['n_features'] = len(feature_cols)
    evaluation_results['feature_columns'] = feature_cols
    
    # Save results to JSON
    with open(output_file, 'w') as f:
        json.dump(evaluation_results, f, indent=2)
    
    logger.info(f"Metrics saved to {output_file}")
    
    # Print summary
    print("\n" + "="*50)
    print("MODEL EVALUATION SUMMARY")
    print("="*50)
    print(f"Best Model: {evaluation_results['comparison']['best_model']}")
    print(f"Best MAE: {evaluation_results['comparison']['best_mae']:.4f}")
    print(f"Baseline MAE: {evaluation_results['comparison']['baseline_mae']:.4f}")
    print(f"Improvement: {evaluation_results['comparison']['best_improvement_pct']:.2f}%")
    print("="*50)
    
    return evaluation_results

if __name__ == "__main__":
    main()