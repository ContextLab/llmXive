"""
Time-based train/test splitting for longitudinal calcium imaging data.

Implements FR-008: Held-out dataset split for statistical validation.
Splits data chronologically to prevent data leakage from future states.
"""

import os
import json
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

import numpy as np
import pandas as pd

from utils.logger import get_logger, log_stage_start, log_stage_end, log_memory_usage
from utils.memory_monitor import check_memory_limit, MemoryExceededError

# Configure logger
logger = get_logger(__name__)

# Default configuration
DEFAULT_TRAIN_RATIO = 0.8
DEFAULT_OUTPUT_DIR = "data/splits"
DEFAULT_RANDOM_SEED = 42


class TimeBasedSplitter:
    """
    Performs time-based train/test splitting on longitudinal data.
    
    Ensures that the training set consists of earlier time points
    and the test set consists of later time points, preventing
    temporal data leakage.
    """

    def __init__(
        self,
        train_ratio: float = DEFAULT_TRAIN_RATIO,
        random_seed: int = DEFAULT_RANDOM_SEED
    ):
        """
        Initialize the splitter.
        
        Args:
            train_ratio: Proportion of data to use for training (0.0 to 1.0).
                        Default is 0.8 (80% train, 20% test).
            random_seed: Seed for reproducibility (used for logging/metadata).
        """
        if not 0.0 < train_ratio < 1.0:
            raise ValueError(f"train_ratio must be between 0 and 1, got {train_ratio}")
        
        self.train_ratio = train_ratio
        self.test_ratio = 1.0 - train_ratio
        self.random_seed = random_seed
        self.logger = get_logger(__name__)

    def split_indices(
        self,
        n_samples: int,
        timestamps: Optional[np.ndarray] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Split indices based on time ordering.
        
        Args:
            n_samples: Total number of samples.
            timestamps: Optional array of timestamps. If provided, splits are
                       made based on time ordering. If None, uses index order.
        
        Returns:
            Tuple of (train_indices, test_indices)
        
        Raises:
            ValueError: If n_samples is too small to split.
        """
        if n_samples < 2:
            raise ValueError(f"Need at least 2 samples to split, got {n_samples}")
        
        # Calculate split point
        split_point = int(n_samples * self.train_ratio)
        
        if split_point < 1:
            raise ValueError(f"Train ratio {self.train_ratio} too small for {n_samples} samples")
        
        if split_point >= n_samples:
            raise ValueError(f"Test ratio {self.test_ratio} too small for {n_samples} samples")
        
        # Generate indices
        all_indices = np.arange(n_samples)
        
        if timestamps is not None:
            # Sort by timestamp to ensure chronological order
            sorted_indices = np.argsort(timestamps)
            train_indices = sorted_indices[:split_point]
            test_indices = sorted_indices[split_point:]
        else:
            # Use index order (assumes data is already time-ordered)
            train_indices = all_indices[:split_point]
            test_indices = all_indices[split_point:]
        
        self.logger.info(
            f"Split complete: {len(train_indices)} train samples, "
            f"{len(test_indices)} test samples (ratio: {self.train_ratio:.2f}/{self.test_ratio:.2f})"
        )
        
        return train_indices, test_indices

    def split_arrays(
        self,
        *arrays: np.ndarray,
        timestamps: Optional[np.ndarray] = None
    ) -> Tuple[Tuple[np.ndarray, ...], Tuple[np.ndarray, ...]]:
        """
        Split multiple arrays using the same indices.
        
        Args:
            *arrays: Variable number of numpy arrays to split (must have same first dimension).
            timestamps: Optional timestamps for time-based splitting.
        
        Returns:
            Tuple of ((train_arrays...), (test_arrays...))
        
        Raises:
            ValueError: If arrays have inconsistent shapes.
        """
        if not arrays:
            raise ValueError("At least one array must be provided")
        
        n_samples = arrays[0].shape[0]
        
        # Validate all arrays have same first dimension
        for i, arr in enumerate(arrays[1:], 1):
            if arr.shape[0] != n_samples:
                raise ValueError(
                    f"Array {i} has {arr.shape[0]} samples, expected {n_samples}"
                )
        
        train_indices, test_indices = self.split_indices(n_samples, timestamps)
        
        train_arrays = tuple(arr[train_indices] for arr in arrays)
        test_arrays = tuple(arr[test_indices] for arr in arrays)
        
        return train_arrays, test_arrays

    def split_dataframe(
        self,
        df: pd.DataFrame,
        time_column: Optional[str] = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Split a DataFrame based on time or index.
        
        Args:
            df: DataFrame to split.
            time_column: Optional column name containing timestamps. If provided,
                        splits are made based on time ordering.
        
        Returns:
            Tuple of (train_df, test_df)
        """
        if time_column is not None:
            if time_column not in df.columns:
                raise ValueError(f"Column '{time_column}' not found in DataFrame")
            timestamps = df[time_column].values
            train_indices, test_indices = self.split_indices(len(df), timestamps)
        else:
            train_indices, test_indices = self.split_indices(len(df))
        
        train_df = df.iloc[train_indices].reset_index(drop=True)
        test_df = df.iloc[test_indices].reset_index(drop=True)
        
        return train_df, test_df

    def save_split_metadata(
        self,
        output_dir: str,
        n_train: int,
        n_test: int,
        train_ratio: float,
        split_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Save metadata about the split to a JSON file.
        
        Args:
            output_dir: Directory to save metadata.
            n_train: Number of training samples.
            n_test: Number of test samples.
            train_ratio: Ratio used for splitting.
            split_info: Optional additional metadata.
        
        Returns:
            Path to the saved metadata file.
        """
        os.makedirs(output_dir, exist_ok=True)
        
        metadata = {
            "split_type": "time_based",
            "train_ratio": train_ratio,
            "test_ratio": 1.0 - train_ratio,
            "n_train": n_train,
            "n_test": n_test,
            "total_samples": n_train + n_test,
            "random_seed": self.random_seed,
            "timestamp": pd.Timestamp.now().isoformat()
        }
        
        if split_info:
            metadata.update(split_info)
        
        metadata_path = os.path.join(output_dir, "split_metadata.json")
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        self.logger.info(f"Split metadata saved to {metadata_path}")
        return metadata_path


def run_split(
    input_path: str,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    train_ratio: float = DEFAULT_TRAIN_RATIO,
    time_column: Optional[str] = None,
    random_seed: int = DEFAULT_RANDOM_SEED
) -> Dict[str, str]:
    """
    Main function to perform time-based splitting on a dataset.
    
    Reads data from input_path, splits it, and saves train/test sets
    along with metadata.
    
    Args:
        input_path: Path to input data file (CSV or HDF5).
        output_dir: Directory to save split outputs.
        train_ratio: Proportion of data for training.
        time_column: Name of column containing timestamps (optional).
        random_seed: Random seed for reproducibility.
    
    Returns:
        Dictionary with paths to output files.
    
    Raises:
        FileNotFoundError: If input file doesn't exist.
        ValueError: If data format is invalid.
        MemoryExceededError: If memory limit is exceeded.
    """
    log_stage_start(logger, "Time-based Split", {
        "input_path": input_path,
        "train_ratio": train_ratio,
        "time_column": time_column
    })
    
    try:
        # Check memory limit before loading
        check_memory_limit()
        
        # Load data
        if input_path.endswith('.csv'):
            df = pd.read_csv(input_path)
            is_dataframe = True
        elif input_path.endswith('.h5') or input_path.endswith('.hdf5'):
            with pd.HDFStore(input_path, 'r') as store:
                keys = store.keys()
                if not keys:
                    raise ValueError("HDF5 file is empty")
                df = store[keys[0]]
            is_dataframe = True
        else:
            raise ValueError(f"Unsupported file format: {input_path}")
        
        log_memory_usage(logger, "After loading data")
        
        # Perform split
        splitter = TimeBasedSplitter(train_ratio=train_ratio, random_seed=random_seed)
        
        if is_dataframe:
            train_df, test_df = splitter.split_dataframe(df, time_column=time_column)
            
            # Save outputs
            train_path = os.path.join(output_dir, "train.csv")
            test_path = os.path.join(output_dir, "test.csv")
            
            train_df.to_csv(train_path, index=False)
            test_df.to_csv(test_path, index=False)
            
            # Save metadata
            metadata_path = splitter.save_split_metadata(
                output_dir,
                n_train=len(train_df),
                n_test=len(test_df),
                train_ratio=train_ratio,
                split_info={
                    "input_file": input_path,
                    "time_column_used": time_column is not None,
                    "n_columns": len(df.columns)
                }
            )
        
        else:
            raise ValueError("Non-DataFrame data format not supported yet")
        
        log_stage_end(logger, "Time-based Split", {
            "train_samples": len(train_df),
            "test_samples": len(test_df),
            "output_dir": output_dir
        })
        
        return {
            "train": train_path,
            "test": test_path,
            "metadata": metadata_path
        }
        
    except MemoryExceededError:
        log_error(logger, "Memory limit exceeded during split", exc_info=True)
        raise
    except Exception as e:
        log_error(logger, f"Split failed: {str(e)}", exc_info=True)
        raise


def main():
    """
    Entry point for command-line execution.
    
    Usage:
        python -m code.data.split --input data/raw/imaging_data.csv --ratio 0.8
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Time-based train/test splitting for longitudinal data"
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to input data file (CSV or HDF5)"
    )
    parser.add_argument(
        "--output", "-o",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})"
    )
    parser.add_argument(
        "--ratio", "-r",
        type=float,
        default=DEFAULT_TRAIN_RATIO,
        help=f"Training ratio (default: {DEFAULT_TRAIN_RATIO})"
    )
    parser.add_argument(
        "--time-column", "-t",
        default=None,
        help="Column name containing timestamps (optional)"
    )
    parser.add_argument(
        "--seed", "-s",
        type=int,
        default=DEFAULT_RANDOM_SEED,
        help=f"Random seed (default: {DEFAULT_RANDOM_SEED})"
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        return 1
    
    try:
        result = run_split(
            input_path=args.input,
            output_dir=args.output,
            train_ratio=args.ratio,
            time_column=args.time_column,
            random_seed=args.seed
        )
        
        logger.info("Split completed successfully!")
        logger.info(f"Train set: {result['train']}")
        logger.info(f"Test set: {result['test']}")
        logger.info(f"Metadata: {result['metadata']}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Split failed: {str(e)}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
