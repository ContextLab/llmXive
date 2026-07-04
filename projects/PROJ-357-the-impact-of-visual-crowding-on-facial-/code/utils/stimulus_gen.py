"""
Stimulus Generation Module for Visual Crowding Experiments.

Generates controlled visual crowding stimuli from RAVDESS frames with:
- Parametric control over flanker count and eccentricity
- Emotion filtering with graceful degradation for missing categories
- Overlap detection and exclusion
- Comprehensive logging and manifest generation
"""
import os
import sys
import json
import logging
import math
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# Import from project API surface
from config import get_seed, set_all_seeds, ensure_directories, get_env_config
from utils.frame_extractor import extract_frames_from_dataset

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/interim/generation_errors.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

# Constants
TARGET_SIZE = (256, 256)
FLANKER_SIZE = 40
MIN_FLANKER_COUNT = 3
MAX_FLANKER_COUNT = 12
ECCENTRICITY_LEVELS = [0.1, 0.2, 0.3]  # Relative to image radius
EMOTION_CATEGORIES = [
    'angry', 'disgusted', 'fearful', 'happy', 
    'neutral', 'sad', 'surprised', 'calm'
]

def load_frames_by_emotion(frames_dir: Path, emotions: List[str]) -> Dict[str, List[Path]]:
    """Load frames filtered by emotion categories."""
    emotion_frames = {emotion: [] for emotion in emotions}
    missing_emotions = []
    
    for emotion in emotions:
        emotion_path = frames_dir / emotion
        if not emotion_path.exists():
            logger.warning(f"Emotion category '{emotion}' not found in dataset. Excluding from generation.")
            missing_emotions.append(emotion)
            continue
        
        for frame_file in emotion_path.glob("*.png"):
            emotion_frames[emotion].append(frame_file)
        
        if not emotion_frames[emotion]:
            logger.warning(f"No frames found for emotion '{emotion}'. Excluding from generation.")
            missing_emotions.append(emotion)
    
    # Log missing emotions
    for emotion in missing_emotions:
        if emotion in emotion_frames:
            del emotion_frames[emotion]
    
    available = list(emotion_frames.keys())
    logger.info(f"Available emotion categories: {available}")
    return emotion_frames

def check_flanker_overlap(
    positions: List[Tuple[float, float]], 
    flanker_size: int
) -> bool:
    """Check if any flankers overlap with each other or the center."""
    center_size = FLANKER_SIZE  # Same size for simplicity
    min_dist = flanker_size + center_size / 2
    
    for i, (x1, y1) in enumerate(positions):
        # Check overlap with center
        dist_to_center = math.sqrt(x1**2 + y1**2)
        if dist_to_center < min_dist:
            return True
        
        # Check overlap with other flankers
        for j in range(i + 1, len(positions)):
            x2, y2 = positions[j]
            dist = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
            if dist < min_dist:
                return True
    
    return False

def generate_flanker_positions(
    eccentricity: float, 
    flanker_count: int, 
    image_size: Tuple[int, int]
) -> List[Tuple[float, float]]:
    """Generate non-overlapping flanker positions around the center."""
    img_w, img_h = image_size
    center = (img_w / 2, img_h / 2)
    radius = min(img_w, img_h) / 2
    target_radius = eccentricity * radius
    
    positions = []
    max_attempts = 1000
    
    for _ in range(max_attempts):
        if len(positions) >= flanker_count:
            break
        
        angle = random.uniform(0, 2 * math.pi)
        # Add some radial variation
        r = target_radius * random.uniform(0.8, 1.2)
        x = r * math.cos(angle)
        y = r * math.sin(angle)
        
        # Check if this position causes overlap
        test_positions = positions + [(x, y)]
        if not check_flanker_overlap(test_positions, FLANKER_SIZE):
            positions.append((x, y))
    
    if len(positions) < flanker_count:
        logger.warning(f"Could only place {len(positions)} non-overlapping flankers out of {flanker_count}")
    
    return [(p[0] + center[0], p[1] + center[1]) for p in positions]

