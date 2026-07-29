import os
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from PIL import Image, ImageDraw

def generate_mask(
    width: int,
    height: int,
    complexity: float = 0.5,
    seed: Optional[int] = None
) -> Tuple[Image.Image, Dict[str, float]]:
    """
    Generate a synthetic mask with specified complexity.
    Returns mask image and metrics (gradient_variance, texture_entropy).
    """
    if seed is not None:
        np.random.seed(seed)

    # Create a blank mask
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)

    # Generate random shapes based on complexity
    num_shapes = int(complexity * 10)
    for _ in range(num_shapes):
        x = np.random.randint(0, width)
        y = np.random.randint(0, height)
        w = np.random.randint(10, width // 4)
        h = np.random.randint(10, height // 4)
        draw.rectangle([x, y, x + w, y + h], fill=255)

    # Calculate metrics (simplified)
    mask_np = np.array(mask)
    # Gradient variance (approximate)
    grad_x = np.diff(mask_np, axis=1)
    grad_y = np.diff(mask_np, axis=0)
    gradient_variance = float(np.var(grad_x) + np.var(grad_y))

    # Texture entropy (approximate)
    hist, _ = np.histogram(mask_np, bins=256, range=(0, 256))
    hist = hist / hist.sum()
    hist = hist[hist > 0]
    texture_entropy = float(-np.sum(hist * np.log2(hist)))

    return mask, {"gradient_variance": gradient_variance, "texture_entropy": texture_entropy}

def generate_mask_batch(
    count: int,
    width: int = 256,
    height: int = 256,
    base_seed: int = 42
) -> List[Tuple[Image.Image, Dict[str, float]]]:
    """Generate a batch of masks."""
    results = []
    for i in range(count):
        mask, metrics = generate_mask(width, height, complexity=(i % 5 + 1) / 5.0, seed=base_seed + i)
        results.append((mask, metrics))
    return results

def main():
    """CLI entry point for mask generation."""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--output-dir", type=str, default="data/processed/masked_images")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    masks = generate_mask_batch(args.count)
    for i, (mask, metrics) in enumerate(masks):
        mask.save(output_dir / f"mask_{i}.png")
        print(f"Saved mask_{i}.png: {metrics}")

if __name__ == "__main__":
    main()
