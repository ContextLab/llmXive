import json
import logging
import math
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml

from config import get_stimuli_dir, get_stimuli_metadata_dir, get_project_root
from utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class ManipulationRecord:
    type: str
    parameters: Dict[str, Any]
    output_path: str
    complexity_score: float

@dataclass
class StimulusMetadata:
    image_id: str
    original_path: str
    manipulations: List[ManipulationRecord]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    version: str = "1.0"

def generate_metadata_for_image(
    image_id: str,
    original_path: str,
    enhanced_path: str,
    reduced_path: str,
    original_score: float,
    enhanced_score: float,
    reduced_score: float,
    manipulation_details: Dict[str, Any]
) -> StimulusMetadata:
    """
    Generate metadata for a processed image.
    
    Args:
        image_id: Unique identifier for the image.
        original_path: Path to the original image.
        enhanced_path: Path to the enhanced image.
        reduced_path: Path to the reduced image.
        original_score: Complexity score of original.
        enhanced_score: Complexity score of enhanced.
        reduced_score: Complexity score of reduced.
        manipulation_details: Details of manipulations performed.
        
    Returns:
        StimulusMetadata object.
    """
    manipulations = [
        ManipulationRecord(
            type="enhanced",
            parameters=manipulation_details.get("enhanced", {}),
            output_path=enhanced_path,
            complexity_score=enhanced_score
        ),
        ManipulationRecord(
            type="reduced",
            parameters=manipulation_details.get("reduced", {}),
            output_path=reduced_path,
            complexity_score=reduced_score
        )
    ]
    
    return StimulusMetadata(
        image_id=image_id,
        original_path=original_path,
        manipulations=manipulations
    )

def save_metadata_as_yaml(metadata: StimulusMetadata, output_path: Path):
    """
    Save metadata to a YAML file.
    
    Args:
        metadata: StimulusMetadata object.
        output_path: Path to save the YAML file.
    """
    try:
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            # Convert dataclass to dict
            data = asdict(metadata)
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Saved metadata to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save metadata to {output_path}: {e}")
        raise

def load_metadata_from_yaml(input_path: Path) -> Optional[StimulusMetadata]:
    """
    Load metadata from a YAML file.
    
    Args:
        input_path: Path to the YAML file.
        
    Returns:
        StimulusMetadata object or None.
    """
    try:
        with open(input_path, 'r') as f:
            data = yaml.safe_load(f)
        
        if not data:
            logger.warning(f"Empty metadata file: {input_path}")
            return None

        # Reconstruct ManipulationRecord objects
        manipulations = []
        for m_data in data.get('manipulations', []):
            manipulations.append(ManipulationRecord(**m_data))
        
        return StimulusMetadata(
            image_id=data['image_id'],
            original_path=data['original_path'],
            manipulations=manipulations,
            created_at=data.get('created_at', ''),
            version=data.get('version', '1.0')
        )
    except Exception as e:
        logger.error(f"Failed to load metadata from {input_path}: {e}")
        return None

def generate_stimulus_metadata(
    image_id: str,
    original_path: str,
    enhanced_path: str,
    reduced_path: str,
    original_score: float,
    enhanced_score: float,
    reduced_score: float,
    manipulation_details: Dict[str, Any]
) -> Path:
    """
    Generate and save metadata for a processed image.
    
    This function orchestrates the generation of metadata and saves it to the
    appropriate directory as a YAML file, adhering to Constitution VII requirements.
    
    Args:
        image_id: Unique identifier for the image.
        original_path: Path to the original image.
        enhanced_path: Path to the enhanced image.
        reduced_path: Path to the reduced image.
        original_score: Complexity score of original.
        enhanced_score: Complexity score of enhanced.
        reduced_score: Complexity score of reduced.
        manipulation_details: Details of manipulations performed.
        
    Returns:
        Path to the saved metadata file.
    """
    metadata = generate_metadata_for_image(
        image_id=image_id,
        original_path=original_path,
        enhanced_path=enhanced_path,
        reduced_path=reduced_path,
        original_score=original_score,
        enhanced_score=enhanced_score,
        reduced_score=reduced_score,
        manipulation_details=manipulation_details
    )
    
    # Ensure metadata directory exists
    metadata_dir = get_stimuli_metadata_dir()
    metadata_dir.mkdir(parents=True, exist_ok=True)
    
    # Save as YAML
    output_path = metadata_dir / f"{image_id}.yaml"
    save_metadata_as_yaml(metadata, output_path)
    
    return output_path

def main():
    """Main entry point for metadata generation (for testing)."""
    logging.basicConfig(level=logging.INFO)
    
    # Example usage for testing
    test_details = {
        "enhanced": {
            "objects_added": 5,
            "positions": [(10, 10), (20, 20)]
        },
        "reduced": {
            "blur_radius": 5,
            "areas_masked": 2
        }
    }
    
    test_metadata = generate_metadata_for_image(
        image_id="test_001",
        original_path="data/stimuli/raw/test_001.jpg",
        enhanced_path="data/stimuli/enhanced/test_001_enh.jpg",
        reduced_path="data/stimuli/reduced/test_001_red.jpg",
        original_score=0.5,
        enhanced_score=0.7,
        reduced_score=0.3,
        manipulation_details=test_details
    )
    
    metadata_dir = get_stimuli_metadata_dir()
    metadata_dir.mkdir(parents=True, exist_ok=True)
    output_path = metadata_dir / "test_001.yaml"
    save_metadata_as_yaml(test_metadata, output_path)
    
    logger.info(f"Test metadata generated at {output_path}")
    
    # Verify loading
    loaded = load_metadata_from_yaml(output_path)
    if loaded:
        logger.info(f"Successfully loaded metadata: {loaded.image_id}")
        logger.info(f"Original complexity: {loaded.manipulations[0].complexity_score}")
    else:
        logger.error("Failed to load test metadata")

if __name__ == "__main__":
    main()