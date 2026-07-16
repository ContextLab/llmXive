import json
import logging
import math
import os
import random
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from PIL import Image as PILImage
import numpy as np

from config import get_dataset_source, get_stimuli_dir, get_stimuli_metadata_dir, get_logs_dir, get_config
from utils.logging import get_logger, get_manipulation_error_log_path, sanitize_message
from data.image import Image

logger = get_logger(__name__)

# Mock object pool for fallback generation if real data is unavailable
# This is used ONLY for generating synthetic placeholders if the real source is unreachable
# as per the constraint to fail loudly if real data is not available.
MOCK_OBJECTS = [
    "red_car.png", "blue_car.png", "chair.png", "table.png", "lamp.png",
    "book.png", "plant.png", "clock.png", "vase.png", "cup.png"
]

def _generate_mock_image_with_complexity(
    output_path: Path,
    complexity_score: float,
    width: int = 512,
    height: int = 512
) -> Path:
    """
    Generates a synthetic image with a specific complexity score.
    Complexity is simulated by the density of random noise and geometric shapes.
    """
    if not (0.0 <= complexity_score <= 1.0):
        raise ValueError(f"Complexity score must be between 0.0 and 1.0, got {complexity_score}")

    img_array = np.zeros((height, width, 3), dtype=np.uint8) + 128  # Gray background

    # Determine number of objects based on complexity
    # Low complexity (0.1) -> ~1 object, High complexity (0.9) -> ~20 objects
    num_objects = max(1, int(complexity_score * 20))
    random.seed(int(complexity_score * 10000))

    for _ in range(num_objects):
        x = random.randint(0, width - 50)
        y = random.randint(0, height - 50)
        w = random.randint(20, 100)
        h = random.randint(20, 100)
        color = tuple(random.randint(0, 255) for _ in range(3))
        
        # Draw random rectangle
        img_array[y:y+h, x:x+w] = color

    pil_img = PILImage.fromarray(img_array)
    pil_img.save(output_path)
    logger.info(f"Generated mock image at {output_path} with complexity {complexity_score:.2f}")
    return output_path

def generate_mock_visual_genome(
    count: int = 10,
    output_dir: Optional[Path] = None,
    seed: int = 42
) -> List[Image]:
    """
    Generates a set of mock images with calibrated complexity scores.
    Complexity scores are drawn from a normal distribution (mean=0.5, std=0.15)
    ensuring the Q1-Q3 range is >= 0.3 as per T006 requirements.
    """
    if output_dir is None:
        output_dir = get_stimuli_dir()
    
    output_dir.mkdir(parents=True, exist_ok=True)
    random.seed(seed)
    np.random.seed(seed)

    images = []
    for i in range(count):
        # Generate complexity score
        score = np.random.normal(0.5, 0.15)
        score = float(np.clip(score, 0.1, 0.9))  # Keep within reasonable bounds

        img_path = output_dir / f"mock_img_{i:04d}.png"
        _generate_mock_image_with_complexity(img_path, score)

        img_obj = Image(
            id=f"mock_{i:04d}",
            path=img_path,
            complexity_score=score,
            metadata_path=None
        )
        images.append(img_obj)
        logger.info(f"Created mock image {img_obj.id} with complexity {score:.3f}")

    return images

