"""
Data Loader Module for UCI Datasets.

This module handles parsing downloaded UCI datasets and identifying
continuous numeric variables for simulation purposes.
"""
import os
import csv
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

from config import get_raw_data_dir, get_processed_data_dir

logger = logging.getLogger(__name__)


def load_uci_dataset_raw(dataset_id: str) -> Tuple[List[str], List[List[Any]]]:
    """
    Load a raw UCI dataset from disk.

    Args:
        dataset_id: The identifier for the dataset (e.g., 'wine', 'ionosphere').
                   Must match the filename in data/raw/ (without extension).

    Returns:
        A tuple of (headers, rows) where headers is a list of column names
        and rows is a list of lists containing the data.

    Raises:
        FileNotFoundError: If the dataset file does not exist.
        ValueError: If the file format is unsupported or empty.
    """
    raw_dir = get_raw_data_dir()
    # Support both .csv and .data extensions, prioritize .csv
    possible_paths = [
        raw_dir / f"{dataset_id}.csv",
        raw_dir / f"{dataset_id}.data",
    ]

    file_path = None
    for p in possible_paths:
        if p.exists():
            file_path = p
            break

    if file_path is None:
        raise FileNotFoundError(f"Dataset file not found for '{dataset_id}'. "
                                f"Searched in {raw_dir}: {[str(p) for p in possible_paths]}")

    logger.info(f"Loading raw dataset from: {file_path}")

    headers = []
    rows = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Try to detect if it's CSV or simple comma-separated
            # UCI datasets often use commas, but some might use spaces or tabs
            # We'll attempt standard CSV first
            reader = csv.reader(f)
            for row_idx, row in enumerate(reader):
                if not row:  # Skip empty lines
                    continue
                # Strip whitespace from all cells
                cleaned_row = [cell.strip() for cell in row]
                if not cleaned_row or all(c == '' for c in cleaned_row):
                    continue

                if row_idx == 0:
                    # First non-empty row is typically headers
                    # Some UCI datasets don't have headers, we'll handle that in identify_continuous_variables
                    # For now, assume first row is headers if it looks like text
                    # Heuristic: if the first cell is not numeric, assume it's a header
                    if not cleaned_row[0].replace('.', '').replace('-', '').isdigit():
                        headers = cleaned_row
                        continue
                    else:
                        # First row is data, no headers provided
                        # We'll generate generic headers later
                        pass
                rows.append(cleaned_row)

    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise

    if not rows:
        raise ValueError(f"Dataset '{dataset_id}' contains no data rows.")

    if not headers:
        # Generate generic headers if none were found
        num_cols = len(rows[0])
        headers = [f"var_{i}" for i in range(num_cols)]
        logger.warning(f"No headers found for '{dataset_id}', generated generic headers: {headers}")

    return headers, rows


def identify_continuous_variables(headers: List[str], rows: List[List[Any]]) -> List[str]:
    """
    Identify which variables in the dataset are continuous numeric.

    This function examines the data to determine which columns contain
    numeric values suitable for continuous statistical analysis.

    Args:
        headers: List of column names.
        rows: List of data rows (each row is a list of strings).

    Returns:
        A list of column names that are identified as continuous numeric variables.
    """
    if not rows:
        logger.warning("No data rows provided to identify_continuous_variables")
        return []

    num_cols = len(headers)
    continuous_vars = []

    # Analyze each column
    for col_idx in range(num_cols):
        if col_idx >= len(headers):
            continue

        col_name = headers[col_idx]
        numeric_count = 0
        total_count = 0
        has_non_numeric = False
        has_inf = False

        for row_idx, row in enumerate(rows):
            if col_idx >= len(row):
                continue

            cell_value = row[col_idx]

            # Skip empty cells (treated as missing, not non-numeric)
            if cell_value == '' or cell_value == '?':
                continue

            total_count += 1

            # Try to parse as float
            try:
                val = float(cell_value)
                if np.isinf(val):
                    has_inf = True
                    has_non_numeric = True
                    break
                numeric_count += 1
            except (ValueError, TypeError):
                has_non_numeric = True
                # If we encounter a clear categorical string, stop checking this column
                # unless it's a very small dataset where we might be too strict
                if total_count > 5:
                    break

        # Determine if column is continuous numeric
        # Criteria: > 80% of non-empty values are numeric and finite
        if total_count > 0:
            numeric_ratio = numeric_count / total_count
            if numeric_ratio >= 0.8 and not has_inf:
                continuous_vars.append(col_name)
                logger.debug(f"Column '{col_name}' identified as continuous ({numeric_ratio:.2%} numeric)")
            else:
                logger.debug(f"Column '{col_name}' NOT continuous (ratio: {numeric_ratio:.2%}, has_inf: {has_inf})")
        else:
            logger.debug(f"Column '{col_name}' skipped (no valid data)")

    logger.info(f"Identified {len(continuous_vars)} continuous variables: {continuous_vars}")
    return continuous_vars


