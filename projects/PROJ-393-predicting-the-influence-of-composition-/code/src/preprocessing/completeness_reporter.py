"""
Completeness Reporter Module.

Generates a JSON report detailing data proportions per source type
after the preprocessing pipeline has run.
"""
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

from src.utils.logging_config import setup_logging

# Configure logger
logger = setup_logging("completeness_reporter")

# Constants
PROCESSED_DATA_PATH = Path("data/processed/alloys_raw.csv")
REPORT_OUTPUT_PATH = Path("data/processed/completeness_report.json")
REQUIRED_SOURCE_COLUMN = "source_type"


def load_processed_data(path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the preprocessed alloys dataset.

    Args:
        path: Optional path to the CSV file. Defaults to PROCESSED_DATA_PATH.

    Returns:
        pd.DataFrame: The loaded dataset.

    Raises:
        FileNotFoundError: If the processed data file does not exist.
        ValueError: If the required 'source_type' column is missing.
    """
    if path is None:
        path = PROCESSED_DATA_PATH

    if not path.exists():
        raise FileNotFoundError(f"Processed data file not found at {path}")

    logger.info(f"Loading processed data from {path}")
    df = pd.read_csv(path)

    if REQUIRED_SOURCE_COLUMN not in df.columns:
        raise ValueError(
            f"Required column '{REQUIRED_SOURCE_COLUMN}' not found in {path}. "
            f"Available columns: {list(df.columns)}"
        )

    return df


def calculate_source_proportions(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate the count and proportion of records for each source type.

    Args:
        df: The preprocessed DataFrame.

    Returns:
        Dict containing 'counts', 'proportions', and 'total_records'.
    """
    total_records = len(df)
    if total_records == 0:
        logger.warning("Processed data is empty. Returning zero counts.")
        return {
            "counts": {},
            "proportions": {},
            "total_records": 0,
            "message": "No records found in dataset."
        }

    # Group by source_type
    counts = df[REQUIRED_SOURCE_COLUMN].value_counts().to_dict()

    # Calculate proportions
    proportions = {
        source: count / total_records
        for source, count in counts.items()
    }

    return {
        "counts": counts,
        "proportions": proportions,
        "total_records": total_records
    }


def generate_completeness_report(df: pd.DataFrame, output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Generate the full completeness report and save it to disk.

    Args:
        df: The preprocessed DataFrame.
        output_path: Optional path to save the JSON report.

    Returns:
        The report dictionary.
    """
    if output_path is None:
        output_path = REPORT_OUTPUT_PATH

    stats = calculate_source_proportions(df)

    report = {
        "report_type": "data_completeness",
        "generated_from": str(PROCESSED_DATA_PATH),
        "source_column": REQUIRED_SOURCE_COLUMN,
        **stats
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to JSON
    logger.info(f"Writing completeness report to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    logger.info("Completeness report generation complete.")
    return report


def run_completeness_report_pipeline(path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Orchestrates loading data and generating the report.

    Args:
        path: Optional path to the processed data CSV.

    Returns:
        The generated report dictionary.
    """
    df = load_processed_data(path)
    return generate_completeness_report(df)


def main():
    """
    Entry point for the completeness report generation script.
    """
    try:
        report = run_completeness_report_pipeline()
        logger.info(f"Report generated successfully. Total records: {report['total_records']}")
        logger.info(f"Source distribution: {report['proportions']}")
        return 0
    except FileNotFoundError as e:
        logger.error(f"Data loading failed: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Validation failed: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during report generation: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