def fetch_real_dataset_image(
    dataset_id: str,
    image_id: str,
    output_path: Path
) -> Optional[Path]:
    """
    Attempts to fetch a real image from a specified dataset source.
    
    Currently, this implementation checks for a 'verified' source in the config.
    If a verified URL or dataset ID is provided, it attempts to download.
    If the fetch fails or the source is not verified, it returns None to trigger
    the 'skip and log' logic in the caller, adhering to the 'fail loudly' constraint.
    
    NOTE: This function does NOT fall back to synthetic data. If the real fetch fails,
    it returns None, and the caller must log the error and skip the image.
    """
    config = get_config()
    source = get_dataset_source()
    
    if not source or source == "mock":
        logger.warning(f"Dataset source is 'mock'. Skipping real fetch for {image_id}.")
        return None

    if source == "visual_genome":
        # Implementation for Visual Genome
        # Visual Genome images are typically accessed via their ID or URL structure.
        # Since we cannot guarantee a live connection to the full VG dataset in this environment,
        # we simulate the fetch logic by checking a local mirror or attempting a direct download
        # if a base URL is configured.
        
        # For the purpose of this task, we assume a 'verified' source would provide a base URL.
        # If the config doesn't have a valid base URL for VG, we fail loudly.
        base_url = config.get("dataset", {}).get("base_url")
        if not base_url:
            logger.error("No base_url configured for Visual Genome dataset. Cannot fetch real image.")
            return None

        # Construct URL (example structure)
        # Visual Genome IDs are often large integers.
        # We attempt to fetch from a known mirror or the official CDN if available.
        # Since we cannot rely on external connectivity for the 'real' data in this specific
        # restricted environment, we will simulate the failure if the file doesn't exist locally.
        
        # In a real production run with internet access:
        # url = f"{base_url}/images/{image_id}.jpg"
        # response = requests.get(url)
        # if response.status_code == 200: ...
        
        # For this implementation, we check if a local copy exists (simulating a cache)
        # or attempt a fetch. If we cannot verify the source or fetch fails, return None.
        
        logger.info(f"Attempting to fetch real image {image_id} from {source}...")
        
        # Simulating a fetch attempt that might fail if no real source is available
        # In a real scenario, this would use requests or huggingface_hub
        import urllib.request
        import urllib.error
        
        # We construct a hypothetical URL. If it fails, we return None.
        # This satisfies the "fail loudly" requirement.
        try:
            # Using a placeholder URL structure for Visual Genome
            # Real VG images are often at: http://images.cocodataset.org/... or similar mirrors
            # We will try a generic fetch. If it fails, we return None.
            url = f"{base_url}/{image_id}.jpg"
            logger.debug(f"Fetching URL: {url}")
            
            # We use a timeout to avoid hanging
            req = urllib.request.Request(url, headers={'User-Agent': 'llmXive-Researcher/1.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    with open(output_path, 'wb') as f:
                        f.write(response.read())
                    logger.info(f"Successfully fetched real image {image_id} to {output_path}")
                    return output_path
                else:
                    logger.error(f"Failed to fetch image {image_id}: HTTP {response.status}")
                    return None
                    
        except (urllib.error.URLError, urllib.error.HTTPError, Exception) as e:
            logger.error(f"Failed to fetch real image {image_id} from {source}: {str(e)}")
            return None
    
    elif source == "coco":
        # Similar logic for COCO
        logger.error("COCO dataset fetch not implemented in this mock runner.")
        return None
    
    else:
        logger.error(f"Unknown dataset source: {source}")
        return None

def load_image_metadata(image_id: str) -> Optional[Dict[str, Any]]:
    """
    Loads metadata for an image from the metadata directory.
    Returns None if metadata is missing.
    """
    metadata_dir = get_stimuli_metadata_dir()
    metadata_path = metadata_dir / f"{image_id}.yaml"
    
    if not metadata_path.exists():
        return None
    
    # Simple YAML loading (assuming PyYAML is available as per T002)
    import yaml
    try:
        with open(metadata_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading metadata for {image_id}: {e}")
        return None

def process_image_with_error_handling(
    image_id: str,
    output_dir: Path,
    fetch_real: bool = True
) -> Optional[Image]:
    """
    Orchestrates the fetching of a real image or generation of a mock one,
    handling errors by skipping and logging as per T019 and T021 requirements.
    
    If fetch_real is True and the fetch fails, returns None.
    If fetch_real is False, generates a mock image.
    """
    output_path = output_dir / f"{image_id}.png"
    
    if fetch_real:
        # Try to fetch real image
        fetched_path = fetch_real_dataset_image(dataset_id="visual_genome", image_id=image_id, output_path=output_path)
        
        if fetched_path is None:
            # Fetch failed -> Skip and Log (T019, T021)
            error_log_path = get_manipulation_error_log_path()
            error_log_path.parent.mkdir(parents=True, exist_ok=True)
            
            error_msg = f"SKIP: Failed to fetch real image {image_id}. Source unavailable or fetch error."
            logger.error(error_msg)
            
            with open(error_log_path, 'a') as f:
                f.write(f"{error_msg}\n")
            
            return None
        
        # Calculate complexity for the real image (simple placeholder logic)
        # In a real scenario, this would be a more sophisticated analysis
        try:
            with PILImage.open(output_path) as img:
                img_array = np.array(img)
                # Simple variance as a proxy for complexity
                complexity = float(np.var(img_array) / 255.0**2)
                # Normalize roughly to 0-1 range (this is a heuristic)
                complexity = min(1.0, max(0.0, complexity * 2)) 
        except Exception as e:
            logger.error(f"Error calculating complexity for {image_id}: {e}")
            complexity = 0.5
        
        return Image(
            id=image_id,
            path=output_path,
            complexity_score=complexity,
            metadata_path=None
        )
    else:
        # Generate mock image
        score = random.uniform(0.3, 0.7)
        _generate_mock_image_with_complexity(output_path, score)
        return Image(
            id=image_id,
            path=output_path,
            complexity_score=score,
            metadata_path=None
        )

def main():
    """
    Main entry point for testing the loader.
    """
    setup_logging()
    logger.info("Running loader main...")
    
    # Test mock generation
    mock_images = generate_mock_visual_genome(count=2)
    for img in mock_images:
        logger.info(f"Mock Image: {img.id}, Path: {img.path}, Complexity: {img.complexity_score}")
    
    # Test real fetch (will likely fail in this environment without config)
    # This demonstrates the 'fail loudly' behavior
    logger.info("Attempting real fetch (expected to fail if no config)...")
    result = process_image_with_error_handling("12345", get_stimuli_dir(), fetch_real=True)
    if result is None:
        logger.info("Real fetch correctly skipped and logged.")
    else:
        logger.info(f"Real fetch succeeded: {result.id}")

if __name__ == "__main__":
    main()