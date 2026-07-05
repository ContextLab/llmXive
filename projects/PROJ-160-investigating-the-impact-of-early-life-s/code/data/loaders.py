"""
Data loading utilities for the hippocampal subfield analysis pipeline.

This module provides functions to load CSV and TSV files, handle
ABCD Study specific data formats, and merge datasets.
"""

import csv
import os
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import pandas as pd
import numpy as np

from code.config import get_project_root, ensure_directories


def load_csv(
    filepath: Union[str, Path],
    sep: str = ",",
    dtype: Optional[Dict[str, Any]] = None,
    na_values: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Load a CSV file into a pandas DataFrame.

    Args:
        filepath: Path to the CSV file.
        sep: Field separator.
        dtype: Data type specification.
        na_values: List of strings to recognize as NA.

    Returns:
        The loaded DataFrame.
    """
    if not Path(filepath).exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    df = pd.read_csv(
        filepath,
        sep=sep,
        dtype=dtype,
        na_values=na_values,
        low_memory=False
    )
    return df


def load_tsv(
    filepath: Union[str, Path],
    dtype: Optional[Dict[str, Any]] = None,
    na_values: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Load a TSV file into a pandas DataFrame.

    Args:
        filepath: Path to the TSV file.
        dtype: Data type specification.
        na_values: List of strings to recognize as NA.

    Returns:
        The loaded DataFrame.
    """
    return load_csv(filepath, sep="\t", dtype=dtype, na_values=na_values)


def load_abc_phenotypic(filepath: Union[str, Path]) -> pd.DataFrame:
    """
    Load ABCD Study phenotypic data.

    Args:
        filepath: Path to the phenotypic data file.

    Returns:
        The phenotypic DataFrame.
    """
    df = load_csv(filepath)
    # Standardize column names if necessary
    df.columns = [col.lower().strip() for col in df.columns]
    return df


def load_subcortical_stats(filepath: Union[str, Path]) -> pd.DataFrame:
    """
    Load ABCD Study subcortical segmentation statistics.

    Args:
        filepath: Path to the subcortical stats file.

    Returns:
        The subcortical statistics DataFrame.
    """
    df = load_csv(filepath)
    df.columns = [col.lower().strip() for col in df.columns]
    return df


def load_merged_dataset(
    phenotypic_df: pd.DataFrame,
    subcortical_df: pd.DataFrame,
    id_col: str = "subjectkey"
) -> pd.DataFrame:
    """
    Merge phenotypic and subcortical data on participant ID.

    Args:
        phenotypic_df: Phenotypic data DataFrame.
        subcortical_df: Subcortical data DataFrame.
        id_col: Column name for participant ID.

    Returns:
        The merged DataFrame.
    """
    # Ensure ID column exists in both
    if id_col not in phenotypic_df.columns:
        raise ValueError(f"ID column '{id_col}' not found in phenotypic data")
    if id_col not in subcortical_df.columns:
        raise ValueError(f"ID column '{id_col}' not found in subcortical data")

    merged = pd.merge(
        phenotypic_df,
        subcortical_df,
        on=id_col,
        how="inner"
    )

    logging.info(f"Merged dataset size: {len(merged)}")
    return merged


def save_dataframe(
    df: pd.DataFrame,
    filepath: Union[str, Path],
    index: bool = False
) -> None:
    """
    Save a DataFrame to a CSV file.

    Args:
        df: The DataFrame to save.
        filepath: Output file path.
        index: Whether to write the index.
    """
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(filepath, index=index)


def main() -> None:
    """
    Main entry point for the loaders module (for testing).
    """
    project_root = get_project_root()
    ensure_directories()

    # Example: Load a file if it exists
    sample_path = project_root / "data" / "raw" / "sample.csv"
    if sample_path.exists():
        df = load_csv(sample_path)
        print(df.head())


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    main()
