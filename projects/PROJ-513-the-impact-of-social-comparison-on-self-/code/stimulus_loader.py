"""
Stimulus Loader Module

Loads static assets (AI and Human images) from the data/stimuli directory
and validates the presence and structure of associated metadata files.

This module ensures that every stimulus image has a corresponding JSON metadata
file containing required fields (e.g., pose, lighting, origin) before
allowing them to be used in the study.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# Constants for required metadata fields based on FR-008 (Metadata Matching)
REQUIRED_METADATA_FIELDS = {
    "pose": "The pose description or identifier (e.g., 'frontal', 'profile')",
    "lighting": "The lighting condition description (e.g., 'studio', 'natural')",
    "origin": "Source of the image ('AI' or 'Human')",
    "stimulus_id": "Unique identifier for the stimulus"
}

class StimulusLoadError(Exception):
    """Custom exception for stimulus loading failures."""
    pass

class MetadataValidationError(Exception):
    """Custom exception for metadata validation failures."""
    pass

def get_stimuli_paths(base_dir: str = "data/stimuli") -> Dict[str, List[Path]]:
    """
    Scans the data/stimuli directory for AI and Human image subdirectories.

    Args:
        base_dir: The root directory containing 'stimuli' subfolder.

    Returns:
        A dictionary mapping 'ai' and 'human' keys to lists of image file paths.

    Raises:
        StimulusLoadError: If the base directory does not exist or subdirectories are missing.
    """
    stimuli_root = Path(base_dir)
    if not stimuli_root.exists():
        raise StimulusLoadError(f"Stimuli root directory not found: {stimuli_root}")

    ai_dir = stimuli_root / "ai"
    human_dir = stimuli_root / "human"

    if not ai_dir.exists():
        raise StimulusLoadError(f"AI stimuli directory not found: {ai_dir}")
    if not human_dir.exists():
        raise StimulusLoadError(f"Human stimuli directory not found: {human_dir}")

    # Support common image extensions
    extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}

    ai_images = [f for f in ai_dir.iterdir() if f.suffix.lower() in extensions]
    human_images = [f for f in human_dir.iterdir() if f.suffix.lower() in extensions]

    if not ai_images and not human_images:
        # Warn but don't error immediately if empty, though likely an issue
        pass

    return {
        "ai": sorted(ai_images),
        "human": sorted(human_images)
    }

def load_metadata(image_path: Path, base_dir: str = "data/stimuli") -> Optional[Dict[str, Any]]:
    """
    Loads the metadata JSON file associated with a specific image.

    The metadata file is expected to have the same name as the image but with a .json extension.
    Example: data/stimuli/ai/image_001.png -> data/stimuli/ai/image_001.json

    Args:
        image_path: Path to the image file.
        base_dir: Root directory for stimuli.

    Returns:
        Parsed JSON dictionary or None if no metadata file exists.

    Raises:
        StimulusLoadError: If the metadata file exists but is invalid JSON.
    """
    metadata_path = image_path.with_suffix(".json")

    if not metadata_path.exists():
        return None

    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise StimulusLoadError(f"Invalid JSON in metadata file {metadata_path}: {e}")

def validate_metadata_fields(metadata: Dict[str, Any], image_path: Path) -> List[str]:
    """
    Validates that the metadata dictionary contains all required fields.

    Args:
        metadata: The loaded metadata dictionary.
        image_path: Path to the image (for error messaging).

    Returns:
        A list of missing field names. Empty list if all present.
    """
    if metadata is None:
        return list(REQUIRED_METADATA_FIELDS.keys())

    missing = []
    for field in REQUIRED_METADATA_FIELDS:
        if field not in metadata:
            missing.append(field)
    return missing

def load_stimuli(base_dir: str = "data/stimuli", strict: bool = True) -> List[Dict[str, Any]]:
    """
    Main entry point to load and validate all stimuli.

    Iterates through AI and Human image directories, loads associated metadata,
    and validates that required fields are present.

    Args:
        base_dir: Root directory for stimuli.
        strict: If True, raises an exception if any stimulus is missing metadata
                or required fields. If False, logs warnings and skips invalid entries.

    Returns:
        A list of dictionaries, each containing:
        - 'path': Path to the image
        - 'origin': 'AI' or 'Human'
        - 'metadata': The loaded metadata dictionary
        - 'id': The stimulus_id from metadata (or filename if missing)

    Raises:
        MetadataValidationError: If strict=True and validation fails for any image.
    """
    paths = get_stimuli_paths(base_dir)
    valid_stimuli = []
    errors = []

    for origin, image_list in paths.items():
        for img_path in image_list:
            metadata = load_metadata(img_path, base_dir)
            missing_fields = validate_metadata_fields(metadata, img_path)

            if missing_fields:
                error_msg = (
                    f"Missing required fields {missing_fields} in metadata for "
                    f"{img_path.name}. Metadata: {metadata}"
                )
                if strict:
                    errors.append(error_msg)
                else:
                    # Log warning (in a real app, use logging module)
                    print(f"WARNING: {error_msg}")
                    continue

            # Construct the stimulus record
            record = {
                "path": img_path,
                "origin": origin,
                "metadata": metadata,
                "id": metadata.get("stimulus_id", img_path.stem) if metadata else img_path.stem
            }
            valid_stimuli.append(record)

    if strict and errors:
        raise MetadataValidationError(
            f"Stimulus validation failed for {len(errors)} images:\n" + "\n".join(errors)
        )

    return valid_stimuli

def get_matched_pairs(stimuli: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Groups stimuli into pairs based on matching metadata criteria (e.g., pose, lighting).

    This is a helper for the data validation logic (FR-008) to ensure AI and Human
    sets are matched.

    Args:
        stimuli: List of loaded stimulus records from load_stimuli().

    Returns:
        A list of pairs (or groups) where AI and Human images share the same
        'pose' and 'lighting' attributes.
    """
    # Group by (pose, lighting)
    groups: Dict[tuple, List[Dict[str, Any]]] = {}

    for item in stimuli:
        meta = item["metadata"]
        if not meta:
            continue
        pose = meta.get("pose")
        lighting = meta.get("lighting")

        if pose and lighting:
            key = (pose, lighting)
            if key not in groups:
                groups[key] = []
            groups[key].append(item)

    # Filter groups that have at least one AI and one Human
    matched_pairs = []
    for key, items in groups.items():
        ai_items = [i for i in items if i["origin"] == "ai"]
        human_items = [i for i in items if i["origin"] == "human"]

        if ai_items and human_items:
            matched_pairs.append({
                "key": key,
                "ai": ai_items,
                "human": human_items,
                "count": len(items)
            })

    return matched_pairs

def main():
    """
    CLI entry point to test loading and validation.
    """
    print("Initializing Stimulus Loader...")
    try:
        stimuli = load_stimuli(base_dir="data/stimuli", strict=True)
        print(f"Successfully loaded {len(stimuli)} valid stimuli.")

        # Check for matched pairs
        pairs = get_matched_pairs(stimuli)
        print(f"Found {len(pairs)} matched (pose, lighting) groups.")

        for p in pairs:
            print(f"  Group {p['key']}: {len(p['ai'])} AI, {len(p['human'])} Human")

    except (StimulusLoadError, MetadataValidationError) as e:
        print(f"Error: {e}")
        raise SystemExit(1)

if __name__ == "__main__":
    main()