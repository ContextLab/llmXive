"""
Module: src.metrics.load_stimuli
Purpose: Load verified, checksummed images from the local archive (data/stimuli/raw/)
for the pilot study. Strictly reads from local files; no network fetching.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

import numpy as np
from PIL import Image

# Import checksum utility from the project's lib layer
from src.lib.utils import compute_file_checksum
from src.config import PROJECT_ROOT, DATA_DIR


class StimuliLoaderError(Exception):
    """Custom exception for stimuli loading failures."""
    pass


def get_stimuli_metadata(archive_dir: Path) -> List[Dict[str, Any]]:
    """
    Load the manifest file (manifest.json) from the archive directory.
    Returns a list of dictionaries containing file path and expected checksum.
    
    Args:
        archive_dir: Path to data/stimuli/raw/
        
    Returns:
        List of metadata dictionaries.
        
    Raises:
        StimuliLoaderError: If manifest is missing or invalid.
    """
    manifest_path = archive_dir / "manifest.json"
    
    if not manifest_path.exists():
        raise StimuliLoaderError(f"Manifest file not found at {manifest_path}")
    
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_data = json.load(f)
    except json.JSONDecodeError as e:
        raise StimuliLoaderError(f"Failed to parse manifest.json: {e}")
    
    if not isinstance(manifest_data, list):
        raise StimuliLoaderError("Manifest must be a list of file entries.")
        
    # Ensure required keys exist
    required_keys = {"filename", "sha256"}
    for i, entry in enumerate(manifest_data):
        if not required_keys.issubset(entry.keys()):
            raise StimuliLoaderError(f"Entry {i} in manifest missing required keys: {required_keys - set(entry.keys())}")
            
    return manifest_data


def load_stimuli_from_archive(
    archive_dir: Path,
    max_images: Optional[int] = None
) -> Tuple[List[Image.Image], List[Dict[str, Any]]]:
    """
    Load images from the local archive, verifying checksums against the manifest.
    
    Args:
        archive_dir: Path to data/stimuli/raw/
        max_images: Optional limit on number of images to load.
        
    Returns:
        Tuple of (List of PIL Image objects, List of metadata dicts for loaded images)
        
    Raises:
        StimuliLoaderError: If checksums fail, files are missing, or images are unreadable.
    """
    if not archive_dir.exists():
        raise StimuliLoaderError(f"Archive directory does not exist: {archive_dir}")
        
    manifest_entries = get_stimuli_metadata(archive_dir)
    
    if max_images is not None:
        manifest_entries = manifest_entries[:max_images]
        
    loaded_images: List[Image.Image] = []
    loaded_metadata: List[Dict[str, Any]] = []
    
    for entry in manifest_entries:
        filename = entry["filename"]
        expected_checksum = entry["sha256"]
        file_path = archive_dir / filename
        
        if not file_path.exists():
            raise StimuliLoaderError(f"Stimulus file missing from archive: {file_path}")
        
        # Verify checksum
        try:
            actual_checksum = compute_file_checksum(file_path)
        except Exception as e:
            raise StimuliLoaderError(f"Failed to compute checksum for {filename}: {e}")
            
        if actual_checksum != expected_checksum:
            raise StimuliLoaderError(
                f"Checksum mismatch for {filename}. "
                f"Expected: {expected_checksum}, Got: {actual_checksum}"
            )
        
        # Load image
        try:
            img = Image.open(file_path)
            img.load() # Force load to catch corruption
            # Convert to RGB if necessary (some datasets might be RGBA or P)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            loaded_images.append(img)
            
            # Store metadata for this specific image
            loaded_metadata.append({
                "filename": filename,
                "path": str(file_path),
                "sha256": actual_checksum,
                "width": img.width,
                "height": img.height,
                "mode": img.mode
            })
            
        except Exception as e:
            raise StimuliLoaderError(f"Failed to load image {filename}: {e}")
            
    return loaded_images, loaded_metadata


def main() -> None:
    """
    CLI entry point to load stimuli and print a summary.
    Usage: python -m src.metrics.load_stimuli [--archive_dir <path>] [--max_images <n>]
    """
    parser = argparse.ArgumentParser(description="Load stimuli from local archive.")
    parser.add_argument(
        "--archive_dir",
        type=str,
        default=str(DATA_DIR / "stimuli" / "raw"),
        help="Path to the stimuli archive directory (default: data/stimuli/raw)"
    )
    parser.add_argument(
        "--max_images",
        type=int,
        default=None,
        help="Maximum number of images to load (optional)"
    )
    
    args = parser.parse_args()
    archive_path = Path(args.archive_dir)
    
    try:
        print(f"Loading stimuli from: {archive_path}")
        images, metadata = load_stimuli_from_archive(archive_path, max_images=args.max_images)
        
        print(f"Successfully loaded {len(images)} images.")
        
        # Print summary of first 3 images
        for i, meta in enumerate(metadata[:3]):
            print(f"  [{i}] {meta['filename']}: {meta['width']}x{meta['height']} ({meta['mode']})")
            
        if len(images) > 3:
            print(f"  ... and {len(images) - 3} more.")
            
    except StimuliLoaderError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
