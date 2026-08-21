"""
Generate counterfactual indices for forced skip intervention (T047).

This module implements the Critical Data Generation task for User Story 3.
It generates a randomized subset of frame indices (>= 5% of total) that will
be forced to skip during hybrid inference, using a fixed seed for reproducibility.

Dependencies:
- T014b: Must have data/processed/sampled_dataset.parquet available
"""
import os
import sys
import argparse
import logging
from pathlib import Path
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
SEED = 42
MIN_SKIP_RATIO = 0.05  # At least 5% of frames must be in the counterfactual set
INPUT_FILE = Path("data/processed/sampled_dataset.parquet")
OUTPUT_FILE = Path("data/processed/counterfactual_indices.parquet")


def load_sampled_dataset(input_path: Path) -> pd.DataFrame:
    """
    Load the sampled dataset from the previous preprocessing step.
    
    Args:
        input_path: Path to the sampled dataset Parquet file
        
    Returns:
        DataFrame containing the sampled dataset
        
    Raises:
        FileNotFoundError: If the input file does not exist
        ValueError: If the file is empty or missing required columns
    """
    if not input_path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {input_path}. "
            f"Ensure T014b (sampled_dataset.parquet) has been completed successfully."
        )
    
    df = pd.read_parquet(input_path)
    
    if df.empty:
        raise ValueError(f"Input dataset at {input_path} is empty.")
    
    if 'frame_id' not in df.columns:
        raise ValueError(
            f"Input dataset missing required column 'frame_id'. "
            f"Available columns: {list(df.columns)}"
        )
    
    logger.info(f"Loaded dataset with {len(df)} frames from {input_path}")
    return df


def generate_counterfactual_indices(df: pd.DataFrame, seed: int = SEED) -> np.ndarray:
    """
    Generate randomized frame indices for the forced skip intervention.
    
    Args:
        df: DataFrame containing the sampled dataset
        seed: Random seed for reproducibility
        
    Returns:
        NumPy array of frame indices to be forced to skip
        
    Raises:
        ValueError: If the generated sample size is less than MIN_SKIP_RATIO
    """
    rng = np.random.default_rng(seed)
    total_frames = len(df)
    min_required = int(np.ceil(total_frames * MIN_SKIP_RATIO))
    
    # Get all frame IDs
    frame_ids = df['frame_id'].values
    
    # Randomly sample indices
    num_to_sample = max(min_required, int(total_frames * MIN_SKIP_RATIO))
    selected_indices = rng.choice(frame_ids, size=num_to_sample, replace=False)
    
    logger.info(f"Total frames: {total_frames}")
    logger.info(f"Minimum required (5%): {min_required}")
    logger.info(f"Selected {len(selected_indices)} frames for counterfactual intervention")
    
    if len(selected_indices) < min_required:
        raise ValueError(
            f"Generated sample size {len(selected_indices)} is less than required "
            f"minimum {min_required} (5% of {total_frames})"
        )
    
    return selected_indices


def save_counterfactual_indices(indices: np.ndarray, output_path: Path) -> None:
    """
    Save the counterfactual indices to a Parquet file.
    
    Args:
        indices: Array of frame indices to save
        output_path: Path to save the output Parquet file
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create DataFrame with required schema
    df_output = pd.DataFrame({
        'frame_id': indices.astype(np.int64)
    })
    
    # Save to Parquet
    df_output.to_parquet(output_path, index=False)
    
    logger.info(f"Saved {len(indices)} counterfactual indices to {output_path}")
    
    # Verify output
    if not output_path.exists():
        raise RuntimeError(f"Failed to create output file: {output_path}")
    
    # Verify schema and size
    df_verify = pd.read_parquet(output_path)
    assert 'frame_id' in df_verify.columns, "Output missing 'frame_id' column"
    assert len(df_verify) == len(indices), "Output row count mismatch"
    assert df_verify['frame_id'].dtype == np.int64, "frame_id should be int64"
    
    logger.info("Output verification passed: schema and size are correct")


def main():
    """Main entry point for generating counterfactual indices."""
    parser = argparse.ArgumentParser(
        description="Generate counterfactual indices for forced skip intervention (T047)"
    )
    parser.add_argument(
        "--input",
        type=str,
        default=str(INPUT_FILE),
        help=f"Path to input sampled dataset (default: {INPUT_FILE})"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(OUTPUT_FILE),
        help=f"Path to output counterfactual indices (default: {OUTPUT_FILE})"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=SEED,
        help=f"Random seed for reproducibility (default: {SEED})"
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    try:
        # Step 1: Load the sampled dataset
        logger.info(f"Step 1: Loading sampled dataset from {input_path}")
        df = load_sampled_dataset(input_path)
        
        # Step 2: Generate counterfactual indices
        logger.info(f"Step 2: Generating counterfactual indices with seed {args.seed}")
        indices = generate_counterfactual_indices(df, seed=args.seed)
        
        # Step 3: Save the indices
        logger.info(f"Step 3: Saving counterfactual indices to {output_path}")
        save_counterfactual_indices(indices, output_path)
        
        # Final verification
        assert len(indices) >= 0.05 * len(df), \
            f"Counterfactual set size {len(indices)} is less than 5% of total {len(df)}"
        
        logger.info("=" * 60)
        logger.info("T047 COMPLETED SUCCESSFULLY")
        logger.info(f"  - Input: {input_path} ({len(df)} frames)")
        logger.info(f"  - Output: {output_path} ({len(indices)} counterfactual indices)")
        logger.info(f"  - Coverage: {len(indices) / len(df) * 100:.2f}% of total frames")
        logger.info(f"  - Seed: {args.seed}")
        logger.info("=" * 60)
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())