import os
import json
import pickle
from typing import Dict, Any, Tuple, List, Optional
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from scipy.stats import pearsonr
import logging

logger = logging.getLogger(__name__)

def train_ridge_model(
    X: np.ndarray,
    y: np.ndarray,
    alpha: float = 1.0,
    random_state: int = 42
) -> Tuple[Ridge, Dict[str, float]]:
    """
    Train a Ridge Regression model and compute metrics.

    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        alpha: Regularization strength
        random_state: Random seed for reproducibility

    Returns:
        Tuple of (trained model, metrics dict with 'rmse', 'pearson_r')
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state
    )

    model = Ridge(alpha=alpha)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    pearson_r, _ = pearsonr(y_test, y_pred)

    metrics = {
        'rmse': float(rmse),
        'pearson_r': float(pearson_r)
    }

    return model, metrics

def compute_bonferroni_pvalue(p_value: float, n_tests: int) -> float:
    """
    Compute Bonferroni-adjusted p-value.

    Args:
        p_value: Raw p-value
        n_tests: Number of hypothesis tests performed

    Returns:
        Adjusted p-value (capped at 1.0)
    """
    return min(p_value * n_tests, 1.0)

def compute_benjamini_hochberg_pvalues(p_values: List[float]) -> List[float]:
    """
    Compute Benjamini-Hochberg (FDR) adjusted p-values.

    Args:
        p_values: List of raw p-values

    Returns:
        List of adjusted p-values
    """
    n = len(p_values)
    if n == 0:
        return []

    indexed_pvals = sorted(enumerate(p_values), key=lambda x: x[1])
    adjusted = [0.0] * n
    last_idx = indexed_pvals[-1][0]
    adjusted[last_idx] = min(p_values[last_idx] * n, 1.0)

    for i in range(n - 2, -1, -1):
        idx, pval = indexed_pvals[i]
        adjusted[idx] = min(pval * n / (i + 1), adjusted[indexed_pvals[i + 1][0]])

    return adjusted

def run_sensitivity_analysis(
    data_path: str,
    output_path: str,
    alpha_range: Optional[List[float]] = None,
    feature_col: str = 'atom_entropy',
    target_col: str = 'logS'
) -> Dict[str, Any]:
    """
    Perform sensitivity analysis by sweeping across alpha values.

    Args:
        data_path: Path to the enriched CSV file
        output_path: Path to save the sensitivity sweep JSON report
        alpha_range: List of alpha values to sweep (low, medium, high)
        feature_col: Name of the entropy feature column
        target_col: Name of the target property column

    Returns:
        Dictionary containing sensitivity metrics
    """
    if alpha_range is None:
        # Default sweep: low (0.1), medium (1.0), high (10.0)
        alpha_range = [0.1, 1.0, 10.0]

    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)

    # Drop rows with missing values in feature or target
    df = df.dropna(subset=[feature_col, target_col])

    if len(df) == 0:
        raise ValueError("No valid data points after dropping NaNs.")

    X = df[[feature_col]].values
    y = df[target_col].values

    results = {
        'alpha_values': alpha_range,
        'metrics': []
    }

    rmse_list = []
    pearson_list = []

    for alpha in alpha_range:
        logger.info(f"Training model with alpha={alpha}")
        model, metrics = train_ridge_model(X, y, alpha=alpha)

        result_entry = {
            'alpha': alpha,
            'rmse': metrics['rmse'],
            'pearson_r': metrics['pearson_r']
        }
        results['metrics'].append(result_entry)
        rmse_list.append(metrics['rmse'])
        pearson_list.append(metrics['pearson_r'])

    # Calculate stability metrics
    rmse_mean = np.mean(rmse_list)
    rmse_range = (max(rmse_list) - min(rmse_list)) / rmse_mean if rmse_mean != 0 else 0.0

    pearson_mean = np.mean(pearson_list)
    pearson_range = (max(pearson_list) - min(pearson_list)) / abs(pearson_mean) if pearson_mean != 0 else 0.0

    stability_metrics = {
        'rmse_relative_range': float(rmse_range),
        'pearson_relative_range': float(pearson_range),
        'rmse_mean': float(rmse_mean),
        'pearson_mean': float(pearson_mean),
        'rmse_min': float(min(rmse_list)),
        'rmse_max': float(max(rmse_list)),
        'pearson_min': float(min(pearson_list)),
        'pearson_max': float(max(pearson_list))
    }

    results['stability_metrics'] = stability_metrics

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Sensitivity analysis results saved to {output_path}")

    return results

def train_models_from_csv(
    data_path: str,
    model_dir: str,
    report_path: str,
    feature_cols: List[str],
    target_cols: List[str],
    alpha: float = 1.0
) -> Dict[str, Any]:
    """
    Train Ridge models for multiple targets and save artifacts.

    Args:
        data_path: Path to enriched CSV
        model_dir: Directory to save model pickles
        report_path: Path to save JSON report
        feature_cols: List of feature column names
        target_cols: List of target column names
        alpha: Ridge regularization parameter

    Returns:
        Dictionary of metrics for all models
    """
    os.makedirs(model_dir, exist_ok=True)

    df = pd.read_csv(data_path)
    df = df.dropna(subset=feature_cols + target_cols)

    X = df[feature_cols].values

    all_metrics = {}

    for target in target_cols:
        y = df[target].values
        model, metrics = train_ridge_model(X, y, alpha=alpha)

        model_path = os.path.join(model_dir, f'ridge_{target}.pkl')
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)

        all_metrics[target] = metrics
        logger.info(f"Trained model for {target}: RMSE={metrics['rmse']:.4f}, r={metrics['pearson_r']:.4f}")

    with open(report_path, 'w') as f:
        json.dump(all_metrics, f, indent=2)

    return all_metrics

def run_full_analysis(
    data_path: str,
    model_dir: str,
    report_path: str,
    sensitivity_path: str,
    feature_cols: List[str],
    target_cols: List[str],
    alpha: float = 1.0
) -> Dict[str, Any]:
    """
    Run full analysis: train models and perform sensitivity sweep.

    Args:
        data_path: Path to enriched CSV
        model_dir: Directory for model files
        report_path: Path for main metrics JSON
        sensitivity_path: Path for sensitivity sweep JSON
        feature_cols: Feature columns
        target_cols: Target columns
        alpha: Default alpha for model training

    Returns:
        Combined analysis results
    """
    # Train main models
    metrics = train_models_from_csv(
        data_path, model_dir, report_path, feature_cols, target_cols, alpha
    )

    # Run sensitivity analysis for each target using the primary feature
    sensitivity_results = {}
    for target in target_cols:
        logger.info(f"Running sensitivity analysis for {target}")
        sweep_data = run_sensitivity_analysis(
            data_path=data_path,
            output_path=sensitivity_path.replace('.json', f'_{target}.json'),
            alpha_range=[0.1, 1.0, 10.0],
            feature_col=feature_cols[0],
            target_col=target
        )
        sensitivity_results[target] = sweep_data['stability_metrics']

    return {
        'model_metrics': metrics,
        'sensitivity_analysis': sensitivity_results
    }
