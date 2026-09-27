import os
import math
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from PIL import Image, ImageDraw

from config import get_mode, is_ci_mode, get_path
from config_env import get_datasets_path
from utils.logger import get_logger
from utils.seed import set_seed
from data.loader import fetch_places365_subset

logger = get_logger(__name__)

def _compute_gradient_variance(mask_array: np.ndarray) -> float:
    """
    Compute the variance of the gradient magnitude of the binary mask.
    Uses Sobel-like finite differences.
    """
    # Convert to float for gradient calculation
    mask_float = mask_array.astype(float)
    
    # Compute gradients
    grad_x = np.gradient(mask_float, axis=1)
    grad_y = np.gradient(mask_float, axis=0)
    
    # Magnitude
    mag = np.sqrt(grad_x**2 + grad_y**2)
    
    # Variance of magnitude
    return float(np.var(mag))

def _compute_texture_entropy(mask_array: np.ndarray) -> float:
    """
    Compute texture entropy based on the spatial distribution of the mask.
    Uses histogram of local variance or simple pixel distribution entropy.
    Here we use pixel distribution entropy of the mask itself as a proxy for complexity.
    """
    # Flatten and normalize
    flat = mask_array.flatten().astype(float)
    # Avoid log(0)
    flat = flat + 1e-10
    # Normalize to probability
    prob = flat / np.sum(flat)
    
    # Shannon entropy
    entropy = -np.sum(prob * np.log2(prob))
    return float(entropy)

def generate_mask(image: Image.Image, complexity: int = 3) -> Tuple[Image.Image, Dict[str, float]]:
    """
    Generate a synthetic mask with varying complexity on a COPY of the input image.
    Complexity 1: Simple rectangle.
    Complexity 5: Complex irregular shape with multiple components.
    
    Returns:
        Tuple of (Mask Image, Metrics Dict)
    """
    width, height = image.size
    
    # Create a new blank mask (0 = background, 255 = masked region)
    mask = Image.new("L", (width, height), 0)
    mask_draw = ImageDraw.Draw(mask)
    
    # Determine number of shapes based on complexity
    num_shapes = complexity 
    shapes_generated = []
    
    for i in range(num_shapes):
        # Randomize parameters based on complexity
        # Higher complexity = more variation in size and position
        if complexity == 1:
            # Fixed simple center rect
            x1, y1 = width // 4, height // 4
            x2, y2 = 3 * width // 4, 3 * height // 4
            mask_draw.rectangle([x1, y1, x2, y2], fill=255)
            shapes_generated.append("rect")
        else:
            # Randomized shapes
            # Size: 10% to 40% of image dimension
            w_range = int(width * 0.1)
            h_range = int(height * 0.1)
            w = np.random.randint(w_range, int(width * 0.4))
            h = np.random.randint(h_range, int(height * 0.4))
            
            x = np.random.randint(0, width - w)
            y = np.random.randint(0, height - h)
            
            shape_type = i % 3
            
            if shape_type == 0:
                # Rectangle
                mask_draw.rectangle([x, y, x + w, y + h], fill=255)
                shapes_generated.append("rect")
            elif shape_type == 1:
                # Ellipse
                mask_draw.ellipse([x, y, x + w, y + h], fill=255)
                shapes_generated.append("ellipse")
            else:
                # Polygon (irregular)
                # Generate 4-6 random points within the bounding box
                points = []
                num_pts = np.random.randint(4, 7)
                for _ in range(num_pts):
                    px = x + np.random.randint(0, w)
                    py = y + np.random.randint(0, h)
                    points.append((px, py))
                mask_draw.polygon(points, fill=255)
                shapes_generated.append("polygon")

    # Convert mask to numpy array for metrics
    mask_np = np.array(mask) > 0 # Boolean array: True where masked
    
    # Calculate metrics
    gradient_variance = _compute_gradient_variance(mask_np)
    texture_entropy = _compute_texture_entropy(mask_np)
    
    return mask, {
        "gradient_variance": gradient_variance,
        "texture_entropy": texture_entropy,
        "complexity": complexity,
        "shapes": shapes_generated
    }

def generate_mask_batch(images: List[Image.Image], complexities: List[int]) -> List[Tuple[Image.Image, Dict[str, float]]]:
    """
    Generate masks for a batch of images.
    """
    if len(images) != len(complexities):
        raise ValueError("Number of images must match number of complexities.")
    
    results = []
    for img, comp in zip(images, complexities):
        results.append(generate_mask(img, comp))
    return results

def run_pipeline(sample_size: int, seed: int, output_dir: Path):
    """
    Main pipeline to fetch data, generate masks, compute metrics, and save results.
    """
    logger.info(f"Starting mask generation pipeline with seed={seed}, sample_size={sample_size}")
    set_seed(seed)
    
    # Ensure output directories exist
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir = output_dir / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    
    # Fetch real data
    # Using Places365 small subset as per T012 dependency
    # We fetch a small subset for processing to stay within memory limits for this specific task run
    logger.info("Fetching Places365 subset...")
    try:
        dataset = fetch_places365_subset(limit=sample_size)
    except Exception as e:
        logger.error(f"Failed to fetch dataset: {e}")
        raise SystemExit(f"Data fetch failed: {e}")
    
    logger.info(f"Fetched {len(dataset)} images.")
    
    all_metrics = []
    processed_count = 0
    
    for idx, item in enumerate(dataset):
        # item is expected to be a dict with 'image' and 'path' (or similar) based on loader
        # Adjust based on actual loader output structure. Assuming 'image' is PIL.Image
        img = item.get('image')
        if img is None:
            logger.warning(f"Item {idx} missing image key, skipping.")
            continue
        
        # Assign complexity based on index to ensure variety
        # Cycle through 1-5
        complexity = (idx % 5) + 1
        
        try:
            mask, metrics = generate_mask(img, complexity)
            
            # Save mask image
            mask_filename = f"mask_{idx:04d}_c{complexity}.png"
            mask_path = metrics_dir / mask_filename
            mask.save(str(mask_path))
            
            # Record metrics
            metrics["image_id"] = idx
            metrics["image_path"] = item.get('path', f"sample_{idx}")
            metrics["mask_path"] = str(mask_path)
            all_metrics.append(metrics)
            
            processed_count += 1
            if processed_count % 50 == 0:
                logger.info(f"Processed {processed_count}/{sample_size} images.")
                
        except Exception as e:
            logger.error(f"Error processing image {idx}: {e}")
            continue
    
    # Save metrics to JSON
    metrics_file = output_dir / "mask_metrics.json"
    with open(metrics_file, 'w') as f:
        json.dump(all_metrics, f, indent=2)
    
    logger.info(f"Pipeline complete. Processed {processed_count} images. Metrics saved to {metrics_file}")
    return all_metrics

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic masks and compute complexity metrics.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--sample-size", type=int, default=500, help="Number of images to process")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory for masks and metrics")
    args = parser.parse_args()
    
    # Determine output directory
    if args.output_dir:
        out_dir = Path(args.output_dir)
    else:
        # Default to data/processed/mask_metrics
        out_dir = get_path("data_processed") / "mask_metrics"
        
    run_pipeline(args.sample_size, args.seed, out_dir)

if __name__ == "__main__":
    main()
