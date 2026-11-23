"""
Metrics calculation and prediction saving utilities.
"""
import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Calculate R2, MAE, and RMSE for a set of predictions.

    Args:
        y_true: Array of true target values.
        y_pred: Array of predicted values.

    Returns:
        Dictionary with keys 'r2', 'mae', 'rmse'.
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    # R-squared
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0

    # MAE
    mae = np.mean(np.abs(y_true - y_pred))

    # RMSE
    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))

    return {
        'r2': float(r2),
        'mae': float(mae),
        'rmse': float(rmse)
    }


def aggregate_metrics(metrics_list: List[Dict[str, any]]) -> Dict[str, float]:
    """
    Aggregate metrics from multiple folds.

    Args:
        metrics_list: List of metric dictionaries from each fold.

    Returns:
        Dictionary with mean and std for each metric.
    """
    if not metrics_list:
        return {}

    r2s = [m['r2'] for m in metrics_list]
    maes = [m['mae'] for m in metrics_list]
    rmses = [m['rmse'] for m in metrics_list]

    return {
        'r2_mean': float(np.mean(r2s)),
        'r2_std': float(np.std(r2s)),
        'mae_mean': float(np.mean(maes)),
        'mae_std': float(np.std(maes)),
        'rmse_mean': float(np.mean(rmses)),
        'rmse_std': float(np.std(rmses))
    }


def save_predictions(
    predictions_df: pd.DataFrame,
    output_path: str,
    columns: Optional[List[str]] = None
) -> None:
    """
    Save predictions to a CSV file.

    The expected schema for the output file is:
    [fold, model, r2, mae, rmse, prediction, target]

    Args:
        predictions_df: DataFrame containing prediction data.
        output_path: Path to the output CSV file.
        columns: Optional list of columns to include. If None, all columns are used.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    required_cols = ['fold', 'model', 'r2', 'mae', 'rmse', 'prediction', 'target']
    
    # Ensure all required columns exist
    missing_cols = set(required_cols) - set(predictions_df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns in predictions_df: {missing_cols}")

    if columns:
        df_to_save = predictions_df[columns]
    else:
        df_to_save = predictions_df[required_cols]

    df_to_save.to_csv(output_path, index=False)
    logger.info(f"Saved predictions to {output_path} with {len(df_to_save)} rows")


def main():
    """
    Main entry point for metrics module.
    This is a placeholder for direct execution if needed.
    """
    logger.info("Metrics module loaded successfully.")


if __name__ == "__main__":
    main()
