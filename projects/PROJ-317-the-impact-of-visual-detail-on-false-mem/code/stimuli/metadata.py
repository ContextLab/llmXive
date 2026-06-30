import json
import logging
import math
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List

@dataclass
class ManipulationRecord:
    type: str
    parameters: dict
    success: bool
    error_message: Optional[str] = None

@dataclass
class StimulusMetadata:
    id: str
    source_image_id: str
    manipulation_records: List[ManipulationRecord] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    complexity_score: Optional[float] = None

def generate_metadata_for_image(image_id: str, source_image_id: str, manipulation_type: str, success: bool, error: Optional[str] = None) -> StimulusMetadata:
    record = ManipulationRecord(
        type=manipulation_type,
        parameters={},
        success=success,
        error_message=error
    )
    return StimulusMetadata(
        id=f"{source_image_id}_{manipulation_type}",
        source_image_id=source_image_id,
        manipulation_records=[record]
    )

def save_metadata_as_yaml(metadata: StimulusMetadata, output_path: Path):
    import yaml
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        yaml.dump(asdict(metadata), f)

def load_metadata_from_yaml(path: Path) -> StimulusMetadata:
    import yaml
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    return StimulusMetadata(**data)

def main():
    # Placeholder for CLI usage if needed
    pass
