"""
Module: code/modeling/group_rare.py

Task T015a: Group rare space groups (<20 samples) into an 'Other' category.

Reads: data/processed/crystal_dataset.csv
Writes: data/processed/grouped_dataset.csv

This script enforces the constraint that rare space groups must be grouped
PRIOR to splitting to prevent data leakage and ensure model robustness.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd

# Import project utilities
from config import get_path_absolute, ensure_directory, get_project_root
from logging_config import get_logger, log_event

# Constants
RARE_THRESHOLD = 20
RARE_LABEL = "Other"
SPACE_GROUP_COLUMN = "space_group"
INPUT_FILE_NAME = "crystal_dataset.csv"
OUTPUT_FILE_NAME = "grouped_dataset.csv"

logger = get_logger(__name__)


def load_dataset(input_path: Path) -> pd.DataFrame:
    """Load the crystal dataset from CSV."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input dataset not found at {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded dataset with {len(df)} rows from {input_path}")
    return df


def group_rare_space_groups(df: pd.DataFrame, threshold: int = RARE_THRESHOLD) -> pd.DataFrame:
    """
    Group rare space groups into a single 'Other' category.
    
    Args:
        df: Input DataFrame containing space group information.
        threshold: Minimum number of samples required for a space group to remain distinct.
        
    Returns:
        DataFrame with 'space_group' column updated.
    """
    if SPACE_GROUP_COLUMN not in df.columns:
        raise ValueError(f"Expected column '{SPACE_GROUP_COLUMN}' not found in dataset.")
    
    # Count occurrences
    value_counts = df[SPACE_GROUP_COLUMN].value_counts()
    logger.info(f"Space group distribution (top 10):\n{value_counts.head(10)}")
    
    # Identify rare space groups
    rare_groups = value_counts[value_counts < threshold].index.tolist()
    
    if not rare_groups:
        logger.info(f"No space groups found below threshold {threshold}. No grouping required.")
        return df.copy()
    
    logger.info(f"Found {len(rare_groups)} rare space groups (count < {threshold}): {rare_groups[:5]}...")
    
    # Create a copy to avoid SettingWithCopyWarning
    df_grouped = df.copy()
    
    # Replace rare groups with 'Other'
    df_grouped.loc[df_grouped[SPACE_GROUP_COLUMN].isin(rare_groups), SPACE_GROUP_COLUMN] = RARE_LABEL
    
    # Log the change
    new_counts = df_grouped[SPACE_GROUP_COLUMN].value_counts()
    logger.info(f"Updated space group distribution (top 10):\n{new_counts.head(10)}")
    
    return df_grouped


def save_dataset(df: pd.DataFrame, output_path: Path) -> None:
    """Save the processed dataset to CSV."""
    ensure_directory(output_path)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved grouped dataset to {output_path} with {len(df)} rows.")


def run_grouping(input_path: Optional[Path] = None, output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Main execution function to group rare space groups.
    
    Returns:
        Dictionary containing execution summary.
    """
    # Resolve paths
    if input_path is None:
        project_root = get_project_root()
        input_path = project_root / "data" / "processed" / INPUT_FILE_NAME
    
    if output_path is None:
        project_root = get_project_root()
        output_path = project_root / "data" / "processed" / OUTPUT_FILE_NAME
    
    log_event(logger, "START", "Grouping rare space groups", {"input": str(input_path)})
    
    try:
        # Load data
        df = load_dataset(input_path)
        
        # Group rare space groups
        df_grouped = group_rare_space_groups(df, threshold=RARE_THRESHOLD)
        
        # Save result
        save_dataset(df_grouped, output_path)
        
        summary = {
            "status": "success",
            "input_rows": len(df),
            "output_rows": len(df_grouped),
            "output_path": str(output_path),
            "threshold_used": RARE_THRESHOLD,
            "rare_label": RARE_LABEL
        }
        
        log_event(logger, "SUCCESS", "Grouping completed", summary)
        return summary
        
    except Exception as e:
        log_event(logger, "ERROR", "Grouping failed", {"error": str(e)})
        raise


def main() -> None:
    """Entry point for the script."""
    # Setup logging
    setup_logger = get_logger(__name__)
    log_event(setup_logger, "INFO", "Script started", {"script": "group_rare.py"})
    
    try:
        result = run_grouping()
        print(json.dumps(result, indent=2))
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        log_event(setup_logger, "ERROR", "Script failed", {"error": str(e)})
        sys.exit(1)


if __name__ == "__main__":
    main()
