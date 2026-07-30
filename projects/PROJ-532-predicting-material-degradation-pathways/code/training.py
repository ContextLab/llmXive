"""
Training utilities for the material degradation pathway prediction project.

This module implements the training pipeline for a Random Forest multi-label
classifier. It loads pre-split training data, trains the model on CPU,
and saves the resulting model artifact and metrics.
"""

import os
import json
import logging
import pickle
from pathlib import Path
from typing import Tuple, Any, Dict

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, confusion_matrix, classification_report
from sklearn.preprocessing import MultiLabelBinarizer

# Import project utilities
from utils import setup_logging, save_json, load_json, get_env_var, ensure_dir, set_deterministic_seed
from preprocessing import perform_ood_split

# Configure logging
logger = setup_logging("training")

# Constants
RANDOM_SEED_ENV = "RANDOM_SEED"
DATA_PATH = Path("data/processed/train_set.parquet")
OUTPUT_MODEL_PATH = Path("results/artifacts/model.pkl")
OUTPUT_METRICS_PATH = Path("results/metrics/training_report.json")
OUTPUT_DIR = Path("results/artifacts")

def load_training_data(data_path: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load the pre-split training dataset.

    Parameters
    ----------
    data_path : Path
        Path to the parquet file containing the training set.

    Returns
    -------
    X : pd.DataFrame
        Feature matrix.
    y : pd.DataFrame
        Multi-label target matrix.
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Training data not found at {data_path}. "
                                "Run T019 (preprocessing) to generate this file first.")

    logger.info(f"Loading training data from {data_path}")
    df = pd.read_parquet(data_path)

    # Assume the dataframe has a 'features' column with list of features and 'labels' with list of labels
    # Or flattened columns. Based on standard preprocessing, we expect:
    # Features are numeric columns, Labels are binary columns or a list column.
    # Let's assume the preprocessing task T019 outputs a clean DataFrame where:
    # - Numeric columns (except 'id' or similar) are features
    # - Columns starting with 'label_' or similar are targets, OR a 'labels' column exists.
    # To be robust, we check for a 'labels' column containing lists of strings.
    
    if 'labels' in df.columns and isinstance(df['labels'].iloc[0], list):
        # Multi-label format: list of strings per row
        mlb = MultiLabelBinarizer()
        y = mlb.fit_transform(df['labels'])
        y_df = pd.DataFrame(y, columns=mlb.classes_, index=df.index)
        X = df.drop(columns=['labels'])
        # Ensure we drop non-feature columns if any (like 'id')
        # For now, assume all other columns are features
        X = X.select_dtypes(include=[np.number])
    else:
        # Assume standard format: numeric features and binary label columns
        # Heuristic: identify label columns (e.g., containing 'pitting', 'scc', 'uniform' or starting with 'label_')
        # If not specific, assume the last N columns are labels? 
        # Let's assume the preprocessing output has clear separation or we rely on T019 output schema.
        # Given T019 output `train_set.parquet`, let's assume standard schema:
        # Features are all numeric columns, Labels are specific known columns or a 'labels' column.
        # If 'labels' column doesn't exist, we might need to infer.
        # Let's assume for T024 that the data has been prepared with a 'labels' column as a list of strings.
        # If not, we fallback to assuming binary columns exist.
        raise ValueError("Expected 'labels' column with list of strings in the training data. "
                         "Please ensure T019 outputs the data in this format.")
    
    return X, y_df

def train_model(
    X: pd.DataFrame, 
    y: pd.DataFrame, 
    random_state: int = 42,
    n_estimators: int = 100
) -> Tuple[RandomForestClassifier, Dict[str, Any]]:
    """
    Train a Random Forest multi-label classifier.

    Parameters
    ----------
    X : pd.DataFrame
        Feature matrix.
    y : pd.DataFrame
        Multi-label target matrix.
    random_state : int, optional
        Random seed for reproducibility.
    n_estimators : int, optional
        Number of trees in the forest.

    Returns
    -------
    model : RandomForestClassifier
        Trained model.
    metrics : dict
        Training metrics (macro-F1, etc.).
    """
    logger.info(f"Training Random Forest with {n_estimators} estimators (CPU-only)")
    logger.info(f"Training set shape: X={X.shape}, y={y.shape}")

    # Train a separate Random Forest for each label (One-vs-Rest strategy)
    # sklearn's MultiOutputClassifier is the standard way to do this, 
    # but for explicit control and metrics per label, we can loop or use MultiOutputClassifier.
    # Let's use MultiOutputClassifier for cleaner API.
    from sklearn.multioutput import MultiOutputClassifier

    base_clf = RandomForestClassifier(
        n_estimators=n_estimators,
        random_state=random_state,
        n_jobs=1,  # Force CPU single-threaded or controlled parallelism as per constraint
        max_depth=None,
        min_samples_split=2,
        min_samples_leaf=1
    )

    model = MultiOutputClassifier(base_clf)
    model.fit(X, y)

    # Calculate training metrics (macro-F1)
    y_pred = model.predict(X)
    
    # Calculate macro-F1 score
    # Since it's multi-label, we calculate F1 per label and average
    f1_scores = []
    for i in range(y.shape[1]):
        f1 = f1_score(y.iloc[:, i], y_pred[:, i], average='binary', zero_division=0)
        f1_scores.append(f1)
    
    macro_f1 = np.mean(f1_scores)
    
    metrics = {
        "macro_f1_score": float(macro_f1),
        "n_estimators": n_estimators,
        "random_state": random_state,
        "training_samples": X.shape[0],
        "n_labels": y.shape[1],
        "label_f1_scores": {y.columns[i]: float(f1) for i, f1 in enumerate(f1_scores)}
    }

    logger.info(f"Training completed. Macro-F1: {macro_f1:.4f}")
    return model, metrics

def save_artifacts(
    model: Any, 
    metrics: Dict[str, Any], 
    output_model_path: Path, 
    output_metrics_path: Path
):
    """
    Save the trained model and metrics to disk.

    Parameters
    ----------
    model : Any
        Trained model object.
    metrics : dict
        Metrics dictionary.
    output_model_path : Path
        Path to save the model pickle.
    output_metrics_path : Path
        Path to save the metrics JSON.
    """
    ensure_dir(output_model_path.parent)
    ensure_dir(output_metrics_path.parent)

    # Save model
    with open(output_model_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {output_model_path}")

    # Save metrics
    save_json(metrics, output_metrics_path)
    logger.info(f"Metrics saved to {output_metrics_path}")

def run_training_pipeline():
    """
    Main entry point to run the training pipeline.
    """
    # Get random seed from environment
    seed_str = get_env_var(RANDOM_SEED_ENV, default="42")
    try:
        random_state = int(seed_str)
    except ValueError:
        logger.warning(f"Invalid RANDOM_SEED '{seed_str}', defaulting to 42")
        random_state = 42
    
    set_deterministic_seed(random_state)
    logger.info(f"Using random seed: {random_state}")

    # Load data
    X, y = load_training_data(DATA_PATH)

    # Train model
    model, metrics = train_model(X, y, random_state=random_state)

    # Save artifacts
    save_artifacts(model, metrics, OUTPUT_MODEL_PATH, OUTPUT_METRICS_PATH)

    return metrics

if __name__ == "__main__":
    run_training_pipeline()
