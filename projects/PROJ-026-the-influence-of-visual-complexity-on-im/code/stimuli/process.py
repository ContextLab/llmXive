import os
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
from config import get_project_root, get_data_path
from utils.logging import get_logger
from stimuli.metrics import process_image_vectorized
from stimuli.validate import get_valid_images

logger = get_logger(__name__)

def categorize_complexity(df: pd.DataFrame, n_bins: int = 3) -> pd.DataFrame:
    """
    Categorize images into Low/Medium/High complexity based on computed scores.
    
    Uses pandas.qcut to create quantile-based bins.
    
    Args:
        df: DataFrame containing at least 'edge_density', 'entropy', 'fractal_dim'
        n_bins: Number of bins to create (default 3 for Low/Medium/High)
        
    Returns:
        DataFrame with added 'complexity_category' column
    """
    if df.empty:
        logger.warning("Empty DataFrame provided to categorize_complexity")
        return df

    # We use the mean of the three normalized metrics for categorization
    # First, normalize each metric to [0, 1] range
    metrics = ['edge_density', 'entropy', 'fractal_dim']
    
    # Check if all metrics exist
    if not all(m in df.columns for m in metrics):
        raise ValueError(f"DataFrame must contain columns: {metrics}")
        
    df_normalized = df.copy()
    for metric in metrics:
        min_val = df_normalized[metric].min()
        max_val = df_normalized[metric].max()
        if max_val - min_val == 0:
            # If all values are the same, set to 0.5
            df_normalized[metric] = 0.5
        else:
            df_normalized[metric] = (df_normalized[metric] - min_val) / (max_val - min_val)
    
    # Calculate composite score (mean of normalized metrics)
    df_normalized['composite_score'] = df_normalized[metrics].mean(axis=1)
    
    # Use qcut to create bins
    # Handle edge case where all values are identical
    try:
        df['complexity_category'] = pd.qcut(
            df_normalized['composite_score'], 
            q=n_bins, 
            labels=['Low', 'Medium', 'High'],
            duplicates='drop'
        )
        
        # If duplicates='drop' resulted in fewer bins than requested, 
        # manually assign based on percentiles
        if df['complexity_category'].nunique() < n_bins:
            logger.warning(f"Only {df['complexity_category'].nunique()} unique categories found. "
                         "Using manual percentile assignment.")
            percentiles = np.linspace(0, 100, n_bins + 1)
            df['complexity_category'] = pd.cut(
                df_normalized['composite_score'],
                bins=percentiles,
                labels=['Low', 'Medium', 'High'][:n_bins]
            )
            
    except ValueError as e:
        logger.error(f"qcut failed: {e}. Falling back to manual binning.")
        # Fallback: manual percentile-based binning
        percentiles = np.linspace(0, 100, n_bins + 1)
        df['complexity_category'] = pd.cut(
            df_normalized['composite_score'],
            bins=percentiles,
            labels=['Low', 'Medium', 'High'][:n_bins]
        )
        
    return df

def process_stimuli_batch(stimuli_dir: str, output_path: str) -> pd.DataFrame:
    """
    Batch process stimuli images and output complexity scores with categories.
    
    Args:
        stimuli_dir: Path to directory containing stimuli images
        output_path: Path to save the output CSV
        
    Returns:
        DataFrame with complexity metrics and categories
    """
    stimuli_path = Path(stimuli_dir)
    if not stimuli_path.exists():
        raise FileNotFoundError(f"Stimuli directory not found: {stimuli_path}")
        
    logger.info(f"Processing stimuli from: {stimuli_path}")
    
    # Get valid images
    valid_images = get_valid_images(stimuli_path)
    logger.info(f"Found {len(valid_images)} valid images")
    
    if not valid_images:
        logger.warning("No valid images found to process")
        # Create empty DataFrame with correct schema
        df = pd.DataFrame(columns=['filename', 'edge_density', 'entropy', 'fractal_dim', 'complexity_category'])
        df.to_csv(output_path, index=False)
        return df
        
    results = []
    for img_path in valid_images:
        try:
            # Process image
            edge_density, entropy, fractal_dim = process_image_vectorized(str(img_path))
            
            results.append({
                'filename': img_path.name,
                'edge_density': edge_density,
                'entropy': entropy,
                'fractal_dim': fractal_dim
            })
        except Exception as e:
            logger.error(f"Failed to process {img_path.name}: {e}")
            continue
            
    if not results:
        logger.warning("No images were successfully processed")
        df = pd.DataFrame(columns=['filename', 'edge_density', 'entropy', 'fractal_dim', 'complexity_category'])
        df.to_csv(output_path, index=False)
        return df
        
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Categorize complexity
    df = categorize_complexity(df)
    
    # Save to CSV
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    logger.info(f"Saved results to {output_file}")
    
    return df

def main():
    """Main entry point for batch processing."""
    root = get_project_root()
    stimuli_dir = root / "data" / "raw" / "stimuli"
    output_path = root / "data" / "processed" / "complexity_scores.csv"
    
    process_stimuli_batch(str(stimuli_dir), str(output_path))

if __name__ == "__main__":
    main()