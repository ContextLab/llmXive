import os
import sys
import json
import logging
import resource
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np

# Import resource monitoring from utils
from code.src.utils import check_limits, get_memory_usage_gb, get_cpu_usage_hours

logger = logging.getLogger("project")

def load_batch_corrected_data(batch_corrected_dir: Path) -> Dict[str, pd.DataFrame]:
    """
    Load batch corrected data for all tumor types.
    Returns a dictionary mapping tumor_type -> DataFrame.
    """
    data_dict = {}
    for file_path in batch_corrected_dir.glob("*_batch_corrected.csv"):
        tumor_type = file_path.stem.replace("_batch_corrected", "")
        try:
            df = pd.read_csv(file_path, index_col=0)
            data_dict[tumor_type] = df
            logger.info(f"Loaded batch corrected data for {tumor_type}: {df.shape}")
        except Exception as e:
            logger.warning(f"Failed to load {file_path}: {e}")
    return data_dict

def get_tumor_types_from_batch_corrected(batch_corrected_dir: Path) -> List[str]:
    """
    Get list of tumor types from batch corrected directory.
    """
    tumor_types = []
    for file_path in batch_corrected_dir.glob("*_batch_corrected.csv"):
        tumor_type = file_path.stem.replace("_batch_corrected", "")
        tumor_types.append(tumor_type)
    return tumor_types

def split_data_stratified(
    data: pd.DataFrame,
    metadata: pd.DataFrame,
    response_col: str = "response_label",
    test_size: float = 0.3,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split data into discovery and training sets with stratified class distribution.
    
    Args:
        data: Expression matrix (Genes x Samples)
        metadata: Metadata DataFrame with response labels
        response_col: Column name for response labels
        test_size: Proportion of samples for discovery set
        random_state: Random seed for reproducibility
        
    Returns:
        Tuple of (discovery_data, training_data, discovery_metadata, training_metadata)
    """
    logger.info(f"Stratified splitting data with test_size={test_size}, random_state={random_state}")
    
    # Ensure metadata has response labels
    if response_col not in metadata.columns:
        raise ValueError(f"Response column '{response_col}' not found in metadata")
    
    # Check for class balance
    class_counts = metadata[response_col].value_counts()
    logger.info(f"Class distribution before split: {class_counts.to_dict()}")
    
    # Perform stratified split
    from sklearn.model_selection import train_test_split
    
    # Split metadata first to get sample indices
    discovery_samples, training_samples = train_test_split(
        metadata.index,
        test_size=test_size,
        stratify=metadata[response_col],
        random_state=random_state
    )
    
    # Split data based on sample indices
    discovery_data = data[discovery_samples]
    training_data = data[training_samples]
    discovery_metadata = metadata.loc[discovery_samples]
    training_metadata = metadata.loc[training_samples]
    
    logger.info(f"Discovery set: {discovery_data.shape[1]} samples")
    logger.info(f"Training set: {training_data.shape[1]} samples")
    
    # Verify class distribution in splits
    logger.info(f"Discovery class distribution: {discovery_metadata[response_col].value_counts().to_dict()}")
    logger.info(f"Training class distribution: {training_metadata[response_col].value_counts().to_dict()}")
    
    return discovery_data, training_data, discovery_metadata, training_metadata

def save_split_data(
    discovery_data: pd.DataFrame,
    training_data: pd.DataFrame,
    discovery_metadata: pd.DataFrame,
    training_metadata: pd.DataFrame,
    output_dir: Path,
    tumor_type: str
):
    """
    Save split data to disk.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save discovery data
    discovery_path = output_dir / f"{tumor_type}_discovery_vst.csv"
    discovery_data.to_csv(discovery_path)
    logger.info(f"Saved discovery data to {discovery_path}")
    
    # Save training data
    training_path = output_dir / f"{tumor_type}_training_vst.csv"
    training_data.to_csv(training_path)
    logger.info(f"Saved training data to {training_path}")
    
    # Save discovery metadata
    discovery_meta_path = output_dir / f"{tumor_type}_discovery_metadata.csv"
    discovery_metadata.to_csv(discovery_meta_path)
    logger.info(f"Saved discovery metadata to {discovery_meta_path}")
    
    # Save training metadata
    training_meta_path = output_dir / f"{tumor_type}_training_metadata.csv"
    training_metadata.to_csv(training_meta_path)
    logger.info(f"Saved training metadata to {training_meta_path}")

def process_tumor_type_split(
    tumor_type: str,
    data: pd.DataFrame,
    metadata: pd.DataFrame,
    output_dir: Path,
    test_size: float = 0.3,
    random_state: int = 42
):
    """
    Process splitting for a single tumor type.
    Includes resource monitoring.
    """
    logger.info(f"Processing split for tumor type: {tumor_type}")
    
    # Monitor RAM usage before split
    ram_gb = get_memory_usage_gb()
    logger.info(f"Current RAM usage: {ram_gb:.2f} GB")
    
    # Check resource limits
    caps = {'cpus': 8, 'ram_gb': 16.0}
    if check_limits({'cpus': 4, 'ram_gb': ram_gb}, caps):
        logger.warning("Warning: Resource usage approaching limit during split operation")
    
    try:
        # Perform stratified split
        discovery_data, training_data, discovery_metadata, training_metadata = split_data_stratified(
            data, metadata, test_size=test_size, random_state=random_state
        )
        
        # Save split data
        save_split_data(
            discovery_data, training_data, discovery_metadata, training_metadata,
            output_dir, tumor_type
        )
        
        logger.info(f"Successfully processed split for {tumor_type}")
        
    except Exception as e:
        logger.error(f"Failed to process split for {tumor_type}: {e}")
        raise

def main():
    """
    Main entry point for preprocessing split functionality.
    This would typically be called from the pipeline orchestrator.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Example usage (would be replaced by actual pipeline logic)
    logger.info("Preprocessing split module loaded successfully")
    logger.info("Use process_tumor_type_split() to split data for each tumor type")

if __name__ == "__main__":
    main()