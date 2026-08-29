import os
import csv
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from PIL import Image

from config import get_mode, is_ci_mode, get_path, ensure_paths_exist
from data.annotator import generate_ci_scores, load_research_annotations, save_scores
from data.mask_generator import generate_mask_batch
from data.loader import fetch_places365_subset
from utils.seed import set_seed
from utils.logger import get_logger

logger = get_logger(__name__)

def compute_image_hash(image_path: Path) -> str:
    """Compute SHA-256 hash of an image file."""
    sha256_hash = hashlib.sha256()
    with open(image_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def persist_masked_images(
    masked_images: List[Tuple[np.ndarray, np.ndarray, str]],
    output_dir: Path,
    hash_registry: Dict[str, str]
) -> List[Dict[str, Any]]:
    """
    Persist masked images to disk and update hash registry.
    
    Args:
        masked_images: List of tuples (image_array, mask_array, image_id)
        output_dir: Directory to save images
        hash_registry: Dictionary to update with image hashes
        
    Returns:
        List of metadata records for each saved image
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    records = []
    
    for idx, (img_arr, mask_arr, image_id) in enumerate(masked_images):
        # Ensure arrays are uint8
        if img_arr.dtype != np.uint8:
            img_arr = (img_arr * 255).astype(np.uint8) if img_arr.max() <= 1.0 else img_arr.astype(np.uint8)
        if mask_arr.dtype != np.uint8:
            mask_arr = (mask_arr * 255).astype(np.uint8) if mask_arr.max() <= 1.0 else mask_arr.astype(np.uint8)
        
        # Create composite image: [Image, Mask, Masked_Image]
        # Format: <image_id>_masked.png (shows image with mask overlay)
        # We'll save the masked version as: original image where masked region is set to 0 (black)
        masked_img = img_arr.copy()
        masked_img[mask_arr > 0] = 0  # Set masked region to black
        
        # Save masked image
        filename = f"{image_id}_masked.png"
        filepath = output_dir / filename
        
        # Convert to PIL Image and save
        img_pil = Image.fromarray(masked_img)
        img_pil.save(filepath, format='PNG')
        
        # Compute hash
        img_hash = compute_image_hash(filepath)
        hash_registry[image_id] = img_hash
        
        # Record metadata
        records.append({
            "image_id": image_id,
            "filename": filename,
            "hash": img_hash,
            "path": str(filepath),
            "original_shape": list(img_arr.shape),
            "mask_shape": list(mask_arr.shape)
        })
        
        if idx % 100 == 0:
            logger.info(f"Persisted {idx}/{len(masked_images)} masked images")
    
    return records

def persist_scores(
    scores: List[Dict[str, Any]],
    output_file: Path
) -> None:
    """
    Persist scores to CSV file.
    
    Args:
        scores: List of score dictionaries
        output_file: Path to output CSV file
    """
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    if not scores:
        logger.warning("No scores to persist")
        return
    
    # Write CSV
    fieldnames = scores[0].keys()
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(scores)
    
    logger.info(f"Persisted {len(scores)} scores to {output_file}")

def run_persistence_pipeline(
    config: Dict[str, Any],
    sample_size: int = 1000
) -> Dict[str, Any]:
    """
    Run the full persistence pipeline:
    1. Fetch dataset
    2. Generate masks
    3. Generate/persist scores
    4. Persist masked images
    
    Args:
        config: Configuration dictionary
        sample_size: Number of images to process
        
    Returns:
        Summary statistics of the pipeline run
    """
    logger.info("Starting persistence pipeline")
    
    # Set seed for reproducibility
    set_seed(config.get('seed', 42))
    
    # Ensure paths exist
    ensure_paths_exist()
    
    # Paths
    masked_images_dir = get_path('processed_images')
    annotations_dir = get_path('annotations')
    scores_file = annotations_dir / ('decoupled_scores.csv' if is_ci_mode() else 'human_scores.csv')
    hash_registry_file = annotations_dir / 'hash_registry.json'
    
    # Load hash registry if exists
    hash_registry = {}
    if hash_registry_file.exists():
        with open(hash_registry_file, 'r') as f:
            hash_registry = json.load(f)
    
    # Step 1: Fetch dataset
    logger.info(f"Fetching Places365 subset (sample_size={sample_size})")
    dataset = fetch_places365_subset(sample_size=sample_size)
    logger.info(f"Fetched {len(dataset)} images")
    
    # Step 2: Generate masks
    logger.info("Generating masks")
    masked_images_data = []
    for idx, item in enumerate(dataset):
        image_id = item['image_id']
        image_arr = item['image']
        
        # Generate mask
        mask_arr, metrics = generate_mask_batch([image_arr], return_metrics=True)
        mask_arr = mask_arr[0]  # Take first mask
        
        # Store for persistence
        masked_images_data.append((image_arr, mask_arr, image_id))
        
        if (idx + 1) % 100 == 0:
            logger.info(f"Generated masks for {idx + 1}/{len(dataset)} images")
    
    # Step 3: Generate or load scores
    if is_ci_mode():
        logger.info("Generating CI mode scores")
        scores = generate_ci_scores(masked_images_data, seed=config.get('seed', 42))
    else:
        logger.info("Loading research mode annotations")
        try:
            scores = load_research_annotations()
        except FileNotFoundError as e:
            logger.error(f"Research mode requires human_scores.csv: {e}")
            raise
    
    # Step 4: Persist masked images
    logger.info("Persisting masked images")
    image_records = persist_masked_images(
        masked_images_data,
        masked_images_dir,
        hash_registry
    )
    
    # Step 5: Persist scores
    logger.info("Persisting scores")
    # Ensure scores have image_id, score, mode columns
    for score_entry in scores:
        score_entry['mode'] = 'CI_MODE' if is_ci_mode() else 'RESEARCH_MODE'
    
    persist_scores(scores, scores_file)
    
    # Step 6: Save hash registry
    with open(hash_registry_file, 'w') as f:
        json.dump(hash_registry, f, indent=2)
    
    # Summary
    summary = {
        "total_images": len(dataset),
        "masks_generated": len(masked_images_data),
        "images_persisted": len(image_records),
        "scores_persisted": len(scores),
        "output_dir": str(masked_images_dir),
        "scores_file": str(scores_file),
        "hash_registry_file": str(hash_registry_file),
        "mode": "CI_MODE" if is_ci_mode() else "RESEARCH_MODE"
    }
    
    logger.info(f"Persistence pipeline complete: {summary}")
    return summary

def main():
    """Main entry point for persistence pipeline."""
    import argparse
    from config import get_config_summary
    
    parser = argparse.ArgumentParser(description="Persist masked images and scores")
    parser.add_argument("--sample-size", type=int, default=1000,
                      help="Number of images to process")
    parser.add_argument("--mode", type=str, choices=["CI", "RESEARCH"], default=None,
                      help="Override config mode")
    args = parser.parse_args()
    
    # Set mode if specified
    if args.mode:
        from config import set_mode
        set_mode(args.mode)
    
    # Load config
    from config import get_mode, is_ci_mode
    config = {
        'seed': 42,
        'mode': get_mode()
    }
    
    logger.info(f"Running persistence pipeline in {get_mode()} mode")
    logger.info(f"Config: {config}")
    
    # Run pipeline
    summary = run_persistence_pipeline(config, sample_size=args.sample_size)
    
    # Print summary
    print("\n=== Persistence Pipeline Summary ===")
    for key, value in summary.items():
        print(f"{key}: {value}")
    print("====================================")

if __name__ == "__main__":
    main()
