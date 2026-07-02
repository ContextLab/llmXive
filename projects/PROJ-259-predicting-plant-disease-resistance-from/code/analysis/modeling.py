import os
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, ElasticNet
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, StratifiedKFold, KFold
from sklearn.metrics import accuracy_score, roc_auc_score, r2_score, make_scorer
from sklearn.preprocessing import StandardScaler
import joblib
import random

from config import get_path, load_config
from utils.logging import setup_logger, log_pipeline_step
from utils.exceptions import PipelineException

# Configure logger
logger = setup_logger(__name__)

def load_split_data(split_dir: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Load training and test splits from CSV files.
    Returns: X_train, X_test, y_train, y_test
    """
    train_X_path = Path(split_dir) / "train_X.csv"
    train_y_path = Path(split_dir) / "train_y.csv"
    test_X_path = Path(split_dir) / "test_X.csv"
    test_y_path = Path(split_dir) / "test_y.csv"

    if not all(p.exists() for p in [train_X_path, train_y_path, test_X_path, test_y_path]):
        raise FileNotFoundError(f"Split data files not found in {split_dir}. Run split pipeline first.")

    X_train = pd.read_csv(train_X_path, index_col=0)
    y_train = pd.read_csv(train_y_path, index_col=0).squeeze()
    X_test = pd.read_csv(test_X_path, index_col=0)
    y_test = pd.read_csv(test_y_path, index_col=0).squeeze()

    return X_train, X_test, y_train, y_test

def load_selected_features(feature_dir: str) -> List[str]:
    """
    Load the list of selected feature IDs from the feature selection output.
    """
    freq_file = Path(feature_dir) / "selection_frequency.csv"
    if not freq_file.exists():
        raise FileNotFoundError(f"Selection frequency file not found at {freq_file}. Run feature selection first.")

    df = pd.read_csv(freq_file)
    # Select features that appear in at least one threshold (frequency > 0)
    # Or specifically filter by the most common threshold if needed. 
    # For now, we take the union of selected features across thresholds or the top ones.
    # The spec says "selected features", implying the output of T016.
    # We assume the file contains columns: feature_id, threshold, frequency.
    # We will select features with frequency > 0 in the primary threshold (e.g., 0.05) or max frequency.
    # To be safe and robust, we take features where frequency > 0 in the '0.05' threshold if available, else max freq.
    
    if '0.05' in df['threshold'].values:
        selected = df[df['threshold'] == '0.05']
    else:
        # Fallback: take top features by max frequency
        selected = df.sort_values('frequency', ascending=False)
    
    return selected['feature_id'].tolist()

def train_model(X: pd.DataFrame, y: pd.Series, model_type: str = "elasticnet", 
                cv_folds: int = 5, random_state: int = 42) -> Tuple[Any, Dict[str, float]]:
    """
    Train the primary model (ElasticNet for regression or GradientBoosting for classification).
    Returns: trained model, metrics dict
    """
    logger.info(f"Training primary model: {model_type} with {cv_folds}-fold CV")
    
    # Determine if classification or regression based on y
    is_classification = y.dtype in ['bool', 'object'] or len(y.unique()) <= 10
    
    if is_classification:
        # Use Gradient Boosting for classification
        base_model = GradientBoostingClassifier(random_state=random_state)
        metric = 'roc_auc'
        scorer = make_scorer(roc_auc_score)
    else:
        # Use ElasticNet for regression
        base_model = ElasticNet(random_state=random_state, max_iter=1000)
        metric = 'r2'
        scorer = make_scorer(r2_score)

    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    if is_classification:
        cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
    else:
        cv = KFold(n_splits=cv_folds, shuffle=True, random_state=random_state)

    # Cross-validation
    cv_scores = cross_val_score(base_model, X_scaled, y, cv=cv, scoring=scorer)
    mean_score = np.mean(cv_scores)
    std_score = np.std(cv_scores)
    
    logger.info(f"CV {metric}: {mean_score:.4f} (+/- {std_score:.4f})")
    
    # Train final model on full data
    base_model.fit(X_scaled, y)
    
    metrics = {
        "cv_mean": float(mean_score),
        "cv_std": float(std_score),
        "metric_name": metric,
        "model_type": model_type,
        "is_classification": is_classification
    }
    
    return base_model, metrics

def train_null_model(X: pd.DataFrame, y: pd.Series, model_type: str = "elasticnet",
                     cv_folds: int = 5, random_state: int = 42) -> Tuple[Any, Dict[str, float]]:
    """
    Train a null model baseline by shuffling labels (random labels).
    Returns: trained null model, metrics dict
    """
    logger.info("Training null model baseline (random labels)...")
    
    # Shuffle y
    y_shuffled = y.sample(frac=1, random_state=random_state).reset_index(drop=True)
    
    # Use the same model architecture as the primary model but with shuffled labels
    # This tests if the model can learn signal from noise
    is_classification = y.dtype in ['bool', 'object'] or len(y.unique()) <= 10
    
    if is_classification:
        base_model = GradientBoostingClassifier(random_state=random_state)
        metric = 'roc_auc'
        scorer = make_scorer(roc_auc_score)
    else:
        base_model = ElasticNet(random_state=random_state, max_iter=1000)
        metric = 'r2'
        scorer = make_scorer(r2_score)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    if is_classification:
        cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
    else:
        cv = KFold(n_splits=cv_folds, shuffle=True, random_state=random_state)

    cv_scores = cross_val_score(base_model, X_scaled, y_shuffled, cv=cv, scoring=scorer)
    mean_score = np.mean(cv_scores)
    std_score = np.std(cv_scores)
    
    logger.info(f"Null Model CV {metric}: {mean_score:.4f} (+/- {std_score:.4f})")
    
    # Train final null model on full data with shuffled labels
    base_model.fit(X_scaled, y_shuffled)
    
    metrics = {
        "cv_mean": float(mean_score),
        "cv_std": float(std_score),
        "metric_name": metric,
        "model_type": f"{model_type}_null",
        "is_classification": is_classification,
        "labels_shuffled": True
    }
    
    return base_model, metrics

def save_model(model: Any, scaler: StandardScaler, model_path: str, metrics: Dict):
    """
    Save the trained model, scaler, and metrics.
    """
    model_dir = Path(model_path).parent
    model_dir.mkdir(parents=True, exist_ok=True)
    
    joblib.dump(model, model_path)
    joblib.dump(scaler, str(model_path).replace('.pkl', '_scaler.pkl'))
    
    metrics_path = str(model_path).replace('.pkl', '_metrics.json')
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Model saved to {model_path}")

def modeling_pipeline(config_path: Optional[str] = None, output_dir: Optional[str] = None):
    """
    Orchestrates the modeling step:
    1. Load split data
    2. Load selected features
    3. Train primary model
    4. Train null model baseline
    5. Compare performance
    6. Save results
    """
    logger.info("Starting modeling pipeline")
    
    config = load_config(config_path)
    split_dir = get_path(config, "split_dir", "data/processed/splits")
    feature_dir = get_path(config, "feature_selection_dir", "artifacts/reports")
    model_dir = get_path(config, "model_dir", "artifacts/models")
    
    if output_dir:
        model_dir = output_dir
        
    Path(model_dir).mkdir(parents=True, exist_ok=True)
    
    # Load data
    X_train, X_test, y_train, y_test = load_split_data(split_dir)
    selected_features = load_selected_features(feature_dir)
    
    # Filter features
    X_train_selected = X_train[selected_features]
    X_test_selected = X_test[selected_features]
    
    logger.info(f"Using {len(selected_features)} selected features")
    
    # Train primary model
    primary_model, primary_metrics = train_model(X_train_selected, y_train)
    
    # Train null model
    null_model, null_metrics = train_null_model(X_train_selected, y_train)
    
    # Evaluate on test set
    # Note: For null model, we use the original y_test because the null model was trained on shuffled y_train
    # but we evaluate how well it predicts the real y_test (which should be poor)
    
    # Prepare scaler for test set
    # We need the scaler from primary model training
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_selected)
    X_test_scaled = scaler.transform(X_test_selected)
    
    # Re-train primary model on full train set with scaler
    is_classification = y_train.dtype in ['bool', 'object'] or len(y_train.unique()) <= 10
    if is_classification:
        final_primary = GradientBoostingClassifier(random_state=42)
        final_primary.fit(X_train_scaled, y_train)
        test_pred = final_primary.predict_proba(X_test_scaled)[:, 1]
        test_score = roc_auc_score(y_test, test_pred)
    else:
        final_primary = ElasticNet(random_state=42, max_iter=1000)
        final_primary.fit(X_train_scaled, y_train)
        test_pred = final_primary.predict(X_test_scaled)
        test_score = r2_score(y_test, test_pred)
        
    primary_metrics["test_score"] = float(test_score)
    
    # Re-train null model on full train set with shuffled y
    y_train_shuffled = y_train.sample(frac=1, random_state=42).reset_index(drop=True)
    if is_classification:
        final_null = GradientBoostingClassifier(random_state=42)
        final_null.fit(X_train_scaled, y_train_shuffled)
        # Evaluate null model on real test set (should be near random)
        null_pred = final_null.predict_proba(X_test_scaled)[:, 1]
        null_test_score = roc_auc_score(y_test, null_pred)
    else:
        final_null = ElasticNet(random_state=42, max_iter=1000)
        final_null.fit(X_train_scaled, y_train_shuffled)
        null_pred = final_null.predict(X_test_scaled)
        null_test_score = r2_score(y_test, null_pred)
        
    null_metrics["test_score"] = float(null_test_score)
    
    # Comparison
    improvement = primary_metrics["test_score"] - null_metrics["test_score"]
    logger.info(f"Primary model outperforms null model by: {improvement:.4f}")
    
    # Compile final metrics for metrics.json
    final_metrics = {
        "primary_model": primary_metrics,
        "null_model": null_metrics,
        "comparison": {
            "improvement": float(improvement),
            "primary_test_score": primary_metrics["test_score"],
            "null_test_score": null_metrics["test_score"]
        }
    }
    
    # Save models
    save_model(final_primary, scaler, Path(model_dir) / "primary_model.pkl", primary_metrics)
    save_model(final_null, scaler, Path(model_dir) / "null_model.pkl", null_metrics)
    
    # Save combined metrics
    metrics_path = Path(model_dir) / "modeling_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(final_metrics, f, indent=2)
    
    logger.info(f"Modeling pipeline complete. Metrics saved to {metrics_path}")
    return final_metrics

def main():
    """
    Entry point for the modeling module.
    """
    modeling_pipeline()

if __name__ == "__main__":
    main()