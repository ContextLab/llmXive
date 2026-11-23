import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Tuple, Optional, List, Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_predict, StratifiedKFold
from sklearn.metrics import roc_auc_score, confusion_matrix
from sklearn.exceptions import ConvergenceWarning

import src.utils.config as config
from src.utils.logging import get_logger, log_error

# Suppress convergence warnings for cleaner logs if they occur during CV
import warnings
warnings.filterwarnings("ignore", category=ConvergenceWarning)

logger = get_logger(__name__)

def load_climate_features(data_dir: Path, species: str) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load climate features and labels for a specific species from processed data.
    
    Args:
        data_dir: Path to the data directory containing processed species data.
        species: The species name (or ID) to load.
        
    Returns:
      - X: DataFrame of climate features.
      - y: Series of binary labels (1=presence, 0=absence).
        
    Raises:
        FileNotFoundError: If the data file for the species does not exist.
        ValueError: If the file is empty or missing required columns.
    """
    file_path = data_dir / f"{species}_climate_features.csv"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Climate feature file not found for species '{species}': {file_path}")
    
    logger.info(f"Loading climate features for {species} from {file_path}")
    df = pd.read_csv(file_path)
    
    if df.empty:
        raise ValueError(f"Climate feature file for {species} is empty.")
    
    if 'presence' not in df.columns:
        raise ValueError(f"Missing 'presence' column in {file_path}")
    
    # Assume feature columns are all except 'presence' and 'species' if present
    feature_cols = [c for c in df.columns if c not in ['presence', 'species']]
    if not feature_cols:
        raise ValueError(f"No feature columns found in {file_path}")
        
    X = df[feature_cols]
    y = df['presence']
    
    # Handle any remaining NaNs in features by dropping rows (simplest robust approach)
    initial_count = len(X)
    X = X.dropna()
    y = y.loc[X.index]
    dropped = initial_count - len(X)
    if dropped > 0:
        logger.warning(f"Dropped {dropped} rows with NaN features for {species}.")
        
    if len(X) == 0:
        raise ValueError(f"No valid records remaining for {species} after cleaning.")
        
    return X, y

def train_random_forest_cv(
    X: pd.DataFrame,
    y: pd.Series,
    max_depth: int = config.MAX_DEPTH,
    n_estimators: int = config.N_ESTIMATORS,
    species: str = "unknown",
    retry_on_failure: bool = True
) -> Dict[str, Any]:
    """
    Train a Random Forest classifier with cross-validation.
    
    Implements error handling for "Model training failure" by retrying with 
    reduced max_depth if the initial training fails.
    
    Args:
        X: Feature matrix.
        y: Target vector.
        max_depth: Maximum depth of the tree (default from config).
        n_estimators: Number of trees.
        species: Species name for logging.
        retry_on_failure: If True, retry with reduced max_depth on failure.
        
    Returns:
        Dictionary containing model, metrics, and training metadata.
        
    Raises:
        RuntimeError: If training fails even after retry with reduced max_depth.
    """
    logger.info(f"Starting RF training for {species} with max_depth={max_depth}, n_estimators={n_estimators}")
    
    attempts = []
    current_depth = max_depth
    
    # Strategy: Try original depth, then half depth if it fails
    depths_to_try = [current_depth]
    if retry_on_failure:
        reduced_depth = max(1, current_depth // 2)
        if reduced_depth < current_depth:
            depths_to_try.append(reduced_depth)
    
    for attempt_idx, depth in enumerate(depths_to_try):
        try:
            logger.info(f"Training attempt {attempt_idx + 1}/{len(depths_to_try)} for {species} with max_depth={depth}")
            
            rf = RandomForestClassifier(
                n_estimators=n_estimators,
                max_depth=depth,
                random_state=config.RANDOM_SEED,
                n_jobs=-1,
                class_weight='balanced' # Handle class imbalance common in SDMs
            )
            
            # Use StratifiedKFold for CV
            n_splits = min(5, len(np.unique(y)))
            if n_splits < 2:
                raise ValueError("Not enough unique classes for stratified CV.")
                
            cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=config.RANDOM_SEED)
            
            # Fit and get predictions
            rf.fit(X, y)
            y_pred_proba = cross_val_predict(rf, X, y, cv=cv, method='predict_proba')[:, 1]
            y_pred = cross_val_predict(rf, X, y, cv=cv, method='predict')
            
            # Calculate metrics
            auc = roc_auc_score(y, y_pred_proba)
            # TSS = Sensitivity + Specificity - 1
            tn, fp, fn, tp = confusion_matrix(y, y_pred).ravel()
            sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
            specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
            tss = sensitivity + specificity - 1
            
            result = {
                "model": rf,
                "species": species,
                "metrics": {
                    "auc": auc,
                    "tss": tss,
                    "sensitivity": sensitivity,
                    "specificity": specificity,
                    "n_estimators": n_estimators,
                    "max_depth": depth
                },
                "success": True,
                "attempt": attempt_idx + 1,
                "depth_used": depth
            }
            
            if attempt_idx > 0:
                logger.warning(f"Training for {species} succeeded on retry with reduced max_depth={depth}.")
            else:
                logger.info(f"Training for {species} succeeded on first attempt.")
                
            return result
            
        except Exception as e:
            logger.error(f"Training attempt {attempt_idx + 1} failed for {species}: {str(e)}")
            attempts.append({"depth": depth, "error": str(e)})
            continue
    
    # If we reach here, all attempts failed
    error_details = "; ".join([f"depth={d}, err={e}" for d, e in [(a['depth'], a['error']) for a in attempts]])
    msg = f"Model training failed for {species} after all retries. Errors: {error_details}"
    logger.error(msg)
    log_error(msg)
    raise RuntimeError(msg)

def save_results(results: Dict[str, Any], output_path: Path):
    """
    Save training results to a JSON file and the model to a pickle file.
    
    Args:
        results: Dictionary containing model and metrics.
        output_path: Path to save the JSON results.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare serializable metrics
    serializable_results = {
        "species": results["species"],
        "metrics": results["metrics"],
        "success": results["success"],
        "attempt": results.get("attempt", 1),
        "depth_used": results.get("depth_used", config.MAX_DEPTH),
        "timestamp": str(pd.Timestamp.now())
    }
    
    json_path = output_path / f"{results['species']}_results.json"
    with open(json_path, 'w') as f:
        json.dump(serializable_results, f, indent=2)
        
    model_path = output_path / f"{results['species']}_model.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(results["model"], f)
        
    logger.info(f"Results saved to {json_path} and model to {model_path}")

