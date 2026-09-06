"""
Data Ingestion Module for QM9-TS Dataset.

This module handles fetching, filtering, and processing the QM9-TS dataset
for transition-metal catalysis research.
"""
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd
from datasets import load_dataset

# Import local utilities
from ..utils.logging import get_logger
from ..utils.config import get_project_root

# Configure logger
logger = get_logger(__name__)

def fetch_dataset_from_hf(dataset_id: str = "mattwet/qm9_ts", split: str = "train") -> pd.DataFrame:
    """
    Fetch the QM9-TS dataset from HuggingFace.
    
    Args:
        dataset_id: HuggingFace dataset identifier
        split: Dataset split to load (train, test, etc.)
        
    Returns:
        DataFrame containing the dataset
    """
    logger.info(f"Fetching dataset {dataset_id} split {split} from HuggingFace...")
    try:
        dataset = load_dataset(dataset_id, split=split, streaming=False)
        df = dataset.to_pandas()
        logger.info(f"Successfully loaded {len(df)} samples from {dataset_id}")
        return df
    except Exception as e:
        logger.error(f"Failed to fetch dataset from HuggingFace: {e}")
        raise

def load_and_count_reactions(df: pd.DataFrame) -> int:
    """
    Count the number of valid reactions in the dataset.
    
    Args:
        df: DataFrame containing reaction data
        
    Returns:
        Count of valid reactions
    """
    # Assuming 'reaction_id' or similar unique identifier exists
    # If not, count rows as reactions
    if 'reaction_id' in df.columns:
        count = df['reaction_id'].nunique()
    else:
        count = len(df)
    
    logger.info(f"Counted {count} reactions in dataset")
    return count

def filter_transition_metals(df: pd.DataFrame, metals: List[str] = ["Pd", "Ni", "Cu"]) -> pd.DataFrame:
    """
    Filter dataset for reactions involving specific transition metals.
    
    Args:
        df: DataFrame containing reaction data
        metals: List of metal symbols to filter for
        
    Returns:
        Filtered DataFrame
    """
    logger.info(f"Filtering for transition metals: {metals}")
    
    # Check if metal information exists in the dataframe
    # Assuming a 'metals' column or similar exists
    if 'metals' in df.columns:
        # Filter rows where any of the target metals are present
        mask = df['metals'].apply(lambda x: any(metal in str(x) for metal in metals))
        filtered_df = df[mask]
    elif 'element_symbols' in df.columns:
        # Alternative column name
        mask = df['element_symbols'].apply(lambda x: any(metal in str(x) for metal in metals))
        filtered_df = df[mask]
    else:
        # If no metal column exists, log warning and return original
        logger.warning("No metal column found in dataset. Returning original data.")
        filtered_df = df
    
    logger.info(f"Filtered dataset contains {len(filtered_df)} samples with metals {metals}")
    return filtered_df

def handle_scarcity(count: int, threshold: int = 120, output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Handle data scarcity logic based on reaction count.
    
    If count < threshold, creates a scarcity flag file.
    
    Args:
        count: Number of valid reactions
        threshold: Minimum required reactions (default 120)
        output_path: Path to write scarcity flag JSON (optional)
        
    Returns:
        Dictionary with count and status
    """
    if output_path is None:
        project_root = get_project_root()
        output_path = project_root / "data" / "processed" / "data_scarcity_flag.json"
    
    result = {
        "count": count,
        "status": "scarcity" if count < threshold else "sufficient"
    }
    
    if count < threshold:
        logger.warning(f"Data scarcity detected: {count} reactions < {threshold} threshold.")
        logger.info(f"Writing scarcity flag to {output_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
    else:
        logger.info(f"Sufficient data: {count} reactions >= {threshold} threshold.")
    
    return result

def main():
    """
    Main entry point for data ingestion and scarcity check.
    """
    logger.info("Starting data ingestion and scarcity check...")
    
    try:
        # Fetch dataset
        df = fetch_dataset_from_hf()
        
        # Count reactions
        count = load_and_count_reactions(df)
        
        # Filter for transition metals
        filtered_df = filter_transition_metals(df)
        
        # Count filtered reactions
        filtered_count = load_and_count_reactions(filtered_df)
        
        # Handle scarcity
        result = handle_scarcity(filtered_count)
        
        logger.info(f"Ingestion complete. Final count: {filtered_count}, Status: {result['status']}")
        
    except Exception as e:
        logger.error(f"Data ingestion failed: {e}")
        raise

if __name__ == "__main__":
    main()