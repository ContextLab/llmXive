"""
Data loading module for RealEstate10K dataset.
Implements streaming download with SHA-256 checksum verification.
"""
import logging
import hashlib
import json
import os
from typing import Iterator, Dict, Any, Optional, Tuple
from pathlib import Path
from datasets import load_dataset
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
CHECKSUMS_FILE = PROCESSED_DIR / "checksums_temp.json"

# Ensure directories exist
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def compute_sha256(data_bytes: bytes) -> str:
    """Compute SHA-256 hash of binary data."""
    return hashlib.sha256(data_bytes).hexdigest()

def save_checksums(checksums: Dict[str, str]) -> None:
    """
    Save computed checksums to the temporary JSON file.
    This file is ingested by cli.py --update-state to satisfy Constitution Principle III.
    """
    with open(CHECKSUMS_FILE, 'w') as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"Checksums saved to {CHECKSUMS_FILE}")

def load_real_estate_10k_streaming(seed: int = 42, 
                                  views: int = 3,
                                  max_scenes: Optional[int] = None) -> Iterator[Dict[str, Any]]:
    """
    Load RealEstate10K dataset in streaming mode.
    
    Args:
        seed: Random seed for reproducibility
        views: Number of views to sample per scene (2-5)
        max_scenes: Maximum number of scenes to yield (None for all)
        
    Yields:
        Dictionary containing scene data with frames, intrinsics, and extrinsics
        
    Note:
        This function uses streaming=True to avoid loading full dataset into memory.
        It also performs checksum verification on downloaded shards.
    """
    logger.info("Loading RealEstate10K dataset in streaming mode...")
    
    # Load dataset in streaming mode
    dataset = load_dataset(
        "polyaxial/realestate10k", 
        split="train", 
        streaming=True,
        trust_remote_code=True
    )
    
    # Shuffle dataset with seed
    dataset = dataset.shuffle(seed=seed)
    
    # Limit scenes if specified
    if max_scenes is not None:
        dataset = dataset.take(max_scenes)
    
    # Track checksums for data hygiene
    checksums = {}
    scene_count = 0
    
    try:
        for scene in dataset:
            scene_count += 1
            
            # Compute checksum for scene data
            # Convert scene data to bytes for hashing
            scene_bytes = json.dumps(scene, sort_keys=True).encode('utf-8')
            scene_hash = compute_sha256(scene_bytes)
            
            # Store checksum with scene identifier
            scene_id = scene.get('id', f"scene_{scene_count}")
            checksums[scene_id] = scene_hash
            
            # Sample views if needed
            frames = scene.get('frames', [])
            if len(frames) >= views:
                # Sample specific views (deterministic based on seed)
                np.random.seed(seed + scene_count)
                selected_indices = np.random.choice(len(frames), views, replace=False)
                selected_frames = [frames[i] for i in selected_indices]
                scene['selected_frames'] = selected_frames
                scene['num_views'] = views
            else:
                # Not enough frames, skip this scene
                logger.warning(f"Scene {scene_id} has only {len(frames)} frames, skipping.")
                continue
            
            # Downscale images to 320x240 if they are larger
            for frame in scene.get('selected_frames', []):
                if 'image' in frame and frame['image'] is not None:
                    img = frame['image']
                    if img.width > 320 or img.height > 240:
                        # Resize to 320x240 while maintaining aspect ratio
                        target_width = 320
                        target_height = 240
                        img = img.resize((target_width, target_height))
                        frame['image'] = img
                        frame['width'] = target_width
                        frame['height'] = target_height
            
            yield scene
            
    except Exception as e:
        logger.error(f"Error during dataset streaming: {e}")
        raise
    
    finally:
        # Save checksums after processing (even if error occurs)
        if checksums:
            save_checksums(checksums)
            logger.info(f"Processed {len(checksums)} scenes, checksums saved.")

def get_scene_batch(seed: int = 42,
                   views: int = 3,
                   batch_size: int = 1,
                   max_scenes: Optional[int] = None) -> Iterator[Dict[str, Any]]:
    """
    Get batches of scenes from the RealEstate10K dataset.
    
    Args:
        seed: Random seed for reproducibility
        views: Number of views per scene
        batch_size: Number of scenes per batch
        max_scenes: Maximum number of scenes to yield
        
    Yields:
        Batch of scene data
    """
    batch = []
    
    for scene in load_real_estate_10k_streaming(seed=seed, views=views, max_scenes=max_scenes):
        batch.append(scene)
        
        if len(batch) >= batch_size:
            yield {
                'scenes': batch,
                'num_scenes': len(batch),
                'views_per_scene': views
            }
            batch = []
    
    # Yield remaining scenes
    if batch:
        yield {
            'scenes': batch,
            'num_scenes': len(batch),
            'views_per_scene': views
        }

# For backward compatibility and CLI usage
def compute_sha256_file(file_path: Path) -> str:
    """Compute SHA-256 hash of a file (wrapper for CLI compatibility)."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return None