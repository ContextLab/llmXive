"""
Optimized batch processor for stimuli images.
Implements vectorized loops to reduce execution time.
"""
import os
import logging
import numpy as np
import cv2
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import pandas as pd

from ..config import get_data_path, get_project_root
from ..utils.logging import get_logger
from .metrics import process_image_vectorized

logger = get_logger(__name__)

def load_images_batch(image_paths: List[Path], max_images: Optional[int] = None) -> List[np.ndarray]:
    """
    Load a batch of images.
    If max_images is set, only load that many.
    """
    if max_images is not None:
        image_paths = image_paths[:max_images]
        
    images = []
    for p in image_paths:
        img = cv2.imread(str(p))
        if img is not None:
            images.append(img)
        else:
            logger.warning(f"Failed to load image: {p}")
    return images

def process_stimuli_vectorized(input_dir: str, output_path: str, max_images: Optional[int] = None) -> pd.DataFrame:
    """
    Process all images in input_dir using vectorized operations.
    This function is optimized for speed by minimizing Python loops
    and leveraging numpy/cv2 internals.
    
    Args:
        input_dir: Directory containing input images.
        output_path: Path to save the output CSV.
        max_images: Optional limit on number of images to process.
        
    Returns:
        DataFrame with complexity scores.
    """
    input_path = Path(input_dir)
    if not input_path.exists():
        logger.error(f"Input directory {input_dir} does not exist.")
        return pd.DataFrame()
        
    image_files = list(input_path.glob("*.png")) + list(input_path.glob("*.jpg")) + list(input_path.glob("*.jpeg"))
    
    if not image_files:
        logger.warning(f"No image files found in {input_dir}")
        return pd.DataFrame()
        
    if max_images is not None:
        image_files = image_files[:max_images]
        
    logger.info(f"Processing {len(image_files)} images with vectorized pipeline...")
    
    results = []
    
    for img_file in image_files:
        try:
            # Use the vectorized wrapper
            edge_density, entropy_val, fractal_dim = process_image_vectorized(cv2.imread(str(img_file)))
            category = _categorize_complexity(edge_density, entropy_val, fractal_dim)
            
            results.append({
                "filename": img_file.name,
                "edge_density": edge_density,
                "entropy": entropy_val,
                "fractal_dim": fractal_dim,
                "complexity_category": category
            })
        except Exception as e:
            logger.error(f"Error processing {img_file}: {e}")
            continue
            
    df = pd.DataFrame(results)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Vectorized processing complete. Saved {len(df)} rows to {output_path}")
    return df

def _categorize_complexity(edge_density: float, entropy: float, fractal_dim: float) -> str:
    """Helper to categorize complexity."""
    score = 0.3 * edge_density + 0.4 * entropy + 0.3 * fractal_dim
    if score < 0.5:
        return "Low"
    elif score < 1.0:
        return "Medium"
    else:
        return "High"

def main():
    """Entry point for vectorized batch processing."""
    import argparse
    parser = argparse.ArgumentParser(description="Vectorized batch processing for stimuli")
    parser.add_argument("--input", type=str, default="data/raw/stimuli", help="Input directory")
    parser.add_argument("--output", type=str, default="data/processed/complexity_scores_vectorized.csv", help="Output file path")
    parser.add_argument("--max-images", type=int, default=None, help="Max images to process")
    args = parser.parse_args()
    
    process_stimuli_vectorized(args.input, args.output, args.max_images)

if __name__ == "__main__":
    main()
