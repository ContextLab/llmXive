"""
Validation module for User Story 3: Generalization Validation and Reporting.

Implements Leave-One-Ecosystem-Out (LOEO) cross-validation and the Trait-Shuffled
Null Model to assess trait efficacy in predicting pollinator networks.
"""
import json
import logging
import os
import pickle
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.ensemble import RandomForestClassifier
from sklearn.utils import shuffle

from config import get_data_processed, get_results_root
from utils.logger import get_logger

# Ensure logger is available
logger = get_logger(__name__)

def load_feature_matrix(path: Optional[Union[str, Path]] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load the unified feature matrix and labels from the processed data directory.
    
    Args:
        path: Optional path to the specific file. If None, looks for the standard
              output from the preprocessing pipeline.
    
    Returns:
        Tuple of (features_df, labels_df)
    """
    if path is None:
        data_root = get_data_processed()
        path = Path(data_root) / "feature_matrix.csv"
    else:
        path = Path(path)
    
    if not path.exists():
        raise FileNotFoundError(f"Feature matrix not found at {path}")
    
    df = pd.read_csv(path)
    
    # Assume the last column is the label 'link_label' based on T019 spec
    # If the column name differs, adjust accordingly.
    label_col = 'link_label'
    if label_col not in df.columns:
        # Fallback: assume last column is label if named differently or unnamed
        label_col = df.columns[-1]
        logger.warning(f"Label column '{label_col}' not found, using last column: {df.columns[-1]}")
    
    features = df.drop(columns=[label_col])
    labels = df[[label_col]]
    
    return features, labels

def load_ecosystem_ids(path: Optional[Union[str, Path]] = None) -> pd.Series:
    """
    Load the ecosystem identifiers corresponding to the feature matrix rows.
    This assumes the 'ecosystem_id' column exists in the processed data.
    """
    if path is None:
        data_root = get_data_processed()
        path = Path(data_root) / "feature_matrix.csv"
    else:
        path = Path(path)
    
    if not path.exists():
        raise FileNotFoundError(f"Feature matrix not found at {path}")
    
    df = pd.read_csv(path)
    
    if 'ecosystem_id' not in df.columns:
        raise ValueError("Column 'ecosystem_id' not found in feature matrix. "
                         "Ensure preprocessing included ecosystem IDs.")
    
    return df['ecosystem_id']

def load_model(path: Optional[Union[str, Path]] = None) -> RandomForestClassifier:
    """
    Load the trained Random Forest model from disk.
    """
    if path is None:
        data_root = get_data_processed()
        path = Path(data_root) / "model.pkl"
    else:
        path = Path(path)
    
    if not path.exists():
        raise FileNotFoundError(f"Trained model not found at {path}")
    
    with open(path, 'rb') as f:
        model = pickle.load(f)
    
    return model

def run_loeo_validation(
    features: pd.DataFrame,
    labels: pd.DataFrame,
    ecosystem_ids: pd.Series,
    model: Optional[RandomForestClassifier] = None,
    n_jobs: int = -1
) -> Dict[str, Any]:
    """
    Perform Leave-One-Ecosystem-Out (LOEO) cross-validation.
    
    For each ecosystem, the model is trained on all other ecosystems and
    evaluated on the held-out ecosystem.
    
    Args:
        features: Feature DataFrame (X)
        labels: Label DataFrame (y)
        ecosystem_ids: Series of ecosystem IDs corresponding to rows in features
        model: Pre-trained model (optional). If None, a new RF is trained for each fold.
        n_jobs: Number of parallel jobs for LOEO (if model supports it)
    
    Returns:
        Dictionary containing LOEO metrics and fold details.
    """
    logger.info("Starting Leave-One-Ecosystem-Out (LOEO) validation...")
    
    logo = LeaveOneGroupOut()
    groups = ecosystem_ids.values
    unique_ecosystems = np.unique(groups)
    
    if len(unique_ecosystems) < 2:
        raise ValueError("LOEO requires at least 2 unique ecosystems to perform validation.")
    
    logger.info(f"Found {len(unique_ecosystems)} unique ecosystems for LOEO.")
    
    loeo_scores = []
    fold_details = []
    
    # If a model is provided, we use it as a template but must retrain on each fold
    # because the training data changes.
    # If no model is provided, we instantiate a new one per fold.
    base_model = model if model else RandomForestClassifier(
        n_estimators=100,
        random_state=42,
        n_jobs=n_jobs,
        class_weight='balanced'
    )
    
    for train_idx, test_idx in logo.split(features, labels, groups):
        X_train, X_test = features.iloc[train_idx], features.iloc[test_idx]
        y_train, y_test = labels.iloc[train_idx].values.ravel(), labels.iloc[test_idx].values.ravel()
        test_ecosystem = groups[test_idx][0] # All test rows belong to one ecosystem
        
        # Train model on N-1 ecosystems
        # Note: If a pre-trained model was passed, we clone it to avoid state leakage
        # or we just fit a new instance. sklearn's fit overwrites the model state.
        current_model = RandomForestClassifier(
            n_estimators=base_model.n_estimators,
            random_state=base_model.random_state,
            n_jobs=n_jobs,
            class_weight='balanced'
        )
        current_model.fit(X_train, y_train)
        
        # Predict probabilities for the held-out ecosystem
        y_prob = current_model.predict_proba(X_test)[:, 1]
        
        # Calculate AUC-ROC
        try:
            auc_score = roc_auc_score(y_test, y_prob)
        except ValueError as e:
            # Handle case where only one class is present in the test set
            logger.warning(f"AUC-ROC could not be calculated for ecosystem {test_ecosystem}: {e}")
            auc_score = np.nan
        
        loeo_scores.append(auc_score)
        fold_details.append({
            "held_out_ecosystem": test_ecosystem,
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "auc_roc": auc_score
        })
    
    mean_loeo_auc = np.nanmean(loeo_scores)
    std_loeo_auc = np.nanstd(loeo_scores)
    
    result = {
        "method": "LOEO",
        "mean_auc_roc": mean_loeo_auc,
        "std_auc_roc": std_loeo_auc,
        "n_ecosystems": len(unique_ecosystems),
        "fold_details": fold_details
    }
    
    logger.info(f"LOEO Validation Complete. Mean AUC: {mean_loeo_auc:.4f} (+/- {std_loeo_auc:.4f})")
    return result

def run_trait_shuffled_null_model(
    features: pd.DataFrame,
    labels: pd.DataFrame,
    ecosystem_ids: pd.Series,
    n_iterations: int = 10,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Implement the Trait-Shuffled Null Model.
    
    This shuffles the trait values (features) across all samples while keeping
    the labels and ecosystem structure intact. This breaks the relationship between
    traits and interactions, providing a baseline for what the model can achieve
    by chance given the label distribution.
    
    Args:
        features: Feature DataFrame
        labels: Label DataFrame
        ecosystem_ids: Ecosystem IDs (needed for LOEO structure)
        n_iterations: Number of shuffling iterations
        random_state: Random seed for reproducibility
    
    Returns:
        Dictionary containing null model metrics.
    """
    logger.info(f"Running Trait-Shuffled Null Model ({n_iterations} iterations)...")
    
    rng = np.random.default_rng(random_state)
    null_scores = []
    
    for i in range(n_iterations):
        # Shuffle the features (X) row-wise, breaking the link to Y
        # We keep the original Y and ecosystem_ids
        shuffled_features = features.sample(frac=1, random_state=rng.integers(0, 2**31)).reset_index(drop=True)
        
        # Run LOEO on the shuffled data
        # We reuse the LOEO logic but with shuffled features
        # To save time, we might skip full training if the model is complex,
        # but for a valid null model, we must train a model on the shuffled data.
        
        # Note: We instantiate a fresh model for each iteration to avoid leakage
        null_model = RandomForestClassifier(
            n_estimators=100,
            random_state=42, # Fixed seed for the null model training itself
            class_weight='balanced'
        )
        
        # Quick LOEO loop (simplified for null model speed if needed, but here we do full)
        logo = LeaveOneGroupOut()
        groups = ecosystem_ids.values
        unique_ecosystems = np.unique(groups)
        
        iteration_scores = []
        
        for train_idx, test_idx in logo.split(shuffled_features, labels, groups):
            X_train, X_test = shuffled_features.iloc[train_idx], shuffled_features.iloc[test_idx]
            y_train, y_test = labels.iloc[train_idx].values.ravel(), labels.iloc[test_idx].values.ravel()
            
            null_model.fit(X_train, y_train)
            y_prob = null_model.predict_proba(X_test)[:, 1]
            
            try:
                auc = roc_auc_score(y_test, y_prob)
            except ValueError:
                auc = np.nan
            
            iteration_scores.append(auc)
        
        mean_iter_auc = np.nanmean(iteration_scores)
        null_scores.append(mean_iter_auc)
        
        if (i + 1) % 5 == 0:
            logger.debug(f"Null Model Iteration {i+1}/{n_iterations}: Mean AUC = {mean_iter_auc:.4f}")
    
    mean_null_auc = np.nanmean(null_scores)
    std_null_auc = np.nanstd(null_scores)
    
    result = {
        "method": "Trait-Shuffled Null Model",
        "n_iterations": n_iterations,
        "mean_auc_roc": mean_null_auc,
        "std_auc_roc": std_null_auc,
        "individual_scores": null_scores
    }
    
    logger.info(f"Trait-Shuffled Null Model Complete. Mean AUC: {mean_null_auc:.4f}")
    return result

def compare_to_cv_mean(
    loeo_results: Dict[str, Any],
    cv_mean_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compare LOEO results against the internal Cross-Validation (CV) mean.
    
    This implements the logic required by SC-003 to validate generalization.
    """
    loeo_mean = loeo_results.get("mean_auc_roc")
    cv_mean = cv_mean_results.get("mean_auc_roc")
    
    if loeo_mean is None or cv_mean is None:
        raise ValueError("Missing metrics for comparison.")
    
    difference = loeo_mean - cv_mean
    
    comparison = {
        "loeo_mean_auc": loeo_mean,
        "cv_mean_auc": cv_mean,
        "difference": difference,
        "interpretation": ""
    }
    
    if difference < -0.1:
        comparison["interpretation"] = "Significant generalization gap detected. Model overfits to specific ecosystem traits."
    elif difference > 0.1:
        comparison["interpretation"] = "LOEO performance exceeds internal CV. Possible data leakage or favorable ecosystem split."
    else:
        comparison["interpretation"] = "LOEO performance is consistent with internal CV. Good generalization."
    
    return comparison

def run_full_validation_pipeline(
    feature_matrix_path: Optional[str] = None,
    model_path: Optional[str] = None,
    cv_metrics_path: Optional[str] = None,
    n_null_iterations: int = 10
) -> Dict[str, Any]:
    """
    Orchestrates the full validation pipeline:
    1. Load data and model.
    2. Run LOEO.
    3. Run Trait-Shuffled Null Model.
    4. Compare results.
    5. Save results to disk.
    
    Args:
        feature_matrix_path: Path to feature matrix CSV
        model_path: Path to trained model pickle
        cv_metrics_path: Path to existing CV metrics JSON (from model_training)
        n_null_iterations: Number of iterations for the null model
    
    Returns:
        Dictionary containing all validation results.
    """
    results_root = get_results_root()
    output_path = Path(results_root) / "validation_results.json"
    
    logger.info("Starting Full Validation Pipeline...")
    
    # 1. Load Data
    features, labels = load_feature_matrix(feature_matrix_path)
    ecosystem_ids = load_ecosystem_ids(feature_matrix_path)
    model = load_model(model_path)
    
    # 2. Run LOEO
    loeo_results = run_loeo_validation(features, labels, ecosystem_ids, model)
    
    # 3. Run Trait-Shuffled Null Model
    null_results = run_trait_shuffled_null_model(
        features, labels, ecosystem_ids, n_iterations=n_null_iterations
    )
    
    # 4. Load CV Mean (from T029/T027 output)
    if cv_metrics_path is None:
        data_root = get_data_processed()
        cv_metrics_path = Path(data_root) / "metrics.json"
    else:
        cv_metrics_path = Path(cv_metrics_path)
    
    if cv_metrics_path.exists():
        with open(cv_metrics_path, 'r') as f:
            cv_data = json.load(f)
        # Assume the CV mean is stored under a key like 'mean_auc_roc' or 'cv_mean'
        # Adjust based on actual output of model_training.py
        cv_mean_val = cv_data.get('mean_auc_roc') or cv_data.get('cv_mean_auc')
        if cv_mean_val is None:
            # Fallback: try to find it in nested structure if T027 output structure differs
            cv_mean_val = cv_data.get('cv_results', {}).get('mean', cv_data.get('mean_auc', 0))
        
        cv_results = {"mean_auc_roc": cv_mean_val}
    else:
        logger.warning(f"CV metrics file not found at {cv_metrics_path}. Skipping comparison.")
        cv_results = {}
    
    comparison = {}
    if cv_results:
        comparison = compare_to_cv_mean(loeo_results, cv_results)
    
    # 5. Compile Final Results
    final_results = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "loeo": loeo_results,
        "null_model": null_results,
        "cv_comparison": comparison
    }
    
    # 6. Save Results
    with open(output_path, 'w') as f:
        json.dump(final_results, f, indent=2)
    
    logger.info(f"Validation results saved to {output_path}")
    return final_results

if __name__ == "__main__":
    # Default execution for testing the module
    run_full_validation_pipeline()
