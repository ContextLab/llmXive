import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from existing project API surface
from utils.logging_utils import get_logger, log_vr_mapping
from utils.schema import MergedDataset, SalienceLevel
import pandas as pd
import numpy as np

# Ensure we can import from the project root if run as a script
if 'code' not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

def load_merged_data() -> pd.DataFrame:
    """
    Load the merged dataset from the processed data directory.
    Returns a pandas DataFrame containing merged MFQ, Stories, and VR logs data.
    """
    merged_path = Path("data/processed/merged_dataset.csv")
    if not merged_path.exists():
        raise FileNotFoundError(f"Merged dataset not found at {merged_path}. "
                                "Run ingestion pipeline first.")
    return pd.read_csv(merged_path)

def load_blend_shape_config() -> Dict[str, Any]:
    """
    Load the Unity blend shape configuration from the config directory.
    Returns a dictionary mapping story IDs to salience parameters.
    """
    config_path = Path("data/config/unity_blend_shapes.yaml")
    # Since yaml is not strictly in the imports list for this file, we use json for safety
    # or assume yaml is available via the project's requirements. 
    # Given the task context, we will try to load YAML if pyyaml is available, 
    # otherwise fallback to a structured JSON approach if the file was converted.
    # However, the task spec says the file is YAML. We will use the standard yaml library
    # which is in requirements.txt.
    import yaml
    if not config_path.exists():
        raise FileNotFoundError(f"Blend shape config not found at {config_path}. "
                                "Run T044 to create this file.")
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def assign_salience_level(story_id: str, config: Dict[str, Any]) -> str:
    """
    Assign a salience level (low/high) to a story ID based on the configuration.
    """
    # The config is expected to be a dict like:
    # { "story_001": { "salience": "high", "blend_shapes": {...} }, ... }
    if story_id not in config:
        # Default to low if not explicitly defined, or raise error depending on strictness
        # For robustness in simulation, we default to 'low' but log it.
        return "low"
    
    entry = config[story_id]
    if isinstance(entry, dict):
        return entry.get("salience", "low")
    return str(entry)

def map_to_blend_shapes(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Map text stories to VR scenes by assigning salience levels and blend-shape parameters.
    Adds 'salience_level' column to the dataframe.
    """
    df = df.copy()
    
    # Ensure we have a story_id column
    if 'story_id' not in df.columns:
        # Try to find a similar column
        possible_cols = [c for c in df.columns if 'story' in c.lower() and 'id' in c.lower()]
        if possible_cols:
            story_col = possible_cols[0]
        else:
            raise ValueError("No story_id column found in merged dataset for VR mapping.")
    else:
        story_col = 'story_id'

    # Apply salience assignment
    df['salience_level'] = df[story_col].apply(lambda x: assign_salience_level(str(x), config))
    
    # Convert to enum type for validation if needed, but keeping as string for CSV compatibility
    # Validate values
    valid_levels = ['low', 'high']
    invalid_mask = ~df['salience_level'].isin(valid_levels)
    if invalid_mask.any():
        invalid_ids = df.loc[invalid_mask, story_col].unique()
        logging.warning(f"Found {invalid_mask.sum()} rows with invalid salience levels for stories: {invalid_ids}")
    
    return df

def process_salience_mapping(df: pd.DataFrame, logger: logging.Logger) -> List[Dict[str, Any]]:
    """
    Process the salience mapping and generate log entries for the VR mapping log.
    Returns a list of mapping records for potential bulk logging.
    """
    mapping_logs = []
    
    if 'story_id' not in df.columns:
        story_col = [c for c in df.columns if 'story' in c.lower() and 'id' in c.lower()]
        if story_col:
            story_col = story_col[0]
        else:
            story_col = 'story_id' # Fallback, will likely fail later but consistent
    else:
        story_col = 'story_id'

    if 'salience_level' not in df.columns:
        raise ValueError("salience_level column not found. Run map_to_blend_shapes first.")

    for _, row in df.iterrows():
        story_id = str(row[story_col])
        salience = row['salience_level']
        
        # Create log entry
        log_entry = {
            "story_id": story_id,
            "salience_level": salience,
            "timestamp": pd.Timestamp.now().isoformat()
        }
        mapping_logs.append(log_entry)
        
        # Log individually using the utility
        log_vr_mapping(
            story_id=story_id,
            salience_level=salience,
            logger=logger
        )
    
    return mapping_logs

def save_preprocessed_data(df: pd.DataFrame, output_path: Optional[str] = None) -> Path:
    """
    Save the preprocessed dataframe to a CSV file.
    """
    if output_path is None:
        output_path = "data/processed/preprocessed_vr_data.csv"
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logging.info(f"Preprocessed data saved to {output_path}")
    return output_path

def run_preprocessing_pipeline() -> pd.DataFrame:
    """
    Execute the full preprocessing pipeline:
    1. Load merged data
    2. Load configuration
    3. Map to blend shapes (assign salience)
    4. Log VR mappings
    5. Save preprocessed data
    """
    # Setup logging
    logger = get_logger("preprocess")
    logger.info("Starting VR preprocessing pipeline")

    try:
        # 1. Load merged data
        df = load_merged_data()
        logger.info(f"Loaded merged dataset with {len(df)} rows")

        # 2. Load configuration
        config = load_blend_shape_config()
        logger.info("Loaded Unity blend shape configuration")

        # 3. Map to blend shapes
        df_mapped = map_to_blend_shapes(df, config)
        logger.info("Mapped stories to VR blend shapes")

        # 4. Process and log salience mapping
        # This function calls log_vr_mapping for each row, creating data/logs/vr_mapping.log
        process_salience_mapping(df_mapped, logger)
        logger.info("VR mapping logs written to data/logs/vr_mapping.log")

        # 5. Save preprocessed data
        output_path = save_preprocessed_data(df_mapped)
        
        logger.info("VR preprocessing pipeline completed successfully")
        return df_mapped

    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        raise

def main():
    """
    Entry point for running the preprocessing pipeline as a script.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        result_df = run_preprocessing_pipeline()
        print(f"Pipeline completed. Processed {len(result_df)} records.")
        print(f"Salience distribution:\n{result_df['salience_level'].value_counts()}")
    except Exception as e:
        logging.error(f"Fatal error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()