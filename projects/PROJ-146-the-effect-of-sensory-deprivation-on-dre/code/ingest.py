import os
import sys
import logging
import pandas as pd
import yaml
from datetime import datetime
from logging_config import setup_logging

# Import from sibling modules
from generate_data import generate_synthetic_datasets, load_protocol

def check_sensory_deprivation_tags(df: pd.DataFrame, column: str = 'condition') -> bool:
    """
    Check if the dataframe contains sensory deprivation tags in the specified column.
    
    Args:
        df: Input DataFrame.
        column: Column name to check.
        
    Returns:
        True if tags are found, False otherwise.
    """
    logger = logging.getLogger(__name__)
    if column not in df.columns:
        logger.warning(f"Column '{column}' not found in dataframe")
        return False
    
    # Check for sensory deprivation related strings
    tags = ['sensory_deprivation', 'deprivation', 'strict', 'moderate', 'partial']
    found = any(df[column].astype(str).str.contains(tag, case=False, na=False).any() for tag in tags)
    
    if found:
        logger.info(f"Found sensory deprivation tags in column '{column}'")
    else:
        logger.info(f"No sensory deprivation tags found in column '{column}'")
        
    return found

def validate_required_columns(df: pd.DataFrame) -> bool:
    """
    Validate that the dataframe contains required columns.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        True if all required columns are present, False otherwise.
    """
    logger = logging.getLogger(__name__)
    required_cols = ['condition', 'recall', 'bizarreness', 'participant_id']
    missing = [col for col in required_cols if col not in df.columns]
    
    if missing:
        logger.error(f"Missing required columns: {missing}")
        return False
    
    logger.info("All required columns present")
    return True

def ingest_csv(filepath: str) -> pd.DataFrame:
    """
    Ingest a CSV file and validate its structure.
    
    Args:
        filepath: Path to the CSV file.
        
    Returns:
        Validated DataFrame.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Ingesting CSV: {filepath}")
    
    try:
        df = pd.read_csv(filepath)
        logger.info(f"Loaded {len(df)} rows from {filepath}")
        
        if not validate_required_columns(df):
            raise ValueError(f"Invalid CSV structure in {filepath}")
        
        # Mark as real data
        df['is_synthetic'] = False
        df['ingestion_source'] = 'real_csv'
        df['ingestion_timestamp'] = datetime.now().isoformat()
        
        return df
        
    except Exception as e:
        logger.error(f"Failed to ingest {filepath}: {e}")
        raise

def auto_generate_data(protocol: dict, output_dir: str = "data/synthetic/") -> pd.DataFrame:
    """
    Automatically generate synthetic data if real data is not suitable.
    
    Args:
        protocol: Protocol dictionary.
        output_dir: Directory for synthetic data.
        
    Returns:
        Generated DataFrame.
    """
    logger = logging.getLogger(__name__)
    logger.warning("No suitable real data found. Triggering synthetic data generation.")
    
    # Log generation parameters
    logger.info(f"Generating synthetic data with parameters:")
    logger.info(f"  - N: {protocol['N']}")
    logger.info(f"  - Effect Sizes: {protocol['effect_sizes']}")
    
    files = generate_synthetic_datasets(protocol, output_dir=output_dir, seed=42)
    
    # Load the first generated file (or combine if needed)
    # For this implementation, we load the 'positive_effect' scenario as default
    default_file = [f for f in files if 'positive_effect' in f][0]
    df = ingest_csv(default_file)
    df['ingestion_source'] = 'synthetic_auto'
    
    logger.info(f"Synthetic data generated and ingested from {default_file}")
    return df

def run_ingestion(input_path: str = None, protocol_path: str = "data/protocols/protocol.yaml") -> pd.DataFrame:
    """
    Main ingestion pipeline: check for real data, fall back to synthetic if needed.
    
    Args:
        input_path: Optional path to real CSV data.
        protocol_path: Path to protocol YAML.
        
    Returns:
        Processed DataFrame.
    """
    logger = logging.getLogger(__name__)
    logger.info("=== Starting Data Ingestion Pipeline ===")
    
    # Load protocol
    protocol = load_protocol(protocol_path)
    
    if input_path and os.path.exists(input_path):
        logger.info(f"Attempting to ingest real data from: {input_path}")
        df = ingest_csv(input_path)
        
        # Check for sensory deprivation tags
        if not check_sensory_deprivation_tags(df):
            logger.warning("Real data lacks sensory deprivation tags. Falling back to synthetic.")
            df = auto_generate_data(protocol)
        else:
            logger.info("Real data validated with sensory deprivation tags.")
    else:
        logger.info(f"No input path provided or file not found at {input_path}. Generating synthetic data.")
        df = auto_generate_data(protocol)
    
    logger.info(f"Ingestion complete. Final dataset shape: {df.shape}")
    logger.info(f"Ingestion source: {df['ingestion_source'].iloc[0]}")
    logger.info("=== Data Ingestion Pipeline Complete ===")
    
    return df

def main():
    """Main entry point for ingestion."""
    logger = setup_logging(log_level=logging.INFO, log_file="logs/ingest.log")
    logger.info("=== Starting Data Ingestion ===")
    
    try:
        # Run ingestion (no input path specified, will generate synthetic)
        df = run_ingestion(input_path=None)
        
        # Log summary
        logger.info(f"Dataset summary:")
        logger.info(f"  - Total rows: {len(df)}")
        logger.info(f"  - Unique participants: {df['participant_id'].nunique()}")
        logger.info(f"  - Conditions: {df['condition'].unique().tolist()}")
        logger.info(f"  - Source: {df['ingestion_source'].iloc[0]}")
        logger.info(f"  - Is Synthetic: {df['is_synthetic'].iloc[0]}")
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
