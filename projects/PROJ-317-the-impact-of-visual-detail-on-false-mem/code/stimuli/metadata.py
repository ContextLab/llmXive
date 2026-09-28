import json
import logging
import os
import random
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

import yaml

from config import get_stimuli_dir, get_project_root
from utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class ManipulationRecord:
    """Record of specific manipulation operations applied to an image."""
    operation_type: str  # 'enhanced' or 'reduced'
    timestamp: str
    asset_count: int
    assets_added: List[Dict[str, Any]]
    assets_removed: List[Dict[str, Any]]
    parameters: Dict[str, Any]

@dataclass
class StimulusMetadata:
    """Complete metadata for a stimulus image (baseline or manipulated)."""
    id: str
    path: str
    type: str  # 'baseline', 'enhanced', 'reduced'
    detail_level: str
    baseline_id: Optional[str]
    manipulation_timestamp: Optional[str]
    complexity_score: Optional[float]
    manipulation_record: Optional[Dict[str, Any]]
    created_at: str
    version: str

def load_generation_log(log_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Load the asset generation log from JSON."""
    if log_path is None:
        # Default path relative to project root
        log_path = get_project_root() / "data" / "assets" / "generation_log.json"
    else:
        log_path = Path(log_path)

    if not log_path.exists():
        raise FileNotFoundError(f"Generation log not found at {log_path}")

    with open(log_path, 'r') as f:
        return json.load(f)

def generate_metadata_for_image(
    image_id: str,
    image_path: str,
    manipulation_type: str,
    baseline_id: Optional[str] = None,
    manipulation_params: Optional[Dict[str, Any]] = None
) -> StimulusMetadata:
    """
    Generate metadata for a specific image based on its manipulation type.

    Args:
        image_id: Unique identifier for the image
        image_path: Path to the image file
        manipulation_type: 'enhanced', 'reduced', or 'baseline'
        baseline_id: ID of the original baseline image (if manipulated)
        manipulation_params: Parameters used in manipulation (e.g., from generation_log)

    Returns:
        StimulusMetadata object
    """
    now = datetime.now(timezone.utc)
    timestamp = now.isoformat()

    if manipulation_type == 'baseline':
        return StimulusMetadata(
            id=image_id,
            path=image_path,
            type='baseline',
            detail_level='baseline',
            baseline_id=None,
            manipulation_timestamp=None,
            complexity_score=None,  # Will be filled by loader if needed
            manipulation_record=None,
            created_at=timestamp,
            version='1.0'
        )

    # For manipulated images, we need to construct a manipulation record
    if manipulation_params is None:
        # Load default params from generation_log if not provided
        try:
            params = load_generation_log()
            # Take first entry as a representative sample for metadata
            manipulation_params = params[0] if params else {}
        except FileNotFoundError:
            logger.warning("No generation log found, using empty params")
            manipulation_params = {}

    record = ManipulationRecord(
        operation_type=manipulation_type,
        timestamp=timestamp,
        asset_count=manipulation_params.get('count', 1),
        assets_added=manipulation_params.get('assets_added', []),
        assets_removed=manipulation_params.get('assets_removed', []),
        parameters=manipulation_params
    )

    return StimulusMetadata(
        id=image_id,
        path=image_path,
        type=manipulation_type,
        detail_level='enhanced' if manipulation_type == 'enhanced' else 'reduced',
        baseline_id=baseline_id,
        manipulation_timestamp=timestamp,
        complexity_score=None,
        manipulation_record=asdict(record),
        created_at=timestamp,
        version='1.0'
    )

def save_metadata_as_yaml(metadata: StimulusMetadata, output_path: str) -> None:
    """Save metadata to a YAML file."""
    data = asdict(metadata)
    with open(output_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

def load_metadata_from_yaml(path: str) -> StimulusMetadata:
    """Load metadata from a YAML file."""
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    return StimulusMetadata(**data)

def generate_stimulus_metadata(
    baseline_ids: List[str],
    enhanced_ids: List[str],
    reduced_ids: List[str],
    generation_log_path: Optional[str] = None
) -> Dict[str, str]:
    """
    Generate metadata files for all stimuli.

    Args:
        baseline_ids: List of baseline image IDs
        enhanced_ids: List of enhanced image IDs
        reduced_ids: List of reduced image IDs
        generation_log_path: Path to the generation log JSON

    Returns:
        Dictionary mapping image ID to generated metadata file path
    """
    output_map = {}
    stimuli_dir = get_stimuli_dir()

    # Load generation log if provided
    gen_log = None
    if generation_log_path:
        try:
            gen_log = load_generation_log(generation_log_path)
            logger.info(f"Loaded {len(gen_log)} entries from generation log")
        except Exception as e:
            logger.warning(f"Failed to load generation log: {e}")

    # Generate baseline metadata
    for img_id in baseline_ids:
        img_path = str(stimuli_dir / f"{img_id}.png")
        meta = generate_metadata_for_image(
            image_id=img_id,
            image_path=img_path,
            manipulation_type='baseline'
        )
        out_path = str(stimuli_dir / f"{img_id}_metadata.yaml")
        save_metadata_as_yaml(meta, out_path)
        output_map[img_id] = out_path
        logger.info(f"Generated baseline metadata: {out_path}")

    # Generate enhanced metadata
    for img_id in enhanced_ids:
        # Extract baseline ID from enhanced ID (assuming naming convention enhanced_{baseline_id})
        if img_id.startswith("enhanced_"):
            base_id = img_id.replace("enhanced_", "", 1)
        else:
            base_id = None

        img_path = str(stimuli_dir / f"{img_id}.png")
        # Use params from generation log if available
        params = gen_log[0] if gen_log else None
        meta = generate_metadata_for_image(
            image_id=img_id,
            image_path=img_path,
            manipulation_type='enhanced',
            baseline_id=base_id,
            manipulation_params=params
        )
        out_path = str(stimuli_dir / f"enhanced_{img_id}_metadata.yaml")
        save_metadata_as_yaml(meta, out_path)
        output_map[img_id] = out_path
        logger.info(f"Generated enhanced metadata: {out_path}")

    # Generate reduced metadata
    for img_id in reduced_ids:
        # Extract baseline ID from reduced ID (assuming naming convention reduced_{baseline_id})
        if img_id.startswith("reduced_"):
            base_id = img_id.replace("reduced_", "", 1)
        else:
            base_id = None

        img_path = str(stimuli_dir / f"{img_id}.png")
        # Use params from generation log if available
        params = gen_log[0] if gen_log else None
        meta = generate_metadata_for_image(
            image_id=img_id,
            image_path=img_path,
            manipulation_type='reduced',
            baseline_id=base_id,
            manipulation_params=params
        )
        out_path = str(stimuli_dir / f"reduced_{img_id}_metadata.yaml")
        save_metadata_as_yaml(meta, out_path)
        output_map[img_id] = out_path
        logger.info(f"Generated reduced metadata: {out_path}")

    return output_map

def main():
    """CLI entry point for generating stimulus metadata."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate metadata for manipulated stimuli")
    parser.add_argument('--baseline', nargs='+', help='List of baseline image IDs')
    parser.add_argument('--enhanced', nargs='+', help='List of enhanced image IDs')
    parser.add_argument('--reduced', nargs='+', help='List of reduced image IDs')
    parser.add_argument('--log', type=str, help='Path to generation log JSON')
    parser.add_argument('--output-dir', type=str, help='Output directory for metadata files')

    args = parser.parse_args()

    baseline_ids = args.baseline or []
    enhanced_ids = args.enhanced or []
    reduced_ids = args.reduced or []

    if not baseline_ids and not enhanced_ids and not reduced_ids:
        # Try to discover existing images in the stimuli directory
        stimuli_dir = get_stimuli_dir()
        if stimuli_dir.exists():
            all_files = list(stimuli_dir.glob("*.png"))
            baseline_ids = [f.stem for f in all_files if not f.stem.startswith(("enhanced_", "reduced_"))]
            enhanced_ids = [f.stem for f in all_files if f.stem.startswith("enhanced_")]
            reduced_ids = [f.stem for f in all_files if f.stem.startswith("reduced_")]
            logger.info(f"Discovered {len(baseline_ids)} baseline, {len(enhanced_ids)} enhanced, {len(reduced_ids)} reduced images")
        else:
            logger.error("No stimuli found. Please provide --baseline, --enhanced, or --reduced arguments.")
            return 1

    output_map = generate_stimulus_metadata(
        baseline_ids=baseline_ids,
        enhanced_ids=enhanced_ids,
        reduced_ids=reduced_ids,
        generation_log_path=args.log
    )

    logger.info(f"Generated {len(output_map)} metadata files.")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
