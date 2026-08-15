"""
T047: Critical Data Generation for Hybrid Inference Simulation.

Generates and logs the specific 'forced skip' ground truth artifact 
`data/processed/counterfactual_indices.parquet` containing frame indices 
for a randomized subset (>= 5% of total) forced to be skipped.

Uses a fixed seed SEED=42 for reproducibility.

Dependency: T014 (must produce data/processed/sampled_dataset.parquet)
"""
import os
import sys
import argparse
import logging
import random
from pathlib import Path
from typing import List, Optional

import pandas as pd
import numpy as np

# Project root setup
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
INPUT_FILE = DATA_PROCESSED_DIR / "sampled_dataset.parquet"
OUTPUT_FILE = DATA_PROCESSED_DIR / "counterfactual_indices.parquet"
MIN_PERCENTAGE = 0.05
SEED = 42

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def load_sampled_dataset(path: Path) -> pd.DataFrame:
    """Load the sampled dataset produced by T014."""
    if not path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {path}. "
            "Ensure T014 (preprocess.py) has completed successfully."
        )
    logger.info(f"Loading sampled dataset from {path}")
    df = pd.read_parquet(path)
    logger.info(f"Loaded dataset with {len(df)} frames.")
    return df

def generate_counterfactual_indices(
    df: pd.DataFrame, 
    seed: int, 
    min_percentage: float
) -> List[int]:
    """
    Generate indices for a randomized subset of frames to be forced-skipped.
    
    Args:
        df: The input DataFrame.
        seed: Random seed for reproducibility.
        min_percentage: Minimum percentage of total frames to select.
    
    Returns:
        List of integer indices.
    """
    total_frames = len(df)
    min_count = int(total_frames * min_percentage)
    
    # Ensure we select at least 1 frame if dataset is non-empty
    target_count = max(min_count, 1)
    
    logger.info(f"Total frames: {total_frames}")
    logger.info(f"Minimum selection count ({min_percentage*100}%): {min_count}")
    logger.info(f"Selecting {target_count} frames for forced skip.")
    
    # Set seed for reproducibility
    random.seed(seed)
    np.random.seed(seed)
    
    # Generate random indices
    all_indices = list(range(total_frames))
    selected_indices = random.sample(all_indices, target_count)
    
    # Sort for consistency in logging/checking
    selected_indices.sort()
    
    logger.info(f"Generated {len(selected_indices)} counterfactual indices.")
    return selected_indices

def save_counterfactual_indices(indices: List[int], path: Path) -> None:
    """Save the generated indices to a Parquet file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create a DataFrame with the indices
    df_out = pd.DataFrame({
        "frame_index": indices,
        "is_forced_skip": True
    })
    
    logger.info(f"Saving counterfactual indices to {path}")
    df_out.to_parquet(path, index=False)
    
    # Verify output
    if not path.exists():
        raise RuntimeError(f"Failed to create output file: {path}")
    
    file_size_kb = path.stat().st_size / 1024
    logger.info(f"Saved {len(indices)} indices to {path} ({file_size_kb:.2f} KB)")

def main():
    parser = argparse.ArgumentParser(
        description="Generate counterfactual indices for hybrid inference simulation (T047)."
    )
    parser.add_argument(
        "--input", 
        type=str, 
        default=str(INPUT_FILE),
        help=f"Path to sampled_dataset.parquet (default: {INPUT_FILE})"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=str(OUTPUT_FILE),
        help=f"Path for output counterfactual_indices.parquet (default: {OUTPUT_FILE})"
    )
    parser.add_argument(
        "--seed", 
        type=int, 
        default=SEED,
        help=f"Random seed (default: {SEED})"
    )
    parser.add_argument(
        "--min-percentage", 
        type=float, 
        default=MIN_PERCENTAGE,
        help=f"Minimum percentage of frames to select (default: {MIN_PERCENTAGE})"
    )
    
    args = parser.parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    try:
        # Load data
        df = load_sampled_dataset(input_path)
        
        # Generate indices
        indices = generate_counterfactual_indices(
            df, 
            seed=args.seed, 
            min_percentage=args.min_percentage
        )
        
        # Save results
        save_counterfactual_indices(indices, output_path)
        
        # Verification assertion
        total_frames = len(df)
        assert len(indices) >= args.min_percentage * total_frames, (
            f"Selection count {len(indices)} is less than required {args.min_percentage * total_frames}"
        )
        
        logger.info("T047 completed successfully. Verification passed.")
        
    except FileNotFoundError as e:
        logger.error(f"Input data missing: {e}")
        sys.exit(1)
    except AssertionError as e:
        logger.error(f"Verification failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()