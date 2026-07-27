import os
import sys
import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.metrics import balanced_accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import joblib

from config import get_processed_data_path, get_results_path, ensure_data_directories
from utils.io import load_csv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def extract_alloy_system(composition: str) -> str:
    """
    Extract the primary base element from a composition string to define the alloy system.
    Example: 'Fe40Ni40B20' -> 'Fe', 'Zr50Cu40Al10' -> 'Zr'
    """
    if not isinstance(composition, str):
        return "Unknown"
    
    # Regex to find the first element symbol followed by optional numbers
    # Element symbols are 1 or 2 letters, first is uppercase, second is lowercase
    match = re.match(r'^([A-Z][a-z]?)', composition)
    if match:
        return match.group(1)
    return "Unknown"

def stratify_by_alloy_system(df: pd.DataFrame, target_col: str = 'phase') -> pd.Series:
    """
    Create a stratification key based on the alloy system (primary element) and target label.
    This ensures each fold has a representative distribution of alloy systems and phases.
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataframe.")
    
    df_copy = df.copy()
    df_copy['alloy_system'] = df_copy['composition'].apply(extract_alloy_system)
    # Create a combined key for stratification
    return df_copy['alloy_system'].astype(str) + '_' + df_copy[target_col].astype(str)

def prepare_data(df: pd.DataFrame, feature_cols: List[str], target_col: str = 'phase') -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Prepare data for training:
    1. Filter rows with valid target labels.
    2. Split into train/test sets with stratification by alloy system.
    3. Return features and targets.
    """
    # Drop rows with missing target or features
    clean_df = df.dropna(subset=[target_col] + feature_cols)
    
    if clean_df.empty:
        raise ValueError("No valid data remaining after cleaning.")

    # Identify unique target classes
    unique_classes = clean_df[target_col].unique()
    if len(unique_classes) < 2:
        raise ValueError(f"Need at least 2 classes for classification, found: {unique_classes}")

    # Stratify by alloy system and target
    try:
        stratify_key = stratify_by_alloy_system(clean_df, target_col)
        X_train, X_test, y_train, y_test = train_test_split(
            clean_df[feature_cols].values,
            clean_df[target_col].values,
            test_size=0.2,
            random_state=42,
            stratify=stratify_key
        )
    except ValueError as e:
        # Fallback if stratification fails due to small sample sizes in some groups
        logger.warning(f"Stratification failed ({e}), falling back to simple split.")
        X_train, X_test, y_train, y_test = train_test_split(
            clean_df[feature_cols].values,
            clean_df[target_col].values,
            test_size=0.2,
            random_state=42
        )

    return X_train, X_test, y_train, y_test

def train_logistic_regression(X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
    """
    Train a Logistic Regression baseline model.
    Returns a dictionary containing the model, metrics, and predictions.
    """
    logger.info("Training Logistic Regression baseline model...")
    
    # Create a pipeline with scaling
    model = Pipeline([
        ('scaler', StandardScaler()),
        ('clf', LogisticRegression(max_iter=1000, solver='lbfgs', multi_class='auto', n_jobs=-1))
    ])

    # Fit the model
    model.fit(X_train, y_train)

    # Predict
    y_pred = model.predict(X_test)

    # Calculate metrics
    metrics = {
        'balanced_accuracy': float(balanced_accuracy_score(y_test, y_pred)),
        'precision': float(precision_score(y_test, y_pred, average='weighted', zero_division=0)),
        'recall': float(recall_score(y_test, y_pred, average='weighted', zero_division=0)),
        'f1': float(f1_score(y_test, y_pred, average='weighted', zero_division=0)),
        'confusion_matrix': confusion_matrix(y_test, y_pred).tolist()
    }

    logger.info(f"Logistic Regression Metrics: {metrics}")

    return {
        'model': model,
        'metrics': metrics,
        'predictions': y_pred.tolist(),
        'test_labels': y_test.tolist()
    }

def run_training_pipeline(feature_cols: List[str], target_col: str = 'phase') -> Dict[str, Any]:
    """
    Orchestrates the full training pipeline for Logistic Regression.
    Loads data, prepares it, trains the model, and returns results.
    """
    ensure_data_directories()
    data_path = get_processed_data_path()
    results_path = get_results_path()

    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Processed dataset not found at {data_path}. Run ingestion first.")

    logger.info(f"Loading dataset from {data_path}")
    df = load_csv(data_path)

    # Ensure feature columns exist
    missing_cols = [col for col in feature_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required feature columns: {missing_cols}")

    X_train, X_test, y_train, y_test = prepare_data(df, feature_cols, target_col)
    
    results = train_logistic_regression(X_train, y_train, X_test, y_test)
    
    # Save the model
    model_path = os.path.join(results_path, 'logistic_regression_model.pkl')
    joblib.dump(results['model'], model_path)
    logger.info(f"Model saved to {model_path}")

    return results

def main():
    """
    Entry point for Logistic Regression training.
    """
    # Define features (assuming these are generated by T012)
    # If specific columns are missing, the prepare_data function will raise an error
    feature_columns = [
        'atomic_radius', 'electronegativity', 'valence_electron_concentration',
        'atomic_size_mismatch', 'mixing_enthalpy', 'atomic_size_difference',
        'valence_electron_size_mismatch', 'electron_atom_ratio',
        'miedema_heat_of_formation', 'atomic_packing_factor'
    ]

    try:
        results = run_training_pipeline(feature_columns)
        
        # Save metrics to JSON
        metrics_path = os.path.join(get_results_path(), 'lr_baseline_metrics.json')
        with open(metrics_path, 'w') as f:
            json.dump(results['metrics'], f, indent=2)
        logger.info(f"Metrics saved to {metrics_path}")
        
        return results
    except Exception as e:
        logger.error(f"Training pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()