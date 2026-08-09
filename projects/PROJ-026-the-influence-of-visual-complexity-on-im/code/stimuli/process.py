import os
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
import cv2
from ..config import get_data_path, get_project_root
from ..utils.logging import get_logger
from .metrics import calculate_edge_density, calculate_entropy, calculate_fractal_dim

logger = get_logger(__name__)

def categorize_complexity(edge_density: float, entropy: float, fractal_dim: float) -> str:
    """
    Categorize image complexity into Low, Medium, or High.
    Uses a simple weighted sum heuristic.
    """
    score = 0.3 * edge_density + 0.4 * entropy + 0.3 * fractal_dim
    if score < 0.5:
        return "Low"
    elif score < 1.0:
        return "Medium"
    else:
        return "High"

def process_stimuli_batch(input_dir: str, output_path: str) -> pd.DataFrame:
    """
    Batch process images in input_dir and output complexity scores to output_path.
    Uses vectorized operations where possible.
    """
    input_path = Path(input_dir)
    if not input_path.exists():
        logger.error(f"Input directory {input_dir} does not exist.")
        return pd.DataFrame()
        
    image_files = list(input_path.glob("*.png")) + list(input_path.glob("*.jpg")) + list(input_path.glob("*.jpeg"))
    if not image_files:
        logger.warning(f"No image files found in {input_dir}")
        return pd.DataFrame()
        
    results = []
    
    for img_file in image_files:
        try:
            image = cv2.imread(str(img_file))
            if image is None:
                logger.warning(f"Could not read image: {img_file}")
                continue
                
            edge_density = calculate_edge_density(image)
            entropy_val = calculate_entropy(image)
            fractal_dim = calculate_fractal_dim(image)
            category = categorize_complexity(edge_density, entropy_val, fractal_dim)
            
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
    logger.info(f"Processed {len(df)} images. Output saved to {output_path}")
    return df

def main():
    """Entry point for batch processing."""
    import argparse
    parser = argparse.ArgumentParser(description="Process stimuli batch")
    parser.add_argument("--input", type=str, default="data/raw/stimuli", help="Input directory")
    parser.add_argument("--output", type=str, default="data/processed/complexity_scores.csv", help="Output file path")
    args = parser.parse_args()
    
    process_stimuli_batch(args.input, args.output)

if __name__ == "__main__":
    main()
