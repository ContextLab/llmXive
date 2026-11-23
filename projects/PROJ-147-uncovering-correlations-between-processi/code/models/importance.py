"""
Permutation Importance Calculation and Ranking Logic.

Implements FR-005: Calculate permutation importance for the trained model
to rank feature importance. This module computes importance by shuffling
feature values and measuring the drop in model performance.
"""

import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

from sklearn.inspection import permutation_importance
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

from code.config import ensure_dirs
from code.utils.logging import get_logger, log_warning_structured
from code.models.evaluator import load_model_predictions


def calculate_permutation_importance(
    model: Any,
    X: pd.DataFrame,
    y: np.ndarray,
    scoring: str = 'r2',
    n_repeats: int = 10,
    random_state: int = 42,
    n_jobs: int = -1
) -> Dict[str, Any]:
    """
    Calculate permutation importance for a trained model.

    Args:
        model: Trained scikit-learn model with predict method.
        X: Feature DataFrame used for training/evaluation.
        y: Target array used for training/evaluation.
        scoring: Scoring metric to use (default: 'r2').
        n_repeats: Number of times to permute a feature (default: 10).
        random_state: Random seed for reproducibility.
        n_jobs: Number of parallel jobs (-1 for all CPUs).

    Returns:
        Dictionary containing:
            - 'importance_scores': Dict mapping feature names to importance values
            - 'ranked_features': List of feature names sorted by importance (descending)
            - 'mean_importance': Mean importance across repeats
            - 'std_importance': Standard deviation across repeats
    """
    logger = get_logger(__name__)
    logger.info(f"Calculating permutation importance with {n_repeats} repeats")

    # Calculate permutation importance
    result = permutation_importance(
        model, X, y,
        scoring=scoring,
        n_repeats=n_repeats,
        random_state=random_state,
        n_jobs=n_jobs
    )

    # Extract feature names from DataFrame
    feature_names = X.columns.tolist()

    # Create importance mapping
    importance_scores = {}
    for i, feature in enumerate(feature_names):
        importance_scores[feature] = result.importances_mean[i]

    # Rank features by importance (descending)
    ranked_features = sorted(
        importance_scores.keys(),
        key=lambda x: importance_scores[x],
        reverse=True
    )

    # Calculate statistics
    mean_importance = result.importances_mean
    std_importance = result.importances_std

    logger.info(f"Top 3 features: {ranked_features[:3]}")
    logger.info(f"Bottom 3 features: {ranked_features[-3:]}")

    return {
        'importance_scores': importance_scores,
        'ranked_features': ranked_features,
        'mean_importance': mean_importance.tolist(),
        'std_importance': std_importance.tolist(),
        'feature_names': feature_names,
        'scoring_metric': scoring,
        'n_repeats': n_repeats
    }


def rank_features_by_importance(
    importance_data: Dict[str, Any],
    top_n: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Rank features by importance and return formatted list.

    Args:
        importance_data: Output from calculate_permutation_importance.
        top_n: Number of top features to return (None for all).

    Returns:
        List of dictionaries with feature name, importance score, and rank.
    """
    ranked_names = importance_data['ranked_features']
    scores = importance_data['importance_scores']
    std_scores = importance_data['std_importance']
    feature_names = importance_data['feature_names']

    # Create indexed list for ranking
    ranked_list = []
    for rank, feature in enumerate(ranked_names, 1):
        idx = feature_names.index(feature)
        ranked_list.append({
            'rank': rank,
            'feature': feature,
            'importance': scores[feature],
            'std': std_scores[idx]
        })

    if top_n is not None:
        ranked_list = ranked_list[:top_n]

    return ranked_list


def save_importance_report(
    importance_data: Dict[str, Any],
    ranked_features: List[Dict[str, Any]],
    output_path: str
) -> None:
    """
    Save importance analysis report to JSON file.

    Args:
        importance_data: Raw importance calculation results.
        ranked_features: Formatted ranked features list.
        output_path: Path to save the JSON report.
    """
    logger = get_logger(__name__)

    # Ensure directory exists
    ensure_dirs([output_path])

    report = {
        'importance_analysis': importance_data,
        'ranked_features': ranked_features,
        'summary': {
            'total_features': len(ranked_features),
            'top_feature': ranked_features[0]['feature'] if ranked_features else None,
            'top_importance': ranked_features[0]['importance'] if ranked_features else 0
        }
    }

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Importance report saved to {output_path}")


def run_importance_analysis(
    model_path: str,
    processed_data_path: str,
    output_report_path: str
) -> Dict[str, Any]:
    """
    Run complete permutation importance analysis pipeline.

    Args:
        model_path: Path to the trained model pickle file.
        processed_data_path: Path to the processed dataset CSV.
        output_report_path: Path to save the importance report.

    Returns:
        Dictionary with importance analysis results.
    """
    logger = get_logger(__name__)
    logger.info(f"Starting importance analysis pipeline")

    # Load processed data
    if not os.path.exists(processed_data_path):
        raise FileNotFoundError(
            f"Processed data not found at {processed_data_path}. "
            "Run the training pipeline first."
        )

    data = pd.read_csv(processed_data_path)

    # Separate features and targets
    # Assuming target columns start with 'texture_' based on project context
    target_cols = [col for col in data.columns if col.startswith('texture_')]
    feature_cols = [col for col in data.columns if col not in target_cols]

    if not target_cols:
        raise ValueError(
            "No target columns found (expected columns starting with 'texture_'). "
            "Check data schema."
        )

    X = data[feature_cols]
    y = data[target_cols].values

    # Load model
    import joblib
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found at {model_path}")

    model = joblib.load(model_path)
    logger.info(f"Model loaded from {model_path}")

    # Calculate importance
    importance_data = calculate_permutation_importance(
        model=model,
        X=X,
        y=y,
        scoring='r2',
        n_repeats=10,
        random_state=42
    )

    # Rank features
    ranked_features = rank_features_by_importance(importance_data, top_n=None)

    # Save report
    save_importance_report(importance_data, ranked_features, output_report_path)

    logger.info("Importance analysis completed successfully")

    return {
        'importance_data': importance_data,
        'ranked_features': ranked_features,
        'report_path': output_report_path
    }