import gc
import logging
import os
import pickle
import resource
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.inspection import permutation_importance
from sklearn.metrics import make_scorer, roc_auc_score, precision_score, recall_score
from sklearn.utils import shuffle

from config import get_data_processed, get_results_root, get_logs_root, ensure_directories_exist
from utils.logger import get_logger, setup_logging

# Ensure directories exist
ensure_directories_exist()

logger = get_logger(__name__)


def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_maxrss / 1024.0


def check_memory_pressure(threshold_mb: float = 6000.0) -> bool:
    """Check if current memory usage exceeds threshold."""
    return get_memory_usage_mb() > threshold_mb


def profile_memory_usage(func):
    """Decorator to profile memory usage of a function."""
    def wrapper(*args, **kwargs):
        start_mem = get_memory_usage_mb()
        result = func(*args, **kwargs)
        end_mem = get_memory_usage_mb()
        logger.info(f"Memory usage for {func.__name__}: {end_mem - start_mem:.2f} MB")
        return result
    return wrapper


def force_gc():
    """Force garbage collection."""
    gc.collect()


def load_feature_matrix(path: Optional[str] = None) -> pd.DataFrame:
    """Load the feature matrix from disk."""
    if path is None:
        path = str(get_data_processed() / "feature_matrix.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Feature matrix not found at {path}")
    logger.info(f"Loading feature matrix from {path}")
    df = pd.read_csv(path)
    return df


def set_class_weights(y: np.ndarray) -> Dict[int, float]:
    """Calculate balanced class weights."""
    n_samples = len(y)
    n_classes = len(np.unique(y))
    class_counts = np.bincount(y)
    weights = {i: n_samples / (n_classes * count) for i, count in enumerate(class_counts)}
    logger.info(f"Class weights: {weights}")
    return weights


def setup_stratified_kfold(n_splits: int = 5, random_state: int = 42) -> StratifiedKFold:
    """Setup stratified k-fold cross-validator."""
    return StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)


def train_random_forest(
    X: pd.DataFrame,
    y: pd.Series,
    class_weight: Dict[int, float],
    random_state: int = 42,
    n_estimators: int = 100
) -> RandomForestClassifier:
    """Train a Random Forest classifier."""
    logger.info("Training Random Forest classifier...")
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        class_weight=class_weight,
        random_state=random_state,
        n_jobs=-1
    )
    model.fit(X, y)
    logger.info("Random Forest training complete.")
    return model


def run_cross_validation(
    X: pd.DataFrame,
    y: pd.Series,
    n_splits: int = 5,
    random_state: int = 42
) -> Dict[str, Any]:
    """Run stratified k-fold cross-validation and return metrics."""
    logger.info(f"Running {n_splits}-fold stratified cross-validation...")
    cv = setup_stratified_kfold(n_splits=n_splits, random_state=random_state)

    # Define scorers
    auc_scorer = make_scorer(roc_auc_score, needs_proba=True)
    precision_scorer = make_scorer(precision_score, average='weighted')
    recall_scorer = make_scorer(recall_score, average='weighted')

    # Calculate scores
    auc_scores = cross_val_score(RandomForestClassifier(random_state=random_state), X, y, cv=cv, scoring=auc_scorer)
    precision_scores = cross_val_score(RandomForestClassifier(random_state=random_state), X, y, cv=cv, scoring=precision_scorer)
    recall_scores = cross_val_score(RandomForestClassifier(random_state=random_state), X, y, cv=cv, scoring=recall_scorer)

    metrics = {
        "auc_scores": auc_scores.tolist(),
        "precision_scores": precision_scores.tolist(),
        "recall_scores": recall_scores.tolist(),
        "auc_mean": float(np.mean(auc_scores)),
        "auc_std": float(np.std(auc_scores)),
        "precision_mean": float(np.mean(precision_scores)),
        "recall_mean": float(np.mean(recall_scores))
    }
    logger.info(f"Cross-validation complete. AUC: {metrics['auc_mean']:.4f} (+/- {metrics['auc_std']:.4f})")
    return metrics


def aggregate_cv_metrics(metrics: Dict[str, Any]) -> Dict[str, float]:
    """Aggregate cross-validation metrics into summary statistics."""
    return {
        "auc_mean": metrics["auc_mean"],
        "auc_std": metrics["auc_std"],
        "precision_mean": metrics["precision_mean"],
        "recall_mean": metrics["recall_mean"]
    }


def log_cv_metrics(metrics: Dict[str, Any], output_path: Optional[str] = None):
    """Log cross-validation metrics to a JSON file."""
    if output_path is None:
        output_path = str(get_results_root() / "metrics.json")
    results_root = get_results_root()
    results_root.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        import json
        json.dump(metrics, f, indent=2)
    logger.info(f"CV metrics saved to {output_path}")


