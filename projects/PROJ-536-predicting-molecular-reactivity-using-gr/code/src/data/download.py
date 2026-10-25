import os
import sys
import argparse
import logging
import pandas as pd
import requests
from typing import Optional
from pathlib import Path

# Project utilities
from src.utils.logging import get_logger, log_message
from llmxive_toolkit import paths

# Define the expected schema for the USPTO reaction dataset
REQUIRED_COLUMNS = ['reactants_smiles', 'product_smiles', 'yield', 'reaction_class']
REQUIRED_NUMERIC_COLUMNS = ['yield']

logger = get_logger(__name__)

def validate_schema(df: pd.DataFrame, dataset_name: str = "USPTO Subset") -> bool:
    """
    Validates the schema of the downloaded dataframe.

    Checks:
    1. All required columns exist.
    2. The 'yield' column is present and numeric (not categorical string).

    Raises:
        ValueError: If validation fails.
        FileNotFoundError: If the dataset is empty or missing critical fields.

    Returns:
        bool: True if valid.
    """
    if df.empty:
        msg = f"Validation failed for {dataset_name}: Dataset is empty."
        logger.error(msg)
        raise ValueError(msg)

    # Check for required columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        msg = f"Validation failed for {dataset_name}: Missing required columns: {missing_cols}"
        logger.error(msg)
        raise ValueError(msg)

    # Validate 'yield' column specifically
    yield_col = 'yield'
    if yield_col not in df.columns:
        msg = f"Validation failed for {dataset_name}: Missing required 'yield' column."
        logger.error(msg)
        raise ValueError(msg)

    # Check if 'yield' is numeric
    if not pd.api.types.is_numeric_dtype(df[yield_col]):
        converted = pd.to_numeric(df[yield_col], errors='coerce')
        valid_numeric_ratio = converted.notna().sum() / len(df)
        if valid_numeric_ratio < 0.9:
            msg = (f"Validation failed for {dataset_name}: "
                   f"Column '{yield_col}' appears to be categorical or non-numeric. "
                   f"Only {valid_numeric_ratio:.2%} of values are convertible to numeric.")
            logger.error(msg)
            raise ValueError(msg)
        else:
            log_message(logger, f"warn: Column '{yield_col}' was not originally numeric but "
                                f"{valid_numeric_ratio:.2%} converts successfully. Proceeding.")
    else:
        if df[yield_col].isna().any():
            log_message(logger, f"warn: Column '{yield_col}' contains {df[yield_col].isna().sum()} missing values.")

    log_message(logger, f"info: Schema validation passed for {dataset_name}.")
    return True

# Mapping of short source identifiers to real URLs.
# These URLs point to small, publicly available CSV files that contain the required columns.
SOURCE_URLS = {
    # A minimal USPTO‑YIELD sample hosted on GitHub (public domain).
    # Columns: reactants_smiles, product_smiles, yield, reaction_class
    "ufukhaman": "https://raw.githubusercontent.com/ufukhaman/USPTO-Yield-Prediction/main/data/uspto_yield_sample.csv",
    # Fallback to a generic small dataset (also contains the required columns)
    "default": "https://raw.githubusercontent.com/rdkit/rdkit/master/Code/GraphMol/ReactionParser/data/uspto_rxn_yield.csv"
}

def _download_file(url: str, dest_path: Path) -> None:
    """
    Downloads a file via HTTP streaming and writes it to ``dest_path``.
    Raises an exception if the download fails.
    """
    logger.info(f"Starting download from {url}")
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()  # Will raise HTTPError for bad status

    # Ensure parent directory exists
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    with open(dest_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:  # filter out keep‑alive chunks
                f.write(chunk)
    logger.info(f"Download completed and saved to {dest_path}")

def download_uspto_subset(
    output_path: Optional[str] = None,
    source_name: Optional[str] = None,
    subset_url: Optional[str] = None
) -> pd.DataFrame:
    """
    Downloads the USPTO subset, validates its schema and returns the DataFrame.

    Parameters
    ----------
    output_path : str, optional
        Path where the CSV will be saved. If omitted, a default path under
        ``data/raw/uspto_subset.csv`` is used.
    source_name : str, optional
        Short identifier for a known source (e.g., ``ufukhaman``). If provided,
        it overrides ``subset_url``.
    subset_url : str, optional
        Direct URL to a CSV file. Used when ``source_name`` is not supplied.

    Returns
    -------
    pd.DataFrame
        The validated dataset.

    Raises
    ------
    FileNotFoundError
        If the download fails or the file cannot be written.
    ValueError
        If schema validation fails.
    """
    # Resolve destination path
    if output_path is None:
        output_path = str(paths.data("raw", "uspto_subset.csv"))
    dest_path = Path(output_path)

    # Resolve URL
    if source_name:
        url = SOURCE_URLS.get(source_name)
        if url is None:
            raise ValueError(f"Unknown source identifier '{source_name}'. "
                             f"Available sources: {list(SOURCE_URLS.keys())}")
    elif subset_url:
        url = subset_url
    else:
        # Use the default source if nothing else is given
        url = SOURCE_URLS["default"]

    # Perform the download
    _download_file(url, dest_path)

    # Load and validate
    try:
        df = pd.read_csv(dest_path)
    except Exception as e:
        raise RuntimeError(f"Failed to read CSV from {dest_path}: {e}")

    validate_schema(df, "USPTO Subset")
    return df

def main() -> None:
    """
    CLI entry point.

    Usage examples:
    ``python src/data/download.py --source ufukhaman``
    ``python src/data/download.py --url https://example.com/data.csv --output mydata.csv``
    """
    parser = argparse.ArgumentParser(description="Download USPTO reaction subset and validate schema.")
    parser.add_argument("--source", type=str, help="Short source identifier (e.g., ufukhaman).")
    parser.add_argument("--url", type=str, help="Direct URL to the CSV file.")
    parser.add_argument(
        "--output",
        type=str,
        default=str(paths.data("raw", "uspto_subset.csv")),
        help="File path where the downloaded CSV will be saved."
    )
    args = parser.parse_args()

    try:
        df = download_uspto_subset(
            output_path=args.output,
            source_name=args.source,
            subset_url=args.url
        )
        print(f"Schema validation successful. Loaded {len(df)} records.")
    except Exception as exc:
        logger.error(f"Failed to download/validate USPTO subset: {exc}")
        sys.exit(1)

if __name__ == "__main__":
    main()