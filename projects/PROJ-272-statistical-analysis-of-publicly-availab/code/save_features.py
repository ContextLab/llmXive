"""
Save processed feature matrix to data/processed/features.csv with metadata.

This module loads the computed features (lexical, syntactic, semantic) and
embeddings from T022, T023, T024, merges them with participant metadata,
and saves the final feature matrix to data/processed/features.csv.
"""
import logging
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
import numpy as np

from config import get_path, ensure_dirs
from features import process_dataset, main as features_main
from utils import get_logger

logger = get_logger(__name__)


def load_embeddings(embeddings_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load embeddings from data/processed/embeddings.npy and convert to DataFrame.
    
    Args:
        embeddings_path: Path to embeddings file. Defaults to config path.
        
    Returns:
        DataFrame with embedding columns (embedding_0, embedding_1, ..., embedding_383)
    """
    if embeddings_path is None:
        embeddings_path = str(get_path("data_processed", "embeddings.npy"))
    
    if not os.path.exists(embeddings_path):
        raise FileNotFoundError(
            f"Embeddings file not found at {embeddings_path}. "
            "Please run feature extraction (T024) first."
        )
    
    logger.info(f"Loading embeddings from {embeddings_path}")
    embeddings = np.load(embeddings_path)
    
    if embeddings.ndim != 2:
        raise ValueError(
            f"Expected 2D embeddings array, got shape {embeddings.shape}"
        )
    
    # Create column names for each embedding dimension
    n_features = embeddings.shape[1]
    col_names = [f"embedding_{i}" for i in range(n_features)]
    
    embeddings_df = pd.DataFrame(embeddings, columns=col_names)
    logger.info(f"Loaded embeddings with shape {embeddings.shape}")
    
    return embeddings_df


def load_feature_matrix(features_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load the feature matrix from the features module output.
    
    This assumes process_dataset() has been run and generated the feature
    data in memory or via a temporary file. We'll call process_dataset
    to get the features.
    """
    if features_path is None:
        features_path = str(get_path("data_processed", "features_temp.csv"))
    
    # Run feature extraction if needed
    if not os.path.exists(features_path):
        logger.info("Running feature extraction to generate feature matrix...")
        # The process_dataset function should have been called already
        # If not, we call it here
        try:
            features_main()
        except Exception as e:
            logger.error(f"Failed to run feature extraction: {e}")
            raise
    
    if not os.path.exists(features_path):
        # Try default path from features module
        features_path = str(get_path("data_processed", "features_temp.csv"))
    
    # If still not found, we need to extract features from the cleaned dataset
    logger.warning("Feature temp file not found, extracting features from cleaned dataset...")
    cleaned_data_path = str(get_path("data_interim", "cleaned_adress.csv"))
    
    if not os.path.exists(cleaned_data_path):
        raise FileNotFoundError(
            f"Cleaned dataset not found at {cleaned_data_path}. "
            "Please run ingestion pipeline (T016) first."
        )
    
    # Extract features using the features module
    features_df = process_dataset(cleaned_data_path, features_path)
    logger.info(f"Extracted features with shape {features_df.shape}")
    
    return features_df


def merge_features_with_metadata(
    features_df: pd.DataFrame,
    embeddings_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge feature matrix with embeddings and participant metadata.
    
    Args:
        features_df: DataFrame with lexical and syntactic features
        embeddings_df: DataFrame with semantic embeddings
        
    Returns:
        Combined DataFrame with all features
    """
    # Ensure both DataFrames have participant_id for merging
    if "participant_id" not in features_df.columns:
        raise ValueError(
            "Feature DataFrame must contain 'participant_id' column for merging"
        )
    
    if "participant_id" not in embeddings_df.columns:
        raise ValueError(
            "Embeddings DataFrame must contain 'participant_id' column for merging"
        )
    
    # Merge on participant_id
    combined_df = features_df.merge(
        embeddings_df,
        on="participant_id",
        how="inner"
    )
    
    logger.info(
        f"Merged features and embeddings: {features_df.shape} + {embeddings_df.shape} -> {combined_df.shape}"
    )
    
    return combined_df


def save_feature_matrix(
    df: pd.DataFrame,
    output_path: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save the final feature matrix to CSV with metadata.
    
    Args:
        df: DataFrame containing all features
        output_path: Path to output CSV. Defaults to config path.
        metadata: Optional metadata to save alongside the CSV
        
    Returns:
        Path to the saved CSV file
    """
    if output_path is None:
        output_path = str(get_path("data_processed", "features.csv"))
    
    # Ensure directory exists
    ensure_dirs(output_path)
    
    # Save metadata if provided
    if metadata:
        metadata_path = output_path.replace(".csv", "_metadata.json")
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Saved metadata to {metadata_path}")
    
    # Save CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Saved feature matrix to {output_path} with shape {df.shape}")
    
    return output_path


def main():
    """
    Main function to save processed feature matrix.
    
    This function:
    1. Loads the feature matrix from T022/T023
    2. Loads embeddings from T024
    3. Merges them with participant metadata
    4. Saves the final matrix to data/processed/features.csv
    """
    logger.info("Starting feature matrix save process (T025)")
    
    try:
        # Load features (lexical + syntactic)
        features_df = load_feature_matrix()
        
        # Load embeddings (semantic)
        embeddings_df = load_embeddings()
        
        # Merge features with embeddings
        # First, ensure embeddings_df has participant_id
        # The embeddings are saved as [N, 384], we need to add participant_id back
        # We'll assume the order matches the features_df
        if "participant_id" not in embeddings_df.columns:
            if "participant_id" in features_df.columns:
                embeddings_df["participant_id"] = features_df["participant_id"].values
            else:
                raise ValueError(
                    "Cannot align embeddings with features: missing participant_id in features"
                )
        
        combined_df = merge_features_with_metadata(features_df, embeddings_df)
        
        # Prepare metadata
        metadata = {
            "source_files": [
                "data/interim/cleaned_adress.csv",
                "data/processed/embeddings.npy"
            ],
            "feature_categories": {
                "lexical": ["ttr", "mtld", "noun_verb_ratio"],
                "syntactic": ["mean_clause_length", "t_unit_count"],
                "semantic": [f"embedding_{i}" for i in range(384)]
            },
            "total_features": len(combined_df.columns),
            "total_participants": len(combined_df),
            "timestamp": pd.Timestamp.now().isoformat()
        }
        
        # Save final feature matrix
        output_path = save_feature_matrix(combined_df, metadata=metadata)
        
        logger.info(f"Successfully saved feature matrix to {output_path}")
        logger.info(f"Total features: {metadata['total_features']}")
        logger.info(f"Total participants: {metadata['total_participants']}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to save feature matrix: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
