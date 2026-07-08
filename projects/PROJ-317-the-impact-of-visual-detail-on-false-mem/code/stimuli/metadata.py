import json
import logging
import math
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml

logger = logging.getLogger(__name__)

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
        with open(output_path, 'w') as f:
            # Convert dataclass to dict
            data = asdict(metadata)
            # Convert ManipulationRecord objects to dict if they are not already
            # asdict handles nested dataclasses recursively
            yaml.dump(data, f, default_flow_style=False)
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

def main():
    """Main entry point for metadata generation (for testing)."""
    logging.basicConfig(level=logging.INFO)
    # This is just a placeholder for CLI usage if needed
    pass

if __name__ == "__main__":
    main()
