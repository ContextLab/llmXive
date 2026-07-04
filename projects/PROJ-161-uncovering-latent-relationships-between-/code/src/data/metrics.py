"""
Module for generating and persisting merge metrics for User Story 1.

This module calculates the success rate of merging antibiotic structure data
with resistance frequency data based on InChIKey matches.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd

from src.config import get_project_root
from src.data.schema import DataVersionFile


def calculate_merge_metrics(
    merged_df: pd.DataFrame, 
    total_requested: int
) -> Dict[str, Any]:
    """
    Calculate merge metrics based on the merged DataFrame.
    
    Args:
        merged_df: The merged DataFrame containing structure and resistance data.
        total_requested: The total number of compounds requested from the source.
        
    Returns:
        Dictionary containing merge metrics.
    """
    if merged_df is None or merged_df.empty:
        matches = 0
    else:
        # Count rows where resistance data is present (not NaN)
        # Assuming the resistance column is named 'resistance_frequency' or similar
        # We check for non-null values in any resistance-related column
        resistance_cols = [col for col in merged_df.columns if 'resistance' in col.lower()]
        
        if resistance_cols:
            # Use the first resistance column found for counting matches
            matches = merged_df[resistance_cols[0]].notna().sum()
        else:
            # Fallback: count all rows if no specific resistance column is found
            matches = len(merged_df)
    
    fraction = matches / total_requested if total_requested > 0 else 0.0
    
    return {
        "total_requested": total_requested,
        "matches": int(matches),
        "fraction": float(fraction),
        "total_merged_rows": int(len(merged_df)) if merged_df is not None else 0
    }


def save_merge_metrics(metrics: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Save merge metrics to a JSON file.
    
    Args:
        metrics: Dictionary containing merge metrics.
        output_path: Optional path to save the file. If None, uses default path.
        
    Returns:
        Path to the saved file.
    """
    if output_path is None:
        output_path = str(Path(get_project_root()) / "data" / "processed" / "merge_metrics.json")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)
    
    return output_path


def generate_merge_metrics_report(merged_df: pd.DataFrame, total_requested: int) -> str:
    """
    Generate and save the merge metrics report.
    
    This is the main entry point for generating the merge metrics report
    required by SC-001.
    
    Args:
        merged_df: The merged DataFrame from the pipeline.
        total_requested: Total number of compounds requested.
        
    Returns:
        Path to the generated metrics file.
    """
    metrics = calculate_merge_metrics(merged_df, total_requested)
    output_path = save_merge_metrics(metrics)
    return output_path
