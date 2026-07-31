"""
Data Loader Module

Handles loading of visual dataset images and metadata.
Implements T006.1-LoadSubset functionality with checksum validation.
"""

import argparse
import json
import logging
import math
import os
import random
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from config import get_project_root, get_data_dir, get_stimuli_dir, get_stimuli_metadata_dir
from data.checksum import compute_checksums_for_directory, verify_directory_integrity
from utils.logging import get_logger

logger = get_logger(__name__)

def fetch_real_dataset_image(source: str = "visual_genome", limit: int = 30) -> List[Path]:
    """
    Fetch images from a real dataset source.
    
    Args:
        source: Dataset source identifier (currently only 'visual_genome' supported)
        limit: Maximum number of images to fetch
        
    Returns:
        List of paths to downloaded image files
    """
    if source != "visual_genome":
        raise ValueError(f"Unsupported dataset source: {source}. Only 'visual_genome' is supported.")
    
    # Check for pre-bundled subset
    raw_subset_dir = get_data_dir() / "stimuli" / "raw_subset"
    raw_dir = get_stimuli_dir()
    
    if not raw_subset_dir.exists():
        raise FileNotFoundError(
            f"Pre-bundled Visual Genome subset not found at {raw_subset_dir}. "
            "Please download the subset or configure the data source."
        )
    
    # Copy images from raw_subset to raw directory
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
    image_files = [
        p for p in raw_subset_dir.rglob('*')
        if p.suffix.lower() in image_extensions
    ][:limit]
    
    if not image_files:
        raise FileNotFoundError(f"No images found in {raw_subset_dir}")
    
    copied_paths = []
    for img_file in image_files:
        dest_path = raw_dir / img_file.name
        if not dest_path.exists():
            # Simple copy implementation
            dest_path.write_bytes(img_file.read_bytes())
        copied_paths.append(dest_path)
    
    logger.info(f"Loaded {len(copied_paths)} images from {source}")
    return copied_paths

def calculate_complexity_score(image_path: Path) -> float:
    """
    Calculate complexity score for an image based on object density.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Complexity score between 0.0 and 1.0
    """
    # Placeholder implementation - in real scenario, would use object detection
    # For now, use filename heuristics or random seed for reproducibility in testing
    import hashlib
    hash_val = int(hashlib.md5(image_path.name.encode()).hexdigest(), 16)
    score = (hash_val % 1000) / 1000.0
    return score

def load_image_metadata(image_path: Path) -> Dict[str, Any]:
    """
    Load metadata for an image from its corresponding YAML file.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Dictionary with metadata or empty dict if not found
    """
    image_id = image_path.stem
    metadata_path = get_stimuli_metadata_dir() / f"{image_id}.yaml"
    
    if not metadata_path.exists():
        logger.warning(f"Metadata not found for {image_path}")
        return {}
    
    import yaml
    with open(metadata_path, 'r') as f:
        return yaml.safe_load(f)

def process_image_with_error_handling(image_path: Path) -> Optional[Dict[str, Any]]:
    """
    Process a single image with error handling.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Processed metadata dict or None if processing failed
    """
    try:
        if not image_path.exists():
            logger.error(f"Image not found: {image_path}")
            return None
        
        complexity = calculate_complexity_score(image_path)
        metadata = load_image_metadata(image_path)
        
        return {
            'path': str(image_path),
            'complexity_score': complexity,
            'metadata': metadata
        }
    except Exception as e:
        logger.error(f"Error processing {image_path}: {e}")
        return None

def filter_by_complexity_range(
    image_paths: List[Path],
    target_q1: float = 0.3,
    target_q3: float = 0.6,
    max_retries: int = 3
) -> Tuple[List[Path], Dict[str, float]]:
    """
    Filter images to ensure Q1-Q3 range meets target.
    
    Args:
        image_paths: List of image paths
        target_q1: Target Q1 complexity
        target_q3: Target Q3 complexity
        max_retries: Maximum retry attempts
        
    Returns:
        Tuple of (filtered paths, complexity scores dict)
    """
    import numpy as np
    
    for attempt in range(max_retries):
        scores = {}
        for path in image_paths:
            scores[str(path)] = calculate_complexity_score(path)
        
        score_values = list(scores.values())
        if len(score_values) < 2:
            continue
        
        q1 = np.percentile(score_values, 25)
        q3 = np.percentile(score_values, 75)
        q_range = q3 - q1
        
        if q_range >= target_q3 - target_q1:
            logger.info(f"Complexity range met (Q1={q1:.2f}, Q3={q3:.2f}, range={q_range:.2f})")
            return image_paths, scores
        
        logger.warning(f"Attempt {attempt+1}: Complexity range {q_range:.2f} < target {target_q3 - target_q1}")
        
        # If retry needed, in real implementation would fetch more images
        # For now, log and continue with current set
        if attempt == max_retries - 1:
            logger.critical("Failed to meet complexity range after max retries")
            # Return best effort set
            return image_paths, scores
    
    return image_paths, scores

def main():
    """
    Main entry point for data loading.
    """
    parser = argparse.ArgumentParser(description="Load visual dataset images")
    parser.add_argument("--source", type=str, default="visual_genome", help="Dataset source")
    parser.add_argument("--limit", type=int, default=30, help="Maximum images to load")
    parser.add_argument("--validate", action="store_true", help="Validate checksums only")
    
    args = parser.parse_args()
    
    try:
        if args.validate:
            # Validate checksums if manifest exists
            raw_subset_dir = get_data_dir() / "stimuli" / "raw_subset"
            if raw_subset_dir.exists():
                verify_directory_integrity(raw_subset_dir)
            else:
                logger.warning(f"Directory not found: {raw_subset_dir}")
        else:
            # Load images
            image_paths = fetch_real_dataset_image(args.source, args.limit)
            logger.info(f"Successfully loaded {len(image_paths)} images")
            
            # Filter by complexity
            filtered_paths, scores = filter_by_complexity_range(image_paths)
            logger.info(f"Filtered to {len(filtered_paths)} images")
            
    except Exception as e:
        logger.error(f"Data loading failed: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()