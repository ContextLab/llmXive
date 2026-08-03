"""
Annotator module for selecting a stratified sample of tasks for human annotation.

This module implements the logic to randomly select a representative subset of tasks
from the filtered dataset, stratified by constraint_count bins: [5, 6, 7+].
"""

import argparse
import os
import sys
import random
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd

# Import config for paths
from config import get_paths, Paths

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_SEED = 42
DEFAULT_SAMPLE_SIZE = 50
BIN_5 = 5
BIN_6 = 6
BIN_7_PLUS = 7  # Includes all tasks with constraint_count >= 7


def load_filtered_tasks(input_path: str) -> pd.DataFrame:
    """
    Load the filtered tasks dataset from CSV.
    
    Args:
        input_path: Path to the filtered_tasks.csv file
        
    Returns:
        DataFrame containing the filtered tasks
        
    Raises:
        FileNotFoundError: If the input file does not exist
        ValueError: If required columns are missing
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Filtered tasks file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Verify required columns
    required_columns = ['task_id', 'raw_prompt', 'progressive_constraints', 'constraint_count']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise ValueError(f"Missing required columns in {input_path}: {missing_columns}")
    
    logger.info(f"Loaded {len(df)} tasks from {input_path}")
    return df


def bin_constraint(constraint_count: int) -> str:
    """
    Assign a constraint count to a bin for stratified sampling.
    
    Bins:
    - '5': constraint_count == 5
    - '6': constraint_count == 6
    - '7+': constraint_count >= 7
    
    Args:
        constraint_count: The number of progressive constraints
        
    Returns:
        Bin label as string
    """
    if constraint_count == BIN_5:
        return '5'
    elif constraint_count == BIN_6:
        return '6'
    else:  # constraint_count >= 7
        return '7+'


def select_random_sample_stratified(
    df: pd.DataFrame,
    sample_size: int,
    seed: int = DEFAULT_SEED
) -> pd.DataFrame:
    """
    Select a stratified random sample from the dataset.
    
    Stratification is by constraint_count bins: [5, 6, 7+].
    If a bin has fewer tasks than the proportional allocation,
    all available tasks from that bin are selected and a WARNING is logged.
    
    Args:
        df: DataFrame with task data including 'constraint_count'
        sample_size: Target total sample size (minimum 50)
        seed: Random seed for reproducibility
        
    Returns:
        DataFrame containing the stratified sample
    """
    random.seed(seed)
    np_random = random.Random(seed)  # Use separate RNG for pandas operations if needed
    
    # Add bin column
    df_with_bins = df.copy()
    df_with_bins['bin'] = df_with_bins['constraint_count'].apply(bin_constraint)
    
    # Calculate bin sizes
    bin_counts = df_with_bins['bin'].value_counts()
    total_tasks = len(df_with_bins)
    
    logger.info(f"Total tasks: {total_tasks}")
    logger.info(f"Bin distribution: {bin_counts.to_dict()}")
    
    # Ensure minimum sample size
    if sample_size < DEFAULT_SAMPLE_SIZE:
        logger.warning(f"Requested sample size ({sample_size}) is below minimum ({DEFAULT_SAMPLE_SIZE}). Using {DEFAULT_SAMPLE_SIZE}.")
        sample_size = DEFAULT_SAMPLE_SIZE
    
    # If total available tasks are less than sample_size, take all
    if total_tasks <= sample_size:
        logger.warning(f"Total available tasks ({total_tasks}) is less than requested sample size ({sample_size}). Selecting all tasks.")
        sample_size = total_tasks
    
    # Calculate proportional allocation per bin
    sample_per_bin = {}
    remaining_sample = sample_size
    
    # First pass: calculate ideal proportions
    for bin_label in ['5', '6', '7+']:
        bin_size = bin_counts.get(bin_label, 0)
        if bin_size > 0:
            proportion = bin_size / total_tasks
            ideal_count = int(round(proportion * sample_size))
            sample_per_bin[bin_label] = ideal_count
    
    # Adjust to ensure we hit the target sample size
    current_total = sum(sample_per_bin.values())
    if current_total != sample_size:
        # Adjust the largest bin to match target
        max_bin = max(sample_per_bin, key=sample_per_bin.get)
        sample_per_bin[max_bin] += (sample_size - current_total)
    
    # Second pass: enforce bin limits and log warnings
    final_sample_per_bin = {}
    for bin_label, target_count in sample_per_bin.items():
        actual_count = bin_counts.get(bin_label, 0)
        if target_count > actual_count:
            logger.warning(f"Bin '{bin_label}' has only {actual_count} tasks, but {target_count} requested. Taking all {actual_count} available.")
            final_sample_per_bin[bin_label] = actual_count
        else:
            final_sample_per_bin[bin_label] = target_count
    
    # Select samples from each bin
    selected_samples = []
    for bin_label, count in final_sample_per_bin.items():
        bin_df = df_with_bins[df_with_bins['bin'] == bin_label]
        
        if count == 0:
            logger.info(f"Bin '{bin_label}': No samples selected")
            continue
        
        if count >= len(bin_df):
            # Take all
            bin_sample = bin_df.copy()
            logger.info(f"Bin '{bin_label}': Taking all {len(bin_sample)} tasks")
        else:
            # Random sample without replacement
            bin_sample = bin_df.sample(n=count, random_state=seed)
            logger.info(f"Bin '{bin_label}': Randomly selected {count} tasks")
        
        selected_samples.append(bin_sample)
    
    # Combine samples
    if not selected_samples:
        logger.warning("No samples were selected. Returning empty DataFrame.")
        return pd.DataFrame(columns=df.columns)
    
    result_df = pd.concat(selected_samples, ignore_index=True)
    
    # Drop the temporary bin column
    result_df = result_df.drop(columns=['bin'])
    
    # Shuffle the final result
    result_df = result_df.sample(frac=1, random_state=seed).reset_index(drop=True)
    
    logger.info(f"Total sample size: {len(result_df)}")
    return result_df


def save_annotation_sample(df: pd.DataFrame, output_path: str) -> None:
    """
    Save the annotation sample to CSV with the required schema.
    
    Output Schema:
    - task_id: string
    - raw_prompt: string
    - constraint_list: string representation of the list
    - constraint_count: integer
    
    Args:
        df: DataFrame containing the sample
        output_path: Path to write the output CSV
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")
    
    # Prepare the output DataFrame with required columns
    output_df = pd.DataFrame()
    output_df['task_id'] = df['task_id']
    output_df['raw_prompt'] = df['raw_prompt']
    
    # Convert progressive_constraints to a string representation for the CSV
    # The column is named 'constraint_list' in the output schema
    if 'progressive_constraints' in df.columns:
        output_df['constraint_list'] = df['progressive_constraints'].apply(
            lambda x: str(x) if isinstance(x, (list, str)) else x
        )
    else:
        # Fallback if column name differs
        output_df['constraint_list'] = ''
        logger.warning("Column 'progressive_constraints' not found. Using empty list for constraint_list.")
    
    output_df['constraint_count'] = df['constraint_count']
    
    # Save to CSV
    output_df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(output_df)} tasks to {output_path}")


