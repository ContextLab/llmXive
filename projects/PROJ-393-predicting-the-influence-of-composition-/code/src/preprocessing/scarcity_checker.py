"""
Scarcity Checker for Heusler Alloy Dataset

Implements T028b: Counts rows in the processed dataset after DFT filtering.
If N < 50, triggers T046 by generating the data scarcity warning report.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.utils.logging_config import setup_logging

# Constants
SCARCITY_THRESHOLD = 50
PROCESSED_DATA_PATH = Path("data/processed/alloys_raw.csv")
WARNING_REPORT_PATH = Path("docs/reports/data_scarcity_warning.md")
CHECK_LOG_PATH = Path("data/processed/scarcity_check_log.json")

logger = setup_logging(__name__)


def load_processed_data(filepath: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the processed alloys dataset.

    Args:
        filepath: Path to the CSV file. Defaults to PROCESSED_DATA_PATH.

    Returns:
        DataFrame containing the processed alloy data.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or has no rows.
    """
    path = filepath or PROCESSED_DATA_PATH
    if not path.exists():
        raise FileNotFoundError(f"Processed data file not found: {path}")

    df = pd.read_csv(path)

    if df.empty:
        raise ValueError(f"Processed data file is empty: {path}")

    logger.info(f"Loaded {len(df)} rows from {path}")
    return df


def check_scarcity(df: pd.DataFrame, threshold: int = SCARCITY_THRESHOLD) -> Dict[str, Any]:
    """
    Check if the dataset size is below the scarcity threshold.

    Args:
        df: The processed DataFrame.
        threshold: Minimum number of rows required (default 50).

    Returns:
        Dictionary with check results:
            - 'row_count': int
            - 'threshold': int
            - 'is_scarce': bool (True if row_count < threshold)
            - 'message': str
    """
    row_count = len(df)
    is_scarce = row_count < threshold

    result = {
        "row_count": row_count,
        "threshold": threshold,
        "is_scarce": is_scarce,
        "message": f"Dataset contains {row_count} rows. Threshold is {threshold}."
    }

    if is_scarce:
        result["message"] += " WARNING: Data scarcity detected."
        logger.warning(result["message"])
    else:
        result["message"] += " Dataset size is sufficient."
        logger.info(result["message"])

    return result


def generate_warning_report(result: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Generate the data scarcity warning report (T046 artifact) if scarcity is detected.

    Args:
        result: The dictionary returned by check_scarcy.
        output_path: Path to write the markdown report. Defaults to WARNING_REPORT_PATH.

    Returns:
        Path to the generated report.

    Raises:
        ValueError: If scarcity is not detected (no report needed).
    """
    if not result.get("is_scarce", False):
        logger.info("No scarcity detected. Skipping warning report generation.")
        return output_path or WARNING_REPORT_PATH

    path = output_path or WARNING_REPORT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    report_content = f"""# Data Scarcity Warning Report

**Generated**: {pd.Timestamp.now().isoformat()}

## Summary
The dataset used for training and validation contains fewer than the recommended number of samples.

## Metrics
- **Total Rows**: {result['row_count']}
- **Threshold**: {result['threshold']}
- **Status**: SCARCE

## Implications
With only {result['row_count']} samples, the following limitations apply:
1. **Statistical Power**: Model performance metrics (R², MAE) may have high variance.
2. **Generalization**: The model may overfit to the specific distribution of this small dataset.
3. **Feature Engineering**: Complex feature interactions may not be statistically significant.

## Recommendations
- **Interpretation**: Results should be treated as exploratory rather than definitive.
- **Validation**: Rely heavily on stratified analysis and bootstrapping confidence intervals.
- **Future Work**: Prioritize data collection to expand the dataset beyond the {result['threshold']} threshold.

## Action
This warning was automatically triggered by the Scarcity Checker (T028b) as part of the US1 preprocessing pipeline.
"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(report_content)

    logger.info(f"Generated scarcity warning report at: {path}")
    return path


def save_check_log(result: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Save the check results to a JSON log file.

    Args:
        result: The dictionary returned by check_scarcy.
        output_path: Path to the log file. Defaults to CHECK_LOG_PATH.

    Returns:
        Path to the saved log file.
    """
    path = output_path or CHECK_LOG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    log_entry = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "result": result
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(log_entry, f, indent=2)

    logger.info(f"Saved scarcity check log to: {path}")
    return path


def run_scarcity_check(
    input_path: Optional[Path] = None,
    threshold: int = SCARCITY_THRESHOLD,
    generate_report: bool = True
) -> Dict[str, Any]:
    """
    Main orchestration function for the scarcity check.

    1. Loads the processed data.
    2. Checks the row count against the threshold.
    3. Saves the check log.
    4. If scarce, generates the T046 warning report.

    Args:
        input_path: Path to the input CSV.
        threshold: Minimum row count.
        generate_report: Whether to generate the markdown warning if scarce.

    Returns:
        The check result dictionary.
    """
    logger.info("Starting Scarcity Check (T028b)...")

    try:
        df = load_processed_data(input_path)
        result = check_scarcy(df, threshold)
        save_check_log(result)

        if generate_report and result["is_scarce"]:
            generate_warning_report(result)

        return result

    except FileNotFoundError as e:
        logger.error(f"Input file missing: {e}")
        raise
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        raise


def main():
    """Entry point for running the scarcity check as a script."""
    logger.info("Running Scarcity Check CLI...")
    try:
        result = run_scarcity_check()
        print(f"Scarcity Check Complete: {result['message']}")
        if result['is_scarce']:
            print(f"WARNING: T046 Triggered. Report saved to {WARNING_REPORT_PATH}")
            sys.exit(0) # Success, but with warning state
    except FileNotFoundError:
        print("ERROR: Processed data file not found. Run T027 (preprocess_pipeline) first.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()