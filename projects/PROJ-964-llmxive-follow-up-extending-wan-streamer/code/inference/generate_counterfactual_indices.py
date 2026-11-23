import os
import sys
import argparse
import logging
import random
from pathlib import Path
from typing import Optional, List, Dict, Any

import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/logs/generate_counterfactual_indices.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
SEED = 42
MIN_SKIP_RATIO = 0.05  # 5%

def load_sampled_dataset(input_path: Path) -> pd.DataFrame:
    """
    Load the sampled dataset produced by T014.
    
    Args:
        input_path: Path to the sampled dataset parquet file.
        
    Returns:
        DataFrame containing the sampled dataset.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file is empty or has no frame_id column.
    """
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Ensure T014 (preprocess.py) has completed successfully."
        )
    
    logger.info(f"Loading sampled dataset from {input_path}")
    df = pd.read_parquet(input_path)
    
    if df.empty:
        raise ValueError("Input dataset is empty. Cannot generate counterfactual indices.")
    
    if 'frame_id' not in df.columns:
        raise ValueError(
            f"Input dataset missing 'frame_id' column. "
            f"Available columns: {list(df.columns)}"
        )
    
    logger.info(f"Loaded {len(df)} frames from dataset")
    return df

def generate_counterfactual_indices(
    df: pd.DataFrame, 
    seed: int = SEED, 
    min_ratio: float = MIN_SKIP_RATIO
) -> np.ndarray:
    """
    Generate random frame indices for the forced-skip counterfactual subset.
    
    This implements the randomized intervention required by FR-008 for US3.
    At least 5% of the total frames are selected using a fixed seed for reproducibility.
    
    Args:
        df: DataFrame containing the sampled dataset.
        seed: Random seed for reproducibility (default: 42).
        min_ratio: Minimum fraction of frames to select (default: 0.05).
        
    Returns:
        1D numpy array of frame IDs to be forced-skipped.
    """
    total_frames = len(df)
    min_count = int(np.ceil(total_frames * min_ratio))
    
    logger.info(f"Total frames: {total_frames}, Minimum skip count: {min_count}")
    
    # Use numpy's random Generator for better reproducibility
    rng = np.random.default_rng(seed)
    
    # Get all frame IDs
    all_frame_ids = df['frame_id'].values
    
    # Randomly sample without replacement
    selected_indices = rng.choice(
        len(all_frame_ids), 
        size=min_count, 
        replace=False
    )
    
    counterfactual_ids = all_frame_ids[selected_indices]
    
    logger.info(f"Generated {len(counterfactual_ids)} counterfactual indices "
               f"({100*len(counterfactual_ids)/total_frames:.2f}% of total)")
    
    return counterfactual_ids

def save_counterfactual_indices(
    indices: np.ndarray, 
    output_path: Path
) -> None:
    """
    Save the counterfactual indices to a parquet file.
    
    Args:
        indices: Array of frame IDs to be forced-skipped.
        output_path: Path to the output parquet file.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create DataFrame with required schema
    df_output = pd.DataFrame({
        'frame_id': indices.astype(np.int64)
    })
    
    logger.info(f"Saving {len(df_output)} counterfactual indices to {output_path}")
    df_output.to_parquet(output_path, index=False)
    
    # Verify the file was written
    if not output_path.exists():
        raise RuntimeError(f"Failed to write output file: {output_path}")
    
    logger.info(f"Successfully saved counterfactual indices to {output_path}")

def main():
    """
    Main entry point for generating counterfactual indices.
    
    This script:
    1. Loads the sampled dataset from T014
    2. Generates a randomized subset of frame indices (≥5%)
    3. Saves the indices to data/processed/counterfactual_indices.parquet
    """
    parser = argparse.ArgumentParser(
        description="Generate counterfactual indices for forced-skip intervention"
    )
    parser.add_argument(
        '--input',
        type=str,
        default='data/processed/sampled_dataset.parquet',
        help='Path to the sampled dataset parquet file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/processed/counterfactual_indices.parquet',
        help='Path to the output counterfactual indices parquet file'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=SEED,
        help=f'Random seed for reproducibility (default: {SEED})'
    )
    parser.add_argument(
        '--min-ratio',
        type=float,
        default=MIN_SKIP_RATIO,
        help=f'Minimum fraction of frames to select (default: {MIN_SKIP_RATIO})'
    )
    
    args = parser.parse_args()
    
    try:
        # Load input data
        input_path = Path(args.input)
        output_path = Path(args.output)
        
        df = load_sampled_dataset(input_path)
        
        # Generate indices
        indices = generate_counterfactual_indices(
            df, 
            seed=args.seed, 
            min_ratio=args.min_ratio
        )
        
        # Validate output
        total_frames = len(df)
        min_count = int(np.ceil(total_frames * args.min_ratio))
        
        if len(indices) < min_count:
            raise RuntimeError(
                f"Generated {len(indices)} indices, but minimum required is {min_count}"
            )
        
        # Save results
        save_counterfactual_indices(indices, output_path)
        
        # Log success
        logger.info("Counterfactual indices generation completed successfully")
        logger.info(f"Output: {output_path}")
        logger.info(f"Total frames: {total_frames}")
        logger.info(f"Counterfactual frames: {len(indices)} "
                   f"({100*len(indices)/total_frames:.2f}%)")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Value error: {e}")
        return 1
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
