"""
Data loading utilities for the Visual Detail and False Memory project.

Handles both mock dataset generation and optional real dataset fetching.
"""
import json
import logging
import math
import os
import random
from pathlib import Path
from typing import Optional, Dict, List, Any

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import requests

from config import get_config, get_stimuli_dir, get_stimuli_metadata_dir, get_project_root
from utils.logging import get_logger, get_manipulation_error_log_path

# Constants for mock data generation
MOCK_COMPLEXITY_MEAN = 0.5
MOCK_COMPLEXITY_STD = 0.15
MIN_Q1_Q3_RANGE = 0.3
MIN_MOCK_IMAGES = 20
MOCK_IMAGE_SIZE = (512, 512)

# Real dataset configuration
VISUAL_GENOME_BASE_URL = "https://visualgenome.org/api/v0"
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 2

logger = get_logger(__name__)


def _generate_complexity_scores(count: int) -> List[float]:
    """
    Generate calibrated complexity scores ensuring Q1-Q3 range >= 0.3.
    
    Args:
        count: Number of scores to generate.
        
    Returns:
        List of complexity scores between 0.0 and 1.0.
    """
    if count < 4:
        # For small samples, force spread manually
        scores = [0.2, 0.5, 0.5, 0.8][:count]
    else:
        # Generate from normal distribution, then adjust
        scores = np.random.normal(MOCK_COMPLEXITY_MEAN, MOCK_COMPLEXITY_STD, count).tolist()
        
        # Clamp to [0.0, 1.0]
        scores = [max(0.0, min(1.0, s)) for s in scores]
        
        # Ensure Q1-Q3 range >= 0.3
        sorted_scores = sorted(scores)
        q1_idx = int(count * 0.25)
        q3_idx = int(count * 0.75)
        q1 = sorted_scores[q1_idx]
        q3 = sorted_scores[q3_idx]
        
        if q3 - q1 < MIN_Q1_Q3_RANGE:
            # Stretch the distribution to meet the requirement
            scale_factor = MIN_Q1_Q3_RANGE / (q3 - q1 + 1e-9)
            center = MOCK_COMPLEXITY_MEAN
            scores = [max(0.0, min(1.0, center + (s - center) * scale_factor)) for s in scores]
            
    return scores


def _create_synthetic_image(width: int, height: int, complexity_score: float) -> Image.Image:
    """
    Create a synthetic image with visual complexity corresponding to the score.
    
    Args:
        width: Image width.
        height: Image height.
        complexity_score: Target complexity (0.0 = simple, 1.0 = complex).
        
    Returns:
        PIL Image object.
    """
    # Base background
    img = Image.new('RGB', (width, height), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)
    
    # Number of elements scales with complexity
    num_elements = int(5 + complexity_score * 45)
    
    # Draw random shapes
    for i in range(num_elements):
        x1 = random.randint(0, width - 50)
        y1 = random.randint(0, height - 50)
        x2 = x1 + random.randint(20, 100)
        y2 = y1 + random.randint(20, 100)
        
        # Color varies with complexity (more varied colors for higher complexity)
        if complexity_score > 0.6:
            color = (
                random.randint(50, 200),
                random.randint(50, 200),
                random.randint(50, 200)
            )
        else:
            # More muted colors for simpler images
            base = int(150 + complexity_score * 50)
            color = (base, base, base)
        
        shape_type = random.choice(['rectangle', 'circle', 'ellipse'])
        
        if shape_type == 'rectangle':
            draw.rectangle([x1, y1, x2, y2], fill=color, outline='black')
        elif shape_type == 'circle':
            draw.ellipse([x1, y1, x2, y2], fill=color, outline='black')
        else:
            draw.ellipse([x1, y1, x2, y2], fill=color, outline='black')
            
        # Add detail (lines/text) for high complexity
        if complexity_score > 0.7 and random.random() < 0.3:
            lx1, ly1 = x1, y1
            lx2, ly2 = x2, y2
            draw.line([(lx1, ly1), (lx2, ly2)], fill='darkgray', width=2)
    
    return img


