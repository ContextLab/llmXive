"""
Aggregate cross-validation metrics from individual fold results.

This module implements T029b: Aggregate cross-validation metrics.
It reads `cv_fold_results.json` and calculates mean and standard deviation
of MAE, RMSE, and Pearson correlation across folds.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np

from src.utils.logging import setup_logger, get_logger

logger = get_logger(__name__)

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def load_cv_fold_results(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load the cross-validation fold results from a JSON file.

    Args:
        file_path: Path to the cv_fold_results.json file.

    Returns:
        List of dictionaries containing metrics for each fold.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"CV fold results file not found: {file_path}")

    with open(file_path, 'r') as f:
        data = json.load(f)

    # Handle both list format and dict with 'folds' key
    if isinstance(data, dict) and 'folds' in data:
        return data['folds']
    elif isinstance(data, list):
        return data
    else:
        raise ValueError(f"Unexpected data format in {file_path}: expected list or dict with 'folds' key")

def aggregate_metrics(fold_results: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate mean and standard deviation of metrics across folds.

    Args:
        fold_results: List of dictionaries containing metrics for each fold.

    Returns:
        Dictionary with mean and std of MAE, RMSE, and Pearson correlation.
    """
    if not fold_results:
        raise ValueError("No fold results provided for aggregation")

    # Extract metrics from each fold
    maes = []
    rmses = []
    pearsons = []

    for i, fold in enumerate(fold_results):
        # Handle different possible key names
        mae = fold.get('mae') or fold.get('MAE') or fold.get('mean_absolute_error')
        rmse = fold.get('rmse') or fold.get('RMSE') or fold.get('root_mean_squared_error')
        pearson = fold.get('pearson') or fold.get('Pearson') or fold.get('pearson_correlation')

        if mae is None or rmse is None or pearson is None:
            logger.warning(f"Fold {i} missing required metrics. Skipping.")
            continue

        maes.append(float(mae))
        rmses.append(float(rmse))
        pearsons.append(float(pearson))

    if not maes:
        raise ValueError("No valid metrics found in fold results")

    # Calculate statistics
    metrics = {
        'mean_mae': float(np.mean(maes)),
        'std_mae': float(np.std(maes)),
        'mean_rmse': float(np.mean(rmses)),
        'std_rmse': float(np.std(rmses)),
        'mean_pearson': float(np.mean(pearsons)),
        'num_folds': len(maes)
    }

    return metrics

def save_metrics(metrics: Dict[str, float], output_path: Path) -> None:
    """
    Save aggregated metrics to a JSON file.

    Args:
        metrics: Dictionary of aggregated metrics.
        output_path: Path to save the metrics JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Saved aggregated metrics to {output_path}")

def run_aggregation(input_path: Optional[Path] = None, output_path: Optional[Path] = None) -> Dict[str, float]:
    """
    Run the full aggregation pipeline.

    Args:
        input_path: Path to cv_fold_results.json. Defaults to project standard path.
        output_path: Path for cv_metrics.json output. Defaults to project standard path.

    Returns:
        Dictionary of aggregated metrics.
    """
    if input_path is None:
        input_path = get_project_root() / 'data' / 'processed' / 'cv_fold_results.json'

    if output_path is None:
        output_path = get_project_root() / 'data' / 'processed' / 'cv_metrics.json'

    logger.info(f"Loading CV fold results from {input_path}")
    fold_results = load_cv_fold_results(input_path)

    logger.info(f"Aggregating metrics from {len(fold_results)} folds")
    metrics = aggregate_metrics(fold_results)

    logger.info(f"Saving aggregated metrics to {output_path}")
    save_metrics(metrics, output_path)

    return metrics

def main() -> None:
    """Main entry point for the aggregation script."""
    setup_logger(level=logging.INFO)

    try:
        metrics = run_aggregation()
        logger.info("Aggregation completed successfully")
        logger.info(f"Mean MAE: {metrics['mean_mae']:.4f} ± {metrics['std_mae']:.4f}")
        logger.info(f"Mean RMSE: {metrics['mean_rmse']:.4f} ± {metrics['std_rmse']:.4f}")
        logger.info(f"Mean Pearson: {metrics['mean_pearson']:.4f}")
    except Exception as e:
        logger.error(f"Aggregation failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
