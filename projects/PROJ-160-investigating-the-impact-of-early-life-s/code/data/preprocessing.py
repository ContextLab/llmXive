"""
Data preprocessing pipeline for the hippocampal subfield analysis.

This module handles data filtering, normalization, and transformation
required for the statistical analysis.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import numpy as np

from code.config import get_project_root, ensure_directories
from code.data.loaders import load_csv, save_dataframe


def filter_missing_ace(df: pd.DataFrame, ace_col: str = "ace_score") -> pd.DataFrame:
    """
    Filter out participants with missing ACE scores.

    Args:
        df: The input dataframe.
        ace_col: Name of the ACE score column.

    Returns:
        Filtered dataframe.
    """
    if ace_col not in df.columns:
        raise ValueError(f"ACE column '{ace_col}' not found")

    initial_count = len(df)
    df = df.dropna(subset=[ace_col])
    retained = len(df)

    logging.info(f"Filtered missing ACE: {initial_count} -> {retained}")
    return df


def filter_mri_quality(df: pd.DataFrame, quality_col: str = "mr_quality_flag") -> pd.DataFrame:
    """
    Filter out participants with poor MRI quality.

    Args:
        df: The input dataframe.
        quality_col: Name of the MRI quality column.

    Returns:
        Filtered dataframe.
    """
    if quality_col not in df.columns:
        logging.warning(f"Quality column '{quality_col}' not found, skipping filter")
        return df

    initial_count = len(df)
    # Assuming 0 or 'good' indicates good quality; adjust based on actual data
    df = df[df[quality_col] == 0]  # or df[df[quality_col] == 'good']
    retained = len(df)

    logging.info(f"Filtered MRI quality: {initial_count} -> {retained}")
    return df


def normalize_volumes(
    df: pd.DataFrame,
    subfields: List[str],
    icv_col: str = "ICV"
) -> pd.DataFrame:
    """
    Normalize subfield volumes by intracranial volume (ICV).

    Args:
        df: The input dataframe.
        subfields: List of subfield column names.
        icv_col: Name of the ICV column.

    Returns:
        Dataframe with normalized volumes.
    """
    df = df.copy()
    if icv_col not in df.columns:
        raise ValueError(f"ICV column '{icv_col}' not found")

    for subfield in subfields:
        norm_col = f"{subfield}_norm"
        if subfield in df.columns:
            # Avoid division by zero
            df[norm_col] = df[subfield] / (df[icv_col] + 1e-6)
            # Round to 4 decimal places
            df[norm_col] = df[norm_col].round(4)

    return df


def check_and_transform_ace(df: pd.DataFrame, ace_col: str = "ace_score") -> pd.DataFrame:
    """
    Check ACE score skewness and apply log transformation if needed.

    Args:
        df: The input dataframe.
        ace_col: Name of the ACE score column.

    Returns:
        Dataframe with transformed ACE scores if necessary.
    """
    if ace_col not in df.columns:
        return df

    skewness = df[ace_col].skew()

    if abs(skewness) > 1.0:
        logging.info(f"ACE skewness ({skewness:.2f}) > 1.0, applying log transformation")
        df = df.copy()
        # Add small constant to avoid log(0)
        df[f"{ace_col}_log"] = np.log1p(df[ace_col])
        return df

    logging.info(f"ACE skewness ({skewness:.2f}) within acceptable range, no transformation")
    return df


def flag_outliers(
    df: pd.DataFrame,
    col: str,
    std_threshold: float = 3.0
) -> pd.DataFrame:
    """
    Flag extreme outliers (>3 SD) in a column.

    Args:
        df: The input dataframe.
        col: Column name to check.
        std_threshold: Number of standard deviations for outlier flagging.

    Returns:
        Dataframe with an outlier flag column.
    """
    df = df.copy()
    mean = df[col].mean()
    std = df[col].std()

    lower = mean - (std_threshold * std)
    upper = mean + (std_threshold * std)

    flag_col = f"{col}_outlier"
    df[flag_col] = ((df[col] < lower) | (df[col] > upper)).astype(int)

    n_outliers = df[flag_col].sum()
    logging.info(f"Flagged {n_outliers} outliers in {col} (>{std_threshold} SD)")

    return df


def run_preprocessing_pipeline(input_path: Optional[str] = None) -> pd.DataFrame:
    """
    Run the full preprocessing pipeline.

    Args:
        input_path: Path to the input dataset. If None, uses default path.

    Returns:
        The preprocessed dataframe.
    """
    project_root = get_project_root()
    ensure_directories()

    if input_path is None:
        input_path = project_root / "data" / "raw" / "merged_data.csv"

    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logging.info(f"Loading data from {input_path}")
    df = load_csv(input_path)

    # 1. Filter missing ACE
    df = filter_missing_ace(df)

    # 2. Filter MRI quality
    df = filter_mri_quality(df)

    # 3. Normalize volumes
    subfields = ["CA3", "DG", "Subiculum"]
    df = normalize_volumes(df, subfields)

    # 4. Check and transform ACE
    df = check_and_transform_ace(df)

    # 5. Flag outliers
    df = flag_outliers(df, "ace_score")

    # 6. Save cleaned dataset
    output_path = project_root / "data" / "processed" / "cleaned_dataset.csv"
    save_dataframe(df, output_path)
    logging.info(f"Cleaned dataset saved to {output_path}")

    return df


def main() -> None:
    """
    Main entry point for the preprocessing module.
    """
    logging.basicConfig(level=logging.INFO)
    run_preprocessing_pipeline()


if __name__ == "__main__":
    main()
