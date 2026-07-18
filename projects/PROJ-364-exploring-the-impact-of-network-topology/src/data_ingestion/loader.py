"""
Data ingestion loader for defect coordinate datasets.

Implements streaming CSV/Parquet loading with chunksize, missing value handling,
and audit logging as per US1 requirements.
"""
import logging
import csv
from pathlib import Path
from typing import Iterator, List, Dict, Any, Optional, Tuple, Union
import pandas as pd
import numpy as np

from src.logging_config import get_data_ingestion_logger

# Initialize logger specific to data ingestion
logger = get_data_ingestion_logger()


class DataIngestionError(Exception):
    """Exception raised when data ingestion fails critically (e.g., all rows dropped)."""
    pass


def _validate_row(row: Dict[str, Any], row_id: int) -> bool:
    """
    Validate a single row for missing x/y coordinates.

    Args:
        row: Dictionary representing a data row.
        row_id: The index/ID of the row for logging purposes.

    Returns:
        True if the row is valid (has x and y), False otherwise.
    """
    x_val = row.get('x')
    y_val = row.get('y')

    # Check for NaN, None, or empty string
    is_x_valid = x_val is not None and pd.notna(x_val) and x_val != ''
    is_y_valid = y_val is not None and pd.notna(y_val) and y_val != ''

    if not is_x_valid or not is_y_valid:
        logger.warning(f"[US1] Dropped row {row_id}: missing coordinate")
        return False

    return True


def load_csv_streaming(
    file_path: Union[str, Path],
    chunk_size: int = 1000
) -> Iterator[pd.DataFrame]:
    """
    Load a CSV file in chunks, filtering out rows with missing x/y coordinates.

    Args:
        file_path: Path to the CSV file.
        chunk_size: Number of rows to process at a time.

    Yields:
        Validated DataFrames containing only rows with valid x/y coordinates.

    Raises:
        DataIngestionError: If the file cannot be read or no valid rows exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    valid_rows = []
    total_rows = 0
    dropped_count = 0
    row_id = 0

    try:
        # Use pandas read_csv with chunksize for streaming
        for chunk in pd.read_csv(path, chunksize=chunk_size):
            total_rows += len(chunk)
            valid_chunk_rows = []

            for idx, row in chunk.iterrows():
                # Create a dictionary for validation
                row_dict = row.to_dict()
                if _validate_row(row_dict, row_id):
                    valid_chunk_rows.append(row_dict)
                else:
                    dropped_count += 1
                row_id += 1

            if valid_chunk_rows:
                valid_df = pd.DataFrame(valid_chunk_rows)
                valid_rows.append(valid_df)

    except Exception as e:
        logger.error(f"Error reading CSV file {path}: {str(e)}")
        raise DataIngestionError(f"Failed to read CSV file: {str(e)}") from e

    if not valid_rows:
        raise DataIngestionError(
            f"No valid rows found in {path}. All {total_rows} rows were dropped due to missing coordinates."
        )

    # Log summary
    logger.info(
        f"Loaded {len(valid_rows)} chunks from {path}. "
        f"Total rows: {total_rows}, Dropped: {dropped_count}, Valid: {total_rows - dropped_count}"
    )

    return iter(valid_rows)


def load_parquet_streaming(
    file_path: Union[str, Path],
    chunk_size: int = 1000
) -> Iterator[pd.DataFrame]:
    """
    Load a Parquet file in chunks, filtering out rows with missing x/y coordinates.

    Note: Parquet files are often column-oriented and may not support true streaming
    row-by-row as efficiently as CSV. This implementation processes in row-groups
    where possible, or falls back to chunked processing if supported by the engine.

    Args:
        file_path: Path to the Parquet file.
        chunk_size: Target number of rows per chunk (may be approximate).

    Yields:
        Validated DataFrames containing only rows with valid x/y coordinates.

    Raises:
        DataIngestionError: If the file cannot be read or no valid rows exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    # PyArrow is required for Parquet reading
    try:
        import pyarrow.parquet as pq
    except ImportError:
        raise ImportError("pyarrow is required to read Parquet files. Install with: pip install pyarrow")

    parquet_file = pq.ParquetFile(path)
    total_rows = parquet_file.metadata.num_rows

    if total_rows == 0:
        raise DataIngestionError(f"Parquet file {path} is empty.")

    valid_rows = []
    dropped_count = 0
    row_id = 0

    try:
        # Iterate over row groups or chunks
        for batch in parquet_file.iter_batches(batch_size=chunk_size):
            df_chunk = batch.to_pandas()
            valid_chunk_rows = []

            for idx, row in df_chunk.iterrows():
                row_dict = row.to_dict()
                if _validate_row(row_dict, row_id):
                    valid_chunk_rows.append(row_dict)
                else:
                    dropped_count += 1
                row_id += 1

            if valid_chunk_rows:
                valid_df = pd.DataFrame(valid_chunk_rows)
                valid_rows.append(valid_df)

    except Exception as e:
        logger.error(f"Error reading Parquet file {path}: {str(e)}")
        raise DataIngestionError(f"Failed to read Parquet file: {str(e)}") from e

    if not valid_rows:
        raise DataIngestionError(
            f"No valid rows found in {path}. All {total_rows} rows were dropped due to missing coordinates."
        )

    logger.info(
        f"Loaded data from {path}. "
        f"Total rows: {total_rows}, Dropped: {dropped_count}, Valid: {total_rows - dropped_count}"
    )

    return iter(valid_rows)


