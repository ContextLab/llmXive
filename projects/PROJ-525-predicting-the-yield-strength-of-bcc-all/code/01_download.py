"""
Data ingestion and filtering pipeline for BCC alloy yield strength prediction.
Handles loading, filtering, normalization, and saving of processed data.
"""
import csv
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import ensure_dirs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/rejected_entries.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

def load_raw_data(filepath: str) -> List[Dict[str, Any]]:
    """Load raw CSV data into a list of dictionaries."""
    data = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        logger.info(f"Loaded {len(data)} rows from {filepath}")
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        raise
    except Exception as e:
        logger.error(f"Error loading file: {e}")
        raise
    return data

def is_valid_yield_strength(row: Dict[str, Any]) -> bool:
    """Check if the yield strength is valid (numeric and not null)."""
    yield_str = row.get('yield_strength')
    if not yield_str or yield_str.lower() in ('null', 'nan', 'na', ''):
        return False
    try:
        val = float(yield_str)
        if val <= 0:
            return False
        return True
    except ValueError:
        return False

def normalize_composition(row: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize composition columns to sum to 1.0."""
    composition_cols = [k for k in row.keys() if k.startswith('element_')]
    if not composition_cols:
        return row

    total = 0.0
    for col in composition_cols:
        try:
            val = float(row[col])
            if val < 0:
                logger.warning(f"Negative composition value for {col} in row {row.get('alloy_id', 'unknown')}: {val}")
            total += val
        except (ValueError, TypeError):
            pass

    if total == 0:
        logger.warning(f"Zero total composition for row {row.get('alloy_id', 'unknown')}, skipping normalization")
        return row

    normalized_row = row.copy()
    for col in composition_cols:
        try:
            val = float(row[col])
            normalized_row[col] = val / total
        except (ValueError, TypeError):
            normalized_row[col] = row[col]

    # Log rounding error
    new_sum = sum(float(normalized_row[col]) for col in composition_cols if isinstance(normalized_row[col], (int, float)))
    if abs(new_sum - 1.0) > 1e-6:
        logger.warning(f"Rounding error in composition sum for row {row.get('alloy_id', 'unknown')}: {new_sum}")

    return normalized_row

def process_alloy(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Process a single alloy row: filter, normalize, and validate."""
    alloy_id = row.get('alloy_id', 'unknown')

    # Filter by crystal structure
    crystal_structure = row.get('crystal_structure', '').upper()
    if crystal_structure != 'BCC':
        logger.info(f"Rejected {alloy_id}: Not BCC ({crystal_structure})")
        return None

    # Filter by yield strength validity
    if not is_valid_yield_strength(row):
        logger.info(f"Rejected {alloy_id}: Invalid yield strength")
        return None

    # Normalize composition
    processed_row = normalize_composition(row)

    # Convert yield strength to float
    processed_row['yield_strength'] = float(processed_row['yield_strength'])

    return processed_row

def check_data_scarcity(data: List[Dict[str, Any]], min_count: int = 80) -> bool:
    """Check if the dataset meets the minimum data requirement."""
    if len(data) < min_count:
        logger.warning(f"Data Scarcity Warning: Only {len(data)} BCC alloys found. Minimum required: {min_count}.")
        return False
    logger.info(f"Data check passed: {len(data)} BCC alloys found.")
    return True

def save_filtered_output(data: List[Dict[str, Any]], output_path: str):
    """Save the filtered and processed data to a CSV file."""
    ensure_dirs(output_path)
    if not data:
        logger.warning("No data to save.")
        return

    fieldnames = list(data[0].keys())
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    logger.info(f"Saved {len(data)} rows to {output_path}")

def main():
    """Main entry point for the data ingestion pipeline."""
    input_path = 'data/raw/mpea_raw.csv'
    output_path = 'data/processed/bcc_filtered.csv'

    # Load raw data
    raw_data = load_raw_data(input_path)

    # Process and filter data
    processed_data = []
    for row in raw_data:
        processed = process_alloy(row)
        if processed:
            processed_data.append(processed)

    # Check data scarcity
    if not check_data_scarcity(processed_data):
        logger.error("Pipeline halted due to data scarcity.")
        sys.exit(1)

    # Save filtered output
    save_filtered_output(processed_data, output_path)

    logger.info("Pipeline completed successfully.")

if __name__ == '__main__':
    main()
