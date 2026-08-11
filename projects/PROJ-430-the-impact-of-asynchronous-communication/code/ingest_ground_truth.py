"""
Ingest Manual Ground Truth Data (Task T022b)

Implements logic to load `data/validation/manual_ground_truth.csv` if present,
validate its schema against `contracts/validation.schema.yaml`, and return
the validated dataframe.
"""
import logging
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd
import yaml
from config import get_config, ensure_directories_exist
from utils.logger import get_logger

logger = get_logger(__name__)

def load_ground_truth(config: Optional[Dict[str, Any]] = None) -> Optional[pd.DataFrame]:
    """
    Load manual ground truth data if it exists.

    Args:
        config: Optional configuration dictionary. If None, loads from defaults.

    Returns:
        pd.DataFrame: The loaded ground truth data if present.
        None: If the file does not exist.

    Raises:
        ValueError: If the file exists but fails schema validation.
        FileNotFoundError: If the file is missing and no synthetic fallback is requested (handled by caller).
    """
    cfg = config if config else get_config()
    data_dir = Path(cfg.get("data_dir", "data"))
    ground_truth_path = data_dir / "validation" / "manual_ground_truth.csv"

    # Ensure directory exists to avoid errors if path is weird, though we are reading
    ensure_directories_exist([ground_truth_path.parent])

    if not ground_truth_path.exists():
        logger.info(f"Manual ground truth file not found at {ground_truth_path}. "
                    "Proceeding to synthetic fallback logic in caller (T022c).")
        return None

    logger.info(f"Loading manual ground truth from {ground_truth_path}")

    try:
        df = pd.read_csv(ground_truth_path)
    except Exception as e:
        logger.error(f"Failed to read manual ground truth CSV: {e}")
        raise

    # Validate Schema
    schema_path = Path("contracts/validation.schema.yaml")
    if schema_path.exists():
        try:
            with open(schema_path, 'r') as f:
                schema = yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Could not load validation schema for checking: {e}")
            schema = None
    else:
        logger.warning(f"Validation schema not found at {schema_path}. Skipping schema validation.")
        schema = None

    if schema:
        required_columns = schema.get("required_columns", [])
        missing_cols = [col for col in required_columns if col not in df.columns]

        if missing_cols:
            error_msg = f"Ground truth file missing required columns: {missing_cols}. " \
                        f"Expected: {required_columns}. Found: {list(df.columns)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Type checks if defined in schema
        column_types = schema.get("column_types", {})
        for col, expected_type in column_types.items():
            if col in df.columns:
                if expected_type == "int" and not pd.api.types.is_integer_dtype(df[col]):
                    logger.warning(f"Column {col} is not integer type, attempting cast.")
                    try:
                        df[col] = pd.to_numeric(df[col], errors='raise').astype(int)
                    except:
                        raise ValueError(f"Column {col} cannot be cast to integer as required.")
                elif expected_type == "float" and not pd.api.types.is_float_dtype(df[col]):
                    try:
                        df[col] = pd.to_numeric(df[col], errors='raise')
                    except:
                        raise ValueError(f"Column {col} cannot be cast to float as required.")

    logger.info(f"Successfully loaded and validated {len(df)} rows of ground truth data.")
    return df

def log_ingestion_stats(df: Optional[pd.DataFrame]) -> None:
    """Log statistics about the loaded ground truth."""
    if df is None:
        logger.info("No ground truth data loaded.")
        return

    logger.info(f"Ground truth stats: {len(df)} rows, {len(df.columns)} columns.")
    if 'project_id' in df.columns:
        logger.info(f"Unique projects: {df['project_id'].nunique()}")
    if 'sentiment_score' in df.columns:
        logger.info(f"Sentiment range: [{df['sentiment_score'].min():.2f}, {df['sentiment_score'].max():.2f}]")

def run_ingest_ground_truth(config: Optional[Dict[str, Any]] = None) -> Optional[pd.DataFrame]:
    """
    Main entry point for the ground truth ingestion pipeline.
    Returns the validated dataframe or None.
    """
    df = load_ground_truth(config)
    log_ingestion_stats(df)
    return df

def main():
    """CLI entry point."""
    logger.info("Starting Manual Ground Truth Ingestion (T022b)")
    try:
        df = run_ingest_ground_truth()
        if df is not None:
            logger.info("Ingestion successful.")
            # Optional: print head for verification
            logger.info(df.head().to_string())
        else:
            logger.info("Ingestion skipped (file not found).")
    except Exception as e:
        logger.critical(f"Ingestion failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()