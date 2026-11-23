"""
Stimulus Generation Module for Visual Crowding Experiments.

Generates controlled visual crowding stimuli from the RAVDESS dataset with
parametric control over flanker count, eccentricity, and emotion.
"""
import os
import sys
import json
import logging
import math
import random
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Add project root to path to resolve imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import set_all_seeds, ensure_directories, get_seed
from utils.frame_extractor import extract_frames_from_dataset

# Constants
RAVDESS_FRAMES_DIR = Path("data/raw/frames")
STIMULI_OUTPUT_DIR = Path("data/interim/stimuli")
ERROR_LOG_PATH = Path("data/interim/generation_errors.log")
MANIFEST_PATH = Path("data/interim/stimuli_manifest.json")

# RAVDESS Emotion Mapping
RAVDESS_EMOTIONS = {
    1: "neutral",
    2: "calm",
    3: "happy",
    4: "sad",
    5: "angry",
    6: "fearful",
    7: "disgusted",
    8: "surprised"
}

# Visual Parameters
TARGET_SIZE = (256, 256)  # Target face size
FLANKER_SIZE = 64  # Flanker image size
MIN_ECCENTRICITY = 1.5  # In units of target radius
MAX_ECCENTRICITY = 3.0  # In units of target radius
FLANKER_COUNTS = [3, 5, 7]  # Levels of crowding

# Setup logging
def setup_logging():
    """Configure logging for the stimulus generation process."""
    ensure_directories([ERROR_LOG_PATH.parent])
    
    # Create file handler for errors
    error_handler = logging.FileHandler(ERROR_LOG_PATH, mode='w')
    error_handler.setLevel(logging.WARNING)
    error_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    error_handler.setFormatter(error_formatter)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    logger = logging.getLogger('stimulus_gen')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)

    return logger

logger = setup_logging()

def load_frames_by_emotion(emotion_id: int, max_frames: int = 10) -> List[Image.Image]:
    """
    Load frames from the RAVDESS dataset filtered by a specific emotion.
    
    Args:
        emotion_id: The numeric ID of the emotion (1-8)
        max_frames: Maximum number of frames to load per actor
        
    Returns:
        List of PIL Image objects
    """
    frames = []
    emotion_name = RAVDESS_EMOTIONS.get(emotion_id, f"unknown_{emotion_id}")
    logger.info(f"Loading frames for emotion: {emotion_name} (ID: {emotion_id})")

    if not RAVDESS_FRAMES_DIR.exists():
        logger.error(f"Frames directory not found: {RAVDESS_FRAMES_DIR}")
        return []

    # Scan for actor directories
    actor_dirs = [d for d in RAVDESS_FRAMES_DIR.iterdir() if d.is_dir()]
    
    if not actor_dirs:
        logger.warning(f"No actor directories found in {RAVDESS_FRAMES_DIR}")
        return []

    for actor_dir in actor_dirs:
        # Look for emotion-specific subdirectories or files
        # RAVDESS structure: actor_XX/actor_XX_s01_emotion_XX.jpg
        emotion_files = list(actor_dir.glob(f"*emotion_{emotion_id}*"))
        
        if not emotion_files:
            # Try case-insensitive or alternative naming
            all_files = list(actor_dir.glob("*"))
            emotion_files = [f for f in all_files if str(emotion_id) in f.stem or emotion_name in f.stem.lower()]

        # Select up to max_frames
        selected = emotion_files[:max_frames]
        for img_path in selected:
            try:
                img = Image.open(img_path).convert('RGB')
                img = img.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
                frames.append(img)
            except Exception as e:
                logger.warning(f"Failed to load image {img_path}: {e}")

    if not frames:
        logger.warning(f"No frames found for emotion ID {emotion_id}. Proceeding with available categories.")
    
    return frames

def generate_flanker_positions(
    target_radius: float, 
    eccentricity: float, 
    count: int
) -> List[Tuple[float, float]]:
    """
    Generate random positions for flankers around a central target.
    
    Args:
        target_radius: Radius of the target face
        eccentricity: Distance from center in units of target radius
        count: Number of flankers to place
        
    Returns:
        List of (x, y) coordinates relative to image center
    """
    positions = []
    min_dist = target_radius + FLANKER_SIZE / 2  # Minimum distance to avoid overlap with target
    max_dist = eccentricity * target_radius
    
    attempts = 0
    max_attempts = 1000
    
    while len(positions) < count and attempts < max_attempts:
        # Random angle
        angle = random.uniform(0, 2 * math.pi)
        # Random distance within eccentricity range
        dist = random.uniform(min_dist, max_dist)
        
        x = dist * math.cos(angle)
        y = dist * math.sin(angle)
        
        # Check for overlap with existing flankers
        overlap = False
        for existing_x, existing_y in positions:
            dx = x - existing_x
            dy = y - existing_y
            if math.hypot(dx, dy) < FLANKER_SIZE:
                overlap = True
                break
        
        if not overlap:
            positions.append((x, y))
        
        attempts += 1
    
    if len(positions) < count:
        logger.warning(f"Could only place {len(positions)} of {count} flankers due to overlap constraints.")
        
    return positions

