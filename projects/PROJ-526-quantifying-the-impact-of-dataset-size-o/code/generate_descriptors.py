import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from matminer.featurizers.composition import Magpie
from config import get_config, require_data_dir
from utils.logging_config import get_logger

logger = get_logger(__name__)

def load_raw_materials(data_dir: Path) -> Dict[str, pd.DataFrame]:
    """
    Load raw material data from CSV files in the data directory.
    
    Args:
        data_dir: Path to the raw data directory.
    
    Returns:
        Dictionary mapping property names to DataFrames.
    """
    raw_dir = data_dir / "raw"
    materials_data: Dict[str, pd.DataFrame] = {}
    
    if not raw_dir.exists():
        logger.warning(f"Raw data directory not found: {raw_dir}")
        return materials_data
    
    for prop_dir in raw_dir.iterdir():
        if prop_dir.is_dir():
            csv_files = list(prop_dir.glob("*.csv"))
            if csv_files:
                # Assuming the first CSV is the main data file
                data_file = csv_files[0]
                try:
                    df = pd.read_csv(data_file)
                    materials_data[prop_dir.name] = df
                    logger.info(f"Loaded {len(df)} rows for property: {prop_dir.name}")
                except Exception as e:
                    logger.error(f"Failed to load {data_file}: {e}")
            else:
                logger.warning(f"No CSV files found in {prop_dir}")
    
    return materials_data

def validate_dataframe(df: pd.DataFrame, required_columns: List[str]) -> bool:
    """
    Validate that a DataFrame contains required columns.
    
    Args:
        df: DataFrame to validate.
        required_columns: List of required column names.
    
    Returns:
        True if valid, False otherwise.
    """
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        return False
    return True

def compute_magpie_descriptors(df: pd.DataFrame, composition_col: str = "composition") -> pd.DataFrame:
    """
    Compute Magpie composition descriptors for a DataFrame.
    
    Args:
        df: DataFrame containing material data.
        composition_col: Name of the column containing chemical formulas.
    
    Returns:
        DataFrame with added Magpie descriptor columns.
    """
    if not validate_dataframe(df, [composition_col]):
        raise ValueError("Invalid DataFrame for descriptor computation")
    
    logger.info(f"Computing Magpie descriptors for {len(df)} materials...")
    
    # Initialize Magpie featurizer
    featurizer = Magpie.from_preset("default")
    
    # Compute descriptors
    try:
        descriptors = featurizer.featurize_dataframe(
            df, 
            col_id=composition_col, 
            ignore_errors=True, 
            pbar=True
        )
        logger.info(f"Successfully computed {len(descriptors.columns) - len(df.columns)} descriptors")
        return descriptors
    except Exception as e:
        logger.error(f"Failed to compute descriptors: {e}")
        raise

def save_master_dataset(
    data_dir: Path,
    processed_data: Dict[str, pd.DataFrame],
    output_filename: str = "materials_master.parquet"
):
    """
    Save consolidated material data to a Parquet file.
    
    Args:
        data_dir: Path to the processed data directory.
        processed_data: Dictionary mapping property names to DataFrames.
        output_filename: Name of the output file.
    """
    processed_dir = data_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = processed_dir / output_filename
    
    # Combine all dataframes
    all_data = []
    for prop_name, df in processed_data.items():
        # Add property column if not present
        if "property" not in df.columns:
            df["property"] = prop_name
        all_data.append(df)
    
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        combined_df.to_parquet(output_path, index=False)
        logger.info(f"Saved master dataset to {output_path} ({len(combined_df)} rows)")
        
        # Log statistics
        stats = {
            "total_rows": len(combined_df),
            "properties": list(processed_data.keys()),
            "output_file": str(output_path)
        }
        logger.info(f"Dataset stats: {json.dumps(stats)}")
    else:
        logger.warning("No data to save")

def main():
    """
    Main entry point for descriptor generation.
    """
    logger.info("Starting descriptor generation process")
    
    try:
        config = get_config()
        data_dir = Path(require_data_dir(config))
        
        # Load raw data
        raw_data = load_raw_materials(data_dir)
        
        if not raw_data:
            logger.warning("No raw data found. Skipping descriptor generation.")
            return
        
        processed_data = {}
        for prop_name, df in raw_data.items():
            try:
                # Compute descriptors
                descriptors_df = compute_magpie_descriptors(df)
                processed_data[prop_name] = descriptors_df
            except Exception as e:
                logger.error(f"Failed to process {prop_name}: {e}")
        
        if processed_data:
            # Save consolidated dataset
            save_master_dataset(data_dir, processed_data)
            logger.info(f"Descriptor generation completed for {len(processed_data)} properties")
        else:
            logger.warning("No properties were successfully processed")
            
    except Exception as e:
        logger.error(f"Descriptor generation failed: {e}", exc_info=True)
        sys.exit(1)
    
    logger.info("Descriptor generation process completed")

if __name__ == "__main__":
    main()