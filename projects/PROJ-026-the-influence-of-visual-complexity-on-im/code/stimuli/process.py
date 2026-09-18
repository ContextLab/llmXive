import os
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import numpy as np

from config import get_project_root, get_data_path
from utils.logging import get_logger
from stimuli.metrics import process_image_vectorized
from stimuli.validate import validate_batch, get_valid_images, get_invalid_images

logger = get_logger(__name__)


def process_stimuli_batch(
    stimuli_dir: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Process all images in the stimuli directory and compute complexity metrics.

    Args:
        stimuli_dir: Path to stimuli directory
        output_path: Path to save raw CSV (optional)

    Returns:
        DataFrame with complexity metrics
    """
    if stimuli_dir is None:
        root = get_project_root()
        stimuli_dir = root / "data" / "raw" / "stimuli"

    if not stimuli_dir.exists():
        raise FileNotFoundError(f"Stimuli directory not found: {stimuli_dir}")

    logger.info(f"Processing stimuli from {stimuli_dir}")

    # Validate images first
    valid_images, invalid_images = validate_batch(stimuli_dir)

    logger.info(f"Found {len(valid_images)} valid images, {len(invalid_images)} invalid")

    results = []

    # Process valid images
    for img_path in valid_images:
        try:
            filename = img_path.name
            edge_density, entropy_val, fractal_dim = process_image_vectorized(str(img_path))

            # Extract metadata from filename (simplified)
            # Expected format: participantID_sessionID_imageName.ext
            parts = filename.split('_')
            participant_id = parts[0] if len(parts) > 0 else 'unknown'
            session_id = parts[1] if len(parts) > 1 else 'unknown'

            results.append({
                'filename': filename,
                'edge_density': edge_density,
                'entropy': entropy_val,
                'fractal_dim': fractal_dim,
                'status': 'valid',
                'session_id': session_id,
                'participant_id': participant_id
            })

        except Exception as e:
            logger.error(f"Error processing {img_path}: {e}")
            results.append({
                'filename': img_path.name,
                'edge_density': np.nan,
                'entropy': np.nan,
                'fractal_dim': np.nan,
                'status': 'error',
                'session_id': 'unknown',
                'participant_id': 'unknown'
            })

    # Add skipped invalid images
    for img_path in invalid_images:
        parts = img_path.name.split('_')
        participant_id = parts[0] if len(parts) > 0 else 'unknown'
        session_id = parts[1] if len(parts) > 1 else 'unknown'

        results.append({
            'filename': img_path.name,
            'edge_density': np.nan,
            'entropy': np.nan,
            'fractal_dim': np.nan,
            'status': 'skipped',
            'session_id': session_id,
            'participant_id': participant_id
        })

    df = pd.DataFrame(results)

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Saved raw complexity scores to {output_path}")

    return df


def categorize_complexity(
    df: pd.DataFrame,
    metric: str = 'edge_density'
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Categorize images into Low, Medium, High complexity based on tertiles.

    Args:
        df: DataFrame with complexity metrics
        metric: Metric to use for categorization

    Returns:
        Tuple of (categorized DataFrame, thresholds dict)
    """
    # Filter valid images for categorization
    valid_df = df[df['status'] == 'valid'].copy()

    if valid_df.empty:
        raise ValueError("No valid images for categorization.")

    # Calculate tertiles
    try:
        valid_df['complexity_category'] = pd.qcut(
            valid_df[metric],
            q=3,
            labels=['Low', 'Medium', 'High'],
            duplicates='drop'
        )
    except ValueError as e:
        logger.warning(f"qcut failed: {e}. Using equal-width bins instead.")
        # Fallback to equal-width bins
        valid_df['complexity_category'] = pd.cut(
            valid_df[metric],
            bins=3,
            labels=['Low', 'Medium', 'High']
        )

    # Extract thresholds
    thresholds = {}
    if 'complexity_category' in valid_df.columns:
        # Get bin edges
        bins = pd.cut(valid_df[metric], bins=3, retbins=True)[1]
        thresholds = {
            'low_threshold': float(bins[0]),
            'medium_threshold': float(bins[1]),
            'high_threshold': float(bins[2])
        }

    # Merge categories back to original DataFrame
    df = df.merge(
        valid_df[['filename', 'complexity_category']],
        on='filename',
        how='left'
    )

    return df, thresholds


def main() -> None:
    """Main entry point for stimulus processing."""
    root = get_project_root()

    stimuli_dir = root / "data" / "raw" / "stimuli"
    raw_output = root / "data" / "processed" / "complexity_scores_raw.csv"
    final_output = root / "data" / "processed" / "complexity_scores.csv"
    log_path = root / "logs" / "categorization_threshold.log"

    # Ensure directories
    raw_output.parent.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Process batch
    df_raw = process_stimuli_batch(stimuli_dir, raw_output)

    # Categorize
    df_final, thresholds = categorize_complexity(df_raw)

    # Add final columns
    df_final['status'] = df_final['status'].fillna('skipped')

    # Save final CSV
    df_final.to_csv(final_output, index=False)
    logger.info(f"Saved final complexity scores to {final_output}")

    # Log thresholds
    with open(log_path, 'w') as f:
        f.write(f"Categorization thresholds (based on {thresholds.get('low_threshold', 'N/A')}):\n")
        for key, val in thresholds.items():
            f.write(f"{key}: {val:.4f}\n")

    logger.info(f"Logged thresholds to {log_path}")


if __name__ == "__main__":
    main()
