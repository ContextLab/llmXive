import gc
import logging
import os
import resource
import sys
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

from config import get_data_processed, get_results_root, set_global_seed
from utils.logger import get_logger

logger = get_logger(__name__)

def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_maxrss / 1024.0  # Convert to MB (Linux/macOS)

def check_memory_pressure(threshold_mb: float = 6000.0) -> bool:
    """Check if current memory usage exceeds a threshold."""
    current_mb = get_memory_usage_mb()
    if current_mb > threshold_mb:
        logger.warning(f"Memory pressure detected: {current_mb:.2f} MB > {threshold_mb} MB")
        return True
    return False

def force_gc() -> None:
    """Force garbage collection to free memory."""
    gc.collect()
    logger.info("Garbage collection triggered.")

def process_in_chunks(
    df: pd.DataFrame,
    chunk_size: int = 10000,
    process_func: Optional[callable] = None
) -> pd.DataFrame:
    """Process a large DataFrame in chunks to manage memory."""
    if process_func is None:
        process_func = lambda x: x

    chunks = []
    total_rows = len(df)
    logger.info(f"Processing {total_rows} rows in chunks of {chunk_size}")

    for i in range(0, total_rows, chunk_size):
        chunk = df.iloc[i : i + chunk_size]
        processed_chunk = process_func(chunk)
        chunks.append(processed_chunk)
        if check_memory_pressure():
            force_gc()

    return pd.concat(chunks, ignore_index=True)

def load_feature_matrix(path: Optional[str] = None) -> Tuple[pd.DataFrame, np.ndarray]:
    """Load the preprocessed feature matrix and labels."""
    if path is None:
        path = str(get_data_processed() / "feature_matrix.csv")

    logger.info(f"Loading feature matrix from {path}")
    df = pd.read_csv(path)

    if 'label' not in df.columns:
        raise ValueError(f"Column 'label' not found in {path}")

    X = df.drop(columns=['label'])
    y = df['label']

    logger.info(f"Loaded matrix with shape {X.shape}, label distribution: {y.value_counts().to_dict()}")
    return X, y

def train_random_forest(
    X: np.ndarray,
    y: np.ndarray,
    random_state: int = 42,
    n_jobs: int = -1
) -> RandomForestClassifier:
    """Train a Random Forest classifier with balanced class weights."""
    logger.info("Training Random Forest classifier...")

    model = RandomForestClassifier(
        n_estimators=500,
        max_depth=None,
        min_samples_split=5,
        min_samples_leaf=2,
        class_weight='balanced',
        random_state=random_state,
        n_jobs=n_jobs,
        verbose=1
    )

    model.fit(X, y)
    logger.info("Random Forest training completed.")
    return model

def run_training_pipeline(
    X: np.ndarray,
    y: np.ndarray,
    cv_folds: int = 5,
    random_state: int = 42
) -> Tuple[RandomForestClassifier, Dict[str, Any]]:
    """Run the full training pipeline: CV, model training, and metrics."""
    set_global_seed(random_state)
    logger.info(f"Starting training pipeline with {cv_folds}-fold CV.")

    # Stratified K-Fold Cross Validation
    skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
    cv_scores = cross_val_score(
        RandomForestClassifier(
            n_estimators=500,
            max_depth=None,
            class_weight='balanced',
            random_state=random_state,
            n_jobs=-1
        ),
        X,
        y,
        cv=skf,
        scoring='roc_auc',
        n_jobs=-1
    )

    mean_auc = np.mean(cv_scores)
    std_auc = np.std(cv_scores)
    logger.info(f"Cross-validation AUC-ROC: {mean_auc:.4f} (+/- {std_auc:.4f})")

    # Train final model on full dataset
    final_model = train_random_forest(X, y, random_state=random_state)

    results = {
        "cv_folds": cv_folds,
        "mean_auc": float(mean_auc),
        "std_auc": float(std_auc),
        "cv_scores": cv_scores.tolist(),
        "random_state": random_state
    }

    return final_model, results

def calculate_permutation_importance(
    model: RandomForestClassifier,
    X: np.ndarray,
    y: np.ndarray,
    n_repeats: int = 10,
    random_state: int = 42
) -> Dict[str, Any]:
    """Calculate permutation importance and return top features."""
    logger.info("Calculating permutation importance...")

    result = permutation_importance(
        model,
        X,
        y,
        n_repeats=n_repeats,
        random_state=random_state,
        n_jobs=-1,
        scoring='roc_auc'
    )

    importance_scores = result.importances_mean
    std_scores = result.importances_std

    # Assuming feature names are available or we generate generic ones
    # In a real pipeline, X.columns would be passed or inferred
    feature_names = [f"Feature_{i}" for i in range(len(importance_scores))]

    # Create a summary dataframe
    importance_df = pd.DataFrame({
        "feature": feature_names,
        "importance": importance_scores,
        "std": std_scores
    }).sort_values(by="importance", ascending=False)

    logger.info(f"Top 5 features: {importance_df.head(5)['feature'].tolist()}")

    return {
        "mean_importance": importance_scores.tolist(),
        "std_importance": std_scores.tolist(),
        "feature_names": feature_names,
        "top_features": importance_df.head(10).to_dict(orient="records")
    }

def save_importance_results(
    importance_data: Dict[str, Any],
    output_path: Optional[str] = None
) -> None:
    """Save permutation importance results to a JSON file."""
    if output_path is None:
        output_path = str(get_results_root() / "importance_results.json")

    with open(output_path, 'w') as f:
        import json
        json.dump(importance_data, f, indent=2)
    logger.info(f"Importance results saved to {output_path}")

def run_importance_analysis(
    model: RandomForestClassifier,
    X: np.ndarray,
    y: np.ndarray,
    n_repeats: int = 10,
    random_state: int = 42
) -> None:
    """Wrapper to run importance analysis and save results."""
    importance_data = calculate_permutation_importance(
        model, X, y, n_repeats=n_repeats, random_state=random_state
    )
    save_importance_results(importance_data)

def save_model(
    model: Any,
    output_path: Optional[str] = None
) -> None:
    """
    Serialize and save the trained model to disk.
    Defaults to data/processed/model.pkl.
    """
    if output_path is None:
        output_path = str(get_data_processed() / "model.pkl")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving model to {output_path}")
    with open(output_path, 'wb') as f:
        pickle.dump(model, f)

    logger.info("Model saved successfully.")

def save_metrics(
    metrics: Dict[str, Any],
    output_path: Optional[str] = None
) -> None:
    """Save training metrics to a JSON file."""
    if output_path is None:
        output_path = str(get_results_root() / "metrics.json")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    import json
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {output_path}")

# Main entry point for the task T031 implementation
def run_full_training_and_save():
    """
    Orchestrates loading data, training, calculating importance,
    saving metrics, and serializing the model.
    """
    logger.info("Starting full training and serialization pipeline.")
    
    # 1. Load Data
    X, y = load_feature_matrix()
    
    # 2. Train Model & Get Metrics
    model, metrics = run_training_pipeline(X, y)
    
    # 3. Calculate Importance
    run_importance_analysis(model, X, y)
    
    # 4. Save Metrics
    save_metrics(metrics)
    
    # 5. Save Model (T031 Task)
    save_model(model)
    
    logger.info("Pipeline completed successfully.")
    return model

if __name__ == "__main__":
    # Set up basic logging if run directly
    logging.basicConfig(level=logging.INFO)
    run_full_training_and_save()
