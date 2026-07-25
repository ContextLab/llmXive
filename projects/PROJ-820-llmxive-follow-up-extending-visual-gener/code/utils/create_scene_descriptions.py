"""
Module to create scene descriptions from real data sources or deterministic fallbacks.

This module implements T011: Create `data/raw/scene_descriptions.csv` with a curated set
of 100 scene descriptions (N=100 scope).

It attempts to fetch from a real source (COCO Captions) and filters for object interaction
scenes. If the fetch fails (network error, missing package, empty results), it executes
a deterministic script using a fixed seed and predefined interaction templates to generate
valid scenes.

CRITICAL: The loader must FAIL LOUDLY if the real fetch fails and no deterministic fallback
is possible, but here we implement the fallback as requested by the task description to
ensure the pipeline can proceed with valid physics-inferable scenes.
"""
import csv
import os
import sys
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

# Constants
TARGET_COUNT = 100
RANDOM_SEED = 42
OUTPUT_PATH = Path("data/raw/scene_descriptions.csv")

# Predefined interaction templates for deterministic fallback
INTERACTION_TEMPLATES = [
    "A {obj1} on top of a {obj2}",
    "A {obj1} next to a {obj2}",
    "A {obj1} above a {obj2}",
    "A {obj1} below a {obj2}",
    "A {obj1} inside a {obj2}",
    "A {obj1} behind a {obj2}",
    "A {obj1} in front of a {obj2}",
    "A {obj1} touching a {obj2}",
    "A {obj1} beside a {obj2}",
    "A {obj1} near a {obj2}",
]

OBJECTS = [
    "car", "dog", "cat", "person", "chair", "table", "book", "cup",
    "laptop", "bottle", "cell phone", "keyboard", "mouse", "clock",
    "vase", "scissors", "teddy bear", "hair drier", "toothbrush", "banana",
    "apple", "sandwich", "orange", "broccoli", "carrot", "pizza", "donut",
    "cake", "train", "bus", "airplane", "bicycle", "motorcycle", "truck",
    "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe",
    "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat", "basketball",
    "tennis racket", "wine glass", "fork", "knife", "spoon", "bowl",
    "hot dog", "orange", "cake", "person", "chair", "couch", "potted plant",
    "bed", "dining table", "toilet", "tv", "laptop", "mouse", "remote",
    "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
    "refrigerator", "book", "clock", "vase", "scissors", "teddy bear",
    "hair drier", "toothbrush"
]

# Remove duplicates while preserving order
OBJECTS = list(dict.fromkeys(OBJECTS))

def generate_fallback_scenes() -> List[Dict[str, Any]]:
    """
    Generate N=100 scene descriptions using a deterministic fallback.
    
    Uses a fixed seed and predefined interaction templates to ensure
    reproducibility and valid physics-inferable scenes.
    
    Returns:
        List of dictionaries with 'scene_id' and 'description' keys.
    """
    random.seed(RANDOM_SEED)
    scenes = []
    
    for i in range(TARGET_COUNT):
        obj1 = random.choice(OBJECTS)
        obj2 = random.choice([o for o in OBJECTS if o != obj1])
        template = random.choice(INTERACTION_TEMPLATES)
        description = template.format(obj1=obj1, obj2=obj2)
        
        scenes.append({
            "scene_id": f"scene_{i:04d}",
            "description": description
        })
    
    return scenes

def fetch_and_filter_coco() -> Optional[List[Dict[str, Any]]]:
    """
    Attempt to fetch and filter object interaction scenes from COCO Captions.
    
    This function tries to load the 'coco-captions' dataset and filters for
    scenes that contain at least two distinct objects with spatial relationships.
    
    Returns:
        List of scene dictionaries if successful, None if fetch fails.
    """
    try:
        # Try to import datasets package
        from datasets import load_dataset
        
        # Load a small subset of COCO Captions for efficiency
        # Using streaming to avoid loading entire dataset into memory
        dataset = load_dataset(
            'coco-captions',
            split='train',
            streaming=True,
            trust_remote_code=True
        )
        
        scenes = []
        count = 0
        
        # Keywords that indicate object interactions
        interaction_keywords = [
            'on', 'next to', 'above', 'below', 'inside', 'behind', 
            'in front of', 'touching', 'beside', 'near', 'with',
            'between', 'around', 'through', 'under', 'over'
        ]
        
        # Iterate through dataset until we have enough scenes
        for item in dataset:
            caption = item.get('caption', '')
            if not caption:
                continue
            
            # Check if caption contains interaction keywords
            has_interaction = any(kw in caption.lower() for kw in interaction_keywords)
            if has_interaction:
                scenes.append({
                    "scene_id": f"coco_{item['id']:06d}",
                    "description": caption
                })
                count += 1
                if count >= TARGET_COUNT:
                    break
        
        # If we didn't get enough scenes, return None to trigger fallback
        if count < TARGET_COUNT:
            return None
        
        return scenes
        
    except Exception as e:
        # Log the error but return None to trigger fallback
        print(f"Warning: Failed to fetch COCO captions: {e}", file=sys.stderr)
        return None

def write_csv(scenes: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write scene descriptions to a CSV file.
    
    Args:
        scenes: List of scene dictionaries with 'scene_id' and 'description' keys.
        output_path: Path to the output CSV file.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['scene_id', 'description']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for scene in scenes:
            writer.writerow(scene)
    
    print(f"Successfully wrote {len(scenes)} scenes to {output_path}")

def main() -> None:
    """
    Main entry point for creating scene descriptions.
    
    Attempts to fetch from COCO Captions first. If that fails or returns
    insufficient data, falls back to deterministic generation.
    """
    print(f"Starting scene description generation (target: {TARGET_COUNT} scenes)...")
    
    # Try to fetch from real source
    scenes = fetch_and_filter_coco()
    
    if scenes is None or len(scenes) < TARGET_COUNT:
        print("COCO fetch failed or insufficient data. Using deterministic fallback...")
        scenes = generate_fallback_scenes()
    
    # Write to CSV
    write_csv(scenes, OUTPUT_PATH)
    
    # Verify output
    if not OUTPUT_PATH.exists():
        raise FileNotFoundError(f"Failed to create output file: {OUTPUT_PATH}")
    
    print("Scene description generation completed successfully.")

if __name__ == "__main__":
    main()
