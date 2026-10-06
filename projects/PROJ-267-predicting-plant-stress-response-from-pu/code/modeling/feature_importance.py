"""
Feature Importance Extraction and Ranking Module.

Extracts and ranks top proteins by absolute importance score for trained
Random Forest and SVR models. Handles both tree-based (RF) and kernel-based
(SVR) models appropriately.

FR-006: Extract and rank top proteins by absolute importance score.
"""

import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import pandas as pd
import numpy as np

# Local imports
from utils.logging_config import get_logger, log_warning
from utils.config import get_results_path, get_project_root
from modeling.train import load_model_checkpoint

logger = get_logger(__name__)


def load_feature_names(feature_file: Optional[Path] = None) -> List[str]:
    """
    Load feature names (protein IDs) from the processed data matrix.

    Args:
        feature_file: Path to the merged matrix CSV. Defaults to
                      data/processed/merged_matrix.csv

    Returns:
        List of feature names (protein IDs)

    Raises:
        FileNotFoundError: If the feature file does not exist
        ValueError: If the file cannot be read or lacks expected columns
    """
    if feature_file is None:
        feature_file = get_project_root() / "data" / "processed" / "merged_matrix.csv"

    if not feature_file.exists():
        raise FileNotFoundError(f"Feature file not found: {feature_file}")

    logger.info(f"Loading feature names from {feature_file}")
    df = pd.read_csv(feature_file)

    # Assume first column is sample ID or metadata, rest are features
    # If there's a specific 'SampleID' column, drop it
    feature_cols = [col for col in df.columns if col not in ['SampleID', 'sample_id', 'ID']]

    if len(feature_cols) == 0:
        raise ValueError(f"No feature columns found in {feature_file}")

    return feature_cols


def extract_rf_importance(model: Any, feature_names: List[str]) -> pd.DataFrame:
    """
    Extract feature importance from a Random Forest model.

    Args:
        model: Trained RandomForestRegressor instance
        feature_names: List of feature names corresponding to model features

    Returns:
        DataFrame with 'feature', 'importance' columns sorted by importance
    """
    if not hasattr(model, 'feature_importances_'):
        raise AttributeError("Model does not have feature_importances_ attribute")

    importances = model.feature_importances_

    if len(importances) != len(feature_names):
        raise ValueError(
            f"Feature count mismatch: model has {len(importances)} features, "
            f"but {len(feature_names)} names provided"
        )

    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': importances
    })

    # Sort by absolute importance (though RF importances are already non-negative)
    importance_df = importance_df.sort_values('importance', ascending=False).reset_index(drop=True)

    return importance_df


def extract_svr_importance(model: Any, feature_names: List[str]) -> pd.DataFrame:
    """
    Extract feature importance from an SVR model using coefficients.

    For linear SVR, we use the coefficients directly.
    For non-linear kernels, we approximate importance via permutation or
    coefficient magnitude (with caveats).

    Args:
        model: Trained SVR instance
        feature_names: List of feature names

    Returns:
        DataFrame with 'feature', 'importance' columns
    """
    # Check if model is linear
    if hasattr(model, 'coef_'):
        coefs = model.coef_

        # Handle both 1D and 2D coefficient arrays
        if len(coefs.shape) == 2:
            coefs = coefs[0]

        if len(coefs) != len(feature_names):
            raise ValueError(
                f"Feature count mismatch: SVR has {len(coefs)} features, "
                f"but {len(feature_names)} names provided"
            )

        # Use absolute values for importance
        importances = np.abs(coefs)

        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': importances
        })

        importance_df = importance_df.sort_values('importance', ascending=False).reset_index(drop=True)

        log_warning(
            f"Using coefficient magnitude for SVR importance. "
            f"For non-linear kernels, this is an approximation."
        )

    else:
        # Fallback: raise error for non-linear kernels without permutation
        raise NotImplementedError(
            "SVR feature importance extraction requires linear kernel or "
            "permutation-based importance calculation. "
            f"Model type: {type(model).__name__}, kernel: {getattr(model, 'kernel', 'unknown')}"
        )

    return importance_df


def get_top_features(
    importance_df: pd.DataFrame,
    n_top: int = 50
) -> pd.DataFrame:
    """
    Get the top N features by importance.

    Args:
        importance_df: DataFrame with 'feature' and 'importance' columns
        n_top: Number of top features to return

    Returns:
        DataFrame with top N features
    """
    return importance_df.head(n_top)


