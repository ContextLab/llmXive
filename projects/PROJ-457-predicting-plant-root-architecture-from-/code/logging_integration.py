"""
Logging integration for User Story 1 (T019).

This module consolidates and enhances the logging capabilities for the
data ingestion and preprocessing pipeline (US1). It ensures that:
1. Exclusion counts (species < 20, missing nutrients, manipulated data)
   are logged with specific context and severity levels.
2. Transformation steps (log-transform, z-score) are logged with
   details on parameters and data statistics.
3. A dedicated logger is configured for pipeline execution to ensure
   traceability and auditability.

The logging output is directed to both console (for immediate feedback)
and a file (for persistent records), as configured in `config.py`.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import setup_logging, get_config


def get_pipeline_logger(name: str = "pipeline") -> logging.Logger:
    """
    Retrieve or create a logger specifically for the US1 pipeline.
    
    Args:
        name: The name for the logger instance.
        
    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        # Logger already configured, return it
        return logger
        
    # Configure based on project settings
    config = get_config()
    log_level = getattr(logging, config.get("LOG_LEVEL", "INFO"))
    
    logger.setLevel(log_level)
    
    # Create handlers
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Ensure log directory exists
    log_dir = Path(config.get("LOG_DIR", "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f"{name}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Prevent propagation to root logger to avoid duplicate logs
    logger.propagate = False
    
    return logger


def log_exclusion_counts(
    logger: logging.Logger,
    total_rows_input: int,
    total_rows_output: int,
    exclusion_breakdown: Dict[str, int],
    species_exclusion_details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log the results of data filtering operations.
    
    This function logs:
    - Total rows before and after filtering.
    - Breakdown of rows excluded by reason (species count, missing nutrients,
      manipulated data).
    - Detailed information about excluded species if available.
    
    Args:
        logger: The logger instance to use.
        total_rows_input: Number of rows before filtering.
        total_rows_output: Number of rows remaining after filtering.
        exclusion_breakdown: Dictionary mapping exclusion reasons to counts.
        species_exclusion_details: Optional dictionary with details about
            excluded species (e.g., list of names, total count).
    """
    excluded_count = total_rows_input - total_rows_output
    
    logger.info("=" * 60)
    logger.info("DATA FILTERING SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Input rows:  {total_rows_input:,}")
    logger.info(f"Output rows: {total_rows_output:,}")
    logger.info(f"Total excluded: {excluded_count:,} ({(excluded_count / max(total_rows_input, 1)) * 100:.2f}%)")
    
    logger.info("Exclusion Breakdown:")
    for reason, count in sorted(exclusion_breakdown.items()):
        logger.info(f"  - {reason}: {count:,}")
    
    if species_exclusion_details:
        total_species_input = species_exclusion_details.get("total_species_input", 0)
        excluded_species_count = species_exclusion_details.get("excluded_species_count", 0)
        excluded_species_list = species_exclusion_details.get("excluded_species_list", [])
        
        logger.info(f"Species Statistics:")
        logger.info(f"  - Total species in input: {total_species_input}")
        logger.info(f"  - Species excluded (n < 20): {excluded_species_count}")
        if excluded_species_list:
            logger.info(f"  - Excluded species list: {', '.join(excluded_species_list[:10])}" + 
                      (f" ... and {len(excluded_species_list) - 10} more" if len(excluded_species_list) > 10 else ""))
    logger.info("=" * 60)

def log_transformation_step(
    logger: logging.Logger,
    step_name: str,
    columns_affected: List[str],
    transformation_type: str,
    parameters: Optional[Dict[str, Any]] = None,
    stats_before: Optional[Dict[str, Any]] = None,
    stats_after: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log details of a data transformation step.
    
    This function provides a structured log entry for transformations such as
    log-transformation or z-score normalization, including statistics before
    and after the operation to verify correctness.
    
    Args:
        logger: The logger instance to use.
        step_name: Name of the transformation step (e.g., "log_transform", "zscore_norm").
        columns_affected: List of column names that were transformed.
        transformation_type: Type of transformation applied.
        parameters: Optional dictionary of parameters used in the transformation.
        stats_before: Optional dictionary of statistics before transformation.
        stats_after: Optional dictionary of statistics after transformation.
    """
    logger.info("-" * 40)
    logger.info(f"TRANSFORMATION: {step_name}")
    logger.info(f"Type: {transformation_type}")
    logger.info(f"Columns affected: {', '.join(columns_affected)}")
    
    if parameters:
        logger.info("Parameters:")
        for key, value in parameters.items():
            logger.info(f"  - {key}: {value}")
    
    if stats_before:
        logger.info("Statistics Before:")
        for col, stat in stats_before.items():
            logger.info(f"  - {col}: {stat}")
    
    if stats_after:
        logger.info("Statistics After:")
        for col, stat in stats_after.items():
            logger.info(f"  - {col}: {stat}")
    
    logger.info("-" * 40)

def log_data_quality_checks(
    logger: logging.Logger,
    column_name: str,
    null_count: int,
    total_count: int,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
    mean_val: Optional[float] = None
) -> None:
    """
    Log results of data quality checks on a specific column.
    
    Args:
        logger: The logger instance to use.
        column_name: Name of the column being checked.
        null_count: Number of null/missing values.
        total_count: Total number of rows.
        min_val: Minimum value (if applicable).
        max_val: Maximum value (if applicable).
        mean_val: Mean value (if applicable).
    """
    null_pct = (null_count / max(total_count, 1)) * 100
    logger.info(f"QUALITY CHECK: {column_name}")
    logger.info(f"  - Total rows: {total_count:,}")
    logger.info(f"  - Null values: {null_count:,} ({null_pct:.2f}%)")
    
    if min_val is not None:
        logger.info(f"  - Min: {min_val}")
    if max_val is not None:
        logger.info(f"  - Max: {max_val}")
    if mean_val is not None:
        logger.info(f"  - Mean: {mean_val}")

def main() -> None:
    """
    Main entry point for demonstrating the logging integration.
    
    This function sets up the logger and demonstrates the various logging
    capabilities for exclusion counts and transformation steps.
    """
    # Initialize logging
    logger = get_pipeline_logger("us1_logging_demo")
    
    logger.info("Starting US1 Logging Integration Demo")
    
    # Demonstrate exclusion logging
    exclusion_breakdown = {
        "species_n_less_than_20": 150,
        "missing_phosphorus": 45,
        "missing_nitrogen": 30,
        "manipulated_data": 200
    }
    
    species_details = {
        "total_species_input": 50,
        "excluded_species_count": 12,
        "excluded_species_list": ["Zea mays", "Solanum lycopersicum", "Arabidopsis thaliana"]
    }
    
    log_exclusion_counts(
        logger,
        total_rows_input=10000,
        total_rows_output=9575,
        exclusion_breakdown=exclusion_breakdown,
        species_exclusion_details=species_details
    )
    
    # Demonstrate transformation logging
    log_transformation_step(
        logger,
        step_name="log_transform_root_metrics",
        columns_affected=["root_length", "branching_density", "surface_area"],
        transformation_type="log1p",
        parameters={"base": "e", "offset": 1},
        stats_before={"root_length": {"mean": 12.5, "min": 0.0, "max": 150.0}},
        stats_after={"root_length": {"mean": 2.4, "min": 0.0, "max": 5.0}}
    )
    
    log_transformation_step(
        logger,
        step_name="zscore_normalize_nutrients",
        columns_affected=["phosphorus", "nitrogen"],
        transformation_type="z_score",
        parameters={"method": "global"},
        stats_before={"phosphorus": {"mean": 45.2, "std": 12.3}},
        stats_after={"phosphorus": {"mean": 0.0, "std": 1.0}}
    )
    
    # Demonstrate data quality logging
    log_data_quality_checks(
        logger,
        column_name="phosphorus",
        null_count=45,
        total_count=10000,
        min_val=0.5,
        max_val=250.0,
        mean_val=45.2
    )
    
    logger.info("US1 Logging Integration Demo Completed")

if __name__ == "__main__":
    main()