def main():
    """Main entry point for the annotator CLI."""
    parser = argparse.ArgumentParser(
        description='Select a stratified random sample of tasks for human annotation.'
    )
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Path to the input filtered_tasks.csv file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Path to the output annotation_sample.csv file. Defaults to data/processed/annotation_sample.csv'
    )
    parser.add_argument(
        '--sample-size',
        type=int,
        default=DEFAULT_SAMPLE_SIZE,
        help=f'Target sample size (minimum {DEFAULT_SAMPLE_SIZE}). Default: {DEFAULT_SAMPLE_SIZE}'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=DEFAULT_SEED,
        help=f'Random seed for reproducibility. Default: {DEFAULT_SEED}'
    )
    
    args = parser.parse_args()
    
    # Determine output path
    if args.output is None:
        paths = get_paths()
        args.output = str(paths.DATA_PROCESSED / 'annotation_sample.csv')
    
    logger.info(f"Starting annotation sample selection")
    logger.info(f"Input: {args.input}")
    logger.info(f"Output: {args.output}")
    logger.info(f"Target sample size: {args.sample_size}")
    logger.info(f"Random seed: {args.seed}")
    
    try:
        # Load data
        df = load_filtered_tasks(args.input)
        
        # Check if we have enough data
        if len(df) == 0:
            logger.error("No tasks found in the input file.")
            sys.exit(1)
        
        # Select stratified sample
        sample_df = select_random_sample_stratified(
            df,
            sample_size=args.sample_size,
            seed=args.seed
        )
        
        # Check if sample was generated
        if len(sample_df) == 0:
            logger.error("Failed to generate a sample. The input file may be empty or malformed.")
            sys.exit(1)
        
        # Save the sample
        save_annotation_sample(sample_df, args.output)
        
        logger.info("Annotation sample selection completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Value error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
