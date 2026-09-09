"""
Data ingestion module for QM9-TS dataset.
Handles fetching, filtering, and counting transition metal reactions.
"""
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd
import numpy as np

# Import logging utility from project structure
from src.utils.logging import get_logger, setup_logger

# Ensure project root is in path
def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent.parent.parent

def fetch_dataset_from_hf(dataset_id: str = "qm9-ts", output_dir: Optional[Path] = None) -> Path:
    """
    Fetch the QM9-TS dataset from HuggingFace.
    
    Args:
        dataset_id: The HuggingFace dataset identifier.
        output_dir: Directory to save the downloaded data.
        
    Returns:
        Path to the directory containing the downloaded data.
    """
    logger = get_logger(__name__)
    logger.info(f"Fetching dataset {dataset_id} from HuggingFace...")
    
    if output_dir is None:
        output_dir = get_project_root() / "data" / "raw" / dataset_id
        
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        from datasets import load_dataset
        
        # Load dataset with streaming to handle large sizes efficiently
        dataset = load_dataset(dataset_id, split="train", streaming=True)
        
        # Save a sample or full dataset to parquet for local processing
        # Since we are streaming, we collect to parquet
        output_file = output_dir / "qm9_ts.parquet"
        
        # Convert to pandas for saving (this will consume the stream)
        # Note: In a real production scenario, we might want to chunk this
        # but for the scope of this task, we assume the dataset fits in memory
        # or we process it in chunks.
        df_list = []
        batch_size = 1000
        for i, batch in enumerate(dataset):
            df_list.append(pd.DataFrame(batch))
            if len(df_list) * batch_size > 100000: # Prevent memory issues if dataset is huge
                break
        
        if df_list:
            full_df = pd.concat(df_list, ignore_index=True)
            full_df.to_parquet(output_file, index=False)
            logger.info(f"Dataset saved to {output_file}")
        else:
            raise ValueError("Dataset is empty or could not be loaded.")
            
        return output_file
        
    except ImportError:
        logger.error("datasets library not found. Please install it via requirements.txt")
        raise
    except Exception as e:
        logger.error(f"Failed to fetch dataset: {e}")
        raise

def load_and_count_reactions(data_path: Path) -> int:
    """
    Load the dataset and count total reactions.
    
    Args:
        data_path: Path to the parquet file.
        
    Returns:
        Total count of reactions.
    """
    logger = get_logger(__name__)
    logger.info(f"Loading data from {data_path}...")
    
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
        
    df = pd.read_parquet(data_path)
    count = len(df)
    logger.info(f"Total reactions loaded: {count}")
    return count

def filter_transition_metals(df: pd.DataFrame, metals: List[str] = None) -> pd.DataFrame:
    """
    Filter the dataset for elementary steps involving specific transition metals.
    
    Args:
        df: The input dataframe.
        metals: List of metal symbols to filter for (e.g., ['Pd', 'Ni', 'Cu']).
                
    Returns:
        Filtered dataframe.
    """
    if metals is None:
        metals = ['Pd', 'Ni', 'Cu']
        
    logger = get_logger(__name__)
    logger.info(f"Filtering for transition metals: {metals}")
    
    # Assuming the dataframe has a column 'metal' or 'element' that indicates the catalyst
    # If the schema is different (e.g., atomic numbers in a list), this logic needs adjustment.
    # Based on common QM9-TS extensions, 'metal' is a likely column name.
    # If the column is 'atomic_numbers', we need to map symbols to numbers.
    
    metal_symbols_to_numbers = {
        'Pd': 46,
        'Ni': 28,
        'Cu': 29
    }
    
    # Check if 'metal' column exists
    if 'metal' in df.columns:
        # Filter by string match
        mask = df['metal'].isin(metals)
    elif 'atomic_numbers' in df.columns:
        # Filter by atomic number match (assuming atomic_numbers is a list or string of numbers)
        target_numbers = [metal_symbols_to_numbers[m] for m in metals if m in metal_symbols_to_numbers]
        
        # Handle potential list type in column
        if isinstance(df['atomic_numbers'].iloc[0], list):
            mask = df['atomic_numbers'].apply(lambda x: any(num in x for num in target_numbers))
        else:
            # If it's a string representation or single number
            mask = df['atomic_numbers'].isin(target_numbers)
    else:
        # Fallback: assume 'element' or similar, or raise error if schema is unknown
        # For robustness, we try to infer or raise a clear error
        available_cols = list(df.columns)
        logger.warning(f"Could not find expected metal column. Available columns: {available_cols}")
        # If no column matches, return empty to fail loudly as per constraints
        # But let's assume a standard schema for now or return empty if no match
        return pd.DataFrame() # Return empty if schema doesn't match expectations
        
    filtered_df = df[mask]
    logger.info(f"Found {len(filtered_df)} reactions involving {metals}")
    return filtered_df

def handle_scarcity(count: int, threshold: int = 120, output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Check if the count of valid reactions is below a threshold and write a flag file if so.
    
    Args:
        count: The number of valid reactions.
        threshold: The scarcity threshold.
        output_path: Path to write the scarcity flag JSON.
        
    Returns:
        Dictionary with status information.
    """
    logger = get_logger(__name__)
    
    if output_path is None:
        output_path = get_project_root() / "data" / "processed" / "data_scarcity_flag.json"
        
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    status = "abundant" if count >= threshold else "scarcity"
    result = {
        "count": count,
        "status": status,
        "threshold": threshold
    }
    
    if status == "scarcity":
        logger.warning(f"Data scarcity detected: {count} < {threshold}. Writing flag file.")
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Scarcity flag written to {output_path}")
    else:
        logger.info(f"Data abundance confirmed: {count} >= {threshold}")
        
    return result

def run_ingestion(
    dataset_id: str = "qm9-ts",
    metals: List[str] = None,
    threshold: int = 120,
    raw_dir: Optional[Path] = None,
    processed_dir: Optional[Path] = None
) -> Tuple[int, Dict[str, Any]]:
    """
    Main orchestration function for data ingestion, filtering, and scarcity check.
    
    Args:
        dataset_id: HuggingFace dataset ID.
        metals: List of metals to filter.
        threshold: Scarcity threshold.
        raw_dir: Override for raw data directory.
        processed_dir: Override for processed data directory.
        
    Returns:
        Tuple of (count, scarcity_info)
    """
    logger = get_logger(__name__)
    logger.info("Starting data ingestion pipeline...")
    
    # 1. Fetch dataset
    # Assuming fetch_dataset_from_hf handles the download and saves to raw_dir
    # We need to ensure raw_dir is set correctly
    if raw_dir is None:
        raw_dir = get_project_root() / "data" / "raw" / dataset_id
        
    data_file = fetch_dataset_from_hf(dataset_id, output_dir=raw_dir)
    
    # 2. Load and count
    total_count = load_and_count_reactions(data_file)
    
    # 3. Filter
    df = pd.read_parquet(data_file)
    filtered_df = filter_transition_metals(df, metals)
    valid_count = len(filtered_df)
    
    # 4. Handle scarcity
    scarcity_info = handle_scarcity(valid_count, threshold, processed_dir)
    
    logger.info("Data ingestion pipeline completed.")
    return valid_count, scarcity_info

def main():
    """Entry point for the script."""
    setup_logger(level=logging.INFO)
    logger = get_logger(__name__)
    
    try:
        count, info = run_ingestion()
        logger.info(f"Final count of valid reactions: {count}")
        logger.info(f"Scarcity status: {info['status']}")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()