"""
Preprocess module for mapping text stories to VR scenes.

This module assigns `salience_level` (low/high) to moral stories
by mapping them to specific VR scene configurations and blend-shape parameters.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from datetime import datetime

# Local imports matching API surface
from code.config import ensure_directories
from code.utils.schema import MergedDataset, SalienceLevel, MoralStory
from code.utils.logging_utils import log_vr_mapping, get_logger
from code.utils.hashing import calculate_sha256, update_state_yaml

# Configure logging
logger = get_logger(__name__)

# Constants for blend-shape mapping
# These map logical salience levels to specific Unity blend-shape weights
# Low Salience: Subtle cues, lower weight on emotional facial features
# High Salience: Exaggerated cues, higher weight on emotional facial features
BLEND_SHAPE_CONFIG = {
    "low": {
        "eye_brows_inner_up": 0.15,
        "mouth_corner_pull": 0.10,
        "jaw_open": 0.05,
        "cheek_puff": 0.0,
        "eye_close_left": 0.0,
        "eye_close_right": 0.0,
        "brow_down_left": 0.05,
        "brow_down_right": 0.05
    },
    "high": {
        "eye_brows_inner_up": 0.85,
        "mouth_corner_pull": 0.90,
        "jaw_open": 0.70,
        "cheek_puff": 0.40,
        "eye_close_left": 0.15,
        "eye_close_right": 0.15,
        "brow_down_left": 0.75,
        "brow_down_right": 0.75
    }
}

# Mapping of story themes to default salience levels based on experimental design
# This simulates the assignment logic where specific story types are assigned
# to high or low salience conditions for the VR environment.
STORY_THEME_SALIENCE_MAP = {
    "harm": "high",
    "fairness": "high",
    "loyalty": "high",
    "authority": "high",
    "purity": "high",
    "neutral": "low",
    "baseline": "low"
}

def load_merged_data(input_path: Path) -> pd.DataFrame:
    """
    Load the merged dataset from the ingestion step.
    
    Args:
        input_path: Path to the merged CSV file.
        
    Returns:
        DataFrame containing merged MFQ and story data.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file is empty or malformed.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Merged data file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    if df.empty:
        raise ValueError(f"Merged data file is empty: {input_path}")
        
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def assign_salience_level(row: pd.Series, theme_map: Optional[Dict[str, str]] = None) -> str:
    """
    Assign a salience level to a story row based on its theme or ID.
    
    This function implements the logic to map text stories to VR scenes
    by determining the appropriate salience level (low/high).
    
    Args:
        row: A single row from the DataFrame.
        theme_map: Optional custom mapping of themes to salience levels.
        
    Returns:
        String representing the salience level ('low' or 'high').
    """
    if theme_map is None:
        theme_map = STORY_THEME_SALIENCE_MAP
    
    # Determine theme from the row
    theme = None
    if 'theme' in row:
        theme = str(row['theme']).lower()
    elif 'story_theme' in row:
        theme = str(row['story_theme']).lower()
    elif 'moral_foundation' in row:
        theme = str(row['moral_foundation']).lower()
    
    # If theme is found, use the mapping
    if theme and theme in theme_map:
        return theme_map[theme]
    
    # Fallback: If no explicit theme, check for specific keywords in story text
    if 'story_text' in row and pd.notna(row['story_text']):
        text = str(row['story_text']).lower()
        if any(kw in text for kw in ['harm', 'hurt', 'damage', 'injury']):
            return "high"
        if any(kw in text for kw in ['fair', 'equal', 'right', 'wrong']):
            return "high"
    
    # Default fallback to low salience
    return "low"

def map_to_blend_shapes(salience_level: str) -> Dict[str, float]:
    """
    Map a salience level to specific blend-shape parameters for VR rendering.
    
    Args:
        salience_level: The salience level ('low' or 'high').
        
    Returns:
        Dictionary of blend-shape names to weight values.
        
    Raises:
        ValueError: If the salience level is invalid.
    """
    if salience_level not in BLEND_SHAPE_CONFIG:
        raise ValueError(f"Invalid salience level: {salience_level}. Must be 'low' or 'high'.")
    
    return BLEND_SHAPE_CONFIG[salience_level].copy()

