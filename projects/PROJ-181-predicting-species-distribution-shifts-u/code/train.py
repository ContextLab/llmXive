import os
import sys
import logging
import pickle
import json
from datetime import datetime
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, confusion_matrix
from sklearn.model_selection import cross_val_score
import config
from logging_config import get_train_logger
from utils.spatial_blocks import generate_spatial_folds
from utils.data_utils import validate_coordinates

# --- Constants ---
PROJECT_ROOT = config.PROJECT_ROOT
DATA_DIR = config.DATA_DIR
PROCESSED_DIR = DATA_DIR / "processed"
ARTIFACTS_DIR = config.ARTIFACTS_DIR
METRICS_DIR = config.METRICS_DIR
RND_SEED = config.RND_SEED
N_JOBS = config.N_JOBS

# Ensure directories exist
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
METRICS_DIR.mkdir(parents=True, exist_ok=True)

def load_clean_data(species: str, data_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the cleaned occurrence data for a specific species.
    Expects the file at data/processed/occurrence_clean.csv (or specified path).
    """
    if data_path is None:
        data_path = PROCESSED_DIR / "occurrence_clean.csv"
    
    if not data_path.exists():
        raise FileNotFoundError(f"Clean data file not found at {data_path}. "
                                "Ensure T017 has run successfully.")
    
    df = pd.read_csv(data_path)
    
    # Filter for the specific species
    df = df[df['species'] == species].copy()
    
    if df.empty:
        raise ValueError(f"No records found for species: {species}")
    
    return df

def get_climate_features(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract climate features (bio1-bio19) and binary labels from the dataframe.
    Returns X (features) and y (labels).
    For Presence-Background (PB) modeling, we create pseudo-absences.
    However, this specific function prepares the data for the Logistic Regression
    which expects binary targets. In the context of the pipeline, we assume
    the 'presence' column exists or we generate background points.
    
    If the dataset is purely presence-only (no 0s), we generate random background points
    to create a binary classification problem (1=Presence, 0=Background).
    """
    climate_cols = [f"bio{i}" for i in range(1, 20)]
    
    # Check if we have existing labels (presence/absence)
    if 'presence' in df.columns:
        X = df[climate_cols].values
        y = df['presence'].values
    else:
        # Presence-Background approach: Generate pseudo-absences
        # We assume the input df contains only presence points for the species.
        # We need to sample background points from the same geographic extent.
        
        # 1. Get climate stats from the presence points to define a bounding box or use global?
        # Standard MaxEnt-style PB uses the study area extent. Since we don't have a mask,
        # we will sample from the same distribution of climate variables as the background
        # available in the dataset (if we had it) or simply generate random points within
        # the range of the presence data (conservative) or global bounds (aggressive).
        # Given the pipeline constraints, we will generate 10x as many background points
        # as presence points, sampled uniformly within the min/max of the climate variables
        # observed in the presence data (or a slightly expanded range).
        
        presence_X = df[climate_cols].values
        n_presence = presence_X.shape[0]
        n_background = n_presence * 10 # Typical PB ratio
        
        # Create background data
        bg_data = {}
        for col in climate_cols:
            min_val = df[col].min()
            max_val = df[col].max()
            # Add a small buffer to ensure coverage
            range_val = max_val - min_val
            bg_data[col] = np.random.uniform(min_val - 0.05*range_val, 
                                             max_val + 0.05*range_val, 
                                             n_background)
        
        bg_df = pd.DataFrame(bg_data)
        
        # Combine
        X_pres = presence_X
        y_pres = np.ones(n_presence, dtype=int)
        
        X_bg = bg_df[climate_cols].values
        y_bg = np.zeros(n_background, dtype=int)
        
        X = np.vstack([X_pres, X_bg])
        y = np.concatenate([y_pres, y_bg])
        
        logging.info(f"Generated {n_background} pseudo-absences for PB model.")

    # Handle any remaining NaNs
    if np.any(np.isnan(X)):
        # Impute with mean of the column
        col_means = np.nanmean(X, axis=0)
        X = np.where(np.isnan(X), col_means, X)
    
    return X, y

def train_logistic_regression(X: np.ndarray, y: np.ndarray, 
                              species: str, 
                              C: float = 1.0, 
                              solver: str = 'lbfgs',
                              max_iter: int = 1000) -> LogisticRegression:
    """
    Train a Regularized Logistic Regression (Presence-Background) model.
    Uses L2 regularization (default in sklearn LogisticRegression).
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        species: Species name for logging
        C: Inverse of regularization strength (L2). Smaller C = stronger regularization.
        solver: Solver algorithm. 'lbfgs' is robust for L2.
        max_iter: Maximum iterations.
    
    Returns:
        Trained LogisticRegression model.
    """
    logger = get_train_logger()
    logger.info(f"Training Logistic Regression (PB) for {species} with C={C}")
    
    model = LogisticRegression(
        C=C, 
        penalty='l2', 
        solver=solver, 
        max_iter=max_iter,
        n_jobs=N_JOBS,
        random_state=RND_SEED,
        class_weight='balanced' # Important for PB to handle imbalance
    )
    
    model.fit(X, y)
    
    # Calculate training metrics (AUC/TSS) on the training set (with caution)
    try:
        y_pred_proba = model.predict_proba(X)[:, 1]
        # Avoid perfect separation issues in AUC calculation
        if len(np.unique(y)) > 1:
            auc = roc_auc_score(y, y_pred_proba)
        else:
            auc = 0.5
        
        # Calculate TSS
        y_pred = model.predict(X)
        tn, fp, fn, tp = confusion_matrix(y, y_pred).ravel()
        sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
        tss = sensitivity + specificity - 1
        
        logger.info(f"Training AUC: {auc:.4f}, TSS: {tss:.4f}")
        
        return model, {'auc': auc, 'tss': tss, 'threshold': 0.5}
    except Exception as e:
        logger.warning(f"Could not calculate training metrics: {e}")
        return model, None

def save_model_artifact(model: Any, species: str, algo: str, output_dir: Path):
    """Save the trained model to a pickle file."""
    filename = f"model_{species}_{algo}.pkl"
    filepath = output_dir / filename
    with open(filepath, 'wb') as f:
        pickle.dump(model, f)
    logging.info(f"Model saved to {filepath}")
    return filepath

def save_metrics(metrics: Dict[str, Any], species: str, algo: str, output_dir: Path):
    """Save metrics to a JSON file."""
    if metrics is None:
        return
    filename = f"metrics_{species}_{algo}.json"
    filepath = output_dir / filename
    metrics['species'] = species
    metrics['algorithm'] = algo
    metrics['timestamp'] = datetime.now().isoformat()
    
    with open(filepath, 'w') as f:
        json.dump(metrics, f, indent=2)
    logging.info(f"Metrics saved to {filepath}")
    return filepath

def run_training(species: str, data_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Main execution function for training the Logistic Regression model for a species.
    """
    logger = get_train_logger()
    logger.info(f"Starting Logistic Regression training for {species}")
    
    try:
        # 1. Load Data
        df = load_clean_data(species, data_path)
        
        # 2. Prepare Features and Labels (PB approach)
        X, y = get_climate_features(df)
        
        # 3. Train Model
        # C=1.0 is standard; can be tuned later
        model, train_metrics = train_logistic_regression(X, y, species, C=1.0)
        
        # 4. Save Artifacts
        model_path = save_model_artifact(model, species, "logistic_regression", ARTIFACTS_DIR)
        metrics_path = save_metrics(train_metrics, species, "logistic_regression", ARTIFACTS_DIR)
        
        return {
            "status": "success",
            "species": species,
            "model_path": str(model_path),
            "metrics_path": str(metrics_path) if train_metrics else None,
            "metrics": train_metrics
        }
        
    except Exception as e:
        logger.error(f"Failed to train Logistic Regression for {species}: {e}", exc_info=True)
        return {
            "status": "failed",
            "species": species,
            "error": str(e)
        }

def main():
    """
    Entry point for the training script.
    Iterates over species defined in config or a provided list.
    """
    # Default species list (can be overridden by config or CLI)
    # For now, we assume config specifies the target species or we process all found in data
    # Since T023 is specific to the algorithm, we will run it for species available in the clean data.
    
    logger = get_train_logger()
    logger.info("Starting Logistic Regression Training Pipeline")
    
    # Read species from config if available, otherwise infer from data
    # Assuming config has a list of target species
    if hasattr(config, 'TARGET_SPECIES') and config.TARGET_SPECIES:
        species_list = config.TARGET_SPECIES
    else:
        # Fallback: Read unique species from the clean data file
        clean_data_path = PROCESSED_DIR / "occurrence_clean.csv"
        if clean_data_path.exists():
            df_temp = pd.read_csv(clean_data_path)
            species_list = df_temp['species'].unique().tolist()
        else:
            logger.error("No target species defined and clean data not found.")
            sys.exit(1)
    
    results = []
    for species in species_list:
        result = run_training(species)
        results.append(result)
        logger.info(f"Finished {species}: {result['status']}")
    
    # Save summary
    summary_path = METRICS_DIR / "training_summary_logistic.json"
    with open(summary_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Training summary saved to {summary_path}")
    return results

if __name__ == "__main__":
    main()