"""
Preprocessing Pipeline (T016-Sim/T016-Real).

Maps text stories to VR scenes, assigning `salience_level` (low/high) via
blend-shape parameters defined in `data/config/unity_blend_shapes.yaml`.

This script handles both the simulation validation path (using synthetic data)
and the real data path (using real MFQ/Stories data).

It reads merged data (either `data/processed/merged_data.csv` or
`data/processed/merged_simulation.csv`) and writes the preprocessed output
to `data/processed/preprocessed_data.csv`.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import yaml

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.config import get_path, load_yaml_config
from code.utils.logging import get_logger, log_operation

# Paths
CONFIG_PATH = "data/config/unity_blend_shapes.yaml"
# Try to detect the merged input file; prefer simulation if in simulation mode
MERGED_DATA_PATH_SIM = "data/processed/merged_simulation.csv"
MERGED_DATA_PATH_REAL = "data/processed/merged_data.csv"
PREPROCESSED_OUTPUT_PATH = "data/processed/preprocessed_data.csv"

logger = get_logger("preprocess")


def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """Load a YAML configuration file."""
    full_path = get_path(config_path)
    if not full_path.exists():
        raise FileNotFoundError(f"Config file not found: {full_path}")
    
    with open(full_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    if config is None:
        raise ValueError(f"Config file is empty: {full_path}")
    
    return config


def load_blend_shape_config() -> Dict[str, Any]:
    """Load the Unity blend shape configuration."""
    logger.info(f"Loading blend shape config from {get_path(CONFIG_PATH)}")
    config = load_yaml_config(CONFIG_PATH)
    
    # Validate structure
    if "low" not in config or "high" not in config:
        raise ValueError(
            "Blend shape config must contain 'low' and 'high' keys. "
            "See data/config/unity_blend_shapes.yaml."
        )
    
    if "blend_shape_params" not in config["low"] or "blend_shape_params" not in config["high"]:
        raise ValueError(
            "Blend shape config must contain 'blend_shape_params' under 'low' and 'high'."
        )
    
    logger.info(f"Loaded {len(config)} story mappings")
    return config


def load_merged_data() -> pd.DataFrame:
    """
    Load the merged dataset.
    
    Tries to load from the simulation path first, then the real path.
    If neither exists, raises FileNotFoundError.
    """
    sim_path = get_path(MERGED_DATA_PATH_SIM)
    real_path = get_path(MERGED_DATA_PATH_REAL)
    
    if sim_path.exists():
        logger.info(f"Loading merged data from {sim_path}")
        return pd.read_csv(sim_path)
    elif real_path.exists():
        logger.info(f"Loading merged data from {real_path}")
        return pd.read_csv(real_path)
    else:
        raise FileNotFoundError(
            f"Merged data file not found. "
            f"Expected one of: {sim_path}, {real_path}. "
            f"Ensure ingestion/simulation tasks (T056-Orch, T054b) have completed."
        )


def assign_salience_level(story_id: str, config: Dict[str, Any]) -> str:
    """
    Assign salience level ('low' or 'high') based on story_id and config.
    
    Args:
        story_id: The identifier for the moral story.
        config: The blend shape configuration dictionary.
        
    Returns:
        'low' or 'high' based on the mapping in config.
        
    Raises:
        ValueError: If story_id is not found in the config.
    """
    # Flatten the config for easier lookup
    # Expected structure: config['low']['blend_shape_params'] and config['high']['blend_shape_params']
    # The keys in these dicts should be story_ids or ranges.
    
    # Check 'high' first
    high_params = config.get("high", {}).get("blend_shape_params", {})
    if story_id in high_params:
        return "high"
    
    # Check 'low'
    low_params = config.get("low", {}).get("blend_shape_params", {})
    if story_id in low_params:
        return "low"
    
    # If not found, raise error
    raise ValueError(f"Story ID '{story_id}' not found in blend shape config.")


def map_to_blend_shapes(row: pd.Series, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map a row's story_id to blend shape parameters.
    
    Args:
        row: A pandas Series representing a single record.
        config: The blend shape configuration.
        
    Returns:
        A dictionary containing the salience_level and the specific blend_shape_params.
    """
    story_id = row.get("story_id")
    if pd.isna(story_id):
        # Fallback for missing story_id
        return {
            "salience_level": "unknown",
            "blend_shape_params": {}
        }
    
    try:
        salience = assign_salience_level(str(story_id), config)
        params = config[salience]["blend_shape_params"][str(story_id)]
        return {
            "salience_level": salience,
            "blend_shape_params": params
        }
    except ValueError:
        logger.warning(f"Could not map story_id '{story_id}', defaulting to unknown")
        return {
            "salience_level": "unknown",
            "blend_shape_params": {}
        }


def process_salience_mapping(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Process the DataFrame to add salience_level and blend_shape_params columns.
    
    Args:
        df: The input DataFrame.
        config: The blend shape configuration.
        
    Returns:
        The DataFrame with new columns added.
    """
    # Apply mapping row-wise
    mapping_results = df.apply(lambda row: map_to_blend_shapes(row, config), axis=1)
    
    # Unpack the results
    df["salience_level"] = mapping_results.apply(lambda x: x["salience_level"])
    # Store params as a JSON string to avoid complex nested structures in CSV
    df["blend_shape_params"] = mapping_results.apply(lambda x: json.dumps(x["blend_shape_params"]))
    
    return df


def save_preprocessed_data(df: pd.DataFrame, output_path: str) -> None:
    """Save the preprocessed DataFrame to a CSV file."""
    full_path = get_path(output_path)
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(full_path, index=False)
    logger.info(f"Preprocessed data saved to {full_path}")


def run_preprocessing_pipeline() -> pd.DataFrame:
    """
    Execute the full preprocessing pipeline.
    
    1. Load configuration.
    2. Load merged data.
    3. Map stories to VR salience levels.
    4. Save results.
    
    Returns:
        The preprocessed DataFrame.
    """
    log_operation("START", "Preprocessing Pipeline")
    
    # 1. Load config
    config = load_blend_shape_config()
    
    # 2. Load data
    df = load_merged_data()
    
    # 3. Process
    df_processed = process_salience_mapping(df, config)
    
    # 4. Save
    save_preprocessed_data(df_processed, PREPROCESSED_OUTPUT_PATH)
    
    log_operation("COMPLETE", "Preprocessing Pipeline", output_path=str(get_path(PREPROCESSED_OUTPUT_PATH)))
    return df_processed


def main() -> None:
    """Entry point for the preprocessing script."""
    try:
        run_preprocessing_pipeline()
        logger.info("Preprocessing pipeline completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()