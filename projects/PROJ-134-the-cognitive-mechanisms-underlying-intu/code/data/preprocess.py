"""
Preprocessing pipeline for mapping text stories to VR scenes.

This module assigns salience levels (low/high) to stories based on the
configuration defined in data/config/unity_blend_shapes.yaml.

It also generates a log of the VR mapping to data/logs/vr_mapping.log
in CSV format with columns: story_id, salience_level, blend_shape_params.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import yaml

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_path, ensure_directories
from utils.logging import get_logger, get_vr_mapping_log_path, log_vr_mapping

# Constants
CONFIG_PATH = "data/config/unity_blend_shapes.yaml"
MERGED_DATA_PATH = "data/processed/merged_data.csv"
PREPROCESSED_OUTPUT_PATH = "data/processed/preprocessed_data.csv"

# Logger setup
logger = get_logger(__name__)

def load_blend_shape_config() -> Dict[str, Any]:
    """
    Load the Unity blend shape configuration from YAML.
    
    Returns:
        Dict containing the configuration mappings.
        
    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the YAML file is malformed.
    """
    config_path = get_path(CONFIG_PATH)
    logger.info(f"Loading blend shape config from {config_path}")
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    logger.info(f"Loaded {len(config.get('mappings', {}))} story mappings")
    return config

def load_merged_data() -> pd.DataFrame:
    """
    Load the merged dataset from the ingestion step.
    
    Returns:
        DataFrame containing the merged MFQ and stories data.
        
    Raises:
        FileNotFoundError: If the merged data file does not exist.
    """
    data_path = get_path(MERGED_DATA_PATH)
    logger.info(f"Loading merged data from {data_path}")
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Merged data file not found: {data_path}")
    
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} rows from merged data")
    return df

def assign_salience_level(story_id: str, config: Dict[str, Any]) -> Tuple[Optional[str], Optional[Dict[str, float]]]:
    """
    Assign a salience level and blend shape parameters to a story ID.
    
    Args:
        story_id: The unique identifier for the story.
        config: The loaded blend shape configuration.
        
    Returns:
        Tuple of (salience_level, blend_shape_params).
        If story_id is not found, returns (None, None).
    """
    mappings = config.get('mappings', {})
    
    if story_id not in mappings:
        logger.warning(f"Story ID '{story_id}' not found in blend shape config")
        return None, None
    
    story_config = mappings[story_id]
    salience_level = story_config.get('salience_level')
    blend_shape_params = story_config.get('blend_shape_params', {})
    
    logger.debug(f"Assigned salience '{salience_level}' to story '{story_id}'")
    return salience_level, blend_shape_params

def map_to_blend_shapes(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Map story IDs in the dataframe to VR blend shape parameters.
    
    This function adds two new columns to the dataframe:
    - salience_level: 'low' or 'high'
    - blend_shape_params: JSON string representation of the parameters
    
    Args:
        df: The input dataframe with story_id column.
        config: The loaded blend shape configuration.
        
    Returns:
        DataFrame with added salience columns.
    """
    # Create copies to avoid SettingWithCopyWarning
    result_df = df.copy()
    
    salience_levels = []
    blend_shape_params_list = []
    missing_ids = []
    
    for idx, row in result_df.iterrows():
        story_id = row.get('story_id')
        
        if pd.isna(story_id):
            salience_levels.append(None)
            blend_shape_params_list.append(None)
            continue
        
        salience, params = assign_salience_level(str(story_id), config)
        
        if salience is None:
            missing_ids.append(story_id)
            salience_levels.append(None)
            blend_shape_params_list.append(None)
        else:
            salience_levels.append(salience)
            # Convert params dict to JSON string for CSV storage
            blend_shape_params_list.append(json.dumps(params) if params else None)
    
    result_df['salience_level'] = salience_levels
    result_df['blend_shape_params'] = blend_shape_params_list
    
    if missing_ids:
        logger.warning(f"Found {len(missing_ids)} story IDs without mapping: {missing_ids[:5]}...")
    
    return result_df