def check_flanker_overlap(
    positions: List[Tuple[float, float]], 
    target_radius: float,
    flanker_radius: float
) -> bool:
    """
    Check if any flankers overlap with the target or each other.
    
    Args:
        positions: List of flanker positions
        target_radius: Radius of the central target
        flanker_radius: Radius of a flanker
        
    Returns:
        True if any overlap is detected, False otherwise
    """
    # Check overlap with target (center at 0,0)
    for x, y in positions:
        if math.hypot(x, y) < target_radius + flanker_radius:
            return True
    
    # Check overlap between flankers
    for i in range(len(positions)):
        for j in range(i + 1, len(positions)):
            dx = positions[i][0] - positions[j][0]
            dy = positions[i][1] - positions[j][1]
            if math.hypot(dx, dy) < 2 * flanker_radius:
                return True
                
    return False

def create_stimulus(
    target_img: Image.Image,
    flanker_positions: List[Tuple[float, float]],
    flanker_count: int,
    eccentricity: float
) -> Tuple[Image.Image, str]:
    """
    Create a crowding stimulus by placing flankers around a target face.
    
    Args:
        target_img: The central target face image
        flanker_positions: List of (x, y) coordinates for flankers
        flanker_count: The intended number of flankers
        eccentricity: The eccentricity value used
        
    Returns:
        Tuple of (stimulus image, exclusion reason or 'success')
    """
    # Create a blank canvas (white background)
    canvas_size = TARGET_SIZE[0] + int(2 * (eccentricity * (TARGET_SIZE[0]/2)))
    canvas = Image.new('RGB', (canvas_size, canvas_size), color=(255, 255, 255))
    
    # Calculate center
    center_x = canvas_size // 2
    center_y = canvas_size // 2
    
    # Paste target in the center
    target_radius = TARGET_SIZE[0] / 2
    canvas.paste(target_img, (center_x - target_radius, center_y - target_radius))
    
    # Create a placeholder flanker (random noise or a generic face patch)
    # For this implementation, we use a simple gray square to represent flankers
    # In a real experiment, these would be scrambled face parts or other faces
    flanker_img = Image.new('RGB', (FLANKER_SIZE, FLANKER_SIZE), color=(128, 128, 128))
    flanker_radius = FLANKER_SIZE / 2
    
    # Place flankers
    for i, (x, y) in enumerate(flanker_positions):
        # Check overlap before placing
        if check_flanker_overlap([pos for j, pos in enumerate(flanker_positions) if j <= i], 
                                 target_radius, 
                                 flanker_radius):
            # Skip if overlap detected (shouldn't happen if generated correctly, but safety check)
            continue
        
        pos_x = int(center_x + x - flanker_radius)
        pos_y = int(center_y + y - flanker_radius)
        canvas.paste(flanker_img, (pos_x, pos_y))
    
    # Verify exclusion condition: if we couldn't place all requested flankers
    if len(flanker_positions) < flanker_count:
        return canvas, f"overlap_exclusion: only placed {len(flanker_positions)} of {flanker_count} flankers"
    
    return canvas, "success"

