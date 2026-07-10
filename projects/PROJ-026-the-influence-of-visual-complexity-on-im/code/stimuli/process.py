import os
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np

from .metrics import calculate_edge_density, calculate_entropy, calculate_fractal_dim
from ..config import get_data_path

logger = logging.getLogger(__name__)

def categorize_complexity(
    edge_density: float,
    entropy: float,
    fractal_dim: float
) -> str:
    """
    Categorize an image into Low, Medium, or High complexity.
    
    Args:
        edge_density: Edge density metric.
        entropy: Entropy metric.
        fractal_dim: Fractal dimension metric.
        
    Returns:
        Complexity category string.
    """
    scores = np.array([edge_density, entropy, fractal_dim])
    mean_score = np.mean(scores)
    
    # Simple thresholding based on mean score (can be refined with clustering)
    if mean_score < 0.33:
        return "Low"
    elif mean_score < 0.66:
        return "Medium"
    else:
        return "High"

def process_stimuli_batch(
    input_dir: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Batch process stimuli images and output complexity scores.
    
    Args:
        input_dir: Directory containing input images.
        output_path: Path to save the output CSV.
        
    Returns:
        DataFrame of complexity scores.
    """
    if input_dir is None:
        data_path = get_data_path()
        input_dir = data_path / "raw" / "stimuli"
    
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    
    image_files = list(input_dir.glob("*.[jp][pn]g")) + list(input_dir.glob("*.[bp][mn]g"))
    
    if not image_files:
        logger.warning("No image files found in input directory.")
        return pd.DataFrame()
    
    results = []
    for img_file in image_files:
        try:
            logger.info(f"Processing {img_file.name}...")
            edge = calculate_edge_density(str(img_file))
            ent = calculate_entropy(str(img_file))
            frac = calculate_fractal_dim(str(img_file))
            
            category = categorize_complexity(edge, ent, frac)
            
            results.append({
                "filename": img_file.name,
                "edge_density": edge,
                "entropy": ent,
                "fractal_dim": frac,
                "complexity_category": category
            })
        except Exception as e:
            logger.error(f"Failed to process {img_file.name}: {e}", exc_info=True)
            continue
    
    df = pd.DataFrame(results)
    
    if output_path is None:
        data_path = get_data_path()
        output_path = data_path / "processed" / "complexity_scores.csv"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    
    logger.info(f"Processed {len(df)} images. Results saved to {output_path}")
    return df

def main() -> int:
    """Main entry point for stimuli processing script."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting stimuli batch processing...")
    
    try:
        process_stimuli_batch()
        return 0
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
