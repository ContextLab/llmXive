"""
Outlier Handling Module for Transition State Graphs.

This module implements logic to detect samples with coordination numbers > 6,
flag them for exclusion from training, but retain them in the test set.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd
import numpy as np

# Import existing utilities from the project
from src.utils.logging import get_logger, log_progress
from src.utils.config import get_project_root

# Constants
COORDINATION_THRESHOLD = 6
OUTLIER_COLUMN = "is_outlier"
COORD_COLUMN = "coordination_number"

logger = get_logger(__name__)

def load_graphs_with_metadata(graphs_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the processed graphs dataframe.
    Expects the file to exist at data/processed/graphs.parquet.
    """
    if graphs_path is None:
        project_root = get_project_root()
        graphs_path = project_root / "data" / "processed" / "graphs.parquet"

    if not graphs_path.exists():
        raise FileNotFoundError(f"Graphs file not found at {graphs_path}. "
                                "Run graph_construction.py first.")

    logger.info(f"Loading graphs from {graphs_path}")
    df = pd.read_parquet(graphs_path)

    # Ensure necessary columns exist (coordination number might be added by graph_construction)
    if COORD_COLUMN not in df.columns:
        # Fallback: if not present, we assume it needs to be computed or is missing.
        # Based on T016, coordination number should be calculated.
        # If strictly missing, we raise an error to prevent silent failure.
        raise ValueError(f"Column '{COORD_COLUMN}' not found in graphs. "
                         "Ensure graph_construction.py calculates coordination numbers.")

    return df

def compute_coordination_numbers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure coordination numbers are present.
    If the column exists, return as is. If not, this function assumes
    the data should have been pre-computed.
    """
    if COORD_COLUMN not in df.columns:
        # In a real pipeline, we might re-calculate here if we had raw geometry access,
        # but T016 should have done this. We raise if missing to enforce T016 completion.
        raise RuntimeError("Coordination numbers missing. T016 must complete first.")
    return df

def flag_outliers(df: pd.DataFrame, threshold: int = COORDINATION_THRESHOLD) -> pd.DataFrame:
    """
    Flag samples with coordination number > threshold as outliers.
    Logic:
      - is_outlier = True if coordination_number > threshold
      - These samples are flagged for EXCLUSION from training.
      - They are RETAINED in the dataset for potential test set inclusion.
    """
    logger.info(f"Flagging outliers with coordination number > {threshold}")

    df = df.copy()
    df[OUTLIER_COLUMN] = df[COORD_COLUMN] > threshold

    outlier_count = df[OUTLIER_COLUMN].sum()
    total_count = len(df)
    log_progress(logger, "Outlier Detection", {
        "total_samples": total_count,
        "outliers_flagged": int(outlier_count),
        "outlier_percentage": float(outlier_count / total_count * 100) if total_count > 0 else 0.0
    })

    return df

def save_outlier_summary(df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    """
    Save a summary of outlier handling to JSON.
    Schema: {
      "total_samples": int,
      "outliers_count": int,
      "outliers_percentage": float,
      "threshold": int,
      "strategy": "exclude_train_retain_test"
    }
    """
    if output_path is None:
        project_root = get_project_root()
        output_path = project_root / "data" / "processed" / "outlier_summary.json"

    summary = {
        "total_samples": int(len(df)),
        "outliers_count": int(df[OUTLIER_COLUMN].sum()),
        "outliers_percentage": float(df[OUTLIER_COLUMN].mean() * 100),
        "threshold": COORDINATION_THRESHOLD,
        "strategy": "exclude_train_retain_test",
        "outlier_indices": df[df[OUTLIER_COLUMN]].index.tolist()
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Saved outlier summary to {output_path}")
    return output_path

def save_flagged_graphs(df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    """
    Save the dataframe with the outlier flag to a new parquet file.
    This file is used for downstream splitting (T028) and training (T024).
    """
    if output_path is None:
        project_root = get_project_root()
        output_path = project_root / "data" / "processed" / "graphs_flagged.parquet"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved flagged graphs to {output_path}")
    return output_path

def run_outlier_handling(
    input_path: Optional[Path] = None,
    output_graphs_path: Optional[Path] = None,
    output_summary_path: Optional[Path] = None,
    threshold: int = COORDINATION_THRESHOLD
) -> Tuple[pd.DataFrame, Path, Path]:
    """
    Main entry point for outlier handling.
    1. Load graphs.
    2. Flag outliers (coordination > threshold).
    3. Save summary and flagged graphs.
    """
    df = load_graphs_with_metadata(input_path)
    df = flag_outliers(df, threshold=threshold)

    summary_path = save_outlier_summary(df, output_summary_path)
    graphs_path = save_flagged_graphs(df, output_graphs_path)

    return df, summary_path, graphs_path

def main():
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting Outlier Handling (T018)")

    try:
        df, summary_path, graphs_path = run_outlier_handling()
        logger.info(f"Outlier handling complete. Summary: {summary_path}, Graphs: {graphs_path}")
    except FileNotFoundError as e:
        logger.error(f"Data not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during outlier handling: {e}")
        raise

if __name__ == "__main__":
    main()