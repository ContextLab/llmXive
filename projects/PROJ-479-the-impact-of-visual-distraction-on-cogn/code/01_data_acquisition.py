"""
Data Acquisition Module for Visual Distraction Study.
Handles data loading, synthetic generation (if no real data), merging, validation, and saving.
"""
import os
import json
import random
import logging
from typing import List, Dict, Any, Tuple
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# Import from local utils
from utils import get_logger, set_random_seed, get_global_seed, log_structured_error

# Configure logging
logger = get_logger(__name__)

# Constants
DATA_RAW_DIR = "data/raw"
DATA_PROCESSED_DIR = "data/processed"
MIN_PARTICIPANTS = 100
MAX_MISSING_PCT = 0.05

def generate_synthetic_cognitive_data(n_participants: int, seed: int) -> List[Dict[str, Any]]:
    """
    Generate synthetic cognitive data with a realistic negative correlation
    between visual complexity and cognitive performance (reaction time, accuracy).
    """
    set_random_seed(seed)
    data = []
    
    # Base parameters
    base_reaction_time = 500  # ms
    base_accuracy = 0.95
    
    for i in range(n_participants):
        # Generate visual complexity (0 to 1)
        visual_complexity = random.uniform(0.1, 0.9)
        
        # Generate reaction time with negative correlation to complexity
        # Higher complexity -> slower reaction time
        reaction_time = base_reaction_time + int(visual_complexity * 300 + random.gauss(0, 50))
        
        # Generate accuracy with negative correlation to complexity
        # Higher complexity -> lower accuracy
        accuracy = max(0.5, min(1.0, base_accuracy - (visual_complexity * 0.3) + random.gauss(0, 0.05)))
        
        # Introduce small amount of missing data (< 5%)
        missing_reaction = random.random() < 0.02
        missing_accuracy = random.random() < 0.02
        
        participant = {
            "participant_id": f"P{i+1:04d}",
            "reaction_time": None if missing_reaction else reaction_time,
            "accuracy": None if missing_accuracy else round(accuracy, 3),
            "visual_complexity": round(visual_complexity, 3)
        }
        data.append(participant)
    
    return data

def generate_workspace_image(participant_id: str, seed: int, output_dir: str) -> str:
    """
    Generate a synthetic workspace image for a participant.
    Saves the image to output_dir with deterministic naming.
    Returns the relative path to the saved image.
    """
    set_random_seed(seed + hash(participant_id) % 10000)
    
    # Determine image properties
    lighting_condition = random.choice(["bright", "dim", "natural"])
    room_type = random.choice(["office", "home", "cafe", "co-working"])
    demographic_group = random.choice(["group_A", "group_B", "group_C"])
    
    # Create image dimensions
    width, height = 400, 300
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw background based on lighting
    if lighting_condition == "bright":
        bg_color = (240, 240, 240)
    elif lighting_condition == "dim":
        bg_color = (100, 100, 100)
    else:  # natural
        bg_color = (200, 220, 200)
    
    draw.rectangle([0, 0, width, height], fill=bg_color)
    
    # Draw furniture elements (randomized)
    num_desks = random.randint(1, 3)
    num_chairs = random.randint(1, 3)
    num_plants = random.randint(0, 2)
    num_monitors = random.randint(1, 2)
    
    # Draw desks
    for _ in range(num_desks):
        x = random.randint(20, width - 100)
        y = random.randint(20, height - 80)
        draw.rectangle([x, y, x + 80, y + 40], fill=(139, 69, 19), outline=(100, 50, 10))
        
        # Draw monitors on desks
        if random.random() > 0.5:
            draw.rectangle([x + 20, y - 20, x + 60, y], fill=(50, 50, 50), outline=(30, 30, 30))
            draw.rectangle([x + 25, y - 15, x + 55, y - 5], fill=(100, 150, 200))
    
    # Draw chairs
    for _ in range(num_chairs):
        x = random.randint(20, width - 60)
        y = random.randint(50, height - 50)
        draw.rectangle([x, y, x + 30, y + 50], fill=(80, 80, 80))
        draw.ellipse([x - 5, y + 45, x + 35, y + 55], fill=(50, 50, 50))
    
    # Draw plants
    for _ in range(num_plants):
        x = random.randint(10, width - 30)
        y = random.randint(10, height - 40)
        draw.ellipse([x, y, x + 20, y + 20], fill=(34, 139, 34))
        draw.rectangle([x + 8, y + 20, x + 12, y + 35], fill=(139, 69, 19))
    
    # Apply blur for realism
    img = img.filter(ImageFilter.GaussianBlur(radius=1))
    
    # Save image with deterministic name
    filename = f"{participant_id}_workspace.png"
    filepath = os.path.join(output_dir, filename)
    img.save(filepath)
    
    return filename, lighting_condition, room_type, demographic_group

