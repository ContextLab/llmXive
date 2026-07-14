"""Data cleaning pipeline for agricultural survey data."""
from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import yaml

from config import get_config, get_processed_data_path, get_raw_data_path
from logging_config import log_operation, update_log_section


class CustomDataError(Exception):
    """Custom exception for data-related errors."""
    pass


def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """Setup logging configuration.

    Args:
        log_file: Optional log file path

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("data_cleaning")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler if specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger


def load_config() -> Dict[str, Any]:
    """Load configuration from YAML file.

    Returns:
        Configuration dictionary
    """
    config_path = get_config("config_path", "code/config.yaml")
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    return {}


@log_operation
def load_raw_data(input_path: Optional[str] = None) -> pd.DataFrame:
    """Load raw survey data from CSV file.

    Args:
        input_path: Optional path to input file

    Returns:
        DataFrame with raw data

    Raises:
        CustomDataError: If file cannot be loaded
    """
    if input_path is None:
        raw_dir = get_raw_data_path()
        input_path = str(raw_dir / "survey_data.csv")

    if not os.path.exists(input_path):
        raise CustomDataError(f"Raw data file not found: {input_path}")

    try:
        df = pd.read_csv(input_path)
        logging.info(f"Loaded {len(df)} records from {input_path}")
        return df
    except Exception as e:
        raise CustomDataError(f"Failed to load raw data: {e}")


@log_operation
def validate_variables(df: pd.DataFrame, required_vars: Optional[List[str]] = None) -> Dict[str, Any]:
    """Validate that required variables are present in the dataset.

    Args:
        df: Input DataFrame
        required_vars: List of required variable names

    Returns:
        Dictionary with validation results
    """
    if required_vars is None:
        required_vars = [
            'age', 'education', 'farm_size', 'credit_access',
            'adoption_sustainable_practices', 'community_engagement'
        ]

    missing_vars = []
    for var in required_vars:
        if var not in df.columns:
            missing_vars.append(var)

    validation_result = {
        "status": "passed" if not missing_vars else "failed",
        "missing_variables": missing_vars,
        "total_variables": len(df.columns),
        "required_variables": len(required_vars)
    }

    logging.info(f"Variable validation: {validation_result['status']}")
    if missing_vars:
        logging.warning(f"Missing variables: {missing_vars}")

    return validation_result


@log_operation
def calculate_missingness(df: pd.DataFrame, threshold: float = 0.3) -> Dict[str, float]:
    """Calculate missing value percentages for each column.

    Args:
        df: Input DataFrame
        threshold: Threshold for flagging high missingness

    Returns:
        Dictionary with missingness percentages
    """
    missingness = (df.isnull().sum() / len(df)) * 100
    high_missingness_cols = missingness[missingness > threshold * 100].index.tolist()

    logging.info(f"Calculated missingness for {len(df.columns)} columns")
    if high_missingness_cols:
        logging.warning(f"Columns with >{threshold*100}% missing: {high_missingness_cols}")

    return missingness.to_dict()


@log_operation
def handle_missing_values(
    df: pd.DataFrame,
    threshold: float = 0.3,
    strategy: str = "drop"
) -> pd.DataFrame:
    """Handle missing values in the dataset.

    Args:
        df: Input DataFrame
        threshold: Maximum allowed missingness per row (0.0 to 1.0)
        strategy: Strategy for handling missing values ('drop' or 'impute')

    Returns:
        Cleaned DataFrame
    """
    original_rows = len(df)

    # Calculate row-wise missingness
    row_missingness = df.isnull().sum(axis=1) / len(df.columns)

    # Drop rows with excessive missingness
    rows_to_drop = row_missingness > threshold
    df_cleaned = df[~rows_to_drop]

    dropped_rows = original_rows - len(df_cleaned)
    logging.info(f"Dropped {dropped_rows} rows with >{threshold*100}% missing values")

    # Handle remaining missing values
    if strategy == "impute":
        # Impute numeric columns with median
        numeric_cols = df_cleaned.select_dtypes(include=['number']).columns
        for col in numeric_cols:
            median_val = df_cleaned[col].median()
            df_cleaned[col] = df_cleaned[col].fillna(median_val)

        # Impute categorical columns with mode
        categorical_cols = df_cleaned.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            mode_val = df_cleaned[col].mode()
            if len(mode_val) > 0:
                df_cleaned[col] = df_cleaned[col].fillna(mode_val[0])

        logging.info("Imputed remaining missing values")
    else:
        # Drop any remaining rows with missing values
        initial_count = len(df_cleaned)
        df_cleaned = df_cleaned.dropna()
        final_dropped = initial_count - len(df_cleaned)
        if final_dropped > 0:
            logging.info(f"Dropped {final_dropped} additional rows with any missing values")

    return df_cleaned


@log_operation
def normalize_categorical_codes(
    df: pd.DataFrame,
    categorical_mappings: Optional[Dict[str, Dict[Any, Any]]] = None
) -> pd.DataFrame:
    """Normalize categorical variable codes.

    Args:
        df: Input DataFrame
        categorical_mappings: Dictionary of column -> {old: new} mappings

    Returns:
        DataFrame with normalized categorical codes
    """
    if categorical_mappings is None:
        # Default mappings for common variables
        categorical_mappings = {
            'education': {
                'none': 0, 'primary': 1, 'secondary': 2, 'tertiary': 3,
                'None': 0, 'Primary': 1, 'Secondary': 2, 'Tertiary': 3
            },
            'credit_access': {
                'yes': 1, 'no': 0, 'Yes': 1, 'No': 0,
                'true': 1, 'false': 0, 'True': 1, 'False': 0
            }
        }

    df_normalized = df.copy()

    for col, mapping in categorical_mappings.items():
        if col in df_normalized.columns:
            df_normalized[col] = df_normalized[col].apply(
                lambda x: mapping.get(x, x) if x in mapping else x
            )
            logging.info(f"Normalized categorical codes for column: {col}")

    return df_normalized


@log_operation
def calculate_power_analysis(
    df: pd.DataFrame,
    outcome_col: str = 'adoption_binary',
    num_predictors: int = 5
) -> Dict[str, Any]:
    """Calculate power analysis metrics for the dataset.

    Args:
        df: Input DataFrame (should contain outcome column)
        outcome_col: Name of the binary outcome column
        num_predictors: Number of predictors in the planned model

    Returns:
        Dictionary with power analysis results
    """
    # Check if outcome column exists
    if outcome_col not in df.columns:
        # Estimate based on a non-negligible proportion if not available
        logging.warning(f"Outcome column '{outcome_col}' not found. Estimating power.")
        # Assume a conservative 20% adoption rate for estimation
        estimated_events = int(len(df) * 0.20)
        ratio = estimated_events / num_predictors if num_predictors > 0 else float('inf')
        return {
            "outcome_column": outcome_col,
            "available": False,
            "estimated_events": estimated_events,
            "num_predictors": num_predictors,
            "ratio": ratio,
            "shortfall": ratio < 10,
            "note": "Estimated based on assumed 20% adoption rate"
        }

    # Count positive outcomes
    positive_outcomes = df[outcome_col].sum()
    total_events = positive_outcomes

    # Calculate ratio
    ratio = total_events / num_predictors if num_predictors > 0 else float('inf')

    result = {
        "outcome_column": outcome_col,
        "available": True,
        "total_samples": len(df),
        "positive_outcomes": int(positive_outcomes),
        "num_predictors": num_predictors,
        "ratio": ratio,
        "shortfall": ratio < 10
    }

    if result["shortfall"]:
        logging.warning(
            f"Power analysis shows shortfall: {result['positive_outcomes']} events "
            f"for {num_predictors} predictors (ratio={ratio:.2f} < 10)"
        )
    else:
        logging.info(
            f"Power analysis: {result['positive_outcomes']} events for "
            f"{num_predictors} predictors (ratio={ratio:.2f})"
        )

    return result


@log_operation
def update_modeling_log_with_power_analysis(
    power_analysis_result: Dict[str, Any],
    log_path: Optional[str] = None
) -> None:
    """Update the modeling log with power analysis results.

    Args:
        power_analysis_result: Dictionary with power analysis results
        log_path: Optional path to modeling log file
    """
    if log_path is None:
        log_path = str(get_config("modeling_log_path", "modeling_log.yaml"))

    # Prepare data for logging
    log_data = {
        "power_analysis": power_analysis_result
    }

    # Add limitation note if there's a shortfall
    if power_analysis_result.get("shortfall", False):
        log_data["study_limitations"] = {
            "power_shortfall": True,
            "description": (
                "The ratio of events to predictors is below the recommended threshold of 10:1. "
                "Results should be interpreted with caution as statistical power may be limited."
            ),
            "ratio": power_analysis_result.get("ratio"),
            "events": power_analysis_result.get("positive_outcomes") or power_analysis_result.get("estimated_events"),
            "predictors": power_analysis_result.get("num_predictors")
        }

    update_log_section("power_analysis", log_data, log_path=log_path)


@log_operation
def export_cleaned_data(
    df: pd.DataFrame,
    output_path: Optional[str] = None,
    include_metadata: bool = True
) -> str:
    """Export cleaned data to CSV file.

    Args:
        df: Cleaned DataFrame
        output_path: Optional output path
        include_metadata: Whether to include metadata in a separate file

    Returns:
        Path to the exported file
    """
    if output_path is None:
        proc_dir = get_processed_data_path()
        output_path = str(proc_dir / "cleaned_data.csv")

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Export to CSV
    df.to_csv(output_path, index=False)
    logging.info(f"Exported cleaned data to {output_path} ({len(df)} rows)")

    # Optionally save metadata
    if include_metadata:
        metadata_path = str(Path(output_path).parent / "cleaned_data_metadata.yaml")
        metadata = {
            "export_date": datetime.utcnow().isoformat(),
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "data_types": df.dtypes.astype(str).to_dict()
        }
        with open(metadata_path, 'w', encoding='utf-8') as f:
            yaml.dump(metadata, f, default_flow_style=False)
        logging.info(f"Exported metadata to {metadata_path}")

    return output_path


@log_operation
def main() -> None:
    """Main entry point for the data cleaning pipeline."""
    parser = argparse.ArgumentParser(description="Clean agricultural survey data")
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to input raw data file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to output cleaned data file"
    )
    parser.add_argument(
        "--missing-threshold",
        type=float,
        default=0.3,
        help="Maximum allowed missingness per row (0.0 to 1.0)"
    )
    parser.add_argument(
        "--strategy",
        type=str,
        choices=["drop", "impute"],
        default="drop",
        help="Strategy for handling missing values"
    )
    parser.add_argument(
        "--num-predictors",
        type=int,
        default=5,
        help="Number of predictors for power analysis"
    )

    args = parser.parse_args()

    # Setup logging
    log_file = "data_cleaning.log"
    logger = setup_logging(log_file)

    logging.info("Starting data cleaning pipeline")

    try:
        # Load raw data
        df = load_raw_data(args.input)

        # Validate variables
        validation_result = validate_variables(df)
        if validation_result["status"] == "failed":
            logging.warning("Variable validation failed, but continuing with available variables")

        # Calculate missingness
        missingness = calculate_missingness(df, args.missing_threshold)

        # Handle missing values
        df_cleaned = handle_missing_values(df, args.missing_threshold, args.strategy)

        # Normalize categorical codes
        df_cleaned = normalize_categorical_codes(df_cleaned)

        # Calculate power analysis
        # Try with 'adoption_binary' if it exists, otherwise estimate
        outcome_col = 'adoption_binary' if 'adoption_binary' in df_cleaned.columns else None
        if outcome_col is None:
            # Check for alternative outcome columns
            alt_outcomes = ['adoption_sustainable_practices', 'adopted_any']
            for alt in alt_outcomes:
                if alt in df_cleaned.columns:
                    outcome_col = alt
                    break

        if outcome_col:
            power_result = calculate_power_analysis(df_cleaned, outcome_col, args.num_predictors)
            update_modeling_log_with_power_analysis(power_result)
        else:
            # Estimate power if no outcome column found
            power_result = calculate_power_analysis(df_cleaned, num_predictors=args.num_predictors)
            update_modeling_log_with_power_analysis(power_result)

        # Export cleaned data
        output_path = export_cleaned_data(df_cleaned, args.output)

        logging.info("Data cleaning pipeline completed successfully")
        logging.info(f"Output saved to: {output_path}")

        # Update final status in log
        update_log_section(
            "data_cleaning",
            {
                "status": "completed",
                "input_rows": len(df),
                "output_rows": len(df_cleaned),
                "dropped_rows": len(df) - len(df_cleaned),
                "output_path": output_path
            }
        )

    except CustomDataError as e:
        logging.error(f"Data cleaning failed: {e}")
        update_log_section(
            "data_cleaning",
            {"status": "failed", "error": str(e)}
        )
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error during data cleaning: {e}")
        update_log_section(
            "data_cleaning",
            {"status": "failed", "error": str(e)}
        )
        sys.exit(1)


if __name__ == "__main__":
    main()