"""
Preprocessing module for mapping text stories to VR scenes.

This module assigns salience levels (low/high) to moral stories based on
blend-shape parameters defined in the Unity configuration. It also handles
the mapping of merged dataset rows to VR scenes and logs the mapping
decisions to data/logs/vr_mapping.log.

Dependencies:
- code/config.py: For path configuration and DATA_MODE validation.
- data/config/unity_blend_shapes.yaml: For salience mapping configuration.
- code/utils/logging_utils.py: For logging exclusion reasons and VR mapping.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import project config and utilities
# Note: We assume the runner adds the project root to sys.path or we are running from code/
try:
    from config import get_path, validate_data_mode
    from utils.logging_utils import log_vr_mapping, get_vr_mapping_log_path
except ImportError:
    # Fallback for direct execution in code/ directory
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import get_path, validate_data_mode
    from utils.logging_utils import log_vr_mapping, get_vr_mapping_log_path

# Constants
CONFIG_PATH = "data/config/unity_blend_shapes.yaml"
MERGED_DATA_PATH = "data/processed/merged_dataset.csv"
PREPROCESSED_OUTPUT_PATH = "data/processed/preprocessed_dataset.csv"

# Configure logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def load_blend_shape_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the Unity blend shape configuration from YAML.

    Args:
        config_path: Optional path to the config file. Defaults to CONFIG_PATH.

    Returns:
        Dictionary containing the configuration.

    Raises:
        FileNotFoundError: If the config file does not exist.
        ValueError: If the config format is invalid.
    """
    if config_path is None:
        config_path = get_path(CONFIG_PATH)

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except ImportError:
        raise ImportError("PyYAML is required to load configuration files. Install it via 'pip install pyyaml'.")
    except Exception as e:
        raise ValueError(f"Failed to parse YAML configuration: {e}")

    if 'mappings' not in config:
        raise ValueError("Configuration must contain a 'mappings' key.")

    return config


def load_merged_data(data_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load the merged dataset from CSV.

    Args:
        data_path: Optional path to the merged dataset. Defaults to MERGED_DATA_PATH.

    Returns:
        List of dictionaries representing the dataset rows.
    """
    if data_path is None:
        data_path = get_path(MERGED_DATA_PATH)

    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Merged dataset not found at {data_path}. "
                                "Please ensure T015 (ingest.py) has been executed successfully.")

    try:
        import pandas as pd
        df = pd.read_csv(data_path)
        # Convert to list of dicts for easier processing
        return df.to_dict('records')
    except ImportError:
        raise ImportError("Pandas is required to load CSV data. Install it via 'pip install pandas'.")
    except Exception as e:
        raise RuntimeError(f"Failed to load merged dataset: {e}")


def assign_salience_level(story_id: str, config: Dict[str, Any]) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Assign a salience level and blend shape parameters to a story ID.

    Args:
        story_id: The unique identifier for the story.
        config: The loaded blend shape configuration.

    Returns:
        Tuple of (salience_level, blend_shape_params).
        Returns (None, None) if the story_id is not found in the configuration.
    """
    mappings = config.get('mappings', {})
    if story_id in mappings:
        entry = mappings[story_id]
        return entry.get('salience_level'), entry.get('blend_shape_params')
    return None, None


def map_to_blend_shapes(story_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map a story ID to its VR blend shape parameters.

    Args:
        story_id: The unique identifier for the story.
        config: The loaded blend shape configuration.

    Returns:
        Dictionary containing the mapping result.
    """
    salience_level, blend_shape_params = assign_salience_level(story_id, config)

    result = {
        'story_id': story_id,
        'salience_level': salience_level,
        'blend_shape_params': blend_shape_params
    }

    if salience_level is None:
        logger.warning(f"Story ID '{story_id}' not found in VR configuration. Skipping mapping.")
    else:
        # Log the mapping decision
        log_vr_mapping(story_id, salience_level, blend_shape_params)

    return result


def process_salience_mapping(data: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Process the entire dataset, assigning salience levels to each row.

    Args:
        data: List of dataset rows (from merged dataset).
        config: The loaded blend shape configuration.

    Returns:
        List of processed rows with added salience information.
    """
    processed_data = []
    excluded_count = 0

    for row in data:
        story_id = row.get('story_id')
        if not story_id:
            logger.error(f"Row missing 'story_id': {row}")
            excluded_count += 1
            continue

        mapping_result = map_to_blend_shapes(story_id, config)

        if mapping_result['salience_level'] is None:
            # Log exclusion reason
            # Assuming log_exclusion exists in logging_utils, if not, we just log warning
            try:
                from utils.logging_utils import log_exclusion
                log_exclusion(story_id, "missing_vr_mapping", "Story ID not found in Unity blend shape config")
            except (ImportError, AttributeError):
                logger.warning(f"Excluded story {story_id}: missing_vr_mapping")
            excluded_count += 1
            continue

        # Merge original row with mapping result
        new_row = {**row, **mapping_result}
        processed_data.append(new_row)

    if excluded_count > 0:
        logger.info(f"Excluded {excluded_count} rows due to missing VR mapping.")
    else:
        logger.info("All rows successfully mapped to VR scenes.")

    return processed_data


def save_preprocessed_data(data: List[Dict[str, Any]], output_path: Optional[str] = None) -> str:
    """
    Save the preprocessed dataset to CSV.

    Args:
        data: List of processed rows.
        output_path: Optional path for the output file. Defaults to PREPROCESSED_OUTPUT_PATH.

    Returns:
        Path to the saved file.
    """
    if output_path is None:
        output_path = get_path(PREPROCESSED_OUTPUT_PATH)

    if not data:
        logger.warning("No data to save.")
        return output_path

    try:
        import pandas as pd
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)
        logger.info(f"Preprocessed data saved to {output_path}")
        return output_path
    except ImportError:
        raise ImportError("Pandas is required to save CSV data.")
    except Exception as e:
        raise RuntimeError(f"Failed to save preprocessed data: {e}")


def run_preprocessing_pipeline() -> str:
    """
    Execute the full preprocessing pipeline:
    1. Load config
    2. Load merged data
    3. Map stories to VR scenes
    4. Save preprocessed data

    Returns:
        Path to the saved preprocessed dataset.
    """
    logger.info("Starting preprocessing pipeline...")

    # Validate data mode (ensure we are not accidentally running real mode without Phase 4)
    validate_data_mode()

    # 1. Load config
    logger.info(f"Loading configuration from {CONFIG_PATH}...")
    config = load_blend_shape_config()

    # 2. Load merged data
    logger.info(f"Loading merged dataset from {MERGED_DATA_PATH}...")
    data = load_merged_data()

    # 3. Process mapping
    logger.info("Mapping stories to VR scenes...")
    processed_data = process_salience_mapping(data, config)

    # 4. Save results
    logger.info("Saving preprocessed dataset...")
    output_path = save_preprocessed_data(processed_data)

    logger.info("Preprocessing pipeline completed successfully.")
    return output_path


def main():
    """Entry point for the preprocessing script."""
    try:
        output_path = run_preprocessing_pipeline()
        print(f"Preprocessing complete. Output: {output_path}")
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()