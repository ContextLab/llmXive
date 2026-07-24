import os
import sys
import csv
import logging
import argparse
from pathlib import Path
from typing import Tuple, List, Dict, Any
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold, cross_validate
from sklearn.metrics import make_scorer, mean_absolute_error
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    'smiles', 'homo_semi', 'lumo_semi', 'mayer_order_semi',
    'homo_dft', 'lumo_dft', 'mayer_order_dft',
    'experimental_barrier'
]

SEMI_FEATURES = ['homo_semi', 'lumo_semi', 'mayer_order_semi']
DFT_FEATURES = ['homo_dft', 'lumo_dft', 'mayer_order_dft']
TARGET_COLUMN = 'experimental_barrier'

def load_data(filepath: str) -> List[Dict[str, Any]]:
    """
    Load molecular descriptor data from a CSV file.
    
    Args:
        filepath: Path to the CSV file containing descriptors.
        
    Returns:
        List of dictionaries, one per molecule.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Data file not found: {filepath}")
    
    data = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Verify required columns exist
        if reader.fieldnames is None:
            raise ValueError("CSV file is empty or has no headers.")
        
        missing_cols = set(REQUIRED_COLUMNS) - set(reader.fieldnames)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        for row_num, row in enumerate(reader, start=2):
            try:
                # Parse numeric fields
                parsed_row = {
                    'smiles': row['smiles'],
                    'homo_semi': float(row['homo_semi']),
                    'lumo_semi': float(row['lumo_semi']),
                    'mayer_order_semi': float(row['mayer_order_semi']),
                    'homo_dft': float(row['homo_dft']),
                    'lumo_dft': float(row['lumo_dft']),
                    'mayer_order_dft': float(row['mayer_order_dft']),
                    'experimental_barrier': float(row['experimental_barrier'])
                }
                data.append(parsed_row)
            except ValueError as e:
                logger.warning(f"Skipping row {row_num} due to parsing error: {e}")
    
    if not data:
        raise ValueError("No valid data rows found in the file.")
        
    logger.info(f"Loaded {len(data)} molecules from {filepath}")
    return data

def prepare_features_target(
    data: List[Dict[str, Any]], 
    feature_type: str
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Prepare feature matrix and target vector from data.
    
    Args:
        data: List of molecule dictionaries.
        feature_type: Either 'semi' or 'dft' to select feature set.
        
    Returns:
        Tuple of (X, y) as numpy arrays.
        
    Raises:
        ValueError: If feature_type is invalid.
    """
    if feature_type not in ('semi', 'dft'):
        raise ValueError(f"Invalid feature_type: {feature_type}. Must be 'semi' or 'dft'.")
    
    features = SEMI_FEATURES if feature_type == 'semi' else DFT_FEATURES
    
    X = np.array([[mol[feat] for feat in features] for mol in data])
    y = np.array([mol[TARGET_COLUMN] for mol in data])
    
    return X, y

def train_and_evaluate_fold(
    X_train: np.ndarray, 
    y_train: np.ndarray, 
    X_test: np.ndarray, 
    y_test: np.ndarray
) -> Dict[str, float]:
    """
    Train a Random Forest model on a single fold and evaluate it.
    
    Args:
        X_train: Training features.
        y_train: Training targets.
        X_test: Test features.
        y_test: Test targets.
        
    Returns:
        Dictionary containing 'mae' (Mean Absolute Error).
    """
    # Create a pipeline with scaling and RF
    model = Pipeline([
        ('scaler', StandardScaler()),
        ('rf', RandomForestRegressor(
            n_estimators=100,
            max_depth=None,
            random_state=42,
            n_jobs=-1
        ))
    ])
    
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    mae = mean_absolute_error(y_test, y_pred)
    
    logger.info(f"Fold MAE: {mae:.4f} kcal/mol")
    
    return {'mae': mae}

def train_models(
    data: List[Dict[str, Any]],
    n_splits: int = 5,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Train and evaluate Random Forest models for both semi-empirical and DFT descriptors.
    
    This function performs 5-fold cross-validation for both feature sets and returns
    the performance metrics.
    
    Args:
        data: List of molecule dictionaries.
        n_splits: Number of CV folds (default 5).
        random_state: Random seed for reproducibility.
        
    Returns:
        Dictionary containing results for both models:
        {
            'semi': {'mae_mean': float, 'mae_std': float, 'fold_maes': List[float]},
            'dft': {'mae_mean': float, 'mae_std': float, 'fold_maes': List[float]}
        }
    """
    results = {}
    
    for feature_type in ['semi', 'dft']:
        logger.info(f"Training {feature_type.upper()} model with {n_splits}-fold CV...")
        
        X, y = prepare_features_target(data, feature_type)
        
        # Setup KFold
        kf = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
        
        fold_maes = []
        for fold_idx, (train_idx, test_idx) in enumerate(kf.split(X)):
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]
            
            fold_result = train_and_evaluate_fold(X_train, y_train, X_test, y_test)
            fold_maes.append(fold_result['mae'])
        
        mae_mean = float(np.mean(fold_maes))
        mae_std = float(np.std(fold_maes))
        
        results[feature_type] = {
            'mae_mean': mae_mean,
            'mae_std': mae_std,
            'fold_maes': fold_maes
        }
        
        logger.info(f"{feature_type.upper()} Model - Mean MAE: {mae_mean:.4f} ± {mae_std:.4f} kcal/mol")
    
    return results

def main():
    """
    Main entry point for training models.
    
    Usage:
        python code/train_models.py --input data/descriptors_combined.csv --output data/model_results.json
    """
    parser = argparse.ArgumentParser(
        description='Train Random Forest models on semi-empirical and DFT descriptors.'
    )
    parser.add_argument(
        '--input', '-i',
        type=str,
        default='data/descriptors_combined.csv',
        help='Path to input CSV file with descriptors (default: data/descriptors_combined.csv)'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='data/model_results.json',
        help='Path to output JSON file for results (default: data/model_results.json)'
    )
    parser.add_argument(
        '--splits', '-s',
        type=int,
        default=5,
        help='Number of CV folds (default: 5)'
    )
    
    args = parser.parse_args()
    
    try:
        # Load data
        data = load_data(args.input)
        
        # Train models
        results = train_models(data, n_splits=args.splits)
        
        # Save results to JSON
        import json
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved to {args.output}")
        
        # Print summary
        print("\n=== Model Training Summary ===")
        print(f"Semi-empirical MAE: {results['semi']['mae_mean']:.4f} ± {results['semi']['mae_std']:.4f} kcal/mol")
        print(f"DFT MAE:            {results['dft']['mae_mean']:.4f} ± {results['dft']['mae_std']:.4f} kcal/mol")
        print("==============================\n")
        
    except FileNotFoundError as e:
        logger.error(f"Input file error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during training: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()