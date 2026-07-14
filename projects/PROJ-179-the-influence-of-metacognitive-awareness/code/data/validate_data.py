import json
import logging
import os
import sys
import pandas as pd
from pathlib import Path

# Configure logging to match project standards
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = ['confidence_rating', 'source_label']


def find_input_file(raw_dir: Path) -> Path:
    """
    Search for a valid input dataset in the raw directory.
    Prioritizes CSV files with 'behavioral' or 'sample' in the name.
    """
    if not raw_dir.exists():
        logger.error(f"Raw data directory not found: {raw_dir}")
        return None

    csv_files = list(raw_dir.glob("*.csv"))
    if not csv_files:
        logger.error(f"No CSV files found in {raw_dir}")
        return None

    # Heuristic: prefer files that look like the expected dataset
    preferred_patterns = ['behavioral', 'sample', 'metacognition']
    for pattern in preferred_patterns:
        for f in csv_files:
            if pattern in f.name.lower():
                logger.info(f"Found preferred input file: {f}")
                return f

    # Fallback to the first CSV found
    logger.info(f"Using fallback input file: {csv_files[0]}")
    return csv_files[0]


def load_dataset(file_path: Path) -> pd.DataFrame:
    """
    Load the dataset from the given file path.
    Handles common CSV parsing issues.
    """
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Loaded dataset with shape: {df.shape}")
        return df
    except Exception as e:
        logger.error(f"Failed to load dataset from {file_path}: {e}")
        raise


def validate_fields(df: pd.DataFrame) -> bool:
    """
    Check for the presence of required behavioral fields.
    Raises ValueError if missing.
    """
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        error_msg = f"Required fields missing: {', '.join(missing)}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info("All required fields present.")
    return True


def write_report(report_path: Path, status: str, details: dict = None):
    """
    Write the validation report to a JSON file.
    """
    report = {
        "status": status,
        "timestamp": pd.Timestamp.now().isoformat(),
        "required_fields": REQUIRED_COLUMNS
    }
    if details:
        report.update(details)

    try:
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Validation report written to {report_path}")
    except Exception as e:
        logger.error(f"Failed to write report: {e}")
        raise


def main():
    """
    Main entry point for T006: Validate downloaded dataset.
    """
    # Determine project root and paths based on typical execution context
    # The script runs from code/data/, so we look for 'raw' relative to project root
    # Project root is typically two levels up from code/data/validate_data.py
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent
    raw_dir = project_root / "code" / "data" / "raw"
    output_dir = project_root / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "validation_report.json"

    logger.info("Starting data validation (T006)...")

    # 1. Find input file
    input_file = find_input_file(raw_dir)
    if not input_file:
        write_report(report_path, "FAIL", {"reason": "No input dataset found"})
        logger.error("No valid input dataset found in known locations.")
        sys.exit(1)

    # 2. Load dataset
    try:
        df = load_dataset(input_file)
    except Exception:
        write_report(report_path, "FAIL", {"reason": "Failed to load dataset"})
        sys.exit(1)

    # 3. Validate fields
    try:
        validate_fields(df)
    except ValueError as e:
        write_report(report_path, "FAIL", {"reason": str(e)})
        sys.exit(1)

    # 4. Success
    write_report(
        report_path,
        "PASS",
        {"rows": len(df), "columns": list(df.columns)}
    )
    logger.info("Data validation successful.")
    sys.exit(0)


if __name__ == "__main__":
    main()