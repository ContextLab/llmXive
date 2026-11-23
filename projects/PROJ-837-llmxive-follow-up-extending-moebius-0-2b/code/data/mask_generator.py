"""
Synthetic mask generation with complexity metrics.

Generates synthetic masks with varying complexity levels and computes:
- gradient_variance: Variance of the image gradients within the masked region
- texture_entropy: Shannon entropy of the texture features within the masked region

Output:
- data/processed/mask_metrics.json: Metrics for each generated mask
- data/processed/masked_images/: Directory containing masked images
"""
import os
import math
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from PIL import Image
import scipy.stats

from config import get_path, is_ci_mode, is_research_mode, get_mode
from utils.seed import set_seed
from utils.logger import get_logger, setup_project_logger
from data.loader import fetch_places365_subset

# Constants
MASK_COMPLEXITY_LEVELS = ['low', 'medium', 'high']
DEFAULT_SAMPLE_SIZE = 100  # Number of masks to generate
OUTPUT_METRICS_FILE = 'data/processed/mask_metrics.json'
OUTPUT_MASKED_DIR = 'data/processed/masked_images'

logger = setup_project_logger("mask_generator")

def compute_gradient_variance(image: np.ndarray, mask: np.ndarray) -> float:
    """
    Compute gradient variance within the masked region.
    
    Args:
        image: RGB image as numpy array (H, W, 3)
        mask: Binary mask as numpy array (H, W)
        
    Returns:
        float: Gradient variance value
    """
    # Convert to grayscale
    gray = np.mean(image, axis=2)
    
    # Apply mask
    masked_gray = gray * mask
    
    # Compute gradients
    grad_x = np.gradient(masked_gray, axis=1)
    grad_y = np.gradient(masked_gray, axis=0)
    
    # Compute gradient magnitude
    grad_magnitude = np.sqrt(grad_x**2 + grad_y**2)
    
    # Compute variance of gradient magnitude within masked region
    masked_magnitude = grad_magnitude[mask > 0]
    
    if len(masked_magnitude) == 0:
        return 0.0
    
    return float(np.var(masked_magnitude))

def compute_texture_entropy(image: np.ndarray, mask: np.ndarray) -> float:
    """
    Compute texture entropy within the masked region using histogram-based approach.
    
    Args:
        image: RGB image as numpy array (H, W, 3)
        mask: Binary mask as numpy array (H, W)
        
    Returns:
        float: Texture entropy value
    """
    # Convert to grayscale
    gray = np.mean(image, axis=2)
    
    # Apply mask
    masked_gray = gray[mask > 0]
    
    if len(masked_gray) == 0:
        return 0.0
    
    # Compute histogram
    hist, _ = np.histogram(masked_gray, bins=256, range=(0, 256))
    
    # Normalize histogram to get probabilities
    probs = hist / hist.sum()
    
    # Remove zero probabilities to avoid log(0)
    probs = probs[probs > 0]
    
    # Compute Shannon entropy
    entropy = -np.sum(probs * np.log2(probs))
    
    return float(entropy)