def validate_variable_type(data: Dict[str, Any], variable_name: str) -> bool:
    """
    Validate that a specific variable in the dataset is continuous numeric.

    Args:
        data: Dictionary containing dataset information with 'headers' and 'rows' keys.
        variable_name: The name of the variable to validate.

    Returns:
        True if the variable is continuous numeric, False otherwise.
    """
    headers = data.get('headers', [])
    rows = data.get('rows', [])

    if variable_name not in headers:
        logger.warning(f"Variable '{variable_name}' not found in dataset headers: {headers}")
        return False

    col_idx = headers.index(variable_name)
    numeric_count = 0
    total_count = 0

    for row in rows:
        if col_idx >= len(row):
            continue
        cell_value = row[col_idx]
        if cell_value == '' or cell_value == '?':
            continue

        total_count += 1
        try:
            val = float(cell_value)
            if np.isfinite(val):
                numeric_count += 1
        except (ValueError, TypeError):
            break

    if total_count == 0:
        return False

    return (numeric_count / total_count) >= 0.8


def prepare_dataset_for_simulation(dataset_id: str) -> Dict[str, Any]:
    """
    Load and prepare a UCI dataset for simulation.

    This function:
    1. Loads the raw dataset from disk
    2. Identifies continuous numeric variables
    3. Returns a structured dictionary containing the filtered data

    Args:
        dataset_id: The identifier for the dataset.

    Returns:
        A dictionary with keys:
            - 'dataset_id': The dataset identifier
            - 'headers': All original headers
            - 'continuous_headers': Headers for continuous variables only
            - 'rows': Original data rows
            - 'continuous_rows': Data rows filtered to continuous variables only
    """
    logger.info(f"Preparing dataset '{dataset_id}' for simulation")

    # Load raw data
    headers, rows = load_uci_dataset_raw(dataset_id)

    # Identify continuous variables
    continuous_headers = identify_continuous_variables(headers, rows)

    if not continuous_headers:
        raise ValueError(f"No continuous numeric variables found in dataset '{dataset_id}'")

    # Filter rows to only include continuous variables
    continuous_indices = [headers.index(h) for h in continuous_headers]
    continuous_rows = []

    for row in rows:
        filtered_row = [row[i] for i in continuous_indices if i < len(row)]
        # Ensure we have the right number of columns
        if len(filtered_row) == len(continuous_headers):
            continuous_rows.append(filtered_row)

    if not continuous_rows:
        raise ValueError(f"No valid data rows after filtering for continuous variables in '{dataset_id}'")

    logger.info(f"Dataset '{dataset_id}' prepared: {len(continuous_rows)} rows, "
                f"{len(continuous_headers)} continuous variables: {continuous_headers}")

    return {
        'dataset_id': dataset_id,
        'headers': headers,
        'continuous_headers': continuous_headers,
        'rows': rows,
        'continuous_rows': continuous_rows
    }


def main():
    """
    Main entry point for testing the data loader.
    """
    logging.basicConfig(level=logging.INFO)

    # Example usage
    dataset_ids = ['wine', 'ionosphere', 'heart-cleveland']

    for ds_id in dataset_ids:
        try:
            result = prepare_dataset_for_simulation(ds_id)
            print(f"\nDataset: {ds_id}")
            print(f"  Continuous variables: {result['continuous_headers']}")
            print(f"  Rows: {len(result['continuous_rows'])}")
        except Exception as e:
            print(f"Error processing {ds_id}: {e}")


if __name__ == "__main__":
    main()