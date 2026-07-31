"""
Stimulus Metadata Generation Module

Generates and manages metadata for baseline images used in the visual detail study.
Produces YAML files containing detail_level, object_list, texture_settings, and timestamp.
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

from config import get_stimuli_dir, get_stimuli_metadata_dir, get_project_root
from utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class ManipulationRecord:
    """Record of a specific manipulation applied to an image."""
    type: str  # 'enhanced' or 'reduced'
    parameters: Dict[str, Any]
    timestamp: str

@dataclass
class StimulusMetadata:
    """Complete metadata structure for a single stimulus image."""
    id: str
    detail_level: str  # 'low', 'medium', 'high', or specific descriptor
    object_list: List[str]
    texture_settings: Dict[str, Any]
    timestamp: str
    complexity_score: Optional[float] = None
    image_path: Optional[str] = None
    manipulation_records: List[ManipulationRecord] = field(default_factory=list)
    source_dataset: Optional[str] = None
    checksum: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert dataclass to dictionary for serialization."""
        return {
            'id': self.id,
            'detail_level': self.detail_level,
            'object_list': self.object_list,
            'texture_settings': self.texture_settings,
            'timestamp': self.timestamp,
            'complexity_score': self.complexity_score,
            'image_path': self.image_path,
            'manipulation_records': [asdict(m) for m in self.manipulation_records],
            'source_dataset': self.source_dataset,
            'checksum': self.checksum
        }

def generate_metadata_for_image(
    image_path: Path,
    image_id: str,
    complexity_score: Optional[float] = None,
    object_list: Optional[List[str]] = None,
    source_dataset: Optional[str] = None,
    checksum: Optional[str] = None
) -> StimulusMetadata:
    """
    Generate metadata for a single baseline image.

    Args:
        image_path: Path to the image file
        image_id: Unique identifier for the image
        complexity_score: Pre-calculated complexity score (optional)
        object_list: List of detected objects (optional, will be generated if missing)
        source_dataset: Name of the source dataset (e.g., 'Visual Genome')
        checksum: SHA256 checksum of the image file (optional)

    Returns:
        StimulusMetadata object with populated fields
    """
    # Determine detail level based on complexity score or filename heuristics
    detail_level = "medium"
    if complexity_score is not None:
        if complexity_score < 0.3:
            detail_level = "low"
        elif complexity_score > 0.7:
            detail_level = "high"
        else:
            detail_level = "medium"
    else:
        # Fallback heuristic based on filename or path
        filename = image_path.name.lower()
        if "simple" in filename or "low" in filename:
            detail_level = "low"
        elif "complex" in filename or "high" in filename:
            detail_level = "high"

    # Generate object list if not provided
    if object_list is None:
        # Heuristic: extract potential object names from filename
        base_name = image_path.stem.replace('_', ' ').replace('-', ' ')
        words = base_name.split()
        # Filter out common stop words and keep potential nouns
        stop_words = {'the', 'a', 'an', 'image', 'of', 'in', 'on', 'at', 'to', 'for'}
        potential_objects = [w for w in words if w not in stop_words and len(w) > 2]
        
        if not potential_objects:
            # Default fallback list based on common dataset objects
            potential_objects = ["background", "scene", "general_objects"]
        
        object_list = potential_objects

    # Generate texture settings based on detail level
    texture_settings = {
        'sharpness': 1.0 if detail_level == "high" else 0.8 if detail_level == "medium" else 0.5,
        'noise_level': 0.1 if detail_level == "low" else 0.05 if detail_level == "medium" else 0.0,
        'color_saturation': 0.9,
        'contrast': 1.0
    }

    metadata = StimulusMetadata(
        id=image_id,
        detail_level=detail_level,
        object_list=object_list,
        texture_settings=texture_settings,
        timestamp=datetime.now().isoformat(),
        complexity_score=complexity_score,
        image_path=str(image_path),
        source_dataset=source_dataset,
        checksum=checksum
    )

    logger.info(f"Generated metadata for image {image_id}: detail_level={detail_level}, objects={len(object_list)}")
    return metadata