def process_salience_mapping(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Process the entire DataFrame to assign salience levels and blend-shape parameters.
    
    This is the core function that implements the task requirement:
    "map text stories to VR scenes, assigning `salience_level` (low/high) 
    via blend-shape parameters".
    
    Args:
        df: The merged DataFrame.
        
    Returns:
        Tuple of (processed DataFrame, list of mapping logs).
    """
    logs = []
    processed_rows = []
    
    for idx, row in df.iterrows():
        try:
            # Assign salience level
            salience = assign_salience_level(row)
            
            # Map to blend shapes
            blend_shapes = map_to_blend_shapes(salience)
            
            # Create new row with added columns
            new_row = row.to_dict()
            new_row['salience_level'] = salience
            new_row['blend_shape_params'] = json.dumps(blend_shapes)
            
            # Log the mapping
            log_entry = {
                "row_index": idx,
                "story_id": new_row.get('story_id', 'unknown'),
                "theme": new_row.get('theme', 'unknown'),
                "salience_level": salience,
                "blend_shapes": blend_shapes,
                "timestamp": datetime.now().isoformat()
            }
            logs.append(log_entry)
            
            processed_rows.append(new_row)
            
        except Exception as e:
            logger.error(f"Error processing row {idx}: {str(e)}")
            # Log exclusion reason
            exclusion_log = {
                "row_index": idx,
                "reason": f"Processing error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
            log_vr_mapping("exclusion", exclusion_log)
            # Skip this row or handle as needed
            continue
    
    processed_df = pd.DataFrame(processed_rows)
    return processed_df, logs

def save_preprocessed_data(df: pd.DataFrame, output_path: Path) -> str:
    """
    Save the preprocessed DataFrame to CSV and return the checksum.
    
    Args:
        df: The processed DataFrame.
        output_path: Path to save the output CSV.
        
    Returns:
        SHA-256 checksum of the saved file.
    """
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Saved preprocessed data to {output_path}")
    
    # Calculate checksum
    checksum = calculate_sha256(output_path)
    logger.info(f"Checksum for {output_path}: {checksum}")
    
    return checksum

def run_preprocessing_pipeline(
    input_path: Path,
    output_path: Path,
    config_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run the complete preprocessing pipeline.
    
    This function orchestrates the loading, mapping, and saving of preprocessed data.
    
    Args:
        input_path: Path to the merged input CSV.
        output_path: Path to save the preprocessed output CSV.
        config_path: Optional path to custom configuration file.
        
    Returns:
        Dictionary containing pipeline results and metadata.
    """
    logger.info("Starting preprocessing pipeline...")
    
    # Load data
    df = load_merged_data(input_path)
    
    # Process salience mapping
    processed_df, logs = process_salience_mapping(df)
    
    # Save results
    checksum = save_preprocessed_data(processed_df, output_path)
    
    # Update state file
    state_entry = {
        "task_id": "T016",
        "input_file": str(input_path),
        "output_file": str(output_path),
        "checksum": checksum,
        "rows_processed": len(processed_df),
        "timestamp": datetime.now().isoformat()
    }
    update_state_yaml(state_entry)
    
    # Log summary
    salience_counts = processed_df['salience_level'].value_counts().to_dict()
    logger.info(f"Salience distribution: {salience_counts}")
    
    return {
        "status": "success",
        "rows_processed": len(processed_df),
        "checksum": checksum,
        "output_path": str(output_path),
        "salience_distribution": salience_counts
    }

def main():
    """
    Main entry point for the preprocessing script.
    
    Reads configuration from environment or defaults, runs the pipeline,
    and writes output to the specified location.
    """
    # Ensure directories exist
    ensure_directories()
    
    # Default paths
    input_path = Path("data/processed/merged_data.csv")
    output_path = Path("data/processed/preprocessed_data.csv")
    
    # Allow override via command line arguments
    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])
    
    try:
        result = run_preprocessing_pipeline(input_path, output_path)
        print(f"Preprocessing completed successfully.")
        print(f"Output: {result['output_path']}")
        print(f"Rows processed: {result['rows_processed']}")
        print(f"Checksum: {result['checksum']}")
        print(f"Salience distribution: {result['salience_distribution']}")
    except Exception as e:
        logger.error(f"Preprocessing failed: {str(e)}")
        print(f"ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()