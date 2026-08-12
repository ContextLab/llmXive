import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.model_selection import StratifiedKFold

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/model_training.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# FR-008: Runtime GPU check (Generic CUDA detection)
# This function checks for GPU acceleration without relying on torch.
# It raises SystemExit(1) if any GPU environment is detected to ensure CPU-only execution.
def check_gpu_disabled():
    """
    Checks for GPU acceleration indicators in the environment.
    Raises SystemExit(1) if GPU is detected.
    """
    # Check environment variable CUDA_VISIBLE_DEVICES
    cuda_visible = os.environ.get('CUDA_VISIBLE_DEVICES', '')
    if cuda_visible and cuda_visible.strip() != '':
        logger.error("GPU acceleration detected via CUDA_VISIBLE_DEVICES environment variable.")
        logger.error("This pipeline is configured to run on CPU only. Please unset CUDA_VISIBLE_DEVICES.")
        raise SystemExit(1)

    # Check for NVIDIA CUDA libraries in loaded modules (generic check)
    # We iterate through loaded modules to see if any CUDA-related libraries are present
    # This is a heuristic check for generic CUDA presence
    import importlib.util
    cuda_lib_names = ['libcuda.so', 'cudart', 'nvrtc']
    for mod_name in sys.modules:
        mod = sys.modules[mod_name]
        if hasattr(mod, '__file__') and mod.__file__:
            try:
                file_path = mod.__file__
                if any(lib in file_path for lib in cuda_lib_names):
                    logger.error(f"GPU acceleration detected via loaded module: {mod_name}")
                    raise SystemExit(1)
            except (AttributeError, TypeError):
                continue

    # Check for specific environment variables often set by CUDA runtimes
    # NCCL, NCCL_DEBUG, etc. can indicate GPU usage intent
    gpu_indicators = ['NCCL_DEBUG', 'CUDA_HOME', 'NVIDIA_DRIVER_CAPABILITIES']
    for var in gpu_indicators:
        if os.environ.get(var):
            logger.warning(f"Potential GPU environment variable detected: {var}. "
                           "Proceeding with caution, but if GPU usage is detected later, execution will halt.")
            # We do not exit on warning for optional vars, only hard checks above

    logger.info("GPU check passed. Running in CPU-only mode.")

