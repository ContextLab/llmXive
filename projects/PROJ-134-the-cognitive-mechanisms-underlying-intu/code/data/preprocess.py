"""
Preprocessing pipeline for moral judgment data.
Maps text stories to VR scenes, assigns salience levels, and prepares data for modeling.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# Import from local modules using project-relative imports
from code.config import get_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(get_path("data/logs/preprocessing.log"))
    ]
)
logger = logging.getLogger(__name__)

CONFIG_PATH = "data/config/unity_blend_shapes.yaml"
MERGED_DATA_PATH = "data/processed/merged_data.csv"
PREPROCESSED_OUTPUT_PATH = "data/processed/preprocessed_data.csv"


def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """Load a YAML configuration file."""
    import yaml
    full_path = get_path(config_path)
    if not full_path.exists():
        raise FileNotFoundError(f"Config file not found: {full_path}")
    
    with open(full_path, 'r') as f:
        return yaml.safe_load(f)


def load_blend_shape_config() -> Dict[str, Any]:
    """Load the Unity blend shape configuration."""
    logger.info(f"Loading blend shape config from {get_path(CONFIG_PATH)}")
    config = load_yaml_config(CONFIG_PATH)
    
    # Validate required keys
    if 'low' not in config or 'high' not in config:
        raise ValueError("Config must contain 'low' and 'high' keys")
    if 'blend_shape_params' not in config['low'] or 'blend_shape_params' not in config['high']:
        raise ValueError("Config must contain 'blend_shape_params' under 'low' and 'high'")
    
    logger.info(f"Loaded {len(config.get('story_mappings', {}))} story mappings")
    return config


def load_merged_data() -> pd.DataFrame:
    """Load the merged dataset from disk."""
    full_path = get_path(MERGED_DATA_PATH)
    if not full_path.exists():
        raise FileNotFoundError(f"Merged data file not found: {full_path}")
    
    logger.info(f"Loading merged data from {full_path}")
    df = pd.read_csv(full_path)
    logger.info(f"Loaded {len(df)} records")
    return df


def assign_salience_level(story_id: str, config: Dict[str, Any]) -> str:
    """
    Assign salience level based on story ID and configuration.
    
    Args:
        story_id: The story identifier
        config: The blend shape configuration
        
    Returns:
        'low' or 'high' salience level
    """
    story_mappings = config.get('story_mappings', {})
    
    if story_id in story_mappings:
        return story_mappings[story_id].get('salience_level', 'low')
    
    # Default to low if not explicitly mapped
    logger.warning(f"Story ID {story_id} not found in mappings, defaulting to 'low'")
    return 'low'


def map_to_blend_shapes(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Map story IDs to VR blend shape parameters.
    
    Args:
        df: DataFrame containing story_id column
        config: Blend shape configuration
        
    Returns:
        DataFrame with added salience_level and blend_shape_params columns
    """
    df = df.copy()
    
    # Assign salience level
    df['salience_level'] = df['story_id'].apply(
        lambda x: assign_salience_level(x, config)
    )
    
    # Add blend shape parameters based on salience level
    def get_blend_params(row):
        level = row['salience_level']
        if level == 'high':
            return config['high']['blend_shape_params']
        else:
            return config['low']['blend_shape_params']
    
    df['blend_shape_params'] = df.apply(get_blend_params, axis=1)
    
    return df


def process_salience_mapping(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process salience mapping to ensure data quality.
    
    Args:
        df: DataFrame with salience_level column
        
    Returns:
        Filtered and validated DataFrame
    """
    # Validate salience levels
    valid_levels = ['low', 'high']
    invalid_mask = ~df['salience_level'].isin(valid_levels)
    if invalid_mask.any():
        logger.warning(f"Found {invalid_mask.sum()} rows with invalid salience levels")
        df = df[~invalid_mask]
    
    # Ensure required columns exist
    required_cols = ['participant_id', 'story_id', 'salience_level']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    logger.info(f"Processed {len(df)} valid records")
    return df


def save_preprocessed_data(df: pd.DataFrame, output_path: str) -> None:
    """Save the preprocessed DataFrame to disk."""
    full_path = get_path(output_path)
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving preprocessed data to {full_path}")
    df.to_csv(full_path, index=False)
    logger.info(f"Saved {len(df)} records to {full_path}")


def run_preprocessing_pipeline() -> pd.DataFrame:
    """
    Execute the full preprocessing pipeline.
    
    Returns:
        The preprocessed DataFrame
    """
    logger.info("Starting preprocessing pipeline")
    
    # Load configuration
    config = load_blend_shape_config()
    
    # Load merged data
    df = load_merged_data()
    
    # Map to blend shapes
    df = map_to_blend_shapes(df, config)
    
    # Process and validate
    df = process_salience_mapping(df)
    
    # Save output
    save_preprocessed_data(df, PREPROCESSED_OUTPUT_PATH)
    
    logger.info("Preprocessing pipeline completed successfully")
    return df


def main() -> None:
    """Main entry point for the preprocessing script."""
    try:
        run_preprocessing_pipeline()
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