def write_dropped_rows_audit(
    file_path: Union[str, Path],
    dropped_rows: List[Dict[str, Any]],
    output_path: Union[str, Path]
) -> None:
    """
    Write dropped rows to an audit CSV file for traceability.

    Args:
        file_path: Path to the original source file (for reference).
        dropped_rows: List of dictionaries representing dropped rows.
        output_path: Path where the audit CSV will be written.
    """
    if not dropped_rows:
        logger.info("No dropped rows to write to audit file.")
        return

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output, 'w', newline='') as f:
            if dropped_rows:
                writer = csv.DictWriter(f, fieldnames=dropped_rows[0].keys())
                writer.writeheader()
                writer.writerows(dropped_rows)
        logger.info(f"Audit file written to {output} containing {len(dropped_rows)} dropped rows.")
    except Exception as e:
        logger.error(f"Failed to write audit file {output}: {str(e)}")
        # Non-fatal error, but log it


def load_data(
    file_path: Union[str, Path],
    dropped_rows_output: Optional[Union[str, Path]] = None
) -> pd.DataFrame:
    """
    Main entry point to load data from CSV or Parquet.

    This function handles streaming, validation, and audit logging.
    It concatenates all valid chunks into a single DataFrame.

    Args:
        file_path: Path to the input file (.csv or .parquet).
        dropped_rows_output: Optional path to write dropped rows audit CSV.

    Returns:
        A pandas DataFrame containing all valid rows.

    Raises:
        DataIngestionError: If loading fails or no valid rows are found.
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    dropped_rows_buffer = []
    row_id = 0

    # Determine loader based on file extension
    if suffix == '.csv':
        loader = load_csv_streaming
    elif suffix == '.parquet':
        loader = load_parquet_streaming
    else:
        raise ValueError(f"Unsupported file format: {suffix}. Use .csv or .parquet.")

    # Stream and validate
    valid_chunks = []
    try:
        for chunk in loader(path):
            # Re-calculate row IDs for dropped rows tracking if needed
            # For simplicity in this audit, we track dropped rows during the chunk iteration
            # inside the loader. However, if we need to capture the actual dropped data:
            # We modify the loader logic slightly to return dropped info or handle it here.
            # Since the loader yields valid DataFrames, we need to capture dropped rows differently.
            # To strictly follow the "write dropped rows" requirement, we need to capture them.
            # Refactoring the loader to yield (valid_df, dropped_rows) is cleaner but changes signature.
            # Instead, we will rely on the internal logging for the count, and for the audit file,
            # we need to re-scan or modify the loader.
            #
            # Correction: The requirement asks for `data/processed/dropped_rows.csv`.
            # The loader currently logs warnings. To write the file, we need the actual dropped data.
            # We will modify the approach: The loader functions above are internal.
            # We will create a wrapper that captures dropped rows.
            pass
    except DataIngestionError:
        raise

    # Re-implementation of the main loop to capture dropped rows for the audit file
    # This ensures we have the data to write to `data/processed/dropped_rows.csv`
    
    final_valid_rows = []
    final_dropped_rows = []
    global_row_id = 0

    try:
        if suffix == '.csv':
            for chunk in pd.read_csv(path, chunksize=1000):
                for idx, row in chunk.iterrows():
                    row_dict = row.to_dict()
                    if _validate_row(row_dict, global_row_id):
                        final_valid_rows.append(row_dict)
                    else:
                        final_dropped_rows.append(row_dict)
                    global_row_id += 1
        elif suffix == '.parquet':
            import pyarrow.parquet as pq
            parquet_file = pq.ParquetFile(path)
            for batch in parquet_file.iter_batches(batch_size=1000):
                df_chunk = batch.to_pandas()
                for idx, row in df_chunk.iterrows():
                    row_dict = row.to_dict()
                    if _validate_row(row_dict, global_row_id):
                        final_valid_rows.append(row_dict)
                    else:
                        final_dropped_rows.append(row_dict)
                    global_row_id += 1
    except Exception as e:
        logger.error(f"Error processing file {path}: {str(e)}")
        raise DataIngestionError(f"Failed to process file: {str(e)}") from e

    if not final_valid_rows:
        raise DataIngestionError(
            f"No valid rows found in {path}. All {global_row_id} rows were dropped."
        )

    result_df = pd.DataFrame(final_valid_rows)

    # Write dropped rows audit file if requested or default path
    if dropped_rows_output:
        write_dropped_rows_audit(path, final_dropped_rows, dropped_rows_output)
    elif final_dropped_rows:
        # Default path as per task description
        default_audit_path = Path("data/processed/dropped_rows.csv")
        write_dropped_rows_audit(path, final_dropped_rows, default_audit_path)

    logger.info(f"Successfully loaded {len(result_df)} valid rows from {path}.")
    return result_df