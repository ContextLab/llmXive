"""
Stimulus Metadata Generation Module.

Generates metadata files for each baseline image, storing detail_level,
object_list, texture_settings, timestamp, and manipulation_timestamp.
"""
import json
import logging
import math
import os
import random
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import yaml

from config import get_project_root, get_stimuli_dir, get_data_dir
from utils.logging import get_logger, log_error

logger = get_logger(__name__)

@dataclass
class ManipulationRecord:
    """Record of a specific manipulation performed on an image."""
    timestamp: str
    manipulation_type: str
    parameters: Dict[str, Any]

@dataclass
class StimulusMetadata:
    """Complete metadata for a stimulus image."""
    id: str
    path: str
    detail_level: str
    object_list: List[str]
    texture_settings: Dict[str, Any]
    timestamp: str
    manipulation_timestamp: str
    baseline_complexity_score: Optional[float] = None
    manipulation_records: List[ManipulationRecord] = field(default_factory=list)

def generate_metadata_for_image(
    image_id: str,
    image_path: Path,
    baseline_complexity: Optional[float] = None,
    object_list: Optional[List[str]] = None,
    texture_settings: Optional[Dict[str, Any]] = None
) -> StimulusMetadata:
    """
    Generate metadata for a single baseline image.

    Args:
        image_id: Unique identifier for the image.
        image_path: Path to the image file.
        baseline_complexity: Optional baseline complexity score.
        object_list: Optional list of detected objects. If None, generates a mock list.
        texture_settings: Optional texture configuration. If None, generates defaults.

    Returns:
        StimulusMetadata object with all required fields populated.
    """
    now = datetime.utcnow().isoformat() + "Z"

    # Default object list if not provided (mock for baseline generation)
    if object_list is None:
        object_list = [
            "background_texture",
            "ambient_lighting",
            "general_shape"
        ]

    # Default texture settings if not provided
    if texture_settings is None:
        texture_settings = {
            "grain": 0.0,
            "sharpness": 1.0,
            "contrast": 1.0
        }

    # Determine detail level based on complexity if available
    detail_level = "baseline"
    if baseline_complexity is not None:
        if baseline_complexity < 0.4:
            detail_level = "low"
        elif baseline_complexity > 0.6:
            detail_level = "high"
        else:
            detail_level = "medium"

    metadata = StimulusMetadata(
        id=image_id,
        path=str(image_path),
        detail_level=detail_level,
        object_list=object_list,
        texture_settings=texture_settings,
        timestamp=now,
        manipulation_timestamp=now,
        baseline_complexity_score=baseline_complexity
    )

    return metadata

def save_metadata_as_yaml(metadata: StimulusMetadata, output_path: Path) -> None:
    """
    Save StimulusMetadata to a YAML file.

    Args:
        metadata: The metadata object to save.
        output_path: Path where the YAML file will be written.
    """
    # Convert dataclass to dict, handling nested dataclasses
    data = {
        "id": metadata.id,
        "path": metadata.path,
        "detail_level": metadata.detail_level,
        "object_list": metadata.object_list,
        "texture_settings": metadata.texture_settings,
        "timestamp": metadata.timestamp,
        "manipulation_timestamp": metadata.manipulation_timestamp,
        "baseline_complexity_score": metadata.baseline_complexity_score
    }

    if metadata.manipulation_records:
        data["manipulation_records"] = [
            asdict(record) for record in metadata.manipulation_records
        ]

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Saved metadata to {output_path}")

def load_metadata_from_yaml(path: Path) -> Optional[StimulusMetadata]:
    """
    Load StimulusMetadata from a YAML file.

    Args:
        path: Path to the YAML file.

    Returns:
        StimulusMetadata object or None if file not found or invalid.
    """
    if not path.exists():
        logger.warning(f"Metadata file not found: {path}")
        return None

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if not data:
            return None

        # Reconstruct nested objects
        manipulation_records = []
        if "manipulation_records" in data:
            for rec in data["manipulation_records"]:
                manipulation_records.append(ManipulationRecord(**rec))

        metadata = StimulusMetadata(
            id=data["id"],
            path=data["path"],
            detail_level=data["detail_level"],
            object_list=data["object_list"],
            texture_settings=data["texture_settings"],
            timestamp=data["timestamp"],
            manipulation_timestamp=data["manipulation_timestamp"],
            baseline_complexity_score=data.get("baseline_complexity_score"),
            manipulation_records=manipulation_records
        )
        return metadata

    except Exception as e:
        logger.error(f"Failed to load metadata from {path}: {e}")
        return None

def generate_stimulus_metadata(
    image_id: str,
    image_path: Path,
    complexity_score: Optional[float] = None
) -> None:
    """
    Generate and save metadata for a single image.

    This function is the primary entry point for creating metadata files.
    It generates the metadata object and saves it to the correct location.

    Args:
        image_id: Unique identifier for the image.
        image_path: Path to the image file.
        complexity_score: Optional baseline complexity score.
    """
    metadata = generate_metadata_for_image(
        image_id=image_id,
        image_path=image_path,
        baseline_complexity=complexity_score
    )

    # Output path: directly inside data/stimuli/ per Constitution VII
    output_dir = get_stimuli_dir()
    output_path = output_dir / f"{image_id}_metadata.yaml"

    save_metadata_as_yaml(metadata, output_path)

def main() -> None:
    """
    Main entry point for generating metadata for all baseline images.

    Iterates over images in data/stimuli/raw/ and generates metadata for each.
    """
    stimuli_dir = get_stimuli_dir()
    raw_dir = stimuli_dir / "raw"

    if not raw_dir.exists():
        logger.warning(f"Raw stimuli directory not found: {raw_dir}")
        logger.info("No images to process. Ensure T006.3-Filter has populated data/stimuli/raw/")
        return

    # Find all image files (common extensions)
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    image_files = [
        f for f in raw_dir.iterdir()
        if f.is_file() and f.suffix.lower() in image_extensions
    ]

    if not image_files:
        logger.warning(f"No image files found in {raw_dir}")
        return

    logger.info(f"Found {len(image_files)} images to process")

    # Try to load complexity scores if available
    complexity_stats_path = get_data_dir() / "processed" / "complexity_stats.json"
    complexity_map: Dict[str, float] = {}
    if complexity_stats_path.exists():
        try:
            with open(complexity_stats_path, 'r') as f:
                stats = json.load(f)
            # Assuming stats contains a mapping or list we can index
            if "image_scores" in stats:
                complexity_map = {item["id"]: item["score"] for item in stats["image_scores"]}
        except Exception as e:
            logger.warning(f"Could not load complexity stats: {e}")

    success_count = 0
    error_count = 0

    for img_path in image_files:
        image_id = img_path.stem
        try:
            complexity = complexity_map.get(image_id)
            generate_stimulus_metadata(image_id, img_path, complexity)
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to generate metadata for {img_path}: {e}")
            error_count += 1

    logger.info(f"Metadata generation complete: {success_count} succeeded, {error_count} failed")

    if error_count > 0:
        logger.warning(f"Some metadata files were not generated. Check logs for details.")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate stimulus metadata for baseline images")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level.upper()))
    main()
