import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, List, Optional, Dict, Any
from loguru import logger
from src.utils.logging import get_logger
from src.utils.validators import validate_dataframe_schema, check_required_fields

logger = get_logger()

def load_interactions(file_path: str) -> pd.DataFrame:
    """
    Load interaction data from a CSV file.
    
    Args:
        file_path: Path to the interactions CSV file.
        
    Returns:
        DataFrame with interaction data.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or has no valid rows.
    """
    path = Path(file_path)
    if not path.exists():
        logger.error(f"Missing Genome/Interaction file not found: {file_path}")
        raise FileNotFoundError(f"Interaction file not found: {file_path}")
    
    df = pd.read_csv(path)
    
    if df.empty:
        logger.error(f"Zero-Feature Pathogen: Interaction file is empty: {file_path}")
        raise ValueError(f"Interaction file is empty: {file_path}")
        
    logger.info(f"Loaded {len(df)} interactions from {file_path}")
    return df

def filter_unknown_labels(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out rows with 'unknown' interaction labels.
    
    Args:
        df: Input DataFrame with interaction labels.
        
    Returns:
        Filtered DataFrame.
    """
    initial_count = len(df)
    df = df[df['interaction_label'] != 'unknown'].reset_index(drop=True)
    removed_count = initial_count - len(df)
    
    if removed_count > 0:
        logger.info(f"Removed {removed_count} rows with 'unknown' labels")
        
    return df

def load_valid_pathogens(file_path: str) -> List[str]:
    """
    Load list of valid pathogen IDs from a JSON file.
    
    Args:
        file_path: Path to the JSON file containing valid pathogens.
        
    Returns:
        List of pathogen IDs.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty.
    """
    path = Path(file_path)
    if not path.exists():
        logger.error(f"Missing Genome/Interaction file not found: {file_path}")
        raise FileNotFoundError(f"Valid pathogens file not found: {file_path}")
        
    with open(path, 'r') as f:
        data = json.load(f)
        
    if not data:
        logger.error(f"Zero-Feature Pathogen: Valid pathogens list is empty: {file_path}")
        raise ValueError(f"Valid pathogens list is empty: {file_path}")
        
    logger.info(f"Loaded {len(data)} valid pathogens from {file_path}")
    return data

def split_pathogen_stratified(
    df: pd.DataFrame, 
    valid_pathogens: List[str], 
    test_size: float = 0.2, 
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split data into train and validation sets, stratified by pathogen.
    
    Args:
        df: Input DataFrame with interactions.
        valid_pathogens: List of valid pathogen IDs.
        test_size: Proportion of data to include in the test split.
        random_state: Random seed for reproducibility.
        
    Returns:
        Tuple of (train_df, val_df).
        
    Raises:
        ValueError: If splitting results in empty sets.
    """
    # Filter to valid pathogens
    df = df[df['pathogen_id'].isin(valid_pathogens)].reset_index(drop=True)
    
    if df.empty:
        logger.error("Zero-Feature Pathogen: No interactions found for valid pathogens after filtering")
        raise ValueError("No interactions found for valid pathogens after filtering")
        
    # Group by pathogen and split
    pathogen_groups = df.groupby('pathogen_id')
    
    train_dfs = []
    val_dfs = []
    
    for pathogen_id, group in pathogen_groups:
        # Split interactions for this pathogen
        if len(group) < 2:
            # If only one interaction, put all in train
            train_dfs.append(group)
        else:
            train_group = group.sample(frac=1 - test_size, random_state=random_state)
            val_group = group.drop(train_group.index)
            
            if not train_group.empty:
                train_dfs.append(train_group)
            if not val_group.empty:
                val_dfs.append(val_group)
    
    if not train_dfs:
        logger.error("Zero-Feature Pathogen: Training set is empty after splitting")
        raise ValueError("Training set is empty after splitting")
        
    if not val_dfs:
        logger.warning("No validation data available after splitting")
        val_df = pd.DataFrame(columns=df.columns)
    else:
        val_df = pd.concat(val_dfs, ignore_index=True)
        
    train_df = pd.concat(train_dfs, ignore_index=True)
    
    logger.info(f"Split data: {len(train_df)} train, {len(val_df)} validation")
    return train_df, val_df

def save_split_metadata(
    train_df: pd.DataFrame, 
    val_df: pd.DataFrame, 
    output_dir: str, 
    filename_prefix: str = "split_metadata"
) -> Dict[str, str]:
    """
    Save metadata about the train/validation split.
    
    Args:
        train_df: Training DataFrame.
        val_df: Validation DataFrame.
        output_dir: Directory to save metadata files.
        filename_prefix: Prefix for output filenames.
        
    Returns:
        Dictionary of output file paths.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    metadata = {
        "train_path": str(output_path / f"{filename_prefix}_train.json"),
        "val_path": str(output_path / f"{filename_prefix}_val.json"),
        "stats": {
            "train_count": len(train_df),
            "val_count": len(val_df),
            "train_pathogens": train_df['pathogen_id'].nunique() if not train_df.empty else 0,
            "val_pathogens": val_df['pathogen_id'].nunique() if not val_df.empty else 0
        }
    }
    
    # Save train metadata
    train_meta = {
        "pathogen_ids": train_df['pathogen_id'].unique().tolist() if not train_df.empty else [],
        "host_ids": train_df['host_id'].unique().tolist() if not train_df.empty else []
    }
    with open(metadata["train_path"], 'w') as f:
        json.dump(train_meta, f, indent=2)
        
    # Save val metadata
    val_meta = {
        "pathogen_ids": val_df['pathogen_id'].unique().tolist() if not val_df.empty else [],
        "host_ids": val_df['host_id'].unique().tolist() if not val_df.empty else []
    }
    with open(metadata["val_path"], 'w') as f:
        json.dump(val_meta, f, indent=2)
        
    # Save stats
    stats_path = output_path / f"{filename_prefix}_stats.json"
    with open(stats_path, 'w') as f:
        json.dump(metadata["stats"], f, indent=2)
        
    metadata["stats_path"] = str(stats_path)
    logger.info(f"Saved split metadata to {output_dir}")
    
    return metadata

def run_preprocessing_pipeline(
    interactions_file: str,
    valid_pathogens_file: str,
    output_dir: str,
    test_size: float = 0.2,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Run the complete preprocessing pipeline with error handling for edge cases.
    
    This function:
    1. Loads interactions and valid pathogens
    2. Filters unknown labels
    3. Splits data stratified by pathogen
    4. Saves metadata
    
    Args:
        interactions_file: Path to interactions CSV.
        valid_pathogens_file: Path to valid pathogens JSON.
        output_dir: Directory for output files.
        test_size: Proportion for validation split.
        random_state: Random seed.
        
    Returns:
        Dictionary containing paths to output files and statistics.
        
    Raises:
        FileNotFoundError: If input files are missing.
        ValueError: If data is empty or splitting fails.
    """
    logger.info("Starting preprocessing pipeline")
    
    try:
        # Load interactions
        logger.info(f"Loading interactions from {interactions_file}")
        interactions_df = load_interactions(interactions_file)
        
        # Load valid pathogens
        logger.info(f"Loading valid pathogens from {valid_pathogens_file}")
        valid_pathogens = load_valid_pathogens(valid_pathogens_file)
        
        # Filter unknown labels
        logger.info("Filtering unknown labels")
        filtered_df = filter_unknown_labels(interactions_df)
        
        if filtered_df.empty:
            logger.error("Zero-Feature Pathogen: All interactions were 'unknown'")
            raise ValueError("All interactions were 'unknown' labels")
        
        # Split data
        logger.info("Splitting data stratified by pathogen")
        train_df, val_df = split_pathogen_stratified(
            filtered_df, 
            valid_pathogens, 
            test_size=test_size, 
            random_state=random_state
        )
        
        # Save metadata
        metadata = save_split_metadata(train_df, val_df, output_dir)
        
        logger.info("Preprocessing pipeline completed successfully")
        
        return {
            "train_df": train_df,
            "val_df": val_df,
            "metadata": metadata
        }
        
    except FileNotFoundError as e:
        logger.error(f"Missing Genome/Interaction file error: {str(e)}")
        raise
    except ValueError as e:
        logger.error(f"Zero-Feature Pathogen error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in preprocessing pipeline: {str(e)}")
        raise