def load_cognitive_data(source: str = "synthetic") -> List[Dict[str, Any]]:
    """
    Load cognitive data. If source is 'real', attempts to load from external source.
    Falls back to synthetic generation if real data is unavailable.
    """
    if source == "real":
        # Attempt to load real data from HuggingFace/OpenML
        # This is a placeholder for actual implementation
        # In production, this would use datasets.load_dataset() or similar
        try:
            # Example: from datasets import load_dataset
            # dataset = load_dataset("stroop_flanker_data", split="train")
            # return [row for row in dataset]
            logger.warning("Real data source not available, falling back to synthetic.")
            raise FileNotFoundError("Real dataset not found")
        except Exception as e:
            log_structured_error("data_acquisition_fail", str(e))
            logger.info("Transitioning to synthetic data generation as per FR-001")
    
    # Generate synthetic data
    seed = get_global_seed()
    return generate_synthetic_cognitive_data(MIN_PARTICIPANTS, seed)

def load_image_metadata(metadata_path: str) -> Dict[str, Dict[str, str]]:
    """
    Load image metadata from JSON file.
    """
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    
    with open(metadata_path, 'r') as f:
        return json.load(f)

def merge_participant_data(cognitive_data: List[Dict], metadata: Dict[str, Dict]) -> List[Dict]:
    """
    Merge cognitive data with image metadata.
    Excludes unmatched records and logs counts.
    """
    merged = []
    unmatched = 0
    
    for record in cognitive_data:
        pid = record["participant_id"]
        if pid in metadata:
            meta = metadata[pid]
            merged_record = {
                "participant_id": pid,
                "reaction_time": record["reaction_time"],
                "accuracy": record["accuracy"],
                "visual_complexity": record["visual_complexity"],
                "image_path": meta["image_path"],
                "lighting_condition": meta["lighting_condition"],
                "room_type": meta["room_type"],
                "demographic_group": meta["demographic_group"]
            }
            merged.append(merged_record)
        else:
            unmatched += 1
    
    if unmatched > 0:
        log_structured_error("unmatched_participant_ids", f"Unmatched: {unmatched} records")
        logger.warning(f"Excluded {unmatched} unmatched participant records")
    
    return merged

def validate_data(data: List[Dict]) -> bool:
    """
    Validate dataset meets requirements:
    - N >= 100
    - <= 5% missing values in key columns
    """
    n = len(data)
    if n < MIN_PARTICIPANTS:
        logger.error(f"Dataset size {n} is below minimum {MIN_PARTICIPANTS}")
        return False
    
    # Check missing values
    missing_rt = sum(1 for d in data if d["reaction_time"] is None)
    missing_acc = sum(1 for d in data if d["accuracy"] is None)
    missing_complexity = sum(1 for d in data if d["visual_complexity"] is None)
    
    total_missing = missing_rt + missing_acc + missing_complexity
    total_possible = n * 3
    missing_pct = total_missing / total_possible if total_possible > 0 else 0
    
    if missing_pct > MAX_MISSING_PCT:
        logger.error(f"Missing value percentage {missing_pct:.2%} exceeds maximum {MAX_MISSING_PCT:.2%}")
        return False
    
    logger.info(f"Validation passed: N={n}, missing={missing_pct:.2%}")
    return True

def save_merged_data(data: List[Dict], output_path: str):
    """
    Save merged dataset to CSV file.
    """
    import csv
    
    if not data:
        raise ValueError("Cannot save empty dataset")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Write CSV
    fieldnames = list(data[0].keys())
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    logger.info(f"Saved {len(data)} records to {output_path}")

def main():
    """
    Main execution flow for data acquisition.
    """
    logger.info("Starting data acquisition pipeline")
    
    # Ensure directories exist
    os.makedirs(DATA_RAW_DIR, exist_ok=True)
    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
    
    # Step 1: Load or generate cognitive data
    cognitive_data = load_cognitive_data("synthetic")  # Default to synthetic as per FR-001
    logger.info(f"Generated {len(cognitive_data)} cognitive records")
    
    # Step 2: Generate synthetic images and metadata
    metadata = {}
    seed = get_global_seed()
    
    for record in cognitive_data:
        pid = record["participant_id"]
        filename, lighting, room, demo = generate_workspace_image(pid, seed, DATA_RAW_DIR)
        metadata[pid] = {
            "image_path": os.path.join(DATA_RAW_DIR, filename),
            "lighting_condition": lighting,
            "room_type": room,
            "demographic_group": demo
        }
    
    # Save metadata
    metadata_path = os.path.join(DATA_RAW_DIR, "metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved metadata to {metadata_path}")
    
    # Step 3: Merge data
    merged_data = merge_participant_data(cognitive_data, metadata)
    logger.info(f"Merged {len(merged_data)} records")
    
    # Step 4: Validate
    if not validate_data(merged_data):
        raise ValueError("Data validation failed")
    
    # Step 5: Save final merged dataset
    output_path = os.path.join(DATA_PROCESSED_DIR, "merged_data.csv")
    save_merged_data(merged_data, output_path)
    
    logger.info("Data acquisition pipeline completed successfully")
    return output_path

if __name__ == "__main__":
    main()
