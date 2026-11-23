import gc
import logging
import os
import pickle
import resource
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.inspection import permutation_importance
from sklearn.metrics import make_scorer, roc_auc_score, precision_score, recall_score
from sklearn.preprocessing import StandardScaler

from config import get_project_root, get_results_root, get_data_processed, ensure_directories_exist
from utils.logger import get_logger

logger = get_logger(__name__)

# --- Memory Profiling (Existing Functions) ---

def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_maxrss / 1024.0  # Convert KB to MB on Linux/macOS

def check_memory_pressure(threshold_mb: float = 6000) -> bool:
    """Check if current memory usage exceeds threshold."""
    return get_memory_usage_mb() > threshold_mb

def profile_memory_usage(func):
    """Decorator to profile memory usage of a function."""
    def wrapper(*args, **kwargs):
        start_mem = get_memory_usage_mb()
        result = func(*args, **kwargs)
        end_mem = get_memory_usage_mb()
        logger.info(f"Memory usage for {func.__name__}: {start_mem:.2f}MB -> {end_mem:.2f}MB (Delta: {end_mem - start_mem:.2f}MB)")
        return result
    return wrapper

def force_gc():
    """Force garbage collection to free memory."""
    gc.collect()
    logger.debug("Garbage collection forced.")

# --- Data Loading (Existing Functions) ---

def load_feature_matrix(filepath: Optional[str] = None) -> pd.DataFrame:
    """Load the processed feature matrix."""
    if filepath is None:
        filepath = str(get_data_processed() / "feature_matrix.csv")
    logger.info(f"Loading feature matrix from {filepath}")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Feature matrix not found at {filepath}. Run preprocessing first.")
    return pd.read_csv(filepath)

# --- Model Configuration (Existing Functions) ---

def set_class_weights(y: np.ndarray) -> Dict[int, float]:
    """Calculate balanced class weights."""
    from sklearn.utils.class_weight import compute_class_weight
    classes = np.unique(y)
    weights = compute_class_weight('balanced', classes=classes, y=y)
    return dict(zip(classes, weights))

def setup_stratified_kfold(n_splits: int = 5, shuffle: bool = True, random_state: int = 42) -> StratifiedKFold:
    """Setup Stratified K-Fold cross-validator."""
    return StratifiedKFold(n_splits=n_splits, shuffle=shuffle, random_state=random_state)

# --- Model Training (Existing Functions) ---

def train_random_forest(X: np.ndarray, y: np.ndarray, class_weight_dict: Dict[int, float], random_state: int = 42) -> RandomForestClassifier:
    """Train a Random Forest classifier."""
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=None,
        class_weight=class_weight_dict,
        random_state=random_state,
        n_jobs=-1
    )
    model.fit(X, y)
    return model

# --- Cross-Validation Logic (Existing Functions) ---

