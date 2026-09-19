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
        Dictionary containing 'r2', 'mae', and 'rmse'.
    """
    if len(y_true) == 0:
        return {'r2': 0.0, 'mae': 0.0, 'rmse': 0.0}

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    # R2 Score
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0:
        r2 = 0.0
    else:
        r2 = 1 - (ss_res / ss_tot)

    # MAE
    mae = np.mean(np.abs(y_true - y_pred))

    # RMSE
    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))

    return {'r2': float(r2), 'mae': float(mae), 'rmse': float(rmse)}

def aggregate_metrics(predictions_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate metrics by fold and model from a predictions dataframe.
    Expects columns: fold, model, prediction, target.

    Args:
        predictions_df: DataFrame with raw predictions.

    Returns:
        DataFrame with aggregated metrics: fold, model, r2, mae, rmse.
    """
    if predictions_df.empty:
        logger.warning("Empty predictions dataframe provided to aggregate_metrics.")
        return pd.DataFrame(columns=['fold', 'model', 'r2', 'mae', 'rmse'])

    results = []

    for (fold, model), group in predictions_df.groupby(['fold', 'model']):
        y_true = group['target'].values
        y_pred = group['prediction'].values
        metrics = calculate_metrics(y_true, y_pred)
        results.append({
            'fold': fold,
            'model': model,
            'r2': metrics['r2'],
            'mae': metrics['mae'],
            'rmse': metrics['rmse']
        })

    return pd.DataFrame(results)

def save_predictions(
    predictions_df: pd.DataFrame,
    output_path: str
) -> None:
    """
    Save predictions to a CSV file.
    Ensures the output has the required columns: fold, model, r2, mae, rmse, prediction, target.
    If the input lacks metric columns, they are calculated and appended.

    Args:
        predictions_df: DataFrame containing at least 'fold', 'model', 'prediction', 'target'.
        output_path: Path to the output CSV file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    required_cols = ['fold', 'model', 'prediction', 'target']
    if not all(col in predictions_df.columns for col in required_cols):
        missing = [c for c in required_cols if c not in predictions_df.columns]
        raise ValueError(f"Input predictions dataframe missing required columns: {missing}")

    df = predictions_df.copy()

    # Ensure we have the metric columns
    if not all(col in df.columns for col in ['r2', 'mae', 'rmse']):
        # Calculate metrics per row group (fold, model) and broadcast
        metric_groups = df.groupby(['fold', 'model'])
        metric_cache = {}
        for (fold, model), group in metric_groups:
            if (fold, model) not in metric_cache:
                metrics = calculate_metrics(group['target'].values, group['prediction'].values)
                metric_cache[(fold, model)] = metrics

        df['r2'] = df.apply(lambda row: metric_cache[(row['fold'], row['model'])]['r2'], axis=1)
        df['mae'] = df.apply(lambda row: metric_cache[(row['fold'], row['model'])]['mae'], axis=1)
        df['rmse'] = df.apply(lambda row: metric_cache[(row['fold'], row['model'])]['rmse'], axis=1)

    # Reorder columns to match specification exactly
    final_cols = ['fold', 'model', 'r2', 'mae', 'rmse', 'prediction', 'target']
    # Filter to only existing columns if any are missing (though logic above ensures they exist)
    existing_final_cols = [c for c in final_cols if c in df.columns]
    df = df[existing_final_cols]

    df.to_csv(output_path, index=False)
    logger.info(f"Saved predictions to {output_path} with {len(df)} rows.")

def main():
    """
    Entry point for testing the metrics module directly.
    Reads a sample predictions file if it exists, calculates metrics, and saves.
    """
    input_path = Path("data/processed/baseline_predictions.csv")
    output_path = Path("data/processed/predictions.csv")

    if not input_path.exists():
        logger.warning(f"Input file {input_path} not found. Skipping execution.")
        return

    logger.info(f"Loading predictions from {input_path}")
    df = pd.read_csv(input_path)
    save_predictions(df, str(output_path))
    logger.info("Done.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()