import os
import logging
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import pandas as pd
from sklearn.model_selection import KFold, cross_val_score, cross_validate
import shap
import xgboost as xgb
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def compare_model_performance(
    X: pd.DataFrame,
    y: pd.Series,
    models: Dict[str, Any],
    cv: int = 3
) -> pd.DataFrame:
    """
    Compare performance of multiple models using cross-validation.

    Args:
        X: Feature DataFrame
        y: Target Series
        models: Dictionary of model name to model instance
        cv: Number of CV folds

    Returns:
        DataFrame with model performance metrics
    """
    results = []
    for name, model in models.items():
        try:
            scores = cross_val_score(model, X, y, cv=cv, scoring='r2')
            results.append({
                'model': name,
                'mean_r2': scores.mean(),
                'std_r2': scores.std(),
                'min_r2': scores.min(),
                'max_r2': scores.max()
            })
        except Exception as e:
            logger.error(f"Error evaluating {name}: {e}")
            results.append({
                'model': name,
                'mean_r2': np.nan,
                'std_r2': np.nan,
                'min_r2': np.nan,
                'max_r2': np.nan,
                'error': str(e)
            })
    return pd.DataFrame(results)

def benjamini_hochberg_correction(
    p_values: List[float],
    alpha: float = 0.05
) -> Tuple[List[float], List[bool]]:
    """
    Apply Benjamini-Hochberg FDR correction to p-values.

    Args:
        p_values: List of raw p-values
        alpha: Significance level

    Returns:
        Tuple of (adjusted p-values, boolean significance flags)
    """
    n = len(p_values)
    if n == 0:
        return [], []

    # Sort p-values and keep original indices
    sorted_indices = np.argsort(p_values)
    sorted_pvals = np.array(p_values)[sorted_indices]

    # Calculate adjusted p-values
    adjusted_pvals = np.zeros(n)
    for i in range(n):
        adjusted_pvals[i] = sorted_pvals[i] * n / (i + 1)

    # Ensure monotonicity (cumulative minimum from the end)
    for i in range(n - 2, -1, -1):
        adjusted_pvals[i] = min(adjusted_pvals[i], adjusted_pvals[i + 1])

    # Clamp to [0, 1]
    adjusted_pvals = np.clip(adjusted_pvals, 0, 1)

    # Map back to original order
    final_adjusted_pvals = np.zeros(n)
    final_adjusted_pvals[sorted_indices] = adjusted_pvals

    # Determine significance
    significant = final_adjusted_pvals <= alpha

    return final_adjusted_pvals.tolist(), significant.tolist()

