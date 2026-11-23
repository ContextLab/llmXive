import os
import sys
import json
import logging
import pandas as pd
from datetime import datetime

# Import from sibling modules as per API surface
from generate_data import load_protocol, generate_synthetic_datasets
from logging_config import setup_logging

def ensure_directory_exists(dir_path: str) -> None:
    """Ensure the target directory exists, creating it if necessary."""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        logging.info(f"Created directory: {dir_path}")

def add_simulation_metadata(df: pd.DataFrame, protocol_params: dict) -> pd.DataFrame:
    """
    Add simulation-based metadata flags to the dataframe.
    
    Args:
        df: The dataframe to augment.
        protocol_params: Dictionary of parameters from protocol.yaml.
        
    Returns:
        The dataframe with added metadata columns.
    """
    df['is_simulation'] = True
    df['simulation_timestamp'] = datetime.now().isoformat()
    df['simulation_seed'] = protocol_params.get('seed', 42)
    df['source'] = 'synthetic_simulation'
    
    # Add effect size context if available
    if 'effect_size' in protocol_params:
        df['effect_size_scenario'] = protocol_params['effect_size']
        
    return df

def save_synthetic_datasets(output_dir: str = "data/synthetic") -> None:
    """
    Generate synthetic datasets and save them to the specified directory
    with clear simulation-based flags in metadata.
    
    This function:
    1. Loads protocol parameters
    2. Generates synthetic datasets based on protocol
    3. Adds simulation metadata flags
    4. Saves to CSV files with clear naming convention
    """
    logger = logging.getLogger(__name__)
    
    # Ensure output directory exists
    ensure_directory_exists(output_dir)
    
    # Load protocol parameters
    protocol_params = load_protocol()
    logger.info(f"Loaded protocol parameters: {protocol_params}")
    
    # Generate synthetic datasets
    logger.info("Generating synthetic datasets...")
    datasets = generate_synthetic_datasets()
    
    # Save each dataset with metadata
    for scenario_name, df in datasets.items():
        # Add simulation metadata
        df_with_metadata = add_simulation_metadata(df, protocol_params)
        
        # Create filename
        filename = f"synthetic_{scenario_name}.csv"
        filepath = os.path.join(output_dir, filename)
        
        # Save to CSV
        df_with_metadata.to_csv(filepath, index=False)
        logger.info(f"Saved synthetic dataset to: {filepath}")
        logger.info(f"  - Rows: {len(df_with_metadata)}")
        logger.info(f"  - Columns: {list(df_with_metadata.columns)}")
        
        # Log metadata verification
        assert 'is_simulation' in df_with_metadata.columns, "Missing is_simulation flag"
        assert 'source' in df_with_metadata.columns, "Missing source flag"
        assert df_with_metadata['is_simulation'].all(), "Not all rows marked as simulation"
        assert (df_with_metadata['source'] == 'synthetic_simulation').all(), "Incorrect source flag"
    
    logger.info("Successfully saved all synthetic datasets with simulation metadata")

def main():
    """Main entry point for the synthetic data saving script."""
    # Setup logging
    logger = setup_logging("save_synthetic_data")
    logger.info("Starting synthetic data generation and saving process")
    
    try:
        save_synthetic_datasets()
        logger.info("Synthetic data saving completed successfully")
    except Exception as e:
        logger.error(f"Error during synthetic data saving: {e}")
        raise

if __name__ == "__main__":
    main()
