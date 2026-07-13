"""
Task T006: Validate downloaded dataset for required behavioral fields.

Checks for the presence of 'confidence_rating' and 'source_label' columns
in the downloaded dataset. Writes a validation report to data/validation_report.json.
"""
import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path

# Configure logging to avoid "No handler found" warnings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Define expected file paths based on T005 download logic
EXPECTED_FILES = [
    'data/ds003386_behavioral.csv',
    'data/downloaded/ds003386_behavioral.csv',
    'data/behavioral_data.csv',
    'data/behavioral_dataset.csv'
]

REQUIRED_COLUMNS = ['confidence_rating', 'source_label']


def log_info(msg):
    logger.info(msg)


def log_error(msg):
    logger.error(msg)


def load_dataset():
    """
    Locate and load the downloaded dataset.
    Returns the DataFrame if found, None otherwise.
    """
    base_dir = Path(os.getcwd())
    # Handle project root structure if running from code/
    if (base_dir / 'data').exists():
        search_root = base_dir
    elif (base_dir.parent / 'data').exists():
        search_root = base_dir.parent
    else:
        log_error("Could not determine project root containing data/ directory.")
        return None

    for filename in EXPECTED_FILES:
        filepath = search_root / filename
        if filepath.exists():
            log_info(f"Found dataset at: {filepath}")
            try:
                # Try loading as CSV first
                df = pd.read_csv(filepath)
                log_info(f"Successfully loaded dataset with {len(df)} rows.")
                return df
            except Exception as e:
                log_error(f"Failed to parse {filepath}: {e}")
                continue
        
        # Check for JSON variant if CSV fails
        json_path = filepath.with_suffix('.json')
        if json_path.exists():
            log_info(f"Found JSON dataset at: {json_path}")
            try:
                df = pd.read_json(json_path)
                log_info(f"Successfully loaded dataset with {len(df)} rows.")
                return df
            except Exception as e:
                log_error(f"Failed to parse {json_path}: {e}")
                continue

    log_error(f"Could not find downloaded dataset. Expected one of: {EXPECTED_FILES}")
    return None


def validate_fields(df):
    """
    Validate that required behavioral fields exist in the DataFrame.
    Raises ValueError if missing.
    """
    if df is None:
        raise ValueError("Dataset is None. Cannot validate fields.")

    available_cols = set(df.columns)
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in available_cols]

    if missing_cols:
        error_msg = f"Required fields missing: {', '.join(missing_cols)}"
        raise ValueError(error_msg)

    log_info("All required fields present.")
    return True


def write_report(status, message, output_path):
    """
    Write the validation report to a JSON file.
    """
    report = {
        "task_id": "T006",
        "status": status,
        "message": message,
        "required_fields": REQUIRED_COLUMNS,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    try:
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        log_info(f"Validation report written to {output_path}")
    except Exception as e:
        log_error(f"Failed to write report: {e}")


def main():
    """
    Main entry point for T006.
    """
    log_info("Starting data validation (T006)...")
    
    # Determine output path relative to project root
    base_dir = Path(os.getcwd())
    if (base_dir / 'data').exists():
        output_dir = base_dir / 'data'
    elif (base_dir.parent / 'data').exists():
        output_dir = base_dir.parent / 'data'
    else:
        output_dir = base_dir / 'data'
        output_dir.mkdir(exist_ok=True)
    
    output_path = output_dir / 'validation_report.json'

    try:
        df = load_dataset()
        if df is None:
            write_report("FAIL", "Dataset file not found.", output_path)
            sys.exit(1)

        validate_fields(df)
        write_report("PASS", "All required fields present and valid.", output_path)
        sys.exit(0)

    except ValueError as e:
        log_error(f"Validation failed: {e}")
        write_report("FAIL", str(e), output_path)
        sys.exit(1)
    except Exception as e:
        log_error(f"Unexpected error during validation: {e}")
        write_report("FAIL", f"Unexpected error: {str(e)}", output_path)
        sys.exit(1)


if __name__ == "__main__":
    main()