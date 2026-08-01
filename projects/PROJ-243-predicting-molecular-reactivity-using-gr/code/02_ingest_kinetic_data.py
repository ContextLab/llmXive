import os
import sys
import logging
import pandas as pd
from typing import Optional, Dict, List

from config import get_config, ensure_directories

# Import local utilities if needed, though pandas is sufficient for this task
# from utils.loaders import calculate_sha256 # Not strictly needed for ingestion if checksum verified by T009e

def setup_script_logging() -> logging.Logger:
    """
    Sets up logging for the script, directing output to the console and
    to a file in artifacts/logs/ if the directory exists.
    """
    logger = logging.getLogger("ingest_kinetic_data")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Add file handler if artifacts/logs exists
        config = get_config()
        log_dir = os.path.join(config['paths']['artifacts'], 'logs')
        if os.path.exists(log_dir):
            log_file = os.path.join(log_dir, 'ingest_kinetic_data.log')
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger

def validate_schema(df: pd.DataFrame, schema: Dict[str, type]) -> List[str]:
    """
    Validates that the DataFrame columns match the expected schema.
    Returns a list of validation errors.
    """
    errors = []
    expected_columns = set(schema.keys())
    actual_columns = set(df.columns)

    missing_cols = expected_columns - actual_columns
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")

    extra_cols = actual_columns - expected_columns
    if extra_cols:
        logging.warning(f"Extra columns found (ignored): {extra_cols}")

    for col, expected_type in schema.items():
        if col in df.columns:
            # Check if the dtype is compatible (e.g., int64 vs int)
            if not pd.api.types.is_dtype_equal(df[col].dtype, expected_type) and not isinstance(df[col].dtype, pd.StringDtype):
                # Allow some flexibility for numeric types
                if not (pd.api.types.is_numeric_dtype(df[col]) and expected_type in [int, float, str]):
                    if expected_type == str and not pd.api.types.is_string_dtype(df[col]):
                        errors.append(f"Column '{col}' has dtype {df[col].dtype}, expected {expected_type}")
                    elif expected_type != str:
                        errors.append(f"Column '{col}' has dtype {df[col].dtype}, expected {expected_type}")
    
    return errors

def ingest_kinetic_dataset(
    raw_path: str,
    output_path: str,
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Ingests the verified kinetic dataset from raw_path to output_path.
    Performs schema validation and ensures data integrity.
    
    Args:
        raw_path: Path to the raw CSV file (verified by T009e).
        output_path: Path where the ingested CSV will be saved.
        logger: Logger instance.
        
    Returns:
        True if ingestion was successful, False otherwise.
    """
    if logger is None:
        logger = setup_script_logging()

    logger.info(f"Starting ingestion of kinetic dataset from {raw_path}")

    if not os.path.exists(raw_path):
        logger.error(f"Raw file not found: {raw_path}")
        return False

    try:
        # Load raw data
        df = pd.read_csv(raw_path)
        logger.info(f"Loaded {len(df)} rows from {raw_path}")

        # Define expected schema based on typical kinetic data requirements
        # Assuming columns: molecule_id, smiles, reaction_type, rate_constant, temperature, units
        # Adjust based on actual data if known, but strict validation is safer
        # Since T009d downloaded a "verified" source, we assume standard columns exist.
        # We will validate that essential columns exist.
        required_columns = ['molecule_id', 'smiles', 'reaction_type', 'rate_constant', 'temperature']
        
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            logger.error(f"Missing required columns: {missing}")
            return False

        # Basic type coercion/validation
        # Ensure numeric columns are numeric
        for col in ['rate_constant', 'temperature']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='raise')

        # Ensure string columns are string
        for col in ['molecule_id', 'smiles', 'reaction_type']:
            if col in df.columns:
                df[col] = df[col].astype(str)

        # Schema validation (logical check)
        schema = {
            'molecule_id': str,
            'smiles': str,
            'reaction_type': str,
            'rate_constant': float,
            'temperature': float
        }
        
        errors = validate_schema(df, schema)
        if errors:
            logger.error(f"Schema validation failed: {errors}")
            return False

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Save to CSV
        df.to_csv(output_path, index=False)
        logger.info(f"Successfully ingested and saved {len(df)} rows to {output_path}")

        # Log summary
        logger.info(f"Dataset summary: {df['reaction_type'].value_counts().to_dict()}")

        return True

    except Exception as e:
        logger.error(f"Error during ingestion: {e}", exc_info=True)
        return False

def main():
    """
    Main entry point for the kinetic dataset ingestion script.
    """
    logger = setup_script_logging()
    config = get_config()

    # Paths
    raw_path = os.path.join(config['paths']['raw'], 'kinetic_dataset_raw.csv')
    output_path = os.path.join(config['paths']['assets'], 'kinetic_dataset.csv')

    logger.info(f"Configuration loaded. Raw: {raw_path}, Output: {output_path}")

    success = ingest_kinetic_dataset(raw_path, output_path, logger)

    if success:
        logger.info("Ingestion completed successfully.")
        sys.exit(0)
    else:
        logger.error("Ingestion failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
