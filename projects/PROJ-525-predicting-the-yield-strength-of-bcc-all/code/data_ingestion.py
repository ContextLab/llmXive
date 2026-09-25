"""
Data Ingestion Module for BCC Alloy Yield Strength Prediction.

This module handles downloading, filtering, normalizing, and saving
the MPEA database for BCC alloys.
"""
import os
import sys
import logging
import requests
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import shared utilities
from utils import setup_logger, get_logger, DataScarcityError, PipelineError
from env_config import get_raw_data_path, get_processed_data_path, get_logs_path, ensure_dirs

# Configure logging
logger = setup_logger("data_ingestion", level=logging.INFO)

# Constants
MPEA_URL = "https://static-content.springer.com/esm/art%3A10.1038%2Fs41597-020-00768-9/MediaObjects/41597_2020_768_MOESM1_ESM.xlsx"
MPEA_FILENAME = "mpea_raw.xlsx"
FILTERED_FILENAME = "bcc_filtered.csv"
REJECTED_LOG_FILENAME = "rejected_entries.log"
MIN_ALLOYS_REQUIRED = 80


def download_mpea_database() -> Path:
    """
    Downloads the MPEA database from the Springer URL.

    Returns:
        Path: Path to the downloaded Excel file.

    Raises:
        PipelineError: If download fails or file is empty.
    """
    raw_dir = get_raw_data_path()
    ensure_dirs([raw_dir])
    output_path = raw_dir / MPEA_FILENAME

    logger.info(f"Downloading MPEA database from {MPEA_URL}")
    try:
        response = requests.get(MPEA_URL, timeout=300)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        if output_path.stat().st_size == 0:
            raise PipelineError("Downloaded file is empty.")
        
        logger.info(f"Successfully downloaded {output_path}")
        return output_path
    except requests.RequestException as e:
        raise PipelineError(f"Failed to download MPEA database: {e}")


def load_raw_data(file_path: Path) -> pd.DataFrame:
    """
    Loads the raw Excel data into a pandas DataFrame.

    Args:
        file_path: Path to the Excel file.

    Returns:
        pd.DataFrame: Loaded data.
    """
    logger.info(f"Loading raw data from {file_path}")
    try:
        # The MPEA dataset typically has headers in the first row, but sometimes
        # there are metadata rows. We assume standard format for now.
        # If the file has multiple sheets, we take the first one.
        df = pd.read_excel(file_path, sheet_name=0)
        logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")
        return df
    except Exception as e:
        raise PipelineError(f"Failed to load raw data: {e}")


def is_valid_yield_strength(row: pd.Series) -> bool:
    """
    Checks if the yield strength value is valid (numeric and non-null).

    Args:
        row: A row from the DataFrame.

    Returns:
        bool: True if valid, False otherwise.
    """
    # Assuming column name 'Yield Strength (MPa)' or similar
    # We need to handle potential variations in column naming
    yield_strength_col = None
    for col in row.index:
        if 'yield' in str(col).lower() and 'strength' in str(col).lower():
            yield_strength_col = col
            break
    
    if yield_strength_col is None:
        # Try to find a generic strength column if specific one not found
        for col in row.index:
            if 'strength' in str(col).lower():
                yield_strength_col = col
                break
    
    if yield_strength_col is None:
        return False

    val = row[yield_strength_col]
    if pd.isna(val):
        return False
    
    try:
        float_val = float(val)
        if float_val <= 0:
            return False
        return True
    except (ValueError, TypeError):
        return False


def is_bcc_phase(row: pd.Series) -> bool:
    """
    Checks if the alloy has a BCC crystal structure.

    Args:
        row: A row from the DataFrame.

    Returns:
        bool: True if BCC, False otherwise.
    """
    # Assuming column name 'Crystal Structure' or 'Phase'
    structure_col = None
    for col in row.index:
        if 'crystal' in str(col).lower() or 'structure' in str(col).lower() or 'phase' in str(col).lower():
            structure_col = col
            break
    
    if structure_col is None:
        return False

    val = str(row[structure_col]).upper()
    # Check for BCC, Body Centered Cubic, etc.
    return 'BCC' in val or 'BODY CENTERED CUBIC' in val


def normalize_composition(row: pd.Series, composition_columns: List[str]) -> Dict[str, float]:
    """
    Normalizes the composition of an alloy so that the sum of atomic fractions is 1.0.
    
    Args:
        row: A row from the DataFrame.
        composition_columns: List of column names representing elemental compositions.
        
    Returns:
        Dict[str, float]: Normalized composition as a dictionary of element -> fraction.
        
    Raises:
        PipelineError: If normalization fails (e.g., sum is zero).
    """
    composition = {}
    total_sum = 0.0
    
    for col in composition_columns:
        if col in row.index:
            val = row[col]
            if pd.notna(val):
                try:
                  val = float(val)
                  if val >= 0:
                      composition[col] = val
                      total_sum += val
                  else:
                      # Negative values are invalid for composition
                      raise ValueError("Negative composition value")
                except (ValueError, TypeError):
                    continue
        
    if total_sum == 0.0:
        raise PipelineError(f"Total composition sum is zero for row. Cannot normalize.")
    
    normalized = {}
    for elem, val in composition.items():
        normalized[elem] = val / total_sum
        
    return normalized


