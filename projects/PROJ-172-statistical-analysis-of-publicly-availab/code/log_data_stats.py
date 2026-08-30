"""
T017: Add logging for data ingestion stats, synthetic fallback triggers, and imputation actions.

This module provides a utility to log key statistics from the data pipeline,
specifically focusing on:
1. Data ingestion statistics (rows, columns, completeness).
2. Synthetic fallback triggers (if real data fetch failed).
3. Imputation actions taken during feature engineering.

It integrates with the existing logging infrastructure in `code/utils/logging.py`.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Import existing logging utilities
from utils.logging import get_logger, log_info, log_warning, log_error, log_debug

# Import config for paths
from config import ensure_directories

def log_data_ingestion_stats(
    logger: logging.Logger,
    stats: Dict[str, Any],
    is_real_data: bool,
    source_path: Optional[str] = None
) -> None:
    """
    Log data ingestion statistics.

    Args:
        logger: The logger instance to use.
        stats: Dictionary containing ingestion stats (e.g., row_count, column_count, completeness_rate).
        is_real_data: Boolean flag indicating if the data source was real or synthetic.
        source_path: Optional path to the source data file.
    """
    log_info(logger, f"Data Ingestion Stats: Real Data = {is_real_data}")
    if source_path:
        log_info(logger, f"Source Path: {source_path}")

    for key, value in stats.items():
        if isinstance(value, float):
            log_info(logger, f"  {key}: {value:.4f}")
        else:
            log_info(logger, f"  {key}: {value}")

    if not is_real_data:
        log_warning(logger, "SYNTHETIC FALLBACK TRIGGERED: Data generated synthetically due to fetch failure.")
        log_warning(logger, "Results should be treated as 'Pipeline Validation Only' until real data is available.")


def log_imputation_actions(
    logger: logging.Logger,
    imputation_summary: Dict[str, Any]
) -> None:
    """
    Log actions taken during imputation of missing advanced metrics.

    Args:
        logger: The logger instance to use.
        imputation_summary: Dictionary describing what was imputed (e.g., { 'wOBA': 'league_avg_2018', 'count': 150 }).
    """
    if not imputation_summary:
        log_debug(logger, "No imputation actions were necessary.")
        return

    log_info(logger, "Imputation Actions Summary:")
    for feature, action in imputation_summary.items():
        if isinstance(action, dict):
            log_info(logger, f"  Feature '{feature}':")
            for sub_key, sub_val in action.items():
                log_info(logger, f"    - {sub_key}: {sub_val}")
        else:
            log_info(logger, f"  Feature '{feature}': {action}")


def log_synthetic_fallback_trigger(
    logger: logging.Logger,
    reason: str,
    error_code: Optional[str] = None
) -> None:
    """
    Explicitly log the trigger of the synthetic data fallback protocol.

    Args:
        logger: The logger instance to use.
        reason: The reason for the fallback (e.g., "403 Forbidden", "Timeout").
        error_code: Optional specific error code.
    """
    log_warning(logger, "=" * 60)
    log_warning(logger, "SYNTHETIC FALLBACK PROTOCOL ACTIVATED")
    log_warning(logger, "=" * 60)
    log_warning(logger, f"Reason: {reason}")
    if error_code:
        log_warning(logger, f"Error Code: {error_code}")
    log_warning(logger, "Switching to synthetic data generation mode.")
    log_warning(logger, "Marking pipeline status as 'Validation-Only'.")
    log_warning(logger, "=" * 60)


def main() -> None:
    """
    Main entry point for demonstration/testing of the logging functions.
    This function simulates a pipeline run to demonstrate the logging output.
    """
    logger = get_logger("data_stats_logger")
    
    # Ensure directories exist
    ensure_directories()

    log_info(logger, "Starting Data Stats Logging Demonstration (T017)...")

    # Simulate Data Ingestion Stats
    ingestion_stats = {
        "row_count": 15000,
        "column_count": 45,
        "completeness_rate": 0.96,
        "missing_values_count": 600
    }
    
    log_data_ingestion_stats(
        logger, 
        stats=ingestion_stats, 
        is_real_data=True, 
        source_path="data/processed/mlb_games_2000_2022.csv"
    )

    # Simulate a Synthetic Fallback Trigger (commented out to avoid spam in real runs, but logic exists)
    # log_synthetic_fallback_trigger(
    #     logger, 
    #     reason="HTTP 429 Too Many Requests from Retrosheet", 
    #     error_code="429"
    # )

    # Simulate Imputation Actions
    imputation_summary = {
        "wOBA": "Imputed with league average for year 2018",
        "BABIP": "Imputed with league average for year 2018",
        "total_imputed_rows": 125
    }

    log_imputation_actions(logger, imputation_summary)

    log_info(logger, "Data stats logging demonstration complete.")


if __name__ == "__main__":
    main()