def perform_nested_permutation_test(
    X: pd.DataFrame,
    y: pd.Series,
    model_class: Any,
    n_permutations: int = 100,
    cv_folds: int = 3,
    feature_indices: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Perform nested permutation test to assess feature importance.

    Args:
        X: Feature DataFrame
        y: Target Series
        model_class: Model class to train
        n_permutations: Number of permutation iterations
        cv_folds: Number of CV folds
        feature_indices: Indices of features to test (None = all)

    Returns:
        Dictionary with test results
    """
    if feature_indices is None:
        feature_indices = list(range(X.shape[1]))

    # Get observed performance
    observed_scores = cross_val_score(
        model_class(), X, y, cv=cv_folds, scoring='r2'
    )
    observed_r2 = observed_scores.mean()

    # Generate null distribution
    null_distribution = []
    for _ in range(n_permutations):
        # Shuffle target
        y_permuted = y.sample(frac=1, replace=False).reset_index(drop=True)
        perm_scores = cross_val_score(
            model_class(), X, y_permuted, cv=cv_folds, scoring='r2'
        )
        null_distribution.append(perm_scores.mean())

    null_distribution = np.array(null_distribution)

    # Calculate p-value
    p_value = (np.sum(null_distribution >= observed_r2) + 1) / (n_permutations + 1)

    return {
        'observed_r2': observed_r2,
        'null_mean': null_distribution.mean(),
        'null_std': null_distribution.std(),
        'p_value': p_value,
        'null_distribution': null_distribution.tolist()
    }

def compute_shap_interaction_values(
    model: Any,
    X: pd.DataFrame,
    background_samples: Optional[pd.DataFrame] = None,
    max_samples: int = 1000
) -> Tuple[np.ndarray, List[str]]:
    """
    Compute SHAP interaction values for a model.

    Args:
        model: Trained model instance
        X: Feature DataFrame
        background_samples: Optional background dataset for explainer
        max_samples: Maximum number of samples to use for explanation

    Returns:
        Tuple of (interaction_values_array, feature_names)
    """
    # Limit samples if necessary
    if X.shape[0] > max_samples:
        sample_indices = np.random.choice(X.shape[0], max_samples, replace=False)
        X_sample = X.iloc[sample_indices]
    else:
        X_sample = X

    # Create background data if not provided
    if background_samples is None:
        background_samples = X_sample.sample(min(100, X_sample.shape[0]), replace=True)

    # Initialize SHAP explainer
    try:
        explainer = shap.Explainer(model, background_samples)
        shap_values = explainer(X_sample)
    except Exception as e:
        logger.warning(f"Standard SHAP explainer failed: {e}. Falling back to KernelExplainer.")
        explainer = shap.KernelExplainer(model, background_samples)
        shap_values = explainer.shap_values(X_sample, nsamples=100)

    # Handle different output formats
    if isinstance(shap_values, list):
        # For multi-output models, take first output
        shap_values = shap_values[0]

    # Check if we have interaction values
    if hasattr(shap_values, 'interaction_values') and shap_values.interaction_values is not None:
        interaction_values = shap_values.interaction_values
    elif isinstance(shap_values, np.ndarray) and len(shap_values.shape) == 3:
        # Some models return 3D arrays for interactions
        interaction_values = shap_values
    else:
        # Fallback: approximate interactions from main effects if not available
        # This is a simplification; real interactions require model-specific handling
        logger.warning("SHAP interaction values not directly available. Using main effects approximation.")
        if len(shap_values.shape) == 2:
            # Create dummy interaction matrix (diagonal only for main effects)
            n_samples, n_features = shap_values.shape
            interaction_values = np.zeros((n_samples, n_features, n_features))
            for i in range(n_features):
                interaction_values[:, i, i] = shap_values[:, i]
        else:
            raise ValueError("Could not extract SHAP values from model output")

    return interaction_values, X.columns.tolist()

def rank_features_by_shap(
    interaction_values: np.ndarray,
    feature_names: List[str]
) -> pd.DataFrame:
    """
    Rank features by mean absolute SHAP value.

    Args:
        interaction_values: 3D array of SHAP interaction values (samples, features, features)
        feature_names: List of feature names

    Returns:
        DataFrame with feature rankings
    """
    # Calculate mean absolute SHAP value for each feature
    # Sum interactions across all pairs for each feature
    n_samples, n_features, _ = interaction_values.shape

    # For each feature, sum absolute interactions with all other features
    shap_importance = np.zeros(n_features)
    for i in range(n_features):
        # Sum interactions where this feature is involved (row or column)
        interactions = np.abs(interaction_values[:, i, :]).sum(axis=1) + \
                       np.abs(interaction_values[:, :, i]).sum(axis=1)
        shap_importance[i] = interactions.mean()

    # Create ranking DataFrame
    ranking_df = pd.DataFrame({
        'feature': feature_names,
        'mean_abs_shap': shap_importance
    })

    # Sort by importance
    ranking_df = ranking_df.sort_values('mean_abs_shap', ascending=False).reset_index(drop=True)

    return ranking_df

def run_evaluation_pipeline(
    models: Dict[str, Any],
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    output_dir: str = "data/results",
    cv_folds: int = 3
) -> Dict[str, Any]:
    """
    Run complete evaluation pipeline including SHAP analysis.

    Args:
        models: Dictionary of trained models
        X_train: Training features
        y_train: Training target
        X_test: Test features
        y_test: Test target
        output_dir: Directory to save results
        cv_folds: Number of CV folds for performance comparison

    Returns:
        Dictionary with all evaluation results
    """
    os.makedirs(output_dir, exist_ok=True)

    results = {}

    # 1. Compare model performance
    logger.info("Comparing model performance...")
    performance_df = compare_model_performance(
        pd.concat([X_train, X_test]),
        pd.concat([y_train, y_test]),
        models,
        cv=cv_folds
    )
    results['performance'] = performance_df.to_dict()
    performance_df.to_csv(os.path.join(output_dir, 'model_performance.csv'), index=False)

    # 2. SHAP analysis for each model
    logger.info("Computing SHAP values...")
    shap_results = {}
    for name, model in models.items():
        try:
            logger.info(f"Computing SHAP for {name}...")
            interaction_values, feature_names = compute_shap_interaction_values(
                model, X_test, max_samples=500
            )
            ranking_df = rank_features_by_shap(interaction_values, feature_names)

            shap_results[name] = {
                'ranking': ranking_df.to_dict(),
                'interaction_shape': list(interaction_values.shape)
            }

            # Save ranking
            ranking_df.to_csv(os.path.join(output_dir, f'{name}_shap_ranking.csv'), index=False)

            # Save top 10 features
            top_features = ranking_df.head(10)['feature'].tolist()
            logger.info(f"Top 10 features for {name}: {top_features}")

        except Exception as e:
            logger.error(f"SHAP analysis failed for {name}: {e}")
            shap_results[name] = {'error': str(e)}

    results['shap'] = shap_results

    # 3. Save summary
    summary_path = os.path.join(output_dir, 'evaluation_summary.json')
    import json
    # Convert numpy types for JSON serialization
    def json_serialize(obj):
        if isinstance(obj, np.integer): return int(obj)
        if isinstance(obj, np.floating): return float(obj)
        if isinstance(obj, np.ndarray): return obj.tolist()
        raise TypeError(f"Type {type(obj)} not serializable")

    with open(summary_path, 'w') as f:
        json.dump(results, f, default=json_serialize, indent=2)

    logger.info(f"Evaluation complete. Results saved to {output_dir}")
    return results