def generate_stimuli(
    seed: int = 42,
    emotions: Optional[List[int]] = None,
    flanker_counts: Optional[List[int]] = None,
    eccentricities: Optional[List[float]] = None,
    frames_per_emotion: int = 5
) -> Dict[str, Any]:
    """
    Generate the full set of crowding stimuli.
    
    Args:
        seed: Random seed for reproducibility
        emotions: List of emotion IDs to process (default: all 1-8)
        flanker_counts: List of flanker counts (default: [3, 5, 7])
        eccentricities: List of eccentricity values (default: linear spacing)
        frames_per_emotion: Number of source frames to use per emotion
        
    Returns:
        Dictionary containing generation statistics and paths
    """
    set_all_seeds(seed)
    ensure_directories([STIMULI_OUTPUT_DIR, ERROR_LOG_PATH.parent])
    
    if emotions is None:
        emotions = list(RAVDESS_EMOTIONS.keys())
    if flanker_counts is None:
        flanker_counts = FLANKER_COUNTS
    if eccentricities is None:
        # Generate 3 levels of eccentricity
        eccentricities = [MIN_ECCENTRICITY, (MIN_ECCENTRICITY + MAX_ECCENTRICITY) / 2, MAX_ECCENTRICITY]
    
    generated_files = []
    errors = []
    missing_emotions = []
    
    logger.info(f"Starting stimulus generation with {len(emotions)} emotions, "
               f"{len(flanker_counts)} flanker counts, and {len(eccentricities)} eccentricities")
    
    for emotion_id in emotions:
        frames = load_frames_by_emotion(emotion_id, max_frames=frames_per_emotion)
        
        if not frames:
            missing_emotions.append(emotion_id)
            errors.append({
                "type": "missing_data",
                "emotion_id": emotion_id,
                "emotion_name": RAVDESS_EMOTIONS.get(emotion_id, "unknown"),
                "reason": "No frames found for this emotion"
            })
            continue
        
        for flanker_count in flanker_counts:
            for eccentricity in eccentricities:
                for frame_idx, frame in enumerate(frames):
                    # Generate positions
                    positions = generate_flanker_positions(
                        target_radius=TARGET_SIZE[0]/2,
                        eccentricity=eccentricity,
                        count=flanker_count
                    )
                    
                    # Create stimulus
                    stimulus, status = create_stimulus(
                        target_img=frame,
                        flanker_positions=positions,
                        flanker_count=flanker_count,
                        eccentricity=eccentricity
                    )
                    
                    if status != "success":
                        errors.append({
                            "type": "generation_error",
                            "emotion_id": emotion_id,
                            "flanker_count": flanker_count,
                            "eccentricity": eccentricity,
                            "frame_idx": frame_idx,
                            "reason": status
                        })
                        logger.warning(f"Excluded stimulus: {status}")
                        continue
                    
                    # Save stimulus
                    filename = (
                        f"stimulus_e{emotion_id}_f{flanker_count}_ec{eccentricity:.2f}_fr{frame_idx:02d}.png"
                    )
                    filepath = STIMULI_OUTPUT_DIR / filename
                    stimulus.save(filepath)
                    
                    generated_files.append({
                        "filename": filename,
                        "filepath": str(filepath),
                        "emotion_id": emotion_id,
                        "emotion_name": RAVDESS_EMOTIONS.get(emotion_id),
                        "flanker_count": flanker_count,
                        "eccentricity": eccentricity,
                        "frame_idx": frame_idx,
                        "status": "success"
                    })
    
    # Log missing emotions as warnings but do not halt
    if missing_emotions:
        missing_names = [RAVDESS_EMOTIONS.get(e, str(e)) for e in missing_emotions]
        logger.warning(f"Missing categories (proceeding with available): {missing_names}")
        for e in missing_emotions:
            errors.append({
                "type": "missing_category",
                "emotion_id": e,
                "emotion_name": RAVDESS_EMOTIONS.get(e),
                "reason": "Category missing from source data"
            })
    
    # Write error log
    if errors:
        with open(ERROR_LOG_PATH, 'w') as f:
            json.dump(errors, f, indent=2)
        logger.info(f"Logged {len(errors)} errors/exclusions to {ERROR_LOG_PATH}")
    else:
        # Create empty log if no errors to ensure file exists for downstream tasks
        with open(ERROR_LOG_PATH, 'w') as f:
            f.write("[]")
    
    return {
        "total_generated": len(generated_files),
        "total_errors": len(errors),
        "files": generated_files,
        "output_dir": str(STIMULI_OUTPUT_DIR)
    }

def main():
    """Entry point for the stimulus generation script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate visual crowding stimuli from RAVDESS.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--emotions", type=int, nargs="+", default=None, 
                       help="Specific emotion IDs to process (default: all 1-8)")
    parser.add_argument("--flankers", type=int, nargs="+", default=None,
                       help="Specific flanker counts (default: 3 5 7)")
    parser.add_argument("--eccentricities", type=float, nargs="+", default=None,
                       help="Specific eccentricity values (default: auto-generated)")
    parser.add_argument("--frames", type=int, default=5, help="Frames per emotion")
    
    args = parser.parse_args()
    
    try:
        result = generate_stimuli(
            seed=args.seed,
            emotions=args.emotions,
            flanker_counts=args.flankers,
            eccentricities=args.eccentricities,
            frames_per_emotion=args.frames
        )
        
        logger.info(f"Generation complete: {result['total_generated']} stimuli created, "
                   f"{result['total_errors']} exclusions logged.")
        logger.info(f"Output directory: {result['output_dir']}")
        
    except Exception as e:
        logger.error(f"Fatal error during generation: {e}")
        raise

if __name__ == "__main__":
    main()