def run_training_pipeline(species: str, data_dir: Path, results_dir: Path) -> Dict[str, Any]:
    """
    Orchestrate the full training pipeline for a single species.
    
    Handles "No occurrence records" by raising a clear error before training.
    Handles "Model training failure" via retry logic in train_random_forest_cv.
    
    Args:
        species: Species name.
        data_dir: Path to data directory.
        results_dir: Path to results directory.
        
    Returns:
        Dictionary with results or error status.
    """
    logger.info(f"--- Processing species: {species} ---")
    
    try:
        # 1. Load Data (Handles "No occurrence records" via FileNotFoundError/ValueError)
        X, y = load_climate_features(data_dir, species)
        
        if len(y) == 0:
            raise ValueError(f"No occurrence records found for species '{species}' after loading.")
        
        if len(y) < 10: # Minimum sample size heuristic
            logger.warning(f"Very few records ({len(y)}) for {species}. Training may be unstable.")
        
        # 2. Train Model (Handles "Model training failure" via retry)
        results = train_random_forest_cv(X, y, species=species, retry_on_failure=True)
        
        # 3. Save Results
        save_results(results, results_dir)
        
        logger.info(f"Successfully completed pipeline for {species}")
        return results
        
    except FileNotFoundError as e:
        error_msg = f"No occurrence records: {str(e)}"
        logger.error(error_msg)
        log_error(error_msg)
        return {"species": species, "success": False, "error": error_msg}
    except ValueError as e:
        error_msg = f"No occurrence records: {str(e)}"
        logger.error(error_msg)
        log_error(error_msg)
        return {"species": species, "success": False, "error": error_msg}
    except RuntimeError as e:
        error_msg = f"Model training failure: {str(e)}"
        logger.error(error_msg)
        log_error(error_msg)
        return {"species": species, "success": False, "error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error for {species}: {str(e)}"
        logger.error(error_msg)
        log_error(error_msg)
        return {"species": species, "success": False, "error": error_msg}

def main():
    """
    Entry point for running the training pipeline for a specific species.
    Usage: python -m src.modeling.train_rf --species Helianthus_annuus
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Train Climate-only SDM")
    parser.add_argument("--species", type=str, required=True, help="Species name")
    parser.add_argument("--data-dir", type=str, default="data/processed", help="Path to data directory")
    parser.add_argument("--results-dir", type=str, default="results", help="Path to results directory")
    
    args = parser.parse_args()
    
    data_dir = Path(args.data_dir)
    results_dir = Path(args.results_dir)
    
    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        sys.exit(1)
        
    results = run_training_pipeline(args.species, data_dir, results_dir)
    
    if not results.get("success", False):
        logger.error(f"Pipeline failed for {args.species}: {results.get('error')}")
        sys.exit(1)
    else:
        logger.info(f"Pipeline completed successfully for {args.species}. AUC: {results['metrics']['auc']:.4f}, TSS: {results['metrics']['tss']:.4f}")
        sys.exit(0)

if __name__ == "__main__":
    main()