@profile_memory_usage
def run_cross_validation(X: np.ndarray, y: np.ndarray, model_class=RandomForestClassifier, cv: StratifiedKFold = None, random_state: int = 42) -> Tuple[List[float], List[Dict[str, Any]]]:
    """Run cross-validation and return scores and fold details."""
    if cv is None:
        cv = setup_stratified_kfold()

    scores = []
    fold_details = []

    # Custom scoring for AUC
    auc_scorer = make_scorer(roc_auc_score, needs_proba=True)

    for fold_idx, (train_idx, test_idx) in enumerate(cv.split(X, y)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # Calculate class weights for this fold
        class_weights = set_class_weights(y_train)

        model = train_random_forest(X_train, y_train, class_weights, random_state)

        # Predict probabilities for AUC
        y_prob = model.predict_proba(X_test)[:, 1]
        y_pred = model.predict(X_test)

        try:
            auc = roc_auc_score(y_test, y_prob)
            precision = precision_score(y_test, y_pred, zero_division=0)
            recall = recall_score(y_test, y_pred, zero_division=0)
        except ValueError as e:
            logger.warning(f"Fold {fold_idx} calculation error (likely single class in test): {e}")
            auc = 0.0
            precision = 0.0
            recall = 0.0

        scores.append(auc)
        fold_details.append({
            "fold": fold_idx,
            "auc": auc,
            "precision": precision,
            "recall": recall,
            "train_size": len(train_idx),
            "test_size": len(test_idx)
        })

        logger.info(f"Fold {fold_idx}: AUC={auc:.4f}, Precision={precision:.4f}, Recall={recall:.4f}")

    return scores, fold_details

@profile_memory_usage
def aggregate_cv_metrics(scores: List[float], fold_details: List[Dict[str, Any]]) -> Dict[str, float]:
    """Aggregate cross-validation metrics."""
    if not scores:
        raise ValueError("No scores provided to aggregate.")

    auc_mean = float(np.mean(scores))
    auc_std = float(np.std(scores))

    # Aggregate precision and recall from fold details
    precisions = [f['precision'] for f in fold_details]
    recalls = [f['recall'] for f in fold_details]

    precision_mean = float(np.mean(precisions))
    recall_mean = float(np.mean(recalls))

    return {
        "auc_mean": auc_mean,
        "auc_std": auc_std,
        "precision_mean": precision_mean,
        "recall_mean": recall_mean,
        "n_folds": len(scores),
        "fold_details": fold_details
    }

# --- T027: Logging Setup Implementation ---

def log_cv_metrics(metrics: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Log cross-validation metrics to a JSON file and the logger.
    Verifies required keys: auc_mean, auc_std, precision_mean, recall_mean.
    """
    required_keys = ["auc_mean", "auc_std", "precision_mean", "recall_mean"]
    missing_keys = [k for k in required_keys if k not in metrics]
    if missing_keys:
        raise ValueError(f"Missing required metric keys in metrics dict: {missing_keys}")

    if output_path is None:
        results_root = get_results_root()
        ensure_directories_exist()
        output_path = str(results_root / "metrics.json")

    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Log to console/file logger
    logger.info(f"Cross-Validation Results -> AUC: {metrics['auc_mean']:.4f} (+/- {metrics['auc_std']:.4f})")
    logger.info(f"Precision: {metrics['precision_mean']:.4f}, Recall: {metrics['recall_mean']:.4f}")

    # Write to JSON file
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Metrics saved to {output_path}")
    return output_path

# --- Permutation Importance (Existing Functions) ---

@profile_memory_usage
def calculate_permutation_importance(model: RandomForestClassifier, X: np.ndarray, y: np.ndarray, n_repeats: int = 10, random_state: int = 42) -> np.ndarray:
    """Calculate permutation importance."""
    result = permutation_importance(model, X, y, n_repeats=n_repeats, random_state=random_state, n_jobs=-1)
    return result.importances_mean

def rank_traits(importance_scores: np.ndarray, feature_names: List[str], top_n: int = 3) -> List[Dict[str, Union[str, float]]]:
    """Rank traits by importance."""
    indices = np.argsort(importance_scores)[::-1]
    ranked = []
    for i in range(min(top_n, len(indices))):
        idx = indices[i]
        ranked.append({
            "rank": i + 1,
            "feature": feature_names[idx],
            "importance": float(importance_scores[idx])
        })
    return ranked

# --- Model Serialization (Existing Functions) ---

def save_model(model: Any, filepath: str):
    """Save model to pickle file."""
    with open(filepath, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {filepath}")

def load_model(filepath: str) -> Any:
    """Load model from pickle file."""
    with open(filepath, 'rb') as f:
        return pickle.load(f)

def save_importance_results(ranked_traits: List[Dict], output_path: str):
    """Save trait importance results to JSON."""
    with open(output_path, 'w') as f:
        json.dump(ranked_traits, f, indent=2)
    logger.info(f"Importance results saved to {output_path}")

# --- Pipeline Orchestrators (Existing Functions) ---

@profile_memory_usage
def run_training_pipeline(data_path: Optional[str] = None, n_splits: int = 5, random_state: int = 42) -> Dict[str, Any]:
    """Run the full training pipeline: load, CV, aggregate, log, importance, save."""
    logger.info("Starting training pipeline...")
    df = load_feature_matrix(data_path)

    # Prepare data
    X = df.drop(columns=['link_label']).values
    y = df['link_label'].values
    feature_names = [c for c in df.columns if c != 'link_label']

    # Setup CV
    cv = setup_stratified_kfold(n_splits=n_splits, random_state=random_state)

    # Run CV
    scores, fold_details = run_cross_validation(X, y, cv=cv, random_state=random_state)

    # Aggregate
    metrics = aggregate_cv_metrics(scores, fold_details)

    # Log metrics (T027)
    log_cv_metrics(metrics)

    # Train final model on full data for importance
    class_weights = set_class_weights(y)
    final_model = train_random_forest(X, y, class_weights, random_state)

    # Importance
    importance_scores = calculate_permutation_importance(final_model, X, y, random_state=random_state)
    ranked = rank_traits(importance_scores, feature_names)
    save_importance_results(ranked, str(get_results_root() / "trait_importance.json"))

    # Save model
    model_path = str(get_data_processed() / "model.pkl")
    save_model(final_model, model_path)

    logger.info("Training pipeline complete.")
    return metrics

def run_full_training_and_save():
    """Entry point for running training."""
    ensure_directories_exist()
    run_training_pipeline()

def main():
    """Main entry point."""
    run_full_training_and_save()

if __name__ == "__main__":
    main()
