import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

from .utils import safe_execute, log_and_reraise

logger = logging.getLogger(__name__)

def write_stability_metrics(metrics_df: pd.DataFrame, output_path: Path) -> None:
    """
    Write the aggregated stability metrics to a CSV file.
    
    Expected columns in metrics_df:
    - dataset_id
    - model_name
    - mean_accuracy
    - cv_accuracy
    - mean_f1
    - cv_f1
    - n_samples (optional, for context)
    - n_features (optional, for context)
    
    Args:
        metrics_df: DataFrame containing aggregated metrics.
        output_path: Path to the output CSV file.
    """
    if not isinstance(metrics_df, pd.DataFrame):
        raise TypeError("metrics_df must be a pandas DataFrame")
    
    required_columns = {'dataset_id', 'model_name', 'mean_accuracy', 'cv_accuracy', 'mean_f1', 'cv_f1'}
    if not required_columns.issubset(metrics_df.columns):
        missing = required_columns - set(metrics_df.columns)
        raise ValueError(f"metrics_df is missing required columns: {missing}")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        metrics_df.to_csv(output_path, index=False)
        logger.info(f"Wrote stability metrics to {output_path} ({len(metrics_df)} rows)")
    except Exception as e:
        log_and_reraise(e, "Failed to write stability metrics")

def write_correlation_results(correlation_df: pd.DataFrame, output_path: Path) -> None:
    """
    Write the correlation analysis results to a CSV file.
    
    Expected columns in correlation_df:
    - property_name (e.g., 'n_samples', 'n_features')
    - metric_type (e.g., 'cv_accuracy', 'cv_f1')
    - pearson_r
    - pearson_pvalue
    - spearman_rho (optional)
    - spearman_pvalue (optional)
    - residual_mean (optional, from regression analysis)
    
    Args:
        correlation_df: DataFrame containing correlation results.
        output_path: Path to the output CSV file.
    """
    if not isinstance(correlation_df, pd.DataFrame):
        raise TypeError("correlation_df must be a pandas DataFrame")
    
    required_columns = {'property_name', 'metric_type', 'pearson_r', 'pearson_pvalue'}
    if not required_columns.issubset(correlation_df.columns):
        missing = required_columns - set(correlation_df.columns)
        raise ValueError(f"correlation_df is missing required columns: {missing}")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        correlation_df.to_csv(output_path, index=False)
        logger.info(f"Wrote correlation results to {output_path} ({len(correlation_df)} rows)")
    except Exception as e:
        log_and_reraise(e, "Failed to write correlation results")

def write_regression_residuals(residuals_df: pd.DataFrame, output_path: Path) -> None:
    """
    Write regression residuals to a CSV file.
    
    Expected columns:
    - dataset_id
    - model_name
    - property_name (e.g., 'log_n_samples')
    - residual
    
    Args:
        residuals_df: DataFrame containing residuals.
        output_path: Path to the output CSV file.
    """
    if not isinstance(residuals_df, pd.DataFrame):
        raise TypeError("residuals_df must be a pandas DataFrame")
    
    required_columns = {'dataset_id', 'model_name', 'property_name', 'residual'}
    if not required_columns.issubset(residuals_df.columns):
        missing = required_columns - set(residuals_df.columns)
        raise ValueError(f"residuals_df is missing required columns: {missing}")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        residuals_df.to_csv(output_path, index=False)
        logger.info(f"Wrote regression residuals to {output_path} ({len(residuals_df)} rows)")
    except Exception as e:
        log_and_reraise(e, "Failed to write regression residuals")

def append_raw_evaluations(new_rows: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Append new evaluation rows to the raw evaluations CSV.
    
    Args:
        new_rows: List of dictionaries containing row data.
        output_path: Path to the raw evaluations CSV file.
    """
    if not new_rows:
        logger.debug("No rows to append to raw evaluations")
        return
    
    df = pd.DataFrame(new_rows)
    
    if output_path.exists():
        existing_df = pd.read_csv(output_path)
        combined_df = pd.concat([existing_df, df], ignore_index=True)
        combined_df.to_csv(output_path, index=False)
        logger.info(f"Appended {len(df)} rows to {output_path} (total: {len(combined_df)})")
    else:
        df.to_csv(output_path, index=False)
        logger.info(f"Created {output_path} with {len(df)} rows")

def write_raw_evaluations(rows: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write raw evaluation results to a CSV file.
    
    Expected columns:
    - dataset_id
    - model_name
    - fold_id
    - repeat_id
    - accuracy
    - f1_score
    
    Args:
        rows: List of dictionaries containing row data.
        output_path: Path to the output CSV file.
    """
    if not rows:
        logger.warning("No raw evaluation rows to write")
        return
    
    df = pd.DataFrame(rows)
    
    required_columns = {'dataset_id', 'model_name', 'fold_id', 'repeat_id', 'accuracy', 'f1_score'}
    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"Raw evaluation data is missing required columns: {missing}")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        df.to_csv(output_path, index=False)
        logger.info(f"Wrote {len(df)} raw evaluation rows to {output_path}")
    except Exception as e:
        log_and_reraise(e, "Failed to write raw evaluations")
