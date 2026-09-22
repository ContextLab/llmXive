"""
Ingestion module for glass-forming alloy data.
Handles dataset fetching, validation, and filtering.
"""
import logging
import os
import sys
import re
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
from datasets import load_dataset
from mendeleev import element

# Ensure directories exist
def ensure_dir(path: str) -> None:
    """Ensure the directory for the given path exists."""
    dir_path = os.path.dirname(path)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)

# Setup logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Constants
DATASET_ID = "matsci/glass-forming-ability"
RAW_DATA_DIR = "data/processed"
LOGS_DIR = "data/logs"
FETCH_ERROR_LOG = os.path.join(LOGS_DIR, "fetch_error.log")
EXCLUSION_LOG = os.path.join(LOGS_DIR, "exclusion_log.txt")
RAW_OUTPUT_FILE = os.path.join(RAW_DATA_DIR, "processed_alloys_raw.csv")

# Ensure log directories exist before any file operations
ensure_dir(LOGS_DIR)
ensure_dir(RAW_DATA_DIR)

def parse_composition(composition_str: str) -> Optional[Dict[str, float]]:
    """
    Parse a composition string like "Fe50Ni30Cr20" or "Fe_50 Ni_30 Cr_20"
    into a dictionary of {element: atomic_fraction}.

    Supports formats:
    - "Fe50Ni30Cr20" (no separators)
    - "Fe50 Ni30 Cr20" (space separated)
    - "Fe_50 Ni_30 Cr_20" (underscore separated)

    Returns None if parsing fails.
    """
    if not isinstance(composition_str, str) or not composition_str.strip():
        return None

    # Normalize separators
    comp_str = composition_str.replace('_', ' ').strip()

    # Regex to match element symbol and optional number
    # Element symbols: One uppercase followed by optional lowercase
    pattern = r'([A-Z][a-z]?)(\d*\.?\d*)'

    matches = re.findall(pattern, comp_str)

    if not matches:
        return None

    result = {}
    total_atoms = 0.0

    for elem, amount_str in matches:
        try:
            # If no number provided, assume equal distribution (handled later)
            if amount_str == '':
                amount = 1.0  # Placeholder, will normalize later
            else:
                amount = float(amount_str)
            result[elem] = amount
            total_atoms += amount
        except ValueError:
            return None

    if total_atoms == 0:
        return None

    # Normalize to fractions
    for elem in result:
        result[elem] /= total_atoms

    return result

def validate_ternary_elements(composition_dict: Dict[str, float]) -> bool:
    """
    Validate that the composition has exactly 3 distinct elements
    and all elements exist in the periodic table (mendeleev).
    """
    if len(composition_dict) != 3:
        return False

    for elem_symbol in composition_dict.keys():
        try:
            # Check if element exists
            element(elem_symbol)
        except (ValueError, TypeError):
            return False

    return True

def load_glass_data() -> pd.DataFrame:
    """
    Load the glass-forming ability dataset from Hugging Face.
    Implements robust error handling as per T008.

    Returns:
        pd.DataFrame: The loaded dataset.

    Raises:
        ValueError: If the dataset fetch fails or schema is invalid.
    """
    logger.info(f"Attempting to fetch dataset: {DATASET_ID}")

    try:
        # Attempt to load the dataset
        # Using streaming to handle large datasets and avoid OOM
        ds = load_dataset(DATASET_ID, split="train", streaming=True)

        # Convert to a list of dicts first to inspect schema
        # We need to verify the schema immediately
        sample = next(iter(ds))
        columns = list(sample.keys())

        logger.info(f"Dataset schema verified. Columns: {columns}")

        # Check for critical column
        if 'critical_cooling_rate' not in columns:
            error_msg = f"Verified Data Source Mismatch: Dataset lacks critical_cooling_rate column. Found: {columns}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # If schema is valid, load the full data (chunked processing happens in caller)
        # We return the dataset object to allow streaming processing
        return ds

    except Exception as e:
        # Log detailed error
        error_details = {
            "timestamp": datetime.now().isoformat(),
            "dataset_id": DATASET_ID,
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": str(e.__traceback__) if hasattr(e, '__traceback__') else "N/A"
        }

        logger.error(f"Failed to fetch dataset: {error_details}")

        # Write error log to file
        try:
            ensure_dir(FETCH_ERROR_LOG)
            with open(FETCH_ERROR_LOG, 'w') as f:
                json.dump(error_details, f, indent=2)
            logger.info(f"Error details written to {FETCH_ERROR_LOG}")
        except IOError as io_err:
            logger.error(f"Failed to write error log: {io_err}")

        # Raise ValueError as required by T008
        raise ValueError(f"Dataset fetch failed: {str(e)}") from e