def get_bemis_murcko_scaffold(smiles: str) -> Optional[str]:
    """
    Extracts the Bemis-Murcko scaffold from a SMILES string.
    Returns None if the molecule is invalid or has no scaffold.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        scaffold = MurckoScaffold.GetScaffoldForMol(mol)
        return Chem.MolToSmiles(scaffold)
    except Exception as e:
        logger.warning(f"Failed to extract scaffold from SMILES: {smiles}, Error: {e}")
        return None

def stratified_scaffold_split(
    df: pd.DataFrame,
    n_splits: int = 5,
    random_state: int = 42
) -> List[Tuple[np.ndarray, np.ndarray]]:
    """
    Performs a stratified scaffold split.
    Returns a list of (train_indices, test_indices) tuples.
    """
    # Generate scaffolds
    scaffolds = df['smiles'].apply(get_bemis_murcko_scaffold)
    # Drop rows with invalid scaffolds for splitting purposes, but keep track of indices
    valid_mask = scaffolds.notna()
    if not valid_mask.all():
        logger.warning(f"Dropping { (~valid_mask).sum()} rows with invalid scaffolds for split generation.")
    
    scaffold_series = scaffolds[valid_mask]
    
    # Use StratifiedKFold on the scaffold labels
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    
    # Get indices for the valid subset
    valid_indices = df.index[valid_mask].values
    scaffold_labels = scaffold_series.values
    
    splits = []
    for train_idx, test_idx in skf.split(valid_indices, scaffold_labels):
        # Map back to original dataframe indices
        train_indices = valid_indices[train_idx]
        test_indices = valid_indices[test_idx]
        splits.append((train_indices, test_indices))
    
    return splits

def train_and_evaluate_fold(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    model_type: str,
    model_params: Dict[str, Any]
) -> Dict[str, float]:
    """
    Trains a model and returns evaluation metrics.
    """
    if model_type == 'linear':
        model = LinearRegression(**model_params)
    elif model_type == 'rf':
        model = RandomForestRegressor(**model_params)
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    return {
        'r2': r2,
        'rmse': rmse
    }

def run_model_training(
    features_path: str,
    target_column: str = 'logP',
    model_types: List[str] = ['linear', 'rf'],
    n_splits: int = 5,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Main function to run model training and evaluation.
    """
    # FR-008: Check for GPU before starting
    check_gpu_disabled()

    logger.info(f"Loading features from {features_path}")
    df = pd.read_csv(features_path)
    
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found in dataset.")
    
    # Prepare data
    feature_cols = [col for col in df.columns if col != target_column and col != 'smiles']
    X = df[feature_cols].values
    y = df[target_column].values
    
    # Handle any NaNs in features
    if np.isnan(X).any() or np.isnan(y).any():
        logger.warning("NaN values detected in data. Dropping rows with NaNs.")
        mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
        X = X[mask]
        y = y[mask]
        df = df[mask]
    
    # Generate scaffold splits
    splits = stratified_scaffold_split(df, n_splits=n_splits, random_state=random_state)
    
    results = {}
    
    for model_type in model_types:
        logger.info(f"Training model: {model_type}")
        
        if model_type == 'linear':
            params = {'alpha': 1.0}
        elif model_type == 'rf':
            params = {'n_estimators': 100, 'max_depth': 10, 'random_state': random_state}
        else:
            continue
        
        fold_metrics = []
        
        for fold_idx, (train_idx, test_idx) in enumerate(splits):
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]
            
            metrics = train_and_evaluate_fold(X_train, y_train, X_test, y_test, model_type, params)
            metrics['fold'] = fold_idx + 1
            fold_metrics.append(metrics)
            logger.info(f"  Fold {fold_idx + 1}: R²={metrics['r2']:.4f}, RMSE={metrics['rmse']:.4f}")
        
        # Aggregate metrics
        avg_r2 = np.mean([m['r2'] for m in fold_metrics])
        std_r2 = np.std([m['r2'] for m in fold_metrics])
        avg_rmse = np.mean([m['rmse'] for m in fold_metrics])
        std_rmse = np.std([m['rmse'] for m in fold_metrics])
        
        results[model_type] = {
            'avg_r2': avg_r2,
            'std_r2': std_r2,
            'avg_rmse': avg_rmse,
            'std_rmse': std_rmse,
            'fold_results': fold_metrics
        }
    
    return results

def main():
    """
    Entry point for the model training script.
    """
    # Default paths
    features_path = 'data/processed/combined_features.csv'
    if not os.path.exists(features_path):
        # Fallback if combined features not yet generated, try loading separately
        # This is a simple fallback logic; ideally, the pipeline ensures this file exists
        logger.warning(f"Combined features file not found at {features_path}. "
                       "Attempting to load from traditional and TDA files if available.")
        # In a real pipeline, we would call 03_feature_engineering here or assume it ran.
        # For this script to be standalone, we expect the combined file to exist.
        raise FileNotFoundError(f"Required features file not found: {features_path}")
    
    try:
        results = run_model_training(features_path)
        
        # Save results
        output_path = 'reports/metrics/model_performance.json'
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Model training complete. Results saved to {output_path}")
        
        # Print summary
        for model_type, metrics in results.items():
            print(f"{model_type.upper()}: R²={metrics['avg_r2']:.4f} (+/- {metrics['std_r2']:.4f}), "
                  f"RMSE={metrics['avg_rmse']:.4f} (+/- {metrics['std_rmse']:.4f})")
            
    except SystemExit as e:
        # Re-raise SystemExit from GPU check
        raise
    except Exception as e:
        logger.error(f"Error during model training: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()