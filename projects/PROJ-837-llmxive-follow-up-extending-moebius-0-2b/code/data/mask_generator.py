"""
Synthetic Mask Generator for Moebius Inpainting.

Generates synthetic masks with varying complexity and computes
gradient_variance and texture_entropy metrics.
"""
import os
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw
import torch
from torch import nn
import torch.nn.functional as F

from config import is_ci_mode
from utils.logger import get_logger
from utils.seed import set_seed
from config_env import get_data_path, get_results_path, register_artifact

logger = get_logger(__name__)

# Constants for mask generation
MIN_MASK_RATIO = 0.05
MAX_MASK_RATIO = 0.50
MIN_SHAPE_SIZE = 16
MAX_SHAPE_SIZE = 128
NUM_SHAPES_RANGE = (1, 10)  # Number of shapes per mask

# Metrics calculation constants
GRADIENT_KERNEL = torch.tensor([[-1, 0, 1],
                                [-2, 0, 2],
                                [-1, 0, 1]], dtype=torch.float32)
ENTROPY_WINDOW_SIZE = 3


def _get_sobel_kernel(device: torch.device) -> Tuple[torch.Tensor, torch.Tensor]:
    """Get Sobel kernels for gradient calculation."""
    kernel_x = torch.tensor([[-1, 0, 1],
                             [-2, 0, 2],
                             [-1, 0, 1]], dtype=torch.float32, device=device)
    kernel_y = torch.tensor([[-1, -2, -1],
                             [0, 0, 0],
                             [1, 2, 1]], dtype=torch.float32, device=device)
    return kernel_x, kernel_y


def _calculate_gradient_variance(image: torch.Tensor) -> float:
    """
    Calculate the variance of gradient magnitudes in the image.
    Used as a proxy for texture complexity.

    Args:
        image: Tensor of shape (C, H, W) or (H, W)

    Returns:
        float: Variance of gradient magnitudes
    """
    if image.dim() == 3 and image.shape[0] in [1, 3]:
        # Convert to grayscale if RGB
        if image.shape[0] == 3:
            image = 0.299 * image[0] + 0.587 * image[1] + 0.114 * image[2]
        else:
            image = image[0]

    device = image.device
    kernel_x, kernel_y = _get_sobel_kernel(device)

    # Pad image for convolution
    image_padded = F.pad(image.unsqueeze(0).unsqueeze(0), (1, 1, 1, 1), mode='reflect')

    # Compute gradients
    grad_x = F.conv2d(image_padded, kernel_x.unsqueeze(0).unsqueeze(0))
    grad_y = F.conv2d(image_padded, kernel_y.unsqueeze(0).unsqueeze(0))

    # Gradient magnitude
    grad_mag = torch.sqrt(grad_x ** 2 + grad_y ** 2 + 1e-8)

    # Flatten and compute variance
    grad_mag_flat = grad_mag.squeeze().flatten()
    variance = torch.var(grad_mag_flat).item()

    return float(variance)


def _calculate_texture_entropy(image: torch.Tensor) -> float:
    """
    Calculate texture entropy using local binary patterns approximation
    via histogram of gradient orientations in local windows.

    Args:
        image: Tensor of shape (C, H, W) or (H, W)

    Returns:
        float: Normalized entropy value [0, 1]
    """
    if image.dim() == 3 and image.shape[0] in [1, 3]:
        if image.shape[0] == 3:
            image = 0.299 * image[0] + 0.587 * image[1] + 0.114 * image[2]
        else:
            image = image[0]

    device = image.device
    H, W = image.shape

    # Compute gradients
    kernel_x, kernel_y = _get_sobel_kernel(device)
    image_padded = F.pad(image.unsqueeze(0).unsqueeze(0), (1, 1, 1, 1), mode='reflect')

    grad_x = F.conv2d(image_padded, kernel_x.unsqueeze(0).unsqueeze(0)).squeeze()
    grad_y = F.conv2d(image_padded, kernel_y.unsqueeze(0).unsqueeze(0)).squeeze()

    # Compute orientation
    orientation = torch.atan2(grad_y, grad_x)
    # Normalize to [0, 2*pi]
    orientation = (orientation + math.pi) % (2 * math.pi)

    # Divide into local windows and compute histogram entropy
    window_size = ENTROPY_WINDOW_SIZE
    stride = window_size
    entropies = []

    for i in range(0, H - window_size + 1, stride):
        for j in range(0, W - window_size + 1, stride):
            window = orientation[i:i+window_size, j:j+window_size]
            # Bin orientations into 8 bins
            bins = torch.floor(window / (2 * math.pi) * 8).long()
            hist = torch.bincount(bins.flatten(), minlength=8).float()
            hist = hist / hist.sum()  # Normalize
            # Compute entropy
            entropy = -torch.sum(hist * torch.log(hist + 1e-10))
            entropies.append(entropy)

    if not entropies:
        return 0.0

    avg_entropy = torch.stack(entropies).mean().item()
    # Normalize by max possible entropy (log(8) for 8 bins)
    max_entropy = math.log(8)
    normalized_entropy = avg_entropy / max_entropy

    return float(min(1.0, normalized_entropy))


