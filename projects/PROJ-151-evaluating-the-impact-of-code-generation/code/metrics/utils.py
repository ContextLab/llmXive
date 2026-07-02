"""
Utility functions for metric aggregation and checksum calculation.

This module provides helper functions to aggregate metric dataframes
and calculate checksums for data integrity verification.
"""
import pandas as pd
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from config import set_global_seed


def calculate_dataframe_checksum(df: pd.DataFrame, algorithm: str = "sha256") -> str:
    """
    Calculate a deterministic checksum of a pandas DataFrame.

    The checksum is based on the sorted index and columns to ensure
    consistency regardless of row order.

    Args:
        df: The pandas DataFrame to checksum.
        algorithm: The hashing algorithm to use ('sha256', 'md5', etc.).

    Returns:
        Hexadecimal string representation of the checksum.
    """
    # Sort index and columns for deterministic ordering
    df_sorted = df.reset_index(drop=True)
    df_sorted = df_sorted.reindex(sorted(df_sorted.columns), axis=1)

    # Convert to JSON with sorted keys for deterministic string representation
    json_str = df_sorted.to_json(orient='records', date_format='iso', sort_keys=True)

    # Calculate hash
    hasher = hashlib.new(algorithm)
    hasher.update(json_str.encode('utf-8'))

    return hasher.hexdigest()


def calculate_file_checksum(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Calculate the checksum of a file.

    Args:
        file_path: Path to the file.
        algorithm: The hashing algorithm to use.

    Returns:
        Hexadecimal string representation of the checksum.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    hasher = hashlib.new(algorithm)
    with open(path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)

    return hasher.hexdigest()


def aggregate_metrics_by_project(
    df: pd.DataFrame,
    project_id_col: str = "project_id",
    metrics_cols: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Aggregate metric columns by project ID.

    Args:
        df: Input DataFrame containing metrics.
        project_id_col: Name of the column containing project IDs.
        metrics_cols: List of metric column names to aggregate.
                      If None, all numeric columns except project_id_col are used.

    Returns:
        Aggregated DataFrame with mean, std, min, max for each metric per project.
    """
    if df.empty:
        return pd.DataFrame()

    if metrics_cols is None:
        # Select all numeric columns except the project_id column
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        metrics_cols = [col for col in numeric_cols if col != project_id_col]

    if not metrics_cols:
        return df.groupby(project_id_col).size().reset_index(name='count')

    # Define aggregation functions
    agg_funcs = {col: ['mean', 'std', 'min', 'max', 'count'] for col in metrics_cols}

    # Perform aggregation
    aggregated = df.groupby(project_id_col)[metrics_cols].agg(agg_funcs)

    # Flatten column names
    aggregated.columns = [f"{col}_{func}" for col, func in aggregated.columns]
    aggregated = aggregated.reset_index()

    return aggregated


def aggregate_metrics_by_origin(
    df: pd.DataFrame,
    origin_col: str = "origin",
    metrics_cols: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Aggregate metric columns by origin (Human vs LLM).

    Args:
        df: Input DataFrame containing metrics.
        origin_col: Name of the column containing origin labels.
                    Expected values: 'human', 'llm', 'generated', etc.
        metrics_cols: List of metric column names to aggregate.

    Returns:
        Aggregated DataFrame with statistics per origin.
    """
    if df.empty:
        return pd.DataFrame()

    if metrics_cols is None:
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        metrics_cols = [col for col in numeric_cols if col != origin_col]

    if not metrics_cols:
        return df.groupby(origin_col).size().reset_index(name='count')

    agg_funcs = {col: ['mean', 'std', 'min', 'max', 'count'] for col in metrics_cols}
    aggregated = df.groupby(origin_col)[metrics_cols].agg(agg_funcs)

    aggregated.columns = [f"{col}_{func}" for col, func in aggregated.columns]
    aggregated = aggregated.reset_index()

    return aggregated


def compute_summary_statistics(
    df: pd.DataFrame,
    metric_name: str
) -> Dict[str, Any]:
    """
    Compute summary statistics for a specific metric column.

    Args:
        df: Input DataFrame.
        metric_name: Name of the metric column.

    Returns:
        Dictionary with count, mean, std, min, max, median, and missing_count.
    """
    if metric_name not in df.columns:
        raise ValueError(f"Column '{metric_name}' not found in DataFrame.")

    series = df[metric_name]
    non_null = series.dropna()

    return {
        "metric": metric_name,
        "count": len(non_null),
        "mean": float(non_null.mean()) if len(non_null) > 0 else None,
        "std": float(non_null.std()) if len(non_null) > 1 else None,
        "min": float(non_null.min()) if len(non_null) > 0 else None,
        "max": float(non_null.max()) if len(non_null) > 0 else None,
        "median": float(non_null.median()) if len(non_null) > 0 else None,
        "missing_count": int(series.isna().sum())
    }


def validate_metrics_schema(df: pd.DataFrame, required_columns: List[str]) -> bool:
    """
    Validate that a DataFrame contains all required metric columns.

    Args:
        df: Input DataFrame.
        required_columns: List of required column names.

    Returns:
        True if all required columns are present, False otherwise.
    """
    missing = set(required_columns) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return True


def export_metrics_to_json(
    df: pd.DataFrame,
    output_path: Union[str, Path],
    include_checksum: bool = True
) -> Dict[str, Any]:
    """
    Export metrics DataFrame to JSON with optional checksum.

    Args:
        df: DataFrame to export.
        output_path: Path to save the JSON file.
        include_checksum: Whether to include a checksum in the metadata.

    Returns:
        Metadata dictionary including checksum and timestamp.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Prepare data
    data = df.to_dict(orient='records')

    # Build metadata
    metadata = {
        "exported_at": datetime.utcnow().isoformat(),
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": df.columns.tolist()
    }

    if include_checksum:
        metadata["checksum"] = calculate_dataframe_checksum(df)

    # Combine metadata and data
    export_data = {
        "metadata": metadata,
        "data": data
    }

    # Write to file
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, default=str)

    return metadata