def process_salience_mapping(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Process the salience mapping for the entire dataset.
    
    This is a wrapper function that performs the mapping and logging.
    
    Args:
        df: Input dataframe.
        config: Loaded configuration.
        
    Returns:
        Processed dataframe with salience information.
    """
    logger.info("Starting salience mapping process")
    
    # Map to blend shapes
    processed_df = map_to_blend_shapes(df, config)
    
    # Generate and write the VR mapping log
    log_path = get_vr_mapping_log_path()
    ensure_directories()
    
    # Prepare log data
    log_data = []
    for idx, row in processed_df.iterrows():
        story_id = row.get('story_id')
        if pd.notna(story_id) and row.get('salience_level') is not None:
            log_data.append({
                'story_id': str(story_id),
                'salience_level': row['salience_level'],
                'blend_shape_params': row.get('blend_shape_params', '')
            })
    
    # Write log using the utility function
    if log_data:
        log_vr_mapping(log_data, log_path)
        logger.info(f"VR mapping log written to {log_path}")
    else:
        logger.warning("No valid salience mappings found to log")
    
    return processed_df

def save_preprocessed_data(df: pd.DataFrame, output_path: Optional[str] = None) -> str:
    """
    Save the preprocessed dataframe to CSV.
    
    Args:
        df: The preprocessed dataframe.
        output_path: Optional custom output path. If None, uses the default.
        
    Returns:
        The path where the file was saved.
    """
    if output_path is None:
        output_path = get_path(PREPROCESSED_OUTPUT_PATH)
    
    ensure_directories()
    
    logger.info(f"Saving preprocessed data to {output_path}")
    df.to_csv(output_path, index=False)
    
    logger.info(f"Saved {len(df)} rows to {output_path}")
    return output_path

def run_preprocessing_pipeline() -> Tuple[pd.DataFrame, str]:
    """
    Run the full preprocessing pipeline.
    
    This function:
    1. Loads the blend shape configuration
    2. Loads the merged data
    3. Maps stories to VR blend shapes
    4. Writes the VR mapping log
    5. Saves the preprocessed data
    
    Returns:
        Tuple of (processed_dataframe, output_file_path)
        
    Raises:
        FileNotFoundError: If required input files are missing.
        RuntimeError: If the pipeline fails at any step.
    """
    try:
        logger.info("Starting preprocessing pipeline")
        
        # Step 1: Load configuration
        config = load_blend_shape_config()
        
        # Step 2: Load merged data
        df = load_merged_data()
        
        # Step 3 & 4: Process salience mapping (includes logging)
        processed_df = process_salience_mapping(df, config)
        
        # Step 5: Save output
        output_path = save_preprocessed_data(processed_df)
        
        logger.info("Preprocessing pipeline completed successfully")
        
        return processed_df, output_path
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        raise RuntimeError(f"Preprocessing pipeline failed: {e}") from e

def main():
    """
    Main entry point for the preprocessing script.
    
    This function runs the preprocessing pipeline and prints summary statistics.
    """
    ensure_directories()
    
    try:
        df, output_path = run_preprocessing_pipeline()
        
        # Print summary
        print(f"\nPreprocessing Complete")
        print(f"=====================")
        print(f"Total rows processed: {len(df)}")
        
        salience_counts = df['salience_level'].value_counts()
        print(f"\nSalience Distribution:")
        for level, count in salience_counts.items():
            print(f"  {level}: {count} ({count/len(df)*100:.1f}%)")
        
        print(f"\nOutput saved to: {output_path}")
        
        # Verify log was created
        log_path = get_vr_mapping_log_path()
        if os.path.exists(log_path):
            print(f"VR mapping log saved to: {log_path}")
            log_df = pd.read_csv(log_path)
            print(f"Log entries: {len(log_df)}")
        
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()