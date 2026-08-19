import os
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import numpy as np

from .metrics import calculate_edge_density, calculate_entropy, calculate_fractal_dim
from .validate import get_invalid_images
from ..config import get_project_root, get_data_path
from ..utils.logging import get_logger

logger = get_logger(__name__)


def categorize_complexity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Categorize images into 'Low' or 'High' complexity based on median scores.
    
    This function calculates the median for each complexity metric (edge_density, 
    entropy, fractal_dim) and categorizes images based on whether their scores
    are <= median (Low) or > median (High).
    
    Args:
        df: DataFrame with complexity metrics columns.
        
    Returns:
        DataFrame with added 'complexity_category' column.
    """
    logger.info("Calculating median thresholds for complexity categorization")
    
    # Calculate median for each metric
    edge_median = df['edge_density'].median()
    entropy_median = df['entropy'].median()
    fractal_median = df['fractal_dim'].median()
    
    logger.info(f"Edge density median: {edge_median:.6f}")
    logger.info(f"Entropy median: {entropy_median:.6f}")
    logger.info(f"Fractal dimension median: {fractal_median:.6f}")
    
    # Log thresholds to file for reproducibility (Constitution Principle IV)
    log_path = Path(get_project_root()) / "logs" / "categorization_threshold.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'w') as f:
        f.write(f"Edge density median: {edge_median}\n")
        f.write(f"Entropy median: {entropy_median}\n")
        f.write(f"Fractal dimension median: {fractal_median}\n")
    
    # Categorize based on median (using edge_density as primary metric)
    def categorize(row):
        if pd.isna(row['edge_density']):
            return 'skipped'
        return 'Low' if row['edge_density'] <= edge_median else 'High'
    
    df['complexity_category'] = df.apply(categorize, axis=1)
    return df


def process_stimuli_batch(
    stimuli_dir: Optional[str] = None,
    output_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Batch process all images in the stimuli directory.
    
    Iterates through data/raw/stimuli/, computes metrics for valid images,
    and outputs a CSV with all images (valid and skipped).
    
    Args:
        stimuli_dir: Path to stimuli directory. Defaults to data/raw/stimuli.
        output_path: Path for output CSV. Defaults to data/processed/complexity_scores_raw.csv.
        
    Returns:
        DataFrame containing all processed results.
        
    Raises:
        FileNotFoundError: If stimuli directory does not exist.
    """
    project_root = get_project_root()
    stimuli_dir = Path(stimuli_dir) if stimuli_dir else project_root / get_data_path() / "raw" / "stimuli"
    output_path = Path(output_path) if output_path else project_root / get_data_path() / "processed" / "complexity_scores_raw.csv"
    
    if not stimuli_dir.exists():
        raise FileNotFoundError(f"Stimuli directory not found: {stimuli_dir}")
    
    logger.info(f"Processing stimuli from: {stimuli_dir}")
    logger.info(f"Output will be written to: {output_path}")
    
    # Get invalid images from validation step (T016)
    invalid_images = get_invalid_images(stimuli_dir)
    logger.info(f"Found {len(invalid_images)} invalid images to skip")
    
    # Collect results
    results = []
    image_files = list(stimuli_dir.glob("*"))
    image_files = [f for f in image_files if f.is_file()]
    
    logger.info(f"Found {len(image_files)} total files in stimuli directory")
    
    for img_path in image_files:
        filename = img_path.name
        
        # Check if image is invalid (corrupted)
        if filename in invalid_images:
            logger.info(f"Skipping corrupted image: {filename}")
            results.append({
                'filename': filename,
                'edge_density': np.nan,
                'entropy': np.nan,
                'fractal_dim': np.nan,
                'status': 'skipped'
            })
            continue
        
        # Compute metrics for valid images
        try:
            logger.debug(f"Processing image: {filename}")
            
            edge_density = calculate_edge_density(img_path)
            entropy_val = calculate_entropy(img_path)
            fractal_dim = calculate_fractal_dim(img_path)
            
            results.append({
                'filename': filename,
                'edge_density': edge_density,
                'entropy': entropy_val,
                'fractal_dim': fractal_dim,
                'status': 'valid'
            })
            
        except Exception as e:
            logger.error(f"Error processing {filename}: {str(e)}")
            results.append({
                'filename': filename,
                'edge_density': np.nan,
                'entropy': np.nan,
                'fractal_dim': np.nan,
                'status': 'skipped'
            })
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Successfully wrote {len(df)} rows to {output_path}")
    
    return df


def main():
    """Main entry point for batch processing."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        df = process_stimuli_batch()
        
        # Log summary statistics
        valid_count = (df['status'] == 'valid').sum()
        skipped_count = (df['status'] == 'skipped').sum()
        
        logger.info(f"Processing complete: {valid_count} valid, {skipped_count} skipped")
        
        if valid_count > 0:
            valid_df = df[df['status'] == 'valid']
            logger.info(f"Mean edge density: {valid_df['edge_density'].mean():.6f}")
            logger.info(f"Mean entropy: {valid_df['entropy'].mean():.6f}")
            logger.info(f"Mean fractal dimension: {valid_df['fractal_dim'].mean():.6f}")
            
    except Exception as e:
        logger.error(f"Batch processing failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()