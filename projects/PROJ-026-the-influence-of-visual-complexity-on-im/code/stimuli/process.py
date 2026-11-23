"""
Stimuli processing pipeline: batch processing and categorization.
"""
import os
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import numpy as np

from stimuli.batch_processor import process_stimuli_vectorized, load_images_batch
from utils.logging import get_logger

logger: logging.Logger = get_logger(__name__)

def process_stimuli_batch(input_dir: str | Path, output_csv: str | Path) -> None:
    """
    Run the full batch processing pipeline for a directory of images.

    Args:
        input_dir: Directory containing input images.
        output_csv: Path to the output CSV file.
    """
    image_paths = load_images_batch(input_dir)
    process_stimuli_vectorized(image_paths, output_csv)

def categorize_complexity(input_csv: str | Path, output_csv: str | Path, metric: str = "edge_density") -> None:
    """
    Categorize images into 'Low' and 'High' complexity based on a median split.

    Args:
        input_csv: Path to the raw metrics CSV.
        output_csv: Path to the output CSV with categories.
        metric: The metric column to use for splitting (default: edge_density).
    """
    if not Path(input_csv).exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")

    df = pd.read_csv(input_csv)

    if metric not in df.columns:
        raise ValueError(f"Metric column '{metric}' not found in {input_csv}")

    # Handle NaN values in the metric column
    if df[metric].isna().all():
        logger.warning("All values in metric column are NaN. Cannot categorize.")
        df["complexity_category"] = "Unknown"
    else:
        median_val = df[metric].median()
        
        def assign_category(val: float) -> str:
            if pd.isna(val):
                return "Unknown"
            return "Low" if val <= median_val else "High"

        df["complexity_category"] = df[metric].apply(assign_category)

    # Ensure output directory exists
    out_path = Path(output_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)
    
    counts = df["complexity_category"].value_counts()
    logger.info(f"Categorization complete. Low: {counts.get('Low', 0)}, High: {counts.get('High', 0)}")