def _generate_random_mask_shape(
    draw: ImageDraw.ImageDraw,
    width: int,
    height: int,
    mask_ratio_target: float
) -> None:
    """
    Generate a random mask shape (ellipse, rectangle, or polygon).
    """
    shape_type = np.random.choice(['ellipse', 'rectangle', 'polygon'])

    # Random position and size
    x1 = np.random.randint(0, width - MAX_SHAPE_SIZE)
    y1 = np.random.randint(0, height - MAX_SHAPE_SIZE)
    size = np.random.randint(MIN_SHAPE_SIZE, MAX_SHAPE_SIZE)
    x2 = min(x1 + size, width)
    y2 = min(y1 + size, height)

    if shape_type == 'ellipse':
        draw.ellipse([x1, y1, x2, y2], fill=255)
    elif shape_type == 'rectangle':
        draw.rectangle([x1, y1, x2, y2], fill=255)
    else:  # polygon
        num_points = np.random.randint(4, 8)
        points = []
        center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
        radius = (x2 - x1) // 2
        for _ in range(num_points):
            angle = np.random.uniform(0, 2 * math.pi)
            r = radius * np.random.uniform(0.5, 1.0)
            px = int(center_x + r * math.cos(angle))
            py = int(center_y + r * math.sin(angle))
            points.append((px, py))
        draw.polygon(points, fill=255)


def generate_mask(
    image_size: Tuple[int, int],
    complexity_target: Optional[float] = None
) -> Tuple[np.ndarray, Dict[str, float]]:
    """
    Generate a synthetic binary mask with controlled complexity.

    Args:
        image_size: Tuple (width, height) of the target image size
        complexity_target: Optional target complexity score (0-1) to guide
                           mask generation. If None, random complexity is used.

    Returns:
        Tuple of (mask_array, metrics_dict)
        mask_array: Binary mask (255 for mask, 0 for background)
        metrics_dict: Dictionary containing 'gradient_variance' and 'texture_entropy'
    """
    width, height = image_size
    total_pixels = width * height

    # Determine mask area ratio
    if complexity_target is not None:
        # Map complexity [0, 1] to mask ratio [MIN, MAX]
        mask_ratio = MIN_MASK_RATIO + complexity_target * (MAX_MASK_RATIO - MIN_MASK_RATIO)
    else:
        mask_ratio = np.random.uniform(MIN_MASK_RATIO, MAX_SHAPE_RATIO)

    # Create blank mask
    mask = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(mask)

    # Calculate number of shapes needed to achieve target mask ratio
    target_mask_pixels = int(total_pixels * mask_ratio)
    current_mask_pixels = 0
    num_shapes = np.random.randint(NUM_SHAPES_RANGE[0], NUM_SHAPES_RANGE[1] + 1)

    for _ in range(num_shapes):
        if current_mask_pixels >= target_mask_pixels:
            break
        _generate_random_mask_shape(draw, width, height, mask_ratio)
        # Estimate added pixels (approximate)
        current_mask_pixels += np.random.randint(500, 2000)

    # Convert to numpy array
    mask_array = np.array(mask)

    # Compute metrics on the mask itself (as a proxy for complexity)
    # We use the mask as a "texture" to compute gradient variance and entropy
    mask_tensor = torch.from_numpy(mask_array).float() / 255.0

    grad_var = _calculate_gradient_variance(mask_tensor)
    tex_ent = _calculate_texture_entropy(mask_tensor)

    metrics = {
        'gradient_variance': grad_var,
        'texture_entropy': tex_ent,
        'mask_ratio': float(np.sum(mask_array > 0) / total_pixels),
        'num_shapes': num_shapes
    }

    return mask_array, metrics


def generate_mask_batch(
    num_images: int,
    image_size: Tuple[int, int],
    output_dir: Optional[Path] = None,
    seed: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Generate a batch of synthetic masks with varying complexity.

    Args:
        num_images: Number of masks to generate
        image_size: Tuple (width, height) for each mask
        output_dir: Directory to save masks (optional)
        seed: Random seed for reproducibility

    Returns:
        List of dictionaries containing mask metadata and metrics
    """
    if seed is not None:
        set_seed(seed)

    if output_dir is None:
        output_dir = get_data_path() / 'masks'

    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    logger.info(f"Generating {num_images} synthetic masks...")

    for i in range(num_images):
        # Random complexity target
        complexity_target = np.random.uniform(0.0, 1.0)
        mask_array, metrics = generate_mask(image_size, complexity_target)

        # Save mask if output_dir is specified
        mask_path = output_dir / f"mask_{i:04d}.png"
        Image.fromarray(mask_array).save(mask_path)

        result = {
            'image_id': f"mask_{i:04d}",
            'mask_path': str(mask_path),
            'image_size': image_size,
            'complexity_target': float(complexity_target),
            'metrics': metrics
        }
        results.append(result)

        if (i + 1) % 10 == 0:
            logger.info(f"Generated {i + 1}/{num_images} masks")

    logger.info(f"Successfully generated {len(results)} masks.")

    # Register output artifact if in research mode or if explicitly needed
    if not is_ci_mode():
        register_artifact(str(output_dir), "synthetic_masks_batch")

    return results


def main():
    """
    Main entry point for generating a batch of synthetic masks.
    Produces masks and saves metrics to a JSON file.
    """
    # Configuration
    num_masks = 100
    image_size = (256, 256)
    seed = 42

    logger.info("Starting synthetic mask generation...")
    logger.info(f"Configuration: num_masks={num_masks}, image_size={image_size}, seed={seed}")

    # Generate masks
    results = generate_mask_batch(
        num_images=num_masks,
        image_size=image_size,
        seed=seed
    )

    # Save metrics to JSON
    results_path = get_results_path()
    results_path.mkdir(parents=True, exist_ok=True)
    metrics_file = results_path / 'mask_generation_metrics.json'

    import json
    with open(metrics_file, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Metrics saved to {metrics_file}")

    # Log summary
    avg_grad_var = np.mean([r['metrics']['gradient_variance'] for r in results])
    avg_tex_ent = np.mean([r['metrics']['texture_entropy'] for r in results])
    logger.info(f"Average gradient variance: {avg_grad_var:.4f}")
    logger.info(f"Average texture entropy: {avg_tex_ent:.4f}")


if __name__ == "__main__":
    main()
