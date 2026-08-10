"""
Outlier Detection Module for GitHub Issue Resolution Times.

Implements the IQR method (Q3 + 1.5 * IQR) to detect extreme outliers
in resolution time data as specified in Spec US-2 Acceptance Scenario 3.
"""

import json
import logging
import sys
import math
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/logs/outlier_detection.log')
    ]
)
logger = logging.getLogger(__name__)

def load_cleaned_data(data_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load the cleaned issues dataset.

    Args:
        data_path: Path to the cleaned CSV file. Defaults to 'data/processed/cleaned_issues.csv'.

    Returns:
        DataFrame containing the cleaned issues data.

    Raises:
        FileNotFoundError: If the cleaned data file does not exist.
        ValueError: If the required 'resolution_time_hours' column is missing.
    """
    if data_path is None:
        data_path = Path(__file__).parent.parent.parent / "data" / "processed" / "cleaned_issues.csv"
    else:
        data_path = Path(data_path)

    if not data_path.exists():
        raise FileNotFoundError(f"Cleaned data file not found: {data_path}")

    logger.info(f"Loading cleaned data from {data_path}")
    df = pd.read_csv(data_path)

    if 'resolution_time_hours' not in df.columns:
        raise ValueError("Required column 'resolution_time_hours' not found in dataset.")

    # Filter out non-numeric or infinite values for calculation
    df = df[df['resolution_time_hours'].apply(lambda x: isinstance(x, (int, float)) and math.isfinite(x))]

    logger.info(f"Loaded {len(df)} valid issues for outlier detection.")
    return df

def detect_outliers_iqr(df: pd.DataFrame, column: str = 'resolution_time_hours') -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Detect outliers using the IQR method (Q3 + 1.5 * IQR).

    This method identifies extreme outliers as values greater than Q3 + 1.5 * IQR.
    Note: Resolution times are strictly positive, so we only check the upper bound.

    Args:
        df: DataFrame containing the data.
        column: Name of the column to analyze for outliers.

    Returns:
        Tuple of (outliers_df, stats_dict) where:
            - outliers_df: DataFrame containing only the outlier rows.
            - stats_dict: Dictionary containing Q1, Q3, IQR, upper_bound, count, and percentage.
    """
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame.")

    values = df[column].dropna()

    if len(values) == 0:
        logger.warning("No valid values found for outlier detection.")
        return df.iloc[0:0], {
            'q1': None,
            'q3': None,
            'iqr': None,
            'upper_bound': None,
            'lower_bound': None,
            'outlier_count': 0,
            'outlier_percentage': 0.0,
            'total_count': 0
        }

    q1 = values.quantile(0.25)
    q3 = values.quantile(0.75)
    iqr = q3 - q1

    # IQR Method: Outliers are values > Q3 + 1.5 * IQR
    # Since resolution time cannot be negative, we ignore the lower bound (Q1 - 1.5*IQR)
    upper_bound = q3 + 1.5 * iqr
    lower_bound = q1 - 1.5 * iqr  # Included for completeness, though likely irrelevant for time

    logger.info(f"Calculated IQR stats for {column}: Q1={q1:.2f}, Q3={q3:.2f}, IQR={iqr:.2f}")
    logger.info(f"Outlier threshold (Upper Bound): {upper_bound:.2f} hours")

    # Identify outliers (strictly greater than upper bound)
    outlier_mask = df[column] > upper_bound
    outliers_df = df[outlier_mask].copy()

    total_count = len(df)
    outlier_count = len(outliers_df)
    outlier_percentage = (outlier_count / total_count * 100) if total_count > 0 else 0.0

    stats = {
        'q1': float(q1),
        'q3': float(q3),
        'iqr': float(iqr),
        'upper_bound': float(upper_bound),
        'lower_bound': float(lower_bound),
        'outlier_count': int(outlier_count),
        'outlier_percentage': float(outlier_percentage),
        'total_count': int(total_count)
    }

    logger.info(f"Detected {outlier_count} outliers ({outlier_percentage:.2f}% of total).")

    return outliers_df, stats

def save_report(outliers_df: pd.DataFrame, stats: Dict[str, Any], output_path: Optional[str] = None) -> None:
    """
    Save the outlier detection report to a JSON file.

    Args:
        outliers_df: DataFrame containing the outlier records.
        stats: Dictionary containing the statistical summary.
        output_path: Path for the output JSON file. Defaults to 'data/processed/outlier_report.json'.
    """
    if output_path is None:
        output_path = Path(__file__).parent.parent.parent / "data" / "processed" / "outlier_report.json"
    else:
        output_path = Path(output_path)

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Prepare report content
    report = {
        'method': 'IQR (Q3 + 1.5 * IQR)',
        'statistics': stats,
        'outlier_records': outliers_df.to_dict(orient='records')
    }

    logger.info(f"Saving outlier report to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)

    logger.info("Outlier report saved successfully.")

def main():
    """Main entry point for outlier detection task."""
    logger.info("Starting Outlier Detection (T017)...")

    try:
        # 1. Load Data
        df = load_cleaned_data()

        # 2. Detect Outliers using IQR method
        outliers_df, stats = detect_outliers_iqr(df, column='resolution_time_hours')

        # 3. Save Report
        save_report(outliers_df, stats)

        # 4. Log Summary
        logger.info(f"Task T017 Completed. Found {stats['outlier_count']} outliers ({stats['outlier_percentage']:.2f}%).")

    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during outlier detection: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()