def generate_mock_visual_genome(output_dir: Optional[Path] = None, count: int = MIN_MOCK_IMAGES) -> List[Dict[str, Any]]:
    """
    Generate a mock Visual Genome dataset with calibrated complexity scores.
    
    Args:
        output_dir: Directory to save images. Defaults to project's stimuli dir.
        count: Number of images to generate.
        
    Returns:
        List of metadata dictionaries for generated images.
    """
    if output_dir is None:
        output_dir = get_stimuli_dir()
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Generating {count} mock images in {output_dir}")
    
    scores = _generate_complexity_scores(count)
    metadata_list = []
    
    for i, score in enumerate(scores):
        img_id = f"mock_{i:04d}"
        filename = f"{img_id}.png"
        filepath = output_dir / filename
        
        # Create and save image
        img = _create_synthetic_image(MOCK_IMAGE_SIZE[0], MOCK_IMAGE_SIZE[1], score)
        img.save(filepath, 'PNG')
        
        # Create metadata
        metadata = {
            'id': img_id,
            'filename': filename,
            'path': str(filepath),
            'complexity_score': round(score, 4),
            'source': 'mock',
            'width': MOCK_IMAGE_SIZE[0],
            'height': MOCK_IMAGE_SIZE[1],
            'generated_at': str(Path.cwd())
        }
        metadata_list.append(metadata)
        
        logger.debug(f"Generated {img_id} with complexity {score:.3f}")
    
    logger.info(f"Successfully generated {len(metadata_list)} mock images")
    return metadata_list


def fetch_real_dataset_image(image_id: str, output_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """
    Fetch a real image from Visual Genome dataset.
    
    Args:
        image_id: The Visual Genome image ID to fetch.
        output_dir: Directory to save the image. Defaults to project's stimuli dir.
        
    Returns:
        Metadata dictionary if successful, None if failed.
    """
    config = get_config()
    dataset_source = config.get('dataset_source', 'mock')
    
    # Only attempt fetch if explicitly configured for real data
    if dataset_source != 'visual_genome_real':
        logger.warning(f"Dataset source is '{dataset_source}', skipping real fetch for {image_id}")
        return None
        
    if output_dir is None:
        output_dir = get_stimuli_dir()
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Construct URL
    image_url = f"{VISUAL_GENOME_BASE_URL}/image/{image_id}.jpg"
    filename = f"vg_{image_id}.jpg"
    filepath = output_dir / filename
    
    logger.info(f"Attempting to fetch real image {image_id} from Visual Genome")
    
    for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Save image
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            # Get image dimensions
            img = Image.open(filepath)
            width, height = img.size
            img.close()
            
            # Calculate a placeholder complexity (real calculation would require analysis)
            # For now, use a hash-based pseudo-random value in [0, 1]
            complexity_score = (hash(str(image_id)) % 1000) / 1000.0
            
            metadata = {
                'id': f"vg_{image_id}",
                'filename': filename,
                'path': str(filepath),
                'complexity_score': round(complexity_score, 4),
                'source': 'visual_genome_real',
                'width': width,
                'height': height,
                'fetched_at': str(Path.cwd())
            }
            
            logger.info(f"Successfully fetched real image {image_id}")
            return metadata
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Fetch attempt {attempt} failed for {image_id}: {e}")
            if attempt < MAX_RETRY_ATTEMPTS:
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                logger.error(f"Failed to fetch {image_id} after {MAX_RETRY_ATTEMPTS} attempts")
                # Log to error file
                error_log_path = get_manipulation_error_log_path()
                with open(error_log_path, 'a') as log_file:
                    log_file.write(f"Fetch error for {image_id}: {str(e)}\n")
                return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {image_id}: {e}")
            return None
    
    return None


def load_image_metadata(metadata_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load image metadata from a JSON file.
    
    Args:
        metadata_path: Path to the metadata JSON file.
        
    Returns:
        Metadata dictionary or None if file not found/invalid.
    """
    if not metadata_path.exists():
        logger.warning(f"Metadata file not found: {metadata_path}")
        return None
        
    try:
        with open(metadata_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {metadata_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error reading {metadata_path}: {e}")
        return None


def main():
    """Main entry point for generating mock dataset or testing fetch."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Visual Genome Data Loader")
    parser.add_argument(
        '--mode',
        choices=['mock', 'fetch'],
        default='mock',
        help="Mode: 'mock' to generate synthetic data, 'fetch' to get real data"
    )
    parser.add_argument(
        '--count',
        type=int,
        default=MIN_MOCK_IMAGES,
        help="Number of mock images to generate"
    )
    parser.add_argument(
        '--image-id',
        type=str,
        help="Visual Genome image ID to fetch (required for fetch mode)"
    )
    
    args = parser.parse_args()
    
    if args.mode == 'mock':
        logger.info(f"Generating {args.count} mock images...")
        metadata = generate_mock_visual_genome(count=args.count)
        logger.info(f"Generated {len(metadata)} images. Sample metadata:")
        for m in metadata[:3]:
            logger.info(f"  - {m['id']}: complexity={m['complexity_score']}")
            
    elif args.mode == 'fetch':
        if not args.image_id:
            parser.error("--image-id is required for fetch mode")
            
        logger.info(f"Fetching real image {args.image_id}...")
        metadata = fetch_real_dataset_image(args.image_id)
        if metadata:
            logger.info(f"Success: {metadata}")
        else:
            logger.error("Failed to fetch image.")
            
    else:
        parser.error(f"Unknown mode: {args.mode}")


if __name__ == '__main__':
    main()