def generate_complexity_mask(
    width: int,
    height: int,
    complexity: str,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Generate a synthetic mask with specified complexity level.
    
    Args:
        width: Image width
        height: Image height
        complexity: One of 'low', 'medium', 'high'
        seed: Optional random seed for reproducibility
        
    Returns:
        np.ndarray: Binary mask (H, W) with values 0 or 1
    """
    if seed is not None:
        np.random.seed(seed)
    
    mask = np.zeros((height, width), dtype=np.float32)
    
    if complexity == 'low':
        # Simple geometric shapes
        num_shapes = np.random.randint(1, 3)
        for _ in range(num_shapes):
            center_x = np.random.randint(0, width)
            center_y = np.random.randint(0, height)
            radius = np.random.randint(10, 30)
            
            y, x = np.ogrid[:height, :width]
            circle = (x - center_x)**2 + (y - center_y)**2 <= radius**2
            mask[circle] = 1.0
            
    elif complexity == 'medium':
        # Multiple overlapping shapes with varying sizes
        num_shapes = np.random.randint(3, 6)
        for _ in range(num_shapes):
            shape_type = np.random.choice(['circle', 'rectangle', 'ellipse'])
            
            if shape_type == 'circle':
                center_x = np.random.randint(0, width)
                center_y = np.random.randint(0, height)
                radius = np.random.randint(15, 50)
                
                y, x = np.ogrid[:height, :width]
                circle = (x - center_x)**2 + (y - center_y)**2 <= radius**2
                mask[circle] = 1.0
                
            elif shape_type == 'rectangle':
                x1 = np.random.randint(0, width - 20)
                y1 = np.random.randint(0, height - 20)
                w = np.random.randint(20, 60)
                h = np.random.randint(20, 60)
                
                mask[y1:y1+h, x1:x1+w] = 1.0
                
            else:  # ellipse
                center_x = np.random.randint(0, width)
                center_y = np.random.randint(0, height)
                a = np.random.randint(15, 50)
                b = np.random.randint(15, 50)
                
                y, x = np.ogrid[:height, :width]
                ellipse = ((x - center_x)**2 / a**2) + ((y - center_y)**2 / b**2) <= 1
                mask[ellipse] = 1.0
                
    elif complexity == 'high':
        # Complex, irregular shapes (simulating natural masks)
        num_shapes = np.random.randint(8, 15)
        for _ in range(num_shapes):
            # Generate random polygon points
            num_points = np.random.randint(5, 10)
            points = np.random.rand(num_points, 2)
            points[:, 0] *= width
            points[:, 1] *= height
            
            # Create mask from polygon using scipy
            try:
                from scipy.ndimage import binary_fill_holes
                
                # Create a temporary mask for this polygon
                temp_mask = np.zeros((height, width), dtype=np.uint8)
                
                # Fill polygon (simplified approach)
                for i in range(num_points):
                    x1, y1 = points[i]
                    x2, y2 = points[(i + 1) % num_points]
                    # Draw line (simplified)
                    num_steps = max(abs(x2 - x1), abs(y2 - y1))
                    x_coords = np.linspace(x1, x2, num_steps, dtype=int)
                    y_coords = np.linspace(y1, y2, num_steps, dtype=int)
                    x_coords = np.clip(x_coords, 0, width - 1)
                    y_coords = np.clip(y_coords, 0, height - 1)
                    temp_mask[y_coords, x_coords] = 1
                
                # Fill the polygon
                temp_mask = binary_fill_holes(temp_mask)
                mask[temp_mask] = 1.0
                
            except ImportError:
                # Fallback if scipy.ndimage is not available
                # Use simple rectangle approximation
                x_coords = points[:, 0].astype(int)
                y_coords = points[:, 1].astype(int)
                x_min, x_max = np.clip(x_coords.min(), 0, width - 1), np.clip(x_coords.max(), 0, width - 1)
                y_min, y_max = np.clip(y_coords.min(), 0, height - 1), np.clip(y_coords.max(), 0, height - 1)
                mask[y_min:y_max, x_min:x_max] = 1.0
    else:
        raise ValueError(f"Unknown complexity level: {complexity}")
    
    # Ensure mask is binary
    mask = (mask > 0).astype(np.float32)
    
    return mask

def apply_mask_to_image(
    image: np.ndarray,
    mask: np.ndarray,
    mask_value: float = 0.0
) -> np.ndarray:
    """
    Apply mask to image by setting masked regions to a constant value.
    
    Args:
        image: RGB image as numpy array (H, W, 3)
        mask: Binary mask as numpy array (H, W)
        mask_value: Value to set masked regions to (default: 0.0 for black)
        
    Returns:
        np.ndarray: Masked image
    """
    masked_image = image.copy()
    for c in range(3):
        masked_image[:, :, c] = np.where(mask == 0, masked_image[:, :, c], mask_value)
    return masked_image

def generate_mask_batch(
    image_paths: List[str],
    output_dir: str,
    sample_size: int,
    seed: Optional[int] = None,
    complexity_distribution: Optional[Dict[str, float]] = None
) -> List[Dict[str, Any]]:
    """
    Generate masks for a batch of images and compute metrics.
    
    Args:
        image_paths: List of paths to input images
        output_dir: Directory to save masked images
        sample_size: Number of images to process
        seed: Random seed for reproducibility
        complexity_distribution: Dict mapping complexity level to probability
        
    Returns:
        List of dicts containing mask metrics
    """
    if seed is not None:
        set_seed(seed)
    
    if complexity_distribution is None:
        complexity_distribution = {
            'low': 0.33,
            'medium': 0.34,
            'high': 0.33
        }
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    metrics_list = []
    
    # Limit sample size to available images
    actual_sample_size = min(sample_size, len(image_paths))
    logger.info(f"Processing {actual_sample_size} images for mask generation")
    
    for i in range(actual_sample_size):
        image_path = image_paths[i]
        
        try:
            # Load image
            img = Image.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            image = np.array(img)
            
            height, width = image.shape[:2]
            
            # Select complexity level based on distribution
            complexity = np.random.choice(
                list(complexity_distribution.keys()),
                p=list(complexity_distribution.values())
            )
            
            # Generate mask
            if seed is not None:
                mask_seed = seed + i
            else:
                mask_seed = None
            
            mask = generate_complexity_mask(width, height, complexity, seed=mask_seed)
            
            # Compute metrics
            gradient_variance = compute_gradient_variance(image, mask)
            texture_entropy = compute_texture_entropy(image, mask)
            
            # Apply mask
            masked_image = apply_mask_to_image(image, mask)
            
            # Save masked image
            base_name = Path(image_path).stem
            output_path = os.path.join(output_dir, f"{base_name}_masked.png")
            masked_img_pil = Image.fromarray((masked_image * 255).astype(np.uint8))
            masked_img_pil.save(output_path)
            
            # Record metrics
            metric_entry = {
                'image_id': base_name,
                'image_path': image_path,
                'mask_path': output_path,
                'complexity': complexity,
                'gradient_variance': gradient_variance,
                'texture_entropy': texture_entropy,
                'mask_fill_ratio': float(np.mean(mask)),
                'seed_used': mask_seed
            }
            metrics_list.append(metric_entry)
            
            logger.debug(f"Processed image {i+1}/{actual_sample_size}: {base_name} "
                       f"(complexity={complexity}, gv={gradient_variance:.4f}, "
                       f"te={texture_entropy:.4f})")
            
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {str(e)}")
            continue
    
    return metrics_list

def run_pipeline(
    sample_size: int = DEFAULT_SAMPLE_SIZE,
    seed: Optional[int] = None,
    output_metrics_path: Optional[str] = None,
    output_masked_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the complete mask generation pipeline.
    
    Args:
        sample_size: Number of masks to generate
        seed: Random seed for reproducibility
        output_metrics_path: Path to save metrics JSON
        output_masked_dir: Directory to save masked images
        
    Returns:
        Dict containing pipeline results
    """
    # Set paths
    if output_metrics_path is None:
        output_metrics_path = get_path(OUTPUT_METRICS_FILE)
    if output_masked_dir is None:
        output_masked_dir = get_path(OUTPUT_MASKED_DIR)
    
    logger.info(f"Starting mask generation pipeline (sample_size={sample_size}, "
               f"seed={seed})")
    
    # Ensure output directories exist
    os.makedirs(os.path.dirname(output_metrics_path), exist_ok=True)
    os.makedirs(output_masked_dir, exist_ok=True)
    
    # Fetch dataset
    logger.info("Fetching Places365 subset...")
    try:
        image_paths = fetch_places365_subset(limit=sample_size)
    except Exception as e:
        logger.error(f"Failed to fetch dataset: {str(e)}")
        raise SystemExit(1)
    
    if not image_paths:
        logger.error("No images found in dataset")
        raise SystemExit(1)
    
    logger.info(f"Found {len(image_paths)} images")
    
    # Generate masks and compute metrics
    metrics_list = generate_mask_batch(
        image_paths=image_paths,
        output_dir=output_masked_dir,
        sample_size=sample_size,
        seed=seed
    )
    
    if not metrics_list:
        logger.error("No metrics generated")
        raise SystemExit(1)
    
    # Save metrics
    with open(output_metrics_path, 'w') as f:
        json.dump(metrics_list, f, indent=2)
    
    logger.info(f"Saved metrics to {output_metrics_path}")
    logger.info(f"Saved {len(metrics_list)} masked images to {output_masked_dir}")
    
    # Compute summary statistics
    complexity_counts = {}
    for m in metrics_list:
        c = m['complexity']
        complexity_counts[c] = complexity_counts.get(c, 0) + 1
    
    avg_gradient_variance = np.mean([m['gradient_variance'] for m in metrics_list])
    avg_texture_entropy = np.mean([m['texture_entropy'] for m in metrics_list])
    
    result = {
        'num_images': len(metrics_list),
        'complexity_distribution': complexity_counts,
        'avg_gradient_variance': float(avg_gradient_variance),
        'avg_texture_entropy': float(avg_texture_entropy),
        'output_metrics_path': output_metrics_path,
        'output_masked_dir': output_masked_dir,
        'seed_used': seed
    }
    
    logger.info(f"Pipeline complete: {result}")
    return result

def main():
    """CLI entry point for mask generation."""
    parser = argparse.ArgumentParser(description='Generate synthetic masks with complexity metrics')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')
    parser.add_argument('--sample-size', type=int, default=DEFAULT_SAMPLE_SIZE,
                      help=f'Number of masks to generate (default: {DEFAULT_SAMPLE_SIZE})')
    parser.add_argument('--output-dir', type=str, default=None,
                      help='Output directory for masked images')
    parser.add_argument('--metrics-path', type=str, default=None,
                      help='Path to save metrics JSON')
    
    args = parser.parse_args()
    
    # Run pipeline
    result = run_pipeline(
        sample_size=args.sample_size,
        seed=args.seed,
        output_masked_dir=args.output_dir,
        output_metrics_path=args.metrics_path
    )
    
    # Print summary
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()