def process_alloy(row: pd.Series, composition_columns: List[str]) -> Optional[Dict[str, Any]]:
    """
    Processes a single alloy row: validates yield strength, checks BCC phase,
    and normalizes composition.
    
    Args:
        row: A row from the DataFrame.
        composition_columns: List of column names representing elemental compositions.
        
    Returns:
        Optional[Dict[str, Any]]: Processed alloy record or None if invalid.
    """
    # Check Yield Strength
    if not is_valid_yield_strength(row):
        return None
        
    # Check BCC Phase
    if not is_bcc_phase(row):
        return None
        
    # Normalize Composition
    try:
        normalized_comp = normalize_composition(row, composition_columns)
    except PipelineError:
        return None
        
    # Construct record
    record = {
        'original_row': row.to_dict(),
        'normalized_composition': normalized_comp,
        'is_valid': True
    }
    
    return record


def check_data_scarcity(filtered_count: int) -> None:
    """
    Checks if the number of filtered alloys meets the minimum requirement.
    
    Args:
        filtered_count: Number of valid BCC alloys found.
        
    Raises:
        DataScarcityError: If count is below threshold.
    """
    if filtered_count < MIN_ALLOYS_REQUIRED:
        raise DataScarcityError(f"DATA_SCARCITY: Insufficient BCC alloys (N={filtered_count} < {MIN_ALLOYS_REQUIRED})")
    logger.info(f"Data scarcity check passed: {filtered_count} alloys found (>= {MIN_ALLOYS_REQUIRED})")


def save_filtered_output(records: List[Dict[str, Any]], output_path: Path, rejected_log_path: Path) -> None:
    """
    Saves the filtered and normalized data to CSV and logs rejected entries.
    
    Args:
        records: List of processed alloy records.
        output_path: Path to save the filtered CSV.
        rejected_log_path: Path to save the rejected entries log.
    """
    ensure_dirs([output_path.parent, rejected_log_path.parent])
    
    # Prepare data for CSV
    # We need to flatten the composition for CSV storage
    # Find all unique elements across all records to ensure consistent columns
    all_elements = set()
    for rec in records:
        all_elements.update(rec['normalized_composition'].keys())
    
    sorted_elements = sorted(list(all_elements))
    
    csv_data = []
    for rec in records:
        row_data = {
            'yield_strength_mpa': rec['original_row'].get('Yield Strength (MPa)', rec['original_row'].get('Yield Strength', None)),
            'crystal_structure': rec['original_row'].get('Crystal Structure', rec['original_row'].get('Phase', None))
        }
        for elem in sorted_elements:
            row_data[elem] = rec['normalized_composition'].get(elem, 0.0)
        csv_data.append(row_data)
    
    df_output = pd.DataFrame(csv_data)
    df_output.to_csv(output_path, index=False)
    logger.info(f"Saved {len(records)} filtered records to {output_path}")
    
    # Log rejected entries (simplified: just log the count and reasons)
    # In a more complex implementation, we might store the actual rejected rows
    with open(rejected_log_path, 'w') as f:
        f.write(f"Total rejected entries: {len(records)} (placeholder for detailed logging)\n")
        # Note: The actual logic to log specific rejected rows would require
        # storing the rejection reason during the filter loop.
        # For now, we log the summary.
    logger.info(f"Saved rejection log to {rejected_log_path}")


def filter_bcc_and_yield_strength(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Filters the DataFrame to include only BCC alloys with valid yield strength.
    Also normalizes compositions.
    
    Args:
        df: Raw DataFrame.
        
    Returns:
        List[Dict[str, Any]]: List of valid, processed alloy records.
    """
    # Identify composition columns (typically columns with element symbols or names)
    # Heuristic: Columns that are not standard metadata columns
    metadata_cols = {'Yield Strength (MPa)', 'Yield Strength', 'Crystal Structure', 'Phase', 'Sample ID', 'ID'}
    composition_cols = [col for col in df.columns if col not in metadata_cols and not str(col).startswith('Unnamed')]
    
    # If no composition columns found, try to infer from element symbols
    if not composition_cols:
        # Fallback: assume columns with 1-2 letter uppercase starts are elements
        import re
        composition_cols = [col for col in df.columns if re.match(r'^[A-Z]{1,2}$', str(col))]
    
    if not composition_cols:
        raise PipelineError("Could not identify composition columns in the dataset.")
    
    logger.info(f"Identified {len(composition_cols)} composition columns: {composition_cols[:5]}...")
    
    valid_records = []
    rejected_count = 0
    
    for idx, row in df.iterrows():
        processed = process_alloy(row, composition_cols)
        if processed:
            valid_records.append(processed)
        else:
            rejected_count += 1
            
    logger.info(f"Filtered {len(valid_records)} valid BCC alloys, rejected {rejected_count} entries.")
    return valid_records


def main():
    """
    Main entry point for the data ingestion pipeline.
    """
    try:
        # 1. Download
        raw_path = download_mpea_database()
        
        # 2. Load
        df = load_raw_data(raw_path)
        
        # 3. Filter & Normalize (Task T015 implementation)
        valid_records = filter_bcc_and_yield_strength(df)
        
        # 4. Check Data Scarcity
        check_data_scarcity(len(valid_records))
        
        # 5. Save Output
        processed_dir = get_processed_data_path()
        logs_dir = get_logs_path()
        
        output_csv = processed_dir / FILTERED_FILENAME
        rejected_log = logs_dir / REJECTED_LOG_FILENAME
        
        save_filtered_output(valid_records, output_csv, rejected_log)
        
        logger.info("Data ingestion pipeline completed successfully.")
        return 0
        
    except DataScarcityError as e:
        logger.error(str(e))
        return 1
    except PipelineError as e:
        logger.error(f"Pipeline error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())