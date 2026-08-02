"""
Module to load processed EBSD data, calculate texture descriptors, and export them to CSV.

This module implements Task T021: Output descriptors to `data/processed/descriptors.csv` 
linked to original sample IDs.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(project_root))

from utils.logging import get_logger
from config import get_data_path, get_reductions
from data.models import TextureDescriptor
from features.descriptors import calculate_descriptors
from data.preprocess import process_ebsd_dataset

logger = get_logger(__name__)

def load_processed_data() -> pd.DataFrame:
    """
    Load the cleaned EBSD data from the processed directory.
    
    Returns:
        pd.DataFrame: Cleaned EBSD data with columns for sample_id, material, 
                     reduction, and orientation data.
                     
    Raises:
        FileNotFoundError: If the cleaned data file does not exist.
        ValueError: If the data file is empty or malformed.
    """
    data_path = get_data_path()
    cleaned_file = data_path / "processed" / "cleaned_ebsd.parquet"
    
    if not cleaned_file.exists():
        logger.error(f"Cleaned EBSD data file not found: {cleaned_file}")
        raise FileNotFoundError(f"Cleaned EBSD data file not found: {cleaned_file}")
    
    try:
        df = pd.read_parquet(cleaned_file)
        if df.empty:
            logger.error("Cleaned EBSD data file is empty.")
            raise ValueError("Cleaned EBSD data file is empty.")
        
        logger.info(f"Loaded {len(df)} rows from {cleaned_file}")
        return df
    except Exception as e:
        logger.error(f"Error loading cleaned EBSD data: {e}")
        raise

def calculate_and_export_descriptors(input_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Calculate texture descriptors for each sample and export to CSV.
    
    This function:
    1. Loads processed EBSD data (or uses provided DataFrame)
    2. Groups data by sample_id
    3. Calculates descriptors (Texture Index, volume fractions) for each sample
    4. Aggregates results into a summary DataFrame
    5. Exports to data/processed/descriptors.csv
    
    Args:
        input_df: Optional DataFrame of cleaned EBSD data. If None, loads from disk.
        
    Returns:
        pd.DataFrame: DataFrame containing descriptors for each sample.
    """
    if input_df is None:
        input_df = load_processed_data()
    
    logger.info("Starting descriptor calculation for all samples...")
    
    # Group by sample_id to process each sample independently
    grouped = input_df.groupby('sample_id')
    
    descriptor_records = []
    
    for sample_id, group in grouped:
        try:
            logger.debug(f"Processing sample: {sample_id}")
            
            # Extract sample metadata
            material = group['material'].iloc[0]
            reduction = group['reduction'].iloc[0]
            
            # Calculate descriptors using the feature module
            # The calculate_descriptors function expects orientation data
            descriptors = calculate_descriptors(group, material)
            
            # Create a record for this sample
            record = {
                'sample_id': sample_id,
                'material': material,
                'reduction': reduction,
                'texture_index': descriptors.get('texture_index', None),
                'brass_fraction': descriptors.get('brass_fraction', None),
                'copper_fraction': descriptors.get('copper_fraction', None),
                's_fraction': descriptors.get('s_fraction', None),
                'goss_fraction': descriptors.get('goss_fraction', None),
                'random_fraction': descriptors.get('random_fraction', None)
            }
            
            descriptor_records.append(record)
            logger.debug(f"Calculated descriptors for sample {sample_id}")
            
        except Exception as e:
            logger.warning(f"Error processing sample {sample_id}: {e}. Skipping.")
            # Optionally add a record with None values to track failures
            descriptor_records.append({
                'sample_id': sample_id,
                'material': material,
                'reduction': reduction,
                'texture_index': None,
                'brass_fraction': None,
                'copper_fraction': None,
                's_fraction': None,
                'goss_fraction': None,
                'random_fraction': None
            })
    
    # Create DataFrame from records
    descriptors_df = pd.DataFrame(descriptor_records)
    
    # Ensure output directory exists
    data_path = get_data_path()
    output_file = data_path / "processed" / "descriptors.csv"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Export to CSV
    descriptors_df.to_csv(output_file, index=False)
    logger.info(f"Exported descriptors for {len(descriptors_df)} samples to {output_file}")
    
    return descriptors_df

def main():
    """Main entry point for the export descriptors script."""
    logger.info("Starting descriptor export process...")
    
    try:
        descriptors_df = calculate_and_export_descriptors()
        logger.info(f"Successfully exported {len(descriptors_df)} descriptor records.")
        
        # Print summary
        print(f"\nDescriptor Summary:")
        print(f"Total samples processed: {len(descriptors_df)}")
        print(f"Samples with valid descriptors: {descriptors_df['texture_index'].notna().sum()}")
        print(f"Output file: {get_data_path() / 'processed' / 'descriptors.csv'}")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Invalid data: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during descriptor export: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
