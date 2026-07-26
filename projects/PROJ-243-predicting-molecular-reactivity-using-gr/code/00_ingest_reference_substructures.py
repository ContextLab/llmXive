import os
import sys
import logging
import pandas as pd
from typing import Optional

# Import from existing API surface
from utils.loaders import calculate_sha256
from config import get_config, ensure_directories
from utils.logging_utils import setup_logging, get_logger, log_metric

# Constants for schema validation
EXPECTED_COLUMNS = {'substructure_smiles', 'reactive_type', 'source_literature', 'confidence_score'}
REQUIRED_COLUMNS = {'substructure_smiles', 'reactive_type'}
MIN_CONFIDENCE = 0.0
MAX_CONFIDENCE = 1.0

def validate_schema(df: pd.DataFrame, logger: logging.Logger) -> bool:
    """
    Validates the dataframe against the expected schema for reference substructures.
    
    Args:
        df: The dataframe to validate.
        logger: The logger instance.
        
    Returns:
        bool: True if validation passes, False otherwise.
    """
    if df.empty:
        logger.error("DataFrame is empty.")
        return False

    # Check for required columns
    missing_required = REQUIRED_COLUMNS - set(df.columns)
    if missing_required:
        logger.error(f"Missing required columns: {missing_required}")
        return False

    # Check for unexpected columns (strict validation)
    unexpected = set(df.columns) - EXPECTED_COLUMNS
    if unexpected:
        logger.warning(f"Unexpected columns found: {unexpected}. Proceeding with validation of required columns only.")

    # Validate data types and values
    # Check substructure_smiles is not empty
    if df['substructure_smiles'].isna().any() or (df['substructure_smiles'] == '').any():
        logger.error("Found empty or NaN values in 'substructure_smiles' column.")
        return False

    # Validate confidence_score if present
    if 'confidence_score' in df.columns:
        if not pd.api.types.is_numeric_dtype(df['confidence_score']):
            logger.error("Column 'confidence_score' must be numeric.")
            return False
        
        invalid_scores = df[
            (df['confidence_score'] < MIN_CONFIDENCE) | 
            (df['confidence_score'] > MAX_CONFIDENCE)
        ]
        if not invalid_scores.empty:
            logger.error(f"Found {len(invalid_scores)} rows with confidence_score outside [{MIN_CONFIDENCE}, {MAX_CONFIDENCE}].")
            return False

    logger.info("Schema validation passed.")
    return True

def ingest_reference_substructures(
    input_path: str,
    output_path: str,
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Ingests the verified raw data into the assets directory with schema validation.
    
    Args:
        input_path: Path to the raw CSV file (data/raw/reference_substructures_raw.csv).
        output_path: Path to save the validated CSV file (data/assets/reference_substructures.csv).
        logger: Optional logger instance.
        
    Returns:
        bool: True if ingestion is successful, False otherwise.
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    try:
        # Load the raw data
        logger.info(f"Loading raw data from {input_path}")
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} rows.")

        # Validate schema
        if not validate_schema(df, logger):
            logger.error("Schema validation failed. Aborting ingestion.")
            return False

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Save the validated data
        logger.info(f"Saving validated data to {output_path}")
        df.to_csv(output_path, index=False)
        
        # Log success metric
        log_metric("ingestion_rows", len(df), logger=logger)
        log_metric("ingestion_status", "success", logger=logger)

        logger.info("Ingestion completed successfully.")
        return True

    except FileNotFoundError:
        logger.error(f"Input file not found: {input_path}")
        return False
    except pd.errors.EmptyDataError:
        logger.error(f"Input file is empty: {input_path}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during ingestion: {e}")
        return False

def main():
    """Main entry point for the ingestion script."""
    config = get_config()
    logger = setup_logging("ingest_reference_substructures")
    
    input_path = config.get('paths', {}).get('raw_reference_substructures', 'data/raw/reference_substructures_raw.csv')
    output_path = config.get('paths', {}).get('assets_reference_substructures', 'data/assets/reference_substructures.csv')

    # Ensure directories exist
    ensure_directories(config)

    logger.info(f"Starting ingestion of reference substructures from {input_path} to {output_path}")
    
    success = ingest_reference_substructures(input_path, output_path, logger)
    
    if success:
        logger.info("Task T009c completed successfully.")
        sys.exit(0)
    else:
        logger.error("Task T009c failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