def create_stimulus(
    target_frame_path: Path,
    flanker_positions: List[Tuple[float, float]],
    output_path: Path
) -> bool:
    """Create a crowding stimulus by adding flankers to a target frame."""
    try:
        # Load target image
        target_img = Image.open(target_frame_path).convert('RGB')
        target_img = target_img.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
        
        draw = ImageDraw.Draw(target_img)
        
        # Draw flankers (simple circles for now)
        for x, y in flanker_positions:
            # Convert relative coordinates to image coordinates
            img_x, img_y = int(x), int(y)
            
            # Draw flanker circle
            left_up = (img_x - FLANKER_SIZE // 2, img_y - FLANKER_SIZE // 2)
            right_down = (img_x + FLANKER_SIZE // 2, img_y + FLANKER_SIZE // 2)
            
            # Random gray shade for flanker
            gray_value = random.randint(50, 150)
            draw.ellipse([left_up, right_down], fill=(gray_value, gray_value, gray_value))
        
        # Save stimulus
        output_path.parent.mkdir(parents=True, exist_ok=True)
        target_img.save(output_path)
        return True
        
    except Exception as e:
        logger.error(f"Failed to create stimulus from {target_frame_path}: {str(e)}")
        return False

def generate_stimuli(
    frames_dir: Path,
    output_dir: Path,
    emotions: Optional[List[str]] = None,
    flanker_counts: Optional[List[int]] = None,
    eccentricities: Optional[List[float]] = None
) -> List[Dict[str, Any]]:
    """Generate all stimuli combinations."""
    if emotions is None:
        emotions = EMOTION_CATEGORIES
    if flanker_counts is None:
        flanker_counts = list(range(MIN_FLANKER_COUNT, MAX_FLANKER_COUNT + 1, 3))
    if eccentricities is None:
        eccentricities = ECCENTRICITY_LEVELS
    
    # Load available frames
    emotion_frames = load_frames_by_emotion(frames_dir, emotions)
    if not emotion_frames:
        logger.error("No valid emotion categories found. Aborting generation.")
        return []
    
    stimuli_manifest = []
    total_combinations = 0
    successful = 0
    
    for emotion, frames in emotion_frames.items():
        for flanker_count in flanker_counts:
            for eccentricity in eccentricities:
                total_combinations += 1
                
                if not frames:
                    logger.warning(f"No frames available for {emotion}, skipping combination")
                    continue
                
                # Select a random frame for this combination
                frame_path = random.choice(frames)
                
                # Generate flanker positions
                positions = generate_flanker_positions(eccentricity, flanker_count, TARGET_SIZE)
                
                if len(positions) < flanker_count:
                    logger.warning(f"Overlap detection: Could not place {flanker_count} flankers for {emotion} at eccentricity {eccentricity}")
                    # Log exclusion reason
                    logger.error(f"EXCLUSION: {emotion}, {flanker_count}, {eccentricity} - Overlapping flankers could not be placed")
                    continue
                
                # Create output filename
                stem = frame_path.stem
                output_filename = f"{stem}_{emotion}_f{flanker_count}_e{eccentricity:.1f}.png"
                output_path = output_dir / output_filename
                
                # Create stimulus
                if create_stimulus(frame_path, positions, output_path):
                    successful += 1
                    stimuli_manifest.append({
                        "file_path": str(output_path),
                        "emotion": emotion,
                        "flanker_count": flanker_count,
                        "eccentricity": eccentricity,
                        "source_frame": str(frame_path),
                        "status": "success"
                    })
                    logger.info(f"Generated: {output_filename}")
                else:
                    logger.error(f"EXCLUSION: {emotion}, {flanker_count}, {eccentricity} - Failed to create image")
    
    logger.info(f"Generation complete. Success: {successful}/{total_combinations}")
    return stimuli_manifest

def main():
    """Main entry point for stimulus generation."""
    set_all_seeds(get_seed())
    config = get_env_config()
    
    # Ensure directories exist
    ensure_directories()
    
    frames_dir = Path(config.get('frames_dir', 'data/raw/frames'))
    output_dir = Path(config.get('stimuli_dir', 'data/interim/stimuli'))
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting stimulus generation from {frames_dir}")
    
    # Generate stimuli
    manifest = generate_stimuli(
        frames_dir=frames_dir,
        output_dir=output_dir,
        emotions=EMOTION_CATEGORIES,
        flanker_counts=list(range(3, 13, 3)),
        eccentricities=[0.1, 0.2, 0.3]
    )
    
    # Write manifest
    manifest_path = output_dir / "stimuli_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Manifest written to {manifest_path}")
    print(f"Generated {len(manifest)} stimuli")
    
    return manifest

if __name__ == "__main__":
    main()
