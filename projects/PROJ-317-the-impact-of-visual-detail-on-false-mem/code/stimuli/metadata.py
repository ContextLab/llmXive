import json
import logging
import os
import random
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from config import get_data_dir, get_stimuli_dir, get_config
from utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class ManipulationRecord:
    object_name: str
    shape_type: str
    x: float
    y: float
    radius_side: float
    color: List[int]

@dataclass
class StimulusMetadata:
    id: str
    detail_level: str
    object_list: List[str]
    texture_settings: Dict[str, Any]
    timestamp: str
    manipulation_timestamp: str
    asset_parameters: List[Dict[str, Any]] = field(default_factory=list)

def load_generation_log() -> List[Dict[str, Any]]:
    """
    Loads the asset generation log from data/assets/generation_log.json.
    Returns a list of asset parameter dictionaries.
    """
    log_path = Path(get_data_dir()) / "assets" / "generation_log.json"
    if not log_path.exists():
        logger.warning(f"Generation log not found at {log_path}. Returning empty list.")
        return []

    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, list):
            logger.error(f"Generation log at {log_path} is not a list.")
            return []
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse generation log at {log_path}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error reading generation log: {e}")
        return []

def generate_metadata_for_image(
    image_id: str,
    detail_level: str,
    object_list: List[str],
    texture_settings: Dict[str, Any],
    asset_params: Optional[List[Dict[str, Any]]] = None
) -> StimulusMetadata:
    """
    Generates a StimulusMetadata object for a given image.
    
    Args:
        image_id: Unique identifier for the image.
        detail_level: Level of detail (e.g., 'baseline', 'enhanced', 'reduced').
        object_list: List of object names detected or present in the image.
        texture_settings: Dictionary of texture parameters.
        asset_params: Optional list of asset parameter dictionaries from generation_log.
    
    Returns:
        StimulusMetadata instance with UTC timestamps.
    """
    # Use datetime.now(timezone.utc) as mandated by T017
    now = datetime.now(timezone.utc)
    timestamp_str = now.isoformat()
    
    # If asset_params are provided, use them; otherwise empty list
    final_asset_params = asset_params if asset_params is not None else []

    return StimulusMetadata(
        id=image_id,
        detail_level=detail_level,
        object_list=object_list,
        texture_settings=texture_settings,
        timestamp=timestamp_str,
        manipulation_timestamp=timestamp_str,
        asset_parameters=final_asset_params
    )

def save_metadata_as_yaml(metadata: StimulusMetadata, output_path: Path) -> None:
    """
    Saves a StimulusMetadata object to a YAML file.
    
    Args:
        metadata: The metadata object to save.
        output_path: The full path to the output .yaml file.
    """
    try:
        # Convert dataclass to dict for YAML serialization
        data = asdict(metadata)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
        logger.info(f"Metadata saved to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save metadata to {output_path}: {e}")
        raise

def load_metadata_from_yaml(path: Path) -> Optional[StimulusMetadata]:
    """
    Loads a StimulusMetadata object from a YAML file.
    
    Args:
        path: Path to the YAML file.
    
    Returns:
        StimulusMetadata instance or None if loading fails.
    """
    if not path.exists():
        logger.warning(f"Metadata file not found: {path}")
        return None

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if not isinstance(data, dict):
            logger.error(f"Invalid metadata format in {path}")
            return None
        
        return StimulusMetadata(
            id=data.get('id', ''),
            detail_level=data.get('detail_level', ''),
            object_list=data.get('object_list', []),
            texture_settings=data.get('texture_settings', {}),
            timestamp=data.get('timestamp', ''),
            manipulation_timestamp=data.get('manipulation_timestamp', ''),
            asset_parameters=data.get('asset_parameters', [])
        )
    except Exception as e:
        logger.error(f"Failed to load metadata from {path}: {e}")
        return None

def generate_stimulus_metadata(
    image_ids: List[str],
    detail_level: str = "baseline",
    object_list: Optional[List[str]] = None
) -> List[Path]:
    """
    Generates metadata files for a list of image IDs.
    
    This function reads the asset generation log (T015.1-LogParams) and includes
    the specific asset parameters in the metadata for each image.
    
    Args:
        image_ids: List of image identifiers (without extension).
        detail_level: The detail level for the metadata (e.g., 'baseline', 'enhanced').
        object_list: Optional list of objects present in the image. If None, defaults to empty.
    
    Returns:
        List of paths to the generated YAML files.
    """
    generated_paths = []
    
    # Load asset parameters from generation_log.json
    asset_params = load_generation_log()
    
    stimuli_dir = get_stimuli_dir()
    
    if object_list is None:
        object_list = []
    
    for img_id in image_ids:
        metadata = generate_metadata_for_image(
            image_id=img_id,
            detail_level=detail_level,
            object_list=object_list,
            texture_settings={"noise": 0.0, "sharpness": 1.0},
            asset_params=asset_params
        )
        
        output_path = Path(stimuli_dir) / f"{img_id}_metadata.yaml"
        save_metadata_as_yaml(metadata, output_path)
        generated_paths.append(output_path)
        
    return generated_paths

def main():
    """
    CLI entry point for generating stimulus metadata.
    Reads the list of baseline images from data/stimuli/raw/ (or a manifest)
    and generates metadata files for each.
    """
    logger.info("Starting stimulus metadata generation (T017).")
    
    # Identify baseline images
    # We assume images are stored in data/stimuli/raw/ with .png extension
    raw_dir = Path(get_stimuli_dir()) / "raw"
    if not raw_dir.exists():
        # Fallback: check if raw is directly in stimuli_dir
        raw_dir = Path(get_stimuli_dir())
        
    image_files = list(raw_dir.glob("*.png"))
    
    if not image_files:
        logger.error("No baseline images found in raw directory. Aborting.")
        return

    image_ids = [f.stem for f in image_files]
    logger.info(f"Found {len(image_ids)} baseline images: {image_ids}")

    # Generate metadata for all baseline images
    # We use 'baseline' as the detail level for the raw images
    generated_files = generate_stimulus_metadata(
        image_ids=image_ids,
        detail_level="baseline",
        object_list=[] # Object list would be populated by a detector if available
    )

    logger.info(f"Successfully generated {len(generated_files)} metadata files.")
    for p in generated_files:
        logger.info(f"  - {p}")

    # Verification: Check that manipulation_timestamp is present in all files
    missing_timestamps = []
    for p in generated_files:
        meta = load_metadata_from_yaml(p)
        if not meta or not meta.manipulation_timestamp:
            missing_timestamps.append(str(p))
    
    if missing_timestamps:
        logger.error(f"Verification failed: Missing manipulation_timestamp in {len(missing_timestamps)} files.")
        for m in missing_timestamps:
            logger.error(f"  - {m}")
        # Do not raise SystemExit here, just log, as the files were created
    else:
        logger.info("Verification passed: All metadata files contain manipulation_timestamp.")

    # Verification: Check that asset parameters are logged
    if not asset_params:
        logger.warning("No asset parameters found in generation_log.json.")
    else:
        logger.info(f"Asset parameters loaded: {len(asset_params)} entries.")

if __name__ == "__main__":
    main()