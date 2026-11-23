import os
import json
import logging
import pandas as pd
from pathlib import Path
from config import ensure_dirs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_schema(df: pd.DataFrame) -> bool:
    """
    Validate that the sensitivity report has the required schema.
    
    Required columns:
    - threshold
    - metric_name
    - std_dev
    - is_stable
    """
    required_columns = ["threshold", "metric_name", "std_dev", "is_stable"]
    
    for col in required_columns:
        if col not in df.columns:
            logger.error(f"Missing required column: {col}")
            return False
    
    # Validate data types
    if not pd.api.types.is_numeric_dtype(df["threshold"]) and not df["threshold"].apply(lambda x: x == "aggregate" or isinstance(x, float)).all():
        logger.error("threshold column should be numeric or 'aggregate'")
        return False
    
    if not pd.api.types.is_string_dtype(df["metric_name"]) and not pd.api.types.is_object_dtype(df["metric_name"]):
        logger.error("metric_name column should be string")
        return False
    
    if not pd.api.types.is_numeric_dtype(df["std_dev"]):
        logger.error("std_dev column should be numeric")
        return False
    
    if not pd.api.types.is_bool_dtype(df["is_stable"]) and not df["is_stable"].apply(lambda x: isinstance(x, bool) or x in [True, False, "True", "False"]).all():
        logger.error("is_stable column should be boolean")
        return False
    
    return True

def validate_results(df: pd.DataFrame) -> bool:
    """
    Validate the content of the sensitivity report.
    """
    # Check for NaN values in critical columns
    if df["std_dev"].isna().any():
        logger.warning("Some std_dev values are NaN")
    
    # Check that we have results for multiple thresholds
    unique_thresholds = df["threshold"].unique()
    if len(unique_thresholds) < 2:
        logger.warning(f"Only {len(unique_thresholds)} unique thresholds found, expected at least 2")
    
    # Check that we have results for multiple metrics
    unique_metrics = df["metric_name"].unique()
    if len(unique_metrics) < 1:
        logger.error("No metrics found in the report")
        return False
    
    logger.info(f"Found {len(unique_metrics)} unique metrics: {unique_metrics}")
    logger.info(f"Found {len(unique_thresholds)} unique thresholds: {unique_thresholds}")
    
    return True

def main():
    """Validate the sensitivity analysis output."""
    from config import get_config_summary
    
    config = get_config_summary()
    output_path = Path(config["results_dir"]) / "sensitivity_density_report.csv"
    
    if not output_path.exists():
        logger.error(f"Output file not found: {output_path}")
        return 1
    
    try:
        df = pd.read_csv(output_path)
        logger.info(f"Loaded {len(df)} rows from {output_path}")
        
        if not validate_schema(df):
            logger.error("Schema validation failed")
            return 1
        
        if not validate_results(df):
            logger.error("Content validation failed")
            return 1
        
        logger.info("Sensitivity report validation PASSED")
        print(df.to_string())
        return 0
        
    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())