def save_metadata_as_yaml(metadata: StimulusMetadata, output_path: Path) -> None:
    """
    Save StimulusMetadata to a YAML file.

    Args:
        metadata: The metadata object to save
        output_path: Path where the YAML file will be written
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = metadata.to_dict()
    # Convert ManipulationRecord dicts to proper format if needed
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    logger.info(f"Saved metadata to {output_path}")

def load_metadata_from_yaml(path: Path) -> Optional[StimulusMetadata]:
    """
    Load StimulusMetadata from a YAML file.

    Args:
        path: Path to the YAML file

    Returns:
        StimulusMetadata object or None if file not found or invalid
    """
    if not path.exists():
        logger.warning(f"Metadata file not found: {path}")
        return None

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Reconstruct ManipulationRecord objects if present
        if 'manipulation_records' in data and data['manipulation_records']:
            data['manipulation_records'] = [
                ManipulationRecord(**m) for m in data['manipulation_records']
            ]
        
        return StimulusMetadata(**data)
    except Exception as e:
        logger.error(f"Failed to load metadata from {path}: {e}")
        return None

def generate_stimulus_metadata(
    image_paths: List[Path],
    complexity_scores: Optional[Dict[str, float]] = None,
    object_lists: Optional[Dict[str, List[str]]] = None,
    source_dataset: str = "Visual Genome Subset"
) -> List[StimulusMetadata]:
    """
    Generate metadata for a list of baseline images.

    Args:
        image_paths: List of paths to baseline images
        complexity_scores: Optional dict mapping image_id to complexity_score
        object_lists: Optional dict mapping image_id to object_list
        source_dataset: Name of the source dataset

    Returns:
        List of StimulusMetadata objects
    """
    metadata_list = []
    output_dir = get_stimuli_metadata_dir()

    for img_path in image_paths:
        if not img_path.exists():
            logger.warning(f"Image not found, skipping: {img_path}")
            continue

        # Extract ID from filename (stem)
        image_id = img_path.stem
        
        complexity = None
        if complexity_scores and image_id in complexity_scores:
            complexity = complexity_scores[image_id]

        objects = None
        if object_lists and image_id in object_lists:
            objects = object_lists[image_id]

        # Generate checksum if not provided (basic implementation)
        checksum = None
        try:
            import hashlib
            sha256_hash = hashlib.sha256()
            with open(img_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            checksum = sha256_hash.hexdigest()
        except Exception as e:
            logger.warning(f"Could not compute checksum for {img_path}: {e}")

        metadata = generate_metadata_for_image(
            image_path=img_path,
            image_id=image_id,
            complexity_score=complexity,
            object_list=objects,
            source_dataset=source_dataset,
            checksum=checksum
        )

        output_path = output_dir / f"{image_id}.yaml"
        save_metadata_as_yaml(metadata, output_path)
        metadata_list.append(metadata)

    logger.info(f"Generated {len(metadata_list)} metadata files in {output_dir}")
    return metadata_list

def main():
    """
    Main entry point for generating stimulus metadata.
    Scans the stimuli directory and generates metadata for all images.
    """
    stimuli_dir = get_stimuli_dir()
    metadata_dir = get_stimuli_metadata_dir()
    
    if not stimuli_dir.exists():
        logger.error(f"Stimuli directory does not exist: {stimuli_dir}")
        sys.exit(1)

    # Find all image files
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
    image_paths = [
        p for p in stimuli_dir.rglob('*')
        if p.suffix.lower() in image_extensions
    ]

    if not image_paths:
        logger.warning(f"No images found in {stimuli_dir}")
        sys.exit(0)

    logger.info(f"Found {len(image_paths)} images to process")

    # Generate metadata for all images
    generate_stimulus_metadata(image_paths, source_dataset="Visual Genome Subset")

    logger.info("Metadata generation complete")

if __name__ == "__main__":
    import sys
    main()
