"""
code/04_model_training.py

Implements User Story 2: Train and Compare Predictive Models.

This module loads split indices from T008b (data/processed/splits.json),
applies them to the combined feature matrix, and trains Linear Regression
(L2) and Random Forest models on Traditional, Topological, and Combined
feature sets using scaffold splits.

Dependencies:
- T008b: Requires data/processed/splits.json
- T017: Requires data/processed/combined_features.csv (or similar from feature engineering)
"""

import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.model_selection import cross_validate
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold

# Configure logging
LOG_DIR = Path("data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "model_training.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
SEED = 42
N_FOLDS = 5
RANDOM_STATE = 42
RAM_LIMIT_GB = 6.3
CPU_TIME_LIMIT_HOURS = 5.4

def check_gpu_disabled() -> bool:
    """
    Check if GPU acceleration is detected.
    Raises SystemExit(1) if GPU is detected (FR-008).
    """
    gpu_vars = ['CUDA_VISIBLE_DEVICES', 'CUDA_DEVICE_ORDER', 'GPU_DEVICE_ORDINAL']
    for var in gpu_vars:
        if os.environ.get(var):
            logger.error(f"GPU acceleration detected via environment variable {var}. "
                         "Raising SystemExit(1) as per FR-008.")
            raise SystemExit(1)
    
    # Check for common GPU libraries if available
    try:
        import torch
        if torch.cuda.is_available():
            logger.error("GPU acceleration detected via PyTorch. "
                         "Raising SystemExit(1) as per FR-008.")
            raise SystemExit(1)
    except ImportError:
        pass
        
    try:
        import tensorflow as tf
        if tf.config.list_physical_devices('GPU'):
            logger.error("GPU acceleration detected via TensorFlow. "
                         "Raising SystemExit(1) as per FR-008.")
            raise SystemExit(1)
    except ImportError:
        pass
        
    logger.info("No GPU acceleration detected. Proceeding with CPU-only execution.")
    return True

def get_bemis_murcko_scaffold(smiles: str) -> Optional[str]:
    """
    Extract Bemis-Murcko scaffold from a SMILES string.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        scaffold = MurckoScaffold.GetScaffoldForMol(mol)
        return Chem.MolToSmiles(scaffold)
    except Exception as e:
        logger.warning(f"Failed to extract scaffold from SMILES: {smiles}. Error: {e}")
        return None

def stratified_scaffold_split(
    df: pd.DataFrame, 
    scaffold_col: str, 
    n_splits: int = N_FOLDS, 
    seed: int = SEED
) -> List[Tuple[np.ndarray, np.ndarray]]:
    """
    Perform a scaffold-based split ensuring molecules with the same scaffold
    stay in the same fold.
    
    Returns:
        List of (train_indices, test_indices) tuples.
    """
    logger.info(f"Performing scaffold split with {n_splits} folds and seed {seed}.")
    
    # Group by scaffold
    scaffold_groups = df.groupby(scaffold_col).indices
    scaffold_list = list(scaffold_groups.keys())
    
    # Shuffle scaffolds
    np.random.seed(seed)
    np.random.shuffle(scaffold_list)
    
    # Assign scaffolds to folds
    n_scaffolds = len(scaffold_list)
    fold_assignments = np.array_split(np.arange(n_scaffolds), n_splits)
    
    splits = []
    for i in range(n_splits):
        test_scaffolds = [scaffold_list[idx] for idx in fold_assignments[i]]
        train_scaffolds = [s for j, s in enumerate(scaffold_list) if j not in fold_assignments[i]]
        
        test_indices = []
        train_indices = []
        
        for scaffold in test_scaffolds:
            test_indices.extend(scaffold_groups[scaffold])
            
        for scaffold in train_scaffolds:
            train_indices.extend(scaffold_groups[scaffold])
            
        splits.append((np.array(train_indices), np.array(test_indices)))
        
    logger.info(f"Generated {n_splits} scaffold splits.")
    return splits

def train_and_evaluate_fold(
    X_train: np.ndarray, 
    y_train: np.ndarray, 
    X_test: np.ndarray, 
    y_test: np.ndarray, 
    model_name: str, 
    model_params: Dict[str, Any]
) -> Dict[str, float]:
    """
    Train a model on a single fold and evaluate performance.
    
    Args:
        X_train: Training features
        y_train: Training targets
        X_test: Test features
        y_test: Test targets
        model_name: Name of the model ('LinearRegression' or 'RandomForest')
        model_params: Parameters for the model
        
    Returns:
        Dictionary with R² and RMSE scores
    """
    logger.info(f"Training {model_name} on fold...")
    
    if model_name == 'LinearRegression':
        model = LinearRegression(**model_params)
    elif model_name == 'RandomForest':
        model = RandomForestRegressor(**model_params, random_state=RANDOM_STATE)
    else:
        raise ValueError(f"Unsupported model: {model_name}")
        
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    logger.info(f"Fold complete - R²: {r2:.4f}, RMSE: {rmse:.4f}")
    
    return {
        'r2': r2,
        'rmse': rmse
    }

def run_model_training(
    feature_matrix: pd.DataFrame,
    target_column: str,
    splits: List[Tuple[np.ndarray, np.ndarray]],
    feature_sets: Dict[str, List[str]]
) -> Dict[str, Any]:
    """
    Train and evaluate models across all feature sets and folds.
    
    Args:
        feature_matrix: Combined feature DataFrame
        target_column: Name of the target column
        splits: List of (train_indices, test_indices) from scaffold_split
        feature_sets: Dictionary mapping feature set names to column lists
        
    Returns:
        Dictionary containing metrics for each feature set and model
    """
    y = feature_matrix[target_column].values
    
    results = {}
    
    # Define models
    models = {
        'LinearRegression': {
            'alpha': 1.0  # L2 regularization
        },
        'RandomForest': {
            'n_estimators': 100,
            'max_depth': 10
        }
    }
    
    for set_name, feature_cols in feature_sets.items():
        logger.info(f"Processing feature set: {set_name}")
        X = feature_matrix[feature_cols].values
        
        set_results = {
            'r2_per_fold': [],
            'rmse_per_fold': [],
            'r2_mean': 0.0,
            'rmse_mean': 0.0,
            'r2_std': 0.0,
            'rmse_std': 0.0,
            'model_metrics': {}
        }
        
        for model_name, model_params in models.items():
            fold_results = []
            
            for fold_idx, (train_idx, test_idx) in enumerate(splits):
                X_train, X_test = X[train_idx], X[test_idx]
                y_train, y_test = y[train_idx], y[test_idx]
                
                metrics = train_and_evaluate_fold(
                    X_train, y_train, X_test, y_test, 
                    model_name, model_params
                )
                fold_results.append(metrics)
                
                logger.info(f"{model_name} Fold {fold_idx + 1}/{len(splits)}: "
                            f"R²={metrics['r2']:.4f}, RMSE={metrics['rmse']:.4f}")
            
            # Aggregate metrics for this model
            r2_scores = [r['r2'] for r in fold_results]
            rmse_scores = [r['rmse'] for r in fold_results]
            
            set_results['model_metrics'][model_name] = {
                'r2_per_fold': r2_scores,
                'rmse_per_fold': rmse_scores,
                'r2_mean': float(np.mean(r2_scores)),
                'rmse_mean': float(np.mean(rmse_scores)),
                'r2_std': float(np.std(r2_scores)),
                'rmse_std': float(np.std(rmse_scores))
            }
            
            # Also track overall fold metrics (average across models)
            set_results['r2_per_fold'].append(np.mean(r2_scores))
            set_results['rmse_per_fold'].append(np.mean(rmse_scores))
        
        # Calculate overall statistics for the feature set
        set_results['r2_mean'] = float(np.mean(set_results['r2_per_fold']))
        set_results['rmse_mean'] = float(np.mean(set_results['rmse_per_fold']))
        set_results['r2_std'] = float(np.std(set_results['r2_per_fold']))
        set_results['rmse_std'] = float(np.std(set_results['rmse_per_fold']))
        
        results[set_name] = set_results
        
        logger.info(f"Feature set {set_name} complete - Mean R²: {set_results['r2_mean']:.4f}, "
                    f"Mean RMSE: {set_results['rmse_mean']:.4f}")
    
    return results

def main():
    """
    Main entry point for model training pipeline.
    """
    logger.info("Starting model training pipeline (T018).")
    
    # Check GPU status
    check_gpu_disabled()
    
    # Load split indices from T008b
    splits_path = Path("data/processed/splits.json")
    if not splits_path.exists():
        logger.error(f"Splits file not found at {splits_path}. "
                     "Ensure T008b has been completed successfully.")
        raise FileNotFoundError(f"Splits file not found: {splits_path}")
    
    with open(splits_path, 'r') as f:
        splits_data = json.load(f)
    
    logger.info(f"Loaded splits from {splits_path}")
    
    # Convert splits back to numpy arrays
    splits = []
    for fold in splits_data['splits']:
        train_idx = np.array(fold['train'])
        test_idx = np.array(fold['test'])
        splits.append((train_idx, test_idx))
    
    logger.info(f"Loaded {len(splits)} scaffold splits.")
    
    # Load combined features from T017
    features_path = Path("data/processed/combined_features.csv")
    if not features_path.exists():
        logger.error(f"Combined features file not found at {features_path}. "
                     "Ensure T017 has been completed successfully.")
        raise FileNotFoundError(f"Combined features file not found: {features_path}")
    
    feature_df = pd.read_csv(features_path)
    logger.info(f"Loaded {len(feature_df)} molecules with {len(feature_df.columns)-1} features.")
    
    # Define feature sets
    # Assuming columns are prefixed appropriately
    traditional_cols = [col for col in feature_df.columns if col.startswith('traditional_')]
    topological_cols = [col for col in feature_df.columns if col.startswith('tda_') or col.startswith('persistence_')]
    combined_cols = traditional_cols + topological_cols
    
    feature_sets = {
        'traditional': traditional_cols,
        'topological': topological_cols,
        'combined': combined_cols
    }
    
    logger.info(f"Feature sets: Traditional={len(traditional_cols)}, "
                f"Topological={len(topological_cols)}, Combined={len(combined_cols)}")
    
    # Run model training
    target_col = 'logP'  # Assuming this is the target from ESOL
    if target_col not in feature_df.columns:
        logger.error(f"Target column '{target_col}' not found in feature DataFrame.")
        raise ValueError(f"Target column '{target_col}' not found in feature DataFrame.")
    
    results = run_model_training(feature_df, target_col, splits, feature_sets)
    
    # Save results
    output_path = Path("reports/metrics/model_performance.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Model training complete. Results saved to {output_path}")
    
    # Log final summary
    for set_name, metrics in results.items():
        logger.info(f"{set_name} - Mean R²: {metrics['r2_mean']:.4f} ± {metrics['r2_std']:.4f}, "
                    f"Mean RMSE: {metrics['rmse_mean']:.4f} ± {metrics['rmse_std']:.4f}")
    
    return results

if __name__ == "__main__":
    main()