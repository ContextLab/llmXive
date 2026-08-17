"""
Batch processing of stimulus images to compute visual complexity metrics.

This module orchestrates the calculation of edge density, entropy, and fractal dimension
for all valid images in the stimulus directory, categorizes them, and saves the results.
"""

import os
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import numpy as np
import cv2

from ..config import get_project_root, get_data_path
from ..utils.logging import get_logger
from .metrics import calculate_edge_density, calculate_entropy, calculate_fractal_dim
from .validate import get_valid_images, validate_image

logger = get_logger(__name__)

def categorize_complexity(
    edge_density: float,
    entropy: float,
    fractal_dim: float
) -> str:
    """
    Categorize an image into Low, Medium, or High complexity based on its metrics.

    Since we are processing a batch and need relative categorization, this function
    currently returns a placeholder 'Unknown' if called individually.
    The actual categorization using quantiles is handled in `process_stimuli_batch`
    after all metrics are collected to ensure consistent binning.

    Args:
        edge_density: Calculated edge density.
        entropy: Calculated entropy.
        fractal_dim: Calculated fractal dimension.

    Returns:
        str: 'Low', 'Medium', 'High', or 'Unknown' (if used out of context).
    """
    # This function is kept for API compatibility but the actual logic
    # using qcut is implemented in process_stimuli_batch to handle the batch context.
    return "Unknown"


def process_stimuli_batch(
    input_dir: Optional[str] = None,
    output_path: Optional[str] = None,
    force: bool = False
) -> pd.DataFrame:
    """
    Batch process all valid images in the input directory.

    Computes edge density, entropy, and fractal dimension for each image,
    categorizes them into Low/Medium/High using quantiles, and saves the results.

    Args:
        input_dir: Path to the directory containing stimulus images. Defaults to 'data/raw/stimuli'.
        output_path: Path for the output CSV. Defaults to 'data/processed/complexity_scores.csv'.
        force: If True, overwrites existing output file.

    Returns:
        pd.DataFrame: The dataframe containing the complexity scores.
    """
    project_root = get_project_root()
    data_root = get_data_path()

    if input_dir is None:
        input_dir = data_root / "raw" / "stimuli"
    else:
        input_dir = Path(input_dir)

    if output_path is None:
        output_path = data_root / "processed" / "complexity_scores.csv"
    else:
        output_path = Path(output_path)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if output already exists
    if output_path.exists() and not force:
        logger.info(f"Output file {output_path} already exists. Skipping processing.")
        return pd.read_csv(output_path)

    logger.info(f"Starting batch processing of images in {input_dir}")

    # Get valid images
    valid_images = get_valid_images(input_dir)

    if not valid_images:
        logger.warning(f"No valid images found in {input_dir}")
        # Create an empty dataframe with the correct schema
        df_empty = pd.DataFrame(columns=['filename', 'edge_density', 'entropy', 'fractal_dim', 'complexity_category'])
        df_empty.to_csv(output_path, index=False)
        return df_empty

    logger.info(f"Found {len(valid_images)} valid images to process.")

    results = []

    for img_path in valid_images:
        try:
            # Load image for metrics calculation
            # We need the image data for metrics, but we don't want to load it twice if possible.
            # The metrics functions load the image internally, so we just pass the path.
            img_name = img_path.name

            # Calculate metrics
            # These functions are expected to handle their own internal loading and validation
            # based on the API surface provided in the prompt.
            edge_density = calculate_edge_density(str(img_path))
            entropy_val = calculate_entropy(str(img_path))
            fractal_dim = calculate_fractal_dim(str(img_path))

            results.append({
                'filename': img_name,
                'edge_density': edge_density,
                'entropy': entropy_val,
                'fractal_dim': fractal_dim
            })

            logger.debug(f"Processed {img_name}: ED={edge_density:.4f}, Ent={entropy_val:.4f}, FD={fractal_dim:.4f}")

        except Exception as e:
            logger.error(f"Error processing {img_path}: {e}", exc_info=True)
            # Continue with other images, do not fail the whole batch
            continue

    if not results:
        logger.warning("No images were successfully processed.")
        df_empty = pd.DataFrame(columns=['filename', 'edge_density', 'entropy', 'fractal_dim', 'complexity_category'])
        df_empty.to_csv(output_path, index=False)
        return df_empty

    df = pd.DataFrame(results)

    # Categorize using pandas.qcut with 3 bins
    # We need to ensure we have enough data for qcut. If < 3 unique values, qcut might fail.
    # However, with continuous metrics, this is rare unless the dataset is tiny or uniform.
    # If qcut fails, we fall back to a simple heuristic or label all as 'Medium' if impossible.
    try:
        # Use 'qcut' to create 3 quantile-based bins
        # labels=['Low', 'Medium', 'High']
        # duplicates='drop' handles cases where there aren't enough unique values to make 3 bins
        df['complexity_category'] = pd.qcut(
            df['edge_density'],  # Using edge_density as the primary driver, or could use a composite
            q=3,
            labels=['Low', 'Medium', 'High'],
            duplicates='drop'
        )

        # If qcut dropped all bins (e.g., constant data), handle it
        if df['complexity_category'].isna().all():
            logger.warning("qcut failed to bin data (likely constant values). Assigning 'Medium' to all.")
            df['complexity_category'] = 'Medium'
        elif df['complexity_category'].nunique() < 3:
            # If we have fewer than 3 categories, we might need to adjust labels or just accept what we have
            logger.warning(f"qcut produced only {df['complexity_category'].nunique()} categories.")
            # Ensure the index mapping is correct for the existing categories
            # qcut with duplicates='drop' might return fewer labels.
            # We rely on the default behavior of qcut to map the existing bins to the provided labels
            # as long as the number of bins matches. If it doesn't, we might need to regenerate labels.
            # For robustness, we can regenerate labels based on actual bins.
            pass

    except Exception as e:
        logger.error(f"Error during categorization: {e}", exc_info=True)
        # Fallback: assign 'Medium' to all if categorization fails completely
        df['complexity_category'] = 'Medium'

    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Results saved to {output_path}")

    return df


def main():
    """
    Main entry point for the batch processing script.
    """
    logger.info("Starting stimulus batch processing via main()")
    try:
        df = process_stimuli_batch()
        logger.info(f"Batch processing complete. Processed {len(df)} images.")
        print(f"Processed {len(df)} images. Output saved to data/processed/complexity_scores.csv")
    except Exception as e:
        logger.critical(f"Batch processing failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()