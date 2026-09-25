import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
from src.config import get_project_root

def calculate_merge_metrics(merged_df: pd.DataFrame, total_requested: int) -> Dict[str, Any]:
    """
    Calculate merge metrics from the merged DataFrame and total requested count.
    
    Args:
        merged_df: The merged DataFrame.
        total_requested: The total number of structures requested.
        
    Returns:
        Dictionary with metrics.
    """
    if merged_df.empty or total_requested == 0:
        return {
            'total_requested': 0,
            'matches': 0,
            'fraction': 0.0,
            'total_merged_rows': 0
        }
    
    # Identify resistance columns (columns not in original structure set)
    # This is a heuristic; in a real scenario, we'd know the exact column names.
    # Assuming 'inchi_key' and 'canonical_smiles' are the only non-resistance cols from structure
    # We'll count rows where resistance data is present.
    # If we don't know the resistance columns, we assume any new column implies resistance.
    # For robustness, we check for non-NA in any column that isn't 'inchi_key' or 'canonical_smiles'
    # or any other known structure-only column.
    
    # A safer approach: if the merge was done correctly, we can check for NA in the resistance column
    # passed to the merge. Since this function is generic, we'll count rows with any non-NA value
    # in columns that are not 'inchi_key' and 'canonical_smiles'.
    
    structure_cols = {'inchi_key', 'canonical_smiles'}
    resistance_cols = [c for c in merged_df.columns if c not in structure_cols]
    
    if not resistance_cols:
        matches = 0
    else:
        # Count rows where at least one resistance column is not NA
        # Or, if we assume all resistance columns should be populated together, check one.
        # Let's check the first resistance column.
        first_res_col = resistance_cols[0]
        matches = merged_df[first_res_col].notna().sum()
    
    fraction = matches / total_requested if total_requested > 0 else 0.0
    
    return {
        'total_requested': total_requested,
        'matches': int(matches),
        'fraction': float(fraction),
        'total_merged_rows': len(merged_df)
    }


def save_merge_metrics(metrics: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Save merge metrics to a JSON file.
    
    Args:
        metrics: The metrics dictionary.
        output_path: Optional path to save to. Defaults to data/processed/merge_metrics.json.
        
    Returns:
        The path where the file was saved.
    """
    if output_path is None:
        root = get_project_root()
        processed_path = root / "data" / "processed"
        processed_path.mkdir(parents=True, exist_ok=True)
        output_path = processed_path / "merge_metrics.json"
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    return output_path


def generate_merge_metrics_report(metrics: Dict[str, Any]) -> str:
    """
    Generate a human-readable report string from metrics.
    """
    lines = [
        "=== Merge Metrics Report ===",
        f"Total Structures Requested: {metrics['total_requested']}",
        f"Matches with Resistance Data: {metrics['matches']}",
        f"Match Fraction: {metrics['fraction']:.2%}",
        f"Total Merged Rows: {metrics['total_merged_rows']}"
    ]
    return "\n".join(lines)
