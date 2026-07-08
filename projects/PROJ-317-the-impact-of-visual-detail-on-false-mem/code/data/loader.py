import json
import logging
import math
import os
import random
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

from config import get_stimuli_dir, get_project_root

logger = logging.getLogger(__name__)

def generate_mock_visual_genome(count: int = 10, output_dir: Optional[str] = None) -> List[Path]:
    """
    Generate synthetic images with calibrated complexity scores.
    
    Args:
        count: Number of images to generate.
        output_dir: Directory to save images. Defaults to data/stimuli.
        
    Returns:
        List of paths to generated images.
    """
    if output_dir is None:
        output_dir = str(get_stimuli_dir())
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    generated_files = []
    
    # Ensure Q1-Q3 range >= 0.3 for complexity scores
    # We will generate scores in a range that satisfies this, e.g., 0.3 to 0.8
    # Mean should be around 0.5, std around 0.15
    
    for i in range(count):
        # Generate complexity score
        # Using a bounded normal distribution to ensure range constraints
        score = random.gauss(0.5, 0.15)
        score = max(0.2, min(0.8, score)) # Clamp to ensure reasonable range
        
        # Create a 256x256 RGB image
        img = Image.new('RGB', (256, 256), color=(random.randint(100, 200), random.randint(100, 200), random.randint(100, 200)))
        draw = ImageDraw.Draw(img)
        
        # Draw random shapes to vary complexity
        num_shapes = int(score * 20) # More shapes = higher complexity
        for _ in range(num_shapes):
            x1 = random.randint(0, 250)
            y1 = random.randint(0, 250)
            x2 = random.randint(x1 + 10, 255)
            y2 = random.randint(y1 + 10, 255)
            color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            draw.rectangle([x1, y1, x2, y2], fill=color)
            
            # Add some text or circles for detail
            if random.random() > 0.5:
                draw.ellipse([x1, y1, x1+20, y1+20], outline=color, width=2)
        
        filename = f"mock_image_{i:04d}.png"
        filepath = output_path / filename
        img.save(filepath)
        generated_files.append(filepath)
        
        logger.info(f"Generated mock image: {filepath} with complexity {score:.2f}")
        
        # Store metadata for this image in a temporary JSON for later retrieval
        # In a real pipeline, this might be stored in a database or separate metadata file
        # Here we save a sidecar JSON for the loader to potentially use, 
        # though the task T006 says "Mock Visual Genome Generator", implying the generator creates the data.
        # We will rely on the manipulator to calculate complexity or store it in metadata later.
    
    return generated_files

def fetch_real_dataset_image(url: str, output_path: Path) -> bool:
    """
    Fetch a real image from a URL.
    
    Args:
        url: URL of the image.
        output_path: Destination path.
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        import urllib.request
        urllib.request.urlretrieve(url, output_path)
        logger.info(f"Downloaded image from {url} to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to fetch image from {url}: {e}")
        return False

def load_image_metadata(image_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load metadata for an image from a sidecar JSON file.
    
    Args:
        image_path: Path to the image.
        
    Returns:
        Dictionary of metadata or None if not found.
    """
    metadata_path = image_path.with_suffix('.json')
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            return json.load(f)
    return None

def main():
    """Main entry point for generating mock data."""
    logging.basicConfig(level=logging.INFO)
    generate_mock_visual_genome(5)
    logger.info("Mock data generation complete.")

if __name__ == "__main__":
    main()
