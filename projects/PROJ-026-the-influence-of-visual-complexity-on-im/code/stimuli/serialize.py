"""
Serialization utilities for complexity scores.
"""
import os
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import get_project_root, get_data_path
from utils.logging import get_logger

logger: logging.Logger = get_logger(__name__)

def load_raw_complexity_scores(csv_path: str | Path) -> pd.DataFrame:
    """
    Load raw complexity scores from a CSV file.

    Args:
        csv_path: Path to the CSV file.

    Returns:
        pd.DataFrame: DataFrame containing the scores.
    """
    return pd.read_csv(csv_path)

def apply_categorization(df: pd.DataFrame, metric: str = "edge_density") -> pd.DataFrame:
    """
    Apply median split categorization to a DataFrame.

    Args:
        df: Input DataFrame.
        metric: Metric column to use for splitting.

    Returns:
        pd.DataFrame: DataFrame with added 'complexity_category' column.
    """
    if metric not in df.columns:
        raise ValueError(f"Metric column '{metric}' not found in DataFrame")

    median_val = df[metric].median()
    
    def assign_category(val: float) -> str:
        if pd.isna(val):
            return "Unknown"
        return "Low" if val <= median_val else "High"

    df = df.copy()
    df["complexity_category"] = df[metric].apply(assign_category)
    return df

def save_final_csv(df: pd.DataFrame, output_path: str | Path) -> None:
    """
    Save the final categorized scores to a CSV file.

    Args:
        df: DataFrame to save.
        output_path: Path to the output CSV file.
    """
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved final scores to {output_path}")
