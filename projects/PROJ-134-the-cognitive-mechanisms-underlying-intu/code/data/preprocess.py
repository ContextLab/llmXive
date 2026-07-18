"""
Preprocessing module for mapping text stories to VR scenes and assigning salience levels.

This module handles the transformation of merged datasets into VR-ready formats by:
1. Loading the merged dataset from the ingestion pipeline
2. Loading the Unity blend shape configuration
3. Assigning salience levels (low/high) based on story ID
4. Mapping stories to VR blend-shape parameters
5. Logging VR mapping decisions to data/logs/vr_mapping.log
6. Saving the preprocessed dataset
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import ensure_directories
from utils.logging_utils import get_vr_mapping_log_path, get_logger, log_vr_mapping
from utils.schema import MergedDataset, SalienceLevel


def load_merged_data(merged_path: Path) -> pd.DataFrame:
    """
    Load the merged dataset from the ingestion pipeline.
    
    Args:
        merged_path: Path to the merged CSV file
        
    Returns:
        pandas DataFrame containing merged MFQ and story data
    """
    import pandas as pd
    
    if not merged_path.exists():
        raise FileNotFoundError(f"Merged dataset not found at {merged_path}")
    
    df = pd.read_csv(merged_path)
    logging.info(f"Loaded merged dataset with {len(df)} rows from {merged_path}")
    return df


def load_blend_shape_config(config_path: Path) -> Dict[str, Any]:
    """
    Load the Unity blend shape configuration from YAML/JSON.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dictionary containing blend shape mappings
    """
    import yaml
    
    if not config_path.exists():
        raise FileNotFoundError(f"Blend shape config not found at {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    logging.info(f"Loaded blend shape config from {config_path}")
    return config


def assign_salience_level(story_id: str, config: Dict[str, Any]) -> str:
    """
    Assign a salience level (low/high) to a story based on its ID.
    
    Args:
        story_id: The unique identifier for the story
        config: The blend shape configuration dictionary
        
    Returns:
        Salience level string ('low' or 'high')
    """
    mapping = config.get('story_to_salience', {})
    
    if story_id in mapping:
        salience = mapping[story_id]
        if salience not in ['low', 'high']:
            logging.warning(f"Invalid salience level '{salience}' for story {story_id}, defaulting to 'low'")
            return 'low'
        return salience
    else:
        logging.warning(f"Story ID {story_id} not found in config, defaulting to 'low'")
        return 'low'


def map_to_blend_shapes(story_id: str, config: Dict[str, Any]) -> Dict[str, float]:
    """
    Map a story ID to VR blend-shape parameters.
    
    Args:
        story_id: The unique identifier for the story
        config: The blend shape configuration dictionary
        
    Returns:
        Dictionary of blend shape parameters
    """
    blend_shapes = config.get('blend_shapes', {})
    
    if story_id in config.get('story_to_salience', {}):
        salience = assign_salience_level(story_id, config)
        # Use the salience-specific blend shape parameters
        if salience in blend_shapes:
            return blend_shapes[salience]
    
    # Default blend shapes if not found
    return config.get('default_blend_shapes', {
        'jawOpen': 0.0,
        'mouthClose': 0.0,
        'eyeBlinkLeft': 0.0,
        'eyeBlinkRight': 0.0
    })


def process_salience_mapping(df: pd.DataFrame, config: Dict[str, Any], log_path: Path) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Process the entire dataset, assigning salience levels and mapping to blend shapes.
    Logs each mapping decision to the VR mapping log file.
    
    Args:
        df: The merged DataFrame
        config: The blend shape configuration
        log_path: Path to the VR mapping log file
        
    Returns:
        Tuple of (processed DataFrame, list of mapping logs)
    """
    import pandas as pd
    
    # Ensure log directory exists
    ensure_directories()
    
    # Initialize logger for VR mapping
    vr_logger = get_logger('vr_mapping', log_path)
    
    mapping_logs = []
    
    for idx, row in df.iterrows():
        story_id = row['story_id']
        
        # Assign salience level
        salience_level = assign_salience_level(story_id, config)
        
        # Map to blend shapes
        blend_shapes = map_to_blend_shapes(story_id, config)
        
        # Update DataFrame
        df.at[idx, 'salience_level'] = salience_level
        for shape_name, value in blend_shapes.items():
            df.at[idx, f'blend_{shape_name}'] = value
        
        # Log the mapping decision
        log_entry = {
            'story_id': story_id,
            'salience_level': salience_level,
            'blend_shapes': blend_shapes,
            'row_index': int(idx)
        }
        
        # Use the logging utility to write to the log file
        log_vr_mapping(
            story_id=story_id,
            salience_level=salience_level,
            blend_shapes=blend_shapes,
            log_path=log_path
        )
        
        mapping_logs.append(log_entry)
        
        # Log to standard logger as well
        vr_logger.info(f"Mapped story {story_id} -> {salience_level} salience")
    
    logging.info(f"Processed {len(df)} story mappings, logged to {log_path}")
    return df, mapping_logs


def save_preprocessed_data(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the preprocessed dataset to CSV.
    
    Args:
        df: The processed DataFrame
        output_path: Path to save the CSV file
    """
    df.to_csv(output_path, index=False)
    logging.info(f"Saved preprocessed data to {output_path}")


def run_preprocessing_pipeline(
    merged_path: Path,
    config_path: Path,
    output_path: Path
) -> pd.DataFrame:
    """
    Run the full preprocessing pipeline:
    1. Load merged data
    2. Load configuration
    3. Process salience mapping (with logging)
    4. Save preprocessed data
    
    Args:
        merged_path: Path to the merged dataset
        config_path: Path to the blend shape configuration
        output_path: Path to save the preprocessed dataset
        
    Returns:
        The processed DataFrame
    """
    from utils.logging_utils import get_vr_mapping_log_path
    
    # Ensure directories exist
    ensure_directories()
    
    # Get the VR mapping log path
    vr_log_path = get_vr_mapping_log_path()
    
    # Load data and config
    df = load_merged_data(merged_path)
    config = load_blend_shape_config(config_path)
    
    # Process salience mapping and log decisions
    df, mapping_logs = process_salience_mapping(df, config, vr_log_path)
    
    # Save preprocessed data
    save_preprocessed_data(df, output_path)
    
    return df


def main():
    """Main entry point for the preprocessing pipeline."""
    import pandas as pd
    
    # Define paths
    merged_path = Path('data/processed/merged_dataset.csv')
    config_path = Path('data/config/unity_blend_shapes.yaml')
    output_path = Path('data/processed/preprocessed_dataset.csv')
    
    # Run pipeline
    try:
        df = run_preprocessing_pipeline(merged_path, config_path, output_path)
        logging.info("Preprocessing pipeline completed successfully")
    except Exception as e:
        logging.error(f"Preprocessing pipeline failed: {e}")
        raise


if __name__ == '__main__':
    # Configure basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run main
    main()
