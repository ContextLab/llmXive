"""
Train Elastic Net models and perform cross-validation for gene expression prediction.

This module implements the training pipeline for predicting gene expression from
chromatin accessibility features.
"""
import os
import sys
import json
import logging
import argparse
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np
from sklearn.linear_model import ElasticNetCV
from sklearn.model_selection import KFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import joblib

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/training.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def load_variable_peaks(input_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load variable peaks data and separate features (X) and targets (y).
    
    Args:
        input_path: Path to the variable peaks CSV file.
        
    Returns:
        Tuple of (features_df, targets_df) where features are peak accessibility
        and targets are gene expression values.
    """
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Assume first column is gene identifier, remaining columns are peaks/features
    # and there's a separate 'expression' column or the last N columns are expression
    # Based on typical pipeline: columns are [gene_id, peak_1, peak_2, ..., peak_N, expression_cell_line_1, ...]
    # For this implementation, we assume the last column is the target expression for a specific cell line
    # or we process per cell line if multiple expression columns exist.
    
    # Let's assume the input has 'gene_id' and then peak features, and one expression column per cell line.
    # We will process one cell line at a time.
    
    # Identify gene_id column (first) and expression columns (likely containing 'expression' or cell line names)
    # For simplicity, if there's a column named 'expression', use it. Otherwise, assume last column is target.
    if 'expression' in df.columns:
        target_col = 'expression'
        feature_cols = [c for c in df.columns if c not in ['gene_id', 'expression']]
    else:
        # Fallback: assume last column is target, first is gene_id
        target_col = df.columns[-1]
        feature_cols = [c for c in df.columns if c not in ['gene_id', target_col]]
        
    features = df[feature_cols].fillna(0)
    targets = df[[target_col]].fillna(0)
    
    logger.info(f"Loaded {len(features)} samples with {len(feature_cols)} features")
    return features, targets


def train_elastic_net(X: pd.DataFrame, y: pd.DataFrame, cell_line: str, 
                      alphas: Optional[List[float]] = None) -> Tuple[Pipeline, Dict[str, Any]]:
    """
    Train an Elastic Net model with cross-validation.
    
    Args:
        X: Feature matrix (peak accessibility).
        y: Target vector (gene expression).
        cell_line: Name of the cell line for logging and model naming.
        alphas: List of alpha values to test. If None, uses sklearn defaults.
        
    Returns:
        Tuple of (trained_pipeline, training_metadata).
    """
    logger.info(f"Training Elastic Net for cell line: {cell_line}")
    
    if alphas is None:
        alphas = [0.0001, 0.001, 0.01, 0.1, 1.0]
        
    # Create pipeline with scaling and Elastic Net
    # ElasticNetCV handles internal cross-validation for alpha selection
    model = ElasticNetCV(
        alphas=alphas,
        l1_ratio=0.5,  # FR-002: Elastic Net with alpha=0.5
        cv=5,          # 5-fold cross-validation
        random_state=42,
        n_jobs=-1,
        max_iter=10000
    )
    
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('regressor', model)
    ])
    
    # Fit the pipeline
    pipeline.fit(X, y)
    
    # Extract best alpha and R2 score from the CV
    best_alpha = pipeline.named_steps['regressor'].alpha_
    # Get the best score from the CV
    best_score = pipeline.named_steps['regressor'].best_score_
    
    metadata = {
        'cell_line': cell_line,
        'best_alpha': float(best_alpha),
        'best_cv_score': float(best_score),
        'n_features': X.shape[1],
        'n_samples': X.shape[0],
        'l1_ratio': 0.5
    }
    
    logger.info(f"Training complete for {cell_line}. Best alpha: {best_alpha:.4f}, CV Score: {best_score:.4f}")
    return pipeline, metadata


def run_cross_validation(X: pd.DataFrame, y: pd.DataFrame, cell_line: str, 
                         k: int = 5) -> Dict[str, Any]:
    """
    Perform k-fold cross-validation to evaluate model performance.
    
    This function runs a manual k-fold cross-validation loop to generate
    detailed scores for each fold, in addition to the internal CV of 
    ElasticNetCV.
    
    Args:
        X: Feature matrix.
        y: Target vector.
        cell_line: Name of the cell line.
        k: Number of folds. Default is 5.
        
    Returns:
        Dictionary containing cross-validation results.
        
    Note:
        k=5 is a reasonable number for cross-validation as it provides a good
        trade-off between bias and variance in the performance estimate. 
        It ensures each fold has enough samples for reliable training while
        providing sufficient folds to assess model stability. For datasets 
        with moderate size (100-10000 samples), 5-fold CV is standard practice.
    """
    logger.info(f"Running {k}-fold cross-validation for {cell_line}")
    
    # Use the same pipeline structure as training
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('regressor', ElasticNetCV(
            alphas=[0.001, 0.01, 0.1, 1.0],
            l1_ratio=0.5,
            cv=k,
            random_state=42,
            max_iter=10000
        ))
    ])
    
    kf = KFold(n_splits=k, shuffle=True, random_state=42)
    
    fold_scores = []
    fold_metadata = []
    
    for fold_idx, (train_idx, test_idx) in enumerate(kf.split(X)):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        # Fit on training fold
        pipeline.fit(X_train, y_train)
        
        # Evaluate on test fold
        score = pipeline.score(X_test, y_test)
        fold_scores.append(score)
        
        # Extract best alpha for this fold
        best_alpha = pipeline.named_steps['regressor'].alpha_
        fold_metadata.append({
            'fold': fold_idx + 1,
            'score': float(score),
            'best_alpha': float(best_alpha)
        })
        
        logger.info(f"Fold {fold_idx + 1}/{k}: R² = {score:.4f}, Alpha = {best_alpha:.4f}")
    
    results = {
        'cell_line': cell_line,
        'k_folds': k,
        'mean_r2': float(np.mean(fold_scores)),
        'std_r2': float(np.std(fold_scores)),
        'min_r2': float(np.min(fold_scores)),
        'max_r2': float(np.max(fold_scores)),
        'fold_scores': fold_scores,
        'fold_details': fold_metadata
    }
    
    logger.info(f"Cross-validation complete for {cell_line}. Mean R²: {results['mean_r2']:.4f} (+/- {results['std_r2']:.4f})")
    return results


def train_all_cell_lines(input_path: str, output_model_dir: str, output_scores_path: str) -> Dict[str, Any]:
    """
    Train models for all cell lines found in the input data and save results.
    
    Args:
        input_path: Path to the variable peaks CSV file.
        output_model_dir: Directory to save trained models.
        output_scores_path: Path to save cross-validation scores JSON.
        
    Returns:
        Dictionary containing all training results.
    """
    # Ensure output directories exist
    os.makedirs(output_model_dir, exist_ok=True)
    os.makedirs(os.path.dirname(output_scores_path), exist_ok=True)
    
    # Load data
    X, y = load_variable_peaks(input_path)
    
    # If the input contains multiple cell lines (multiple expression columns),
    # we need to split by cell line. For this implementation, we assume the 
    # input is already filtered for one cell line or we process the single 
    # target column provided.
    # If there are multiple target columns, we would loop over them.
    
    # Check for multiple expression columns
    possible_expr_cols = [c for c in y.columns if 'expression' in c.lower() or 'cell' in c.lower()]
    
    results = {
        'training_runs': [],
        'cross_validations': []
    }
    
    # If only one target column, use it directly
    if len(y.columns) == 1:
        cell_line = y.columns[0]
        logger.info(f"Processing single cell line: {cell_line}")
        
        # Train model
        pipeline, train_meta = train_elastic_net(X, y, cell_line)
        
        # Save model
        model_path = os.path.join(output_model_dir, f"elastic_net_{cell_line}.pkl")
        joblib.dump(pipeline, model_path)
        logger.info(f"Model saved to {model_path}")
        
        # Run explicit cross-validation
        cv_results = run_cross_validation(X, y, cell_line, k=5)
        
        results['training_runs'].append({
            'cell_line': cell_line,
            'model_path': model_path,
            **train_meta
        })
        results['cross_validations'].append(cv_results)
        
    else:
        # Process each column as a separate cell line
        for col in y.columns:
            cell_line = col
            y_single = y[[col]]
            
            pipeline, train_meta = train_elastic_net(X, y_single, cell_line)
            
            model_path = os.path.join(output_model_dir, f"elastic_net_{cell_line}.pkl")
            joblib.dump(pipeline, model_path)
            logger.info(f"Model saved to {model_path}")
            
            cv_results = run_cross_validation(X, y_single, cell_line, k=5)
            
            results['training_runs'].append({
                'cell_line': cell_line,
                'model_path': model_path,
                **train_meta
            })
            results['cross_validations'].append(cv_results)
    
    # Save cross-validation scores to JSON
    with open(output_scores_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Cross-validation scores saved to {output_scores_path}")
    return results


def main():
    """Main entry point for the training script."""
    parser = argparse.ArgumentParser(description="Train Elastic Net models for gene expression prediction")
    parser.add_argument(
        '--input', 
        type=str, 
        default='data/processed/variable_peaks.csv',
        help='Input CSV file with variable peaks and expression data'
    )
    parser.add_argument(
        '--output-models', 
        type=str, 
        default='data/models',
        help='Directory to save trained models'
    )
    parser.add_argument(
        '--output-scores', 
        type=str, 
        default='data/processed/cv_scores.json',
        help='Path to save cross-validation scores JSON'
    )
    
    args = parser.parse_args()
    
    logger.info(f"Starting training pipeline with input: {args.input}")
    
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
    
    try:
        results = train_all_cell_lines(
            input_path=args.input,
            output_model_dir=args.output_models,
            output_scores_path=args.output_scores
        )
        
        logger.info("Training pipeline completed successfully")
        print(f"Training complete. Results saved to {args.output_scores}")
        
    except Exception as e:
        logger.error(f"Training pipeline failed: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