def filter_ternary_alloys(ds) -> pd.DataFrame:
    """
    Filter the dataset for valid ternary alloys.
    Processes data in chunks to handle memory constraints.

    Args:
        ds: The Hugging Face dataset object.

    Returns:
        pd.DataFrame: Filtered and processed data.
    """
    logger.info("Starting filtering for ternary alloys...")

    valid_rows = []
    exclusion_reasons = []
    chunk_size = 5000
    buffer = []
    total_processed = 0
    total_valid = 0
    total_excluded = 0

    # Ensure exclusion log exists
    ensure_dir(EXCLUSION_LOG)

    try:
        with open(EXCLUSION_LOG, 'w') as log_file:
            log_file.write(f"Exclusion Log - {datetime.now().isoformat()}\n")
            log_file.write("=" * 50 + "\n")

            for row in ds:
                total_processed += 1
                buffer.append(row)

                # Process in chunks
                if len(buffer) >= chunk_size:
                    chunk_df = pd.DataFrame(buffer)
                    buffer = []

                    # Process chunk
                    for idx, row in chunk_df.iterrows():
                        try:
                            # Check for critical_cooling_rate
                            if pd.isna(row.get('critical_cooling_rate')):
                                exclusion_reasons.append({
                                    "index": total_processed,
                                    "reason": "Missing critical_cooling_rate"
                                })
                                total_excluded += 1
                                continue

                            # Parse composition
                            comp_str = row.get('composition', '')
                            if not isinstance(comp_str, str):
                                exclusion_reasons.append({
                                    "index": total_processed,
                                    "reason": "Invalid composition format"
                                })
                                total_excluded += 1
                                continue

                            comp_dict = parse_composition(comp_str)
                            if not comp_dict:
                                exclusion_reasons.append({
                                    "index": total_processed,
                                    "reason": "Failed to parse composition"
                                })
                                total_excluded += 1
                                continue

                            # Validate ternary
                            if not validate_ternary_elements(comp_dict):
                                exclusion_reasons.append({
                                    "index": total_processed,
                                    "reason": f"Not ternary (found {len(comp_dict)} elements)"
                                })
                                total_excluded += 1
                                continue

                            # Filter unknown labels
                            label = row.get('glass_forming_label', 'unknown')
                            if pd.isna(label) or str(label).lower() in ['unknown', 'mixed', 'null']:
                                exclusion_reasons.append({
                                    "index": total_processed,
                                    "reason": f"Invalid label: {label}"
                                })
                                total_excluded += 1
                                continue

                            # Valid row
                            row_dict = dict(row)
                            row_dict['source_label'] = DATASET_ID
                            row_dict['parsed_composition'] = json.dumps(comp_dict)
                            valid_rows.append(row_dict)
                            total_valid += 1

                        except Exception as e:
                            exclusion_reasons.append({
                                "index": total_processed,
                                "reason": f"Processing error: {str(e)}"
                            })
                            total_excluded += 1

                    # Log exclusions for this chunk
                    for reason in exclusion_reasons:
                        log_file.write(f"Index {reason['index']}: {reason['reason']}\n")
                    exclusion_reasons = []

            # Process remaining buffer
            if buffer:
                chunk_df = pd.DataFrame(buffer)
                for idx, row in chunk_df.iterrows():
                    try:
                        if pd.isna(row.get('critical_cooling_rate')):
                            exclusion_reasons.append({"index": total_processed, "reason": "Missing critical_cooling_rate"})
                            total_excluded += 1
                            continue

                        comp_str = row.get('composition', '')
                        if not isinstance(comp_str, str):
                            exclusion_reasons.append({"index": total_processed, "reason": "Invalid composition format"})
                            total_excluded += 1
                            continue

                        comp_dict = parse_composition(comp_str)
                        if not comp_dict:
                            exclusion_reasons.append({"index": total_processed, "reason": "Failed to parse composition"})
                            total_excluded += 1
                            continue

                        if not validate_ternary_elements(comp_dict):
                            exclusion_reasons.append({"index": total_processed, "reason": f"Not ternary (found {len(comp_dict)} elements)"})
                            total_excluded += 1
                            continue

                        label = row.get('glass_forming_label', 'unknown')
                        if pd.isna(label) or str(label).lower() in ['unknown', 'mixed', 'null']:
                            exclusion_reasons.append({"index": total_processed, "reason": f"Invalid label: {label}"})
                            total_excluded += 1
                            continue

                        row_dict = dict(row)
                        row_dict['source_label'] = DATASET_ID
                        row_dict['parsed_composition'] = json.dumps(comp_dict)
                        valid_rows.append(row_dict)
                        total_valid += 1

                    except Exception as e:
                        exclusion_reasons.append({"index": total_processed, "reason": f"Processing error: {str(e)}"})
                        total_excluded += 1

                # Log remaining exclusions
                for reason in exclusion_reasons:
                    log_file.write(f"Index {reason['index']}: {reason['reason']}\n")

        logger.info(f"Filtering complete. Total processed: {total_processed}, Valid: {total_valid}, Excluded: {total_excluded}")

        if not valid_rows:
            error_msg = "Dataset is empty after filtering. Check composition parsing logic and data source validity."
            logger.error(error_msg)
            raise ValueError(error_msg)

        return pd.DataFrame(valid_rows)

    except Exception as e:
        logger.error(f"Error during filtering: {str(e)}")
        raise

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the dataframe by removing duplicates and standardizing columns.
    """
    logger.info("Cleaning data...")

    # Remove duplicates based on composition and critical_cooling_rate
    if 'parsed_composition' in df.columns and 'critical_cooling_rate' in df.columns:
        df = df.drop_duplicates(subset=['parsed_composition', 'critical_cooling_rate'])

    # Ensure numeric types for critical columns
    if 'critical_cooling_rate' in df.columns:
        df['critical_cooling_rate'] = pd.to_numeric(df['critical_cooling_rate'], errors='coerce')
        df = df.dropna(subset=['critical_cooling_rate'])

    logger.info(f"Cleaning complete. Final shape: {df.shape}")
    return df

def validate_critical_cooling_rate(df: pd.DataFrame) -> None:
    """
    Validate that critical_cooling_rate has non-zero variance.
    """
    if 'critical_cooling_rate' not in df.columns:
        raise ValueError("critical_cooling_rate column missing")

    variance = df['critical_cooling_rate'].var()
    if variance == 0:
        raise ValueError("Zero variance in critical_cooling_rate")

    logger.info(f"Critical cooling rate variance: {variance}")

def run_ingestion() -> None:
    """
    Main entry point for the ingestion pipeline.
    """
    logger.info("Starting ingestion pipeline...")

    try:
        # Load data
        ds = load_glass_data()

        # Filter for ternary alloys
        df = filter_ternary_alloys(ds)

        # Clean data
        df = clean_data(df)

        # Validate variance
        validate_critical_cooling_rate(df)

        # Write output
        ensure_dir(RAW_OUTPUT_FILE)
        df.to_csv(RAW_OUTPUT_FILE, index=False)
        logger.info(f"Successfully wrote {len(df)} rows to {RAW_OUTPUT_FILE}")

        # Write data validation status
        status = "pass"
        message = "Data validation passed"
        n_total = len(df)

        if n_total < 500:
            status = "fail"
            message = f"Data availability error: N < 500. Minimum N >= 500 required by FR-001."
        elif n_total < 1000:
            status = "warning"
            message = f"Data size below target (N < 1000) but above minimum (N >= 500). Proceeding."

        validation_status = {
            "status": status,
            "n_total": n_total,
            "message": message
        }

        ensure_dir(os.path.join(LOGS_DIR, "data_validation_status.json"))
        with open(os.path.join(LOGS_DIR, "data_validation_status.json"), 'w') as f:
            json.dump(validation_status, f, indent=2)
        logger.info(f"Wrote validation status to {os.path.join(LOGS_DIR, 'data_validation_status.json')}")

    except ValueError as e:
        logger.error(f"Ingestion failed with ValueError: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Ingestion failed unexpectedly: {str(e)}")
        raise

if __name__ == "__main__":
    run_ingestion()