def calculate_permutation_importance(
    model: RandomForestClassifier,
    X: pd.DataFrame,
    y: pd.Series,
    n_repeats: int = 10,
    random_state: int = 42
) -> pd.DataFrame:
    """Calculate permutation importance of features."""
    logger.info("Calculating permutation importance...")
    result = permutation_importance(
        model, X, y,
        n_repeats=n_repeats,
        random_state=random_state,
        n_jobs=-1
    )
    importance_df = pd.DataFrame({
        "feature": X.columns,
        "importance_mean": result.importances_mean,
        "importance_std": result.importances_std
    })
    return importance_df


def rank_traits(importance_df: pd.DataFrame, top_n: int = 3) -> List[Dict[str, Any]]:
    """
    Rank traits by permutation importance and return the top N traits.
    
    Args:
        importance_df: DataFrame with columns 'feature', 'importance_mean', 'importance_std'.
        top_n: Number of top traits to return.
        
    Returns:
        List of dictionaries containing rank, feature name, mean importance, and std importance.
    """
    if importance_df.empty:
        logger.warning("Importance DataFrame is empty. Returning empty list.")
        return []
    
    # Sort by mean importance descending
    sorted_df = importance_df.sort_values(by="importance_mean", ascending=False).reset_index(drop=True)
    
    # Select top N
    top_traits_df = sorted_df.head(top_n)
    
    # Format as list of dicts with rank
    ranked_traits = []
    for idx, row in top_traits_df.iterrows():
        ranked_traits.append({
            "rank": int(idx + 1),
            "trait": str(row["feature"]),
            "importance_mean": float(row["importance_mean"]),
            "importance_std": float(row["importance_std"])
        })
    
    logger.info(f"Top {top_n} traits identified: {[t['trait'] for t in ranked_traits]}")
    return ranked_traits


def save_model(model: RandomForestClassifier, path: Optional[str] = None):
    """Save the trained model to disk."""
    if path is None:
        path = str(get_data_processed() / "model.pkl")
    processed_dir = get_data_processed()
    processed_dir.mkdir(parents=True, exist_ok=True)
    with open(path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {path}")


def load_model(path: Optional[str] = None) -> RandomForestClassifier:
    """Load a trained model from disk."""
    if path is None:
        path = str(get_data_processed() / "model.pkl")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model not found at {path}")
    with open(path, 'rb') as f:
        model = pickle.load(f)
    logger.info(f"Model loaded from {path}")
    return model


def save_importance_results(ranked_traits: List[Dict[str, Any]], output_path: Optional[str] = None):
    """Save ranked trait importance results to a JSON file."""
    if output_path is None:
        output_path = str(get_results_root() / "trait_importance.json")
    results_root = get_results_root()
    results_root.mkdir(parents=True, exist_ok=True)
    import json
    with open(output_path, 'w') as f:
        json.dump(ranked_traits, f, indent=2)
    logger.info(f"Trait importance results saved to {output_path}")


def run_training_pipeline(
    feature_matrix_path: Optional[str] = None,
    n_splits: int = 5,
    n_estimators: int = 100,
    random_state: int = 42
) -> Tuple[RandomForestClassifier, Dict[str, Any], List[Dict[str, Any]]]:
    """
    Run the full training pipeline: load data, cross-validation, train model, calculate importance, rank traits.
    
    Returns:
        Tuple of (model, cv_metrics, ranked_traits)
    """
    # Load data
    df = load_feature_matrix(feature_matrix_path)
    
    # Separate features and target
    # Assuming 'link_label' is the target column based on T019a schema
    if 'link_label' not in df.columns:
        raise ValueError("Feature matrix must contain 'link_label' column.")
    
    X = df.drop(columns=['link_label'])
    y = df['link_label']
    
    # Handle potential non-numeric columns if any (though schema says all traits + effort + label)
    # Ensure all features are numeric
    X = X.select_dtypes(include=[np.number])
    
    if X.empty:
        raise ValueError("No numeric features found in the dataset after dropping target.")
    
    # Cross-validation
    cv_metrics = run_cross_validation(X, y, n_splits=n_splits, random_state=random_state)
    log_cv_metrics(cv_metrics)
    
    # Train final model on full data
    class_weights = set_class_weights(y.values)
    model = train_random_forest(
        X, y,
        class_weight=class_weights,
        random_state=random_state,
        n_estimators=n_estimators
    )
    
    # Calculate permutation importance
    importance_df = calculate_permutation_importance(model, X, y, random_state=random_state)
    
    # Rank traits
    ranked_traits = rank_traits(importance_df, top_n=3)
    save_importance_results(ranked_traits)
    
    # Save model
    save_model(model)
    
    return model, cv_metrics, ranked_traits


def run_full_training_and_save():
    """Entry point to run the full training pipeline and save artifacts."""
    logger.info("Starting full training pipeline...")
    model, metrics, ranks = run_training_pipeline()
    logger.info("Training pipeline completed successfully.")
    logger.info(f"Top 3 traits: {[r['trait'] for r in ranks]}")
    return model, metrics, ranks


def main():
    """Main entry point for the script."""
    setup_logging()
    try:
        run_full_training_and_save()
    except Exception as e:
        logger.error(f"Training pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()