def save_importance_report(
    importance_df: pd.DataFrame,
    model_type: str,
    output_path: Path
) -> None:
    """
    Save feature importance report to JSON and CSV.

    Args:
        importance_df: DataFrame with feature importance data
        model_type: Type of model (e.g., 'RandomForest', 'SVR')
        output_path: Path to save the report (without extension)
    """
    output_path = Path(output_path)

    # Save as JSON
    json_path = output_path.with_suffix('.json')
    report_data = {
        'model_type': model_type,
        'total_features': len(importance_df),
        'top_features': importance_df.to_dict(orient='records')
    }

    with open(json_path, 'w') as f:
        json.dump(report_data, f, indent=2)

    logger.info(f"Saved JSON report to {json_path}")

    # Save as CSV
    csv_path = output_path.with_suffix('.csv')
    importance_df.to_csv(csv_path, index=False)
    logger.info(f"Saved CSV report to {csv_path}")


def run_feature_importance_analysis(
    model_type: str = 'RandomForest',
    n_top: int = 50,
    feature_file: Optional[Path] = None
) -> Tuple[pd.DataFrame, Path]:
    """
    Run the full feature importance analysis pipeline.

    Args:
        model_type: Type of model to analyze ('RandomForest' or 'SVR')
        n_top: Number of top features to extract
        feature_file: Path to feature names file (optional)

    Returns:
        Tuple of (importance DataFrame, path to saved report)
    """
    results_path = get_results_path()
    results_path.mkdir(parents=True, exist_ok=True)

    # Load feature names
    feature_names = load_feature_names(feature_file)
    logger.info(f"Loaded {len(feature_names)} feature names")

    # Load the latest model checkpoint
    model_type_lower = model_type.lower()
    checkpoint_dir = results_path / "checkpoints"

    if not checkpoint_dir.exists():
        raise FileNotFoundError(f"Checkpoint directory not found: {checkpoint_dir}")

    # Find the latest checkpoint for the specified model type
    latest_checkpoint = None
    latest_time = 0

    for ckpt_file in checkpoint_dir.glob(f"{model_type_lower}_*.pkl"):
        mtime = ckpt_file.stat().st_mtime
        if mtime > latest_time:
            latest_time = mtime
            latest_checkpoint = ckpt_file

    if latest_checkpoint is None:
        raise FileNotFoundError(
            f"No checkpoint found for model type: {model_type} in {checkpoint_dir}"
        )

    logger.info(f"Loading model from {latest_checkpoint}")
    model = load_model_checkpoint(latest_checkpoint)

    # Extract importance based on model type
    if model_type_lower == 'randomforest':
        importance_df = extract_rf_importance(model, feature_names)
    elif model_type_lower == 'svr':
        importance_df = extract_svr_importance(model, feature_names)
    else:
        raise ValueError(f"Unsupported model type: {model_type}")

    # Get top features
    top_features = get_top_features(importance_df, n_top)

    # Save report
    report_base = results_path / f"{model_type_lower}_feature_importance"
    save_importance_report(top_features, model_type, report_base)

    logger.info(f"Feature importance analysis complete. Top {n_top} features saved.")

    return top_features, report_base.with_suffix('.json')


def main():
    """Main entry point for feature importance analysis."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract and rank top proteins by importance score"
    )
    parser.add_argument(
        '--model-type',
        choices=['RandomForest', 'SVR'],
        default='RandomForest',
        help='Model type to analyze (default: RandomForest)'
    )
    parser.add_argument(
        '--n-top',
        type=int,
        default=50,
        help='Number of top features to extract (default: 50)'
    )
    parser.add_argument(
        '--feature-file',
        type=str,
        default=None,
        help='Path to feature names CSV (default: data/processed/merged_matrix.csv)'
    )

    args = parser.parse_args()

    try:
        top_features, report_path = run_feature_importance_analysis(
            model_type=args.model_type,
            n_top=args.n_top,
            feature_file=Path(args.feature_file) if args.feature_file else None
        )

        print(f"Analysis complete. Report saved to: {report_path}")
        print(f"Top 5 features:")
        print(top_features.head().to_string(index=False))

    except Exception as e:
        logger.error(f"Feature importance analysis failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()