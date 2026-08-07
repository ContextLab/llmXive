import os
import csv
import logging
import argparse
import h5py
import pandas as pd
import numpy as np

from typing import Dict, List, Optional, Tuple, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/merge_datasets.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Paths based on project structure
ATTENTION_MAPS_PATH = "data/intermediate/attention_maps.h5"
FEATURES_PATH = "data/intermediate/static_features.csv"
ANOMALIES_PATH = "data/logs/anomalies.csv"
OUTPUT_PATH = "data/intermediate/merged_dataset.csv"

def load_ground_truth_labels(attention_maps_path: str) -> Dict[str, Any]:
    """
    Load ground truth labels (RTPurbo indices and attention data) from HDF5 file.
    
    Returns a dictionary mapping document_id to a dict containing:
    - 'rtpurbo_indices': list of int
    - 'attention_stats': dict of stats (if available)
    """
    if not os.path.exists(attention_maps_path):
        raise FileNotFoundError(f"Attention maps file not found: {attention_maps_path}")
    
    logger.info(f"Loading ground truth labels from {attention_maps_path}")
    
    labels_data = {}
    
    with h5py.File(attention_maps_path, 'r') as hf:
        for doc_id in hf.keys():
            doc_group = hf[doc_id]
            
            # Extract RTPurbo indices
            if 'rtpurbo_indices' in doc_group:
                indices = doc_group['rtpurbo_indices'][:]
            else:
                logger.warning(f"Document {doc_id} missing rtpurbo_indices, skipping")
                continue
            
            # Extract attention stats if available
            attention_stats = {}
            if 'attention_stats' in doc_group:
                stats_group = doc_group['attention_stats']
                for key in stats_group.keys():
                    val = stats_group[key][()]
                    # Convert numpy types to Python native types
                    if isinstance(val, (np.integer, np.floating)):
                        val = float(val)
                    attention_stats[key] = val
            
            labels_data[doc_id] = {
                'rtpurbo_indices': indices.tolist(),
                'attention_stats': attention_stats
            }
    
    logger.info(f"Loaded {len(labels_data)} document labels")
    return labels_data

def load_static_features(features_path: str) -> pd.DataFrame:
    """
    Load static features from CSV file.
    
    Returns a DataFrame with columns including:
    - doc_id
    - token_id
    - entropy
    - pos_tag
    - position
    - kenlm_perplexity
    """
    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Features file not found: {features_path}")
    
    logger.info(f"Loading static features from {features_path}")
    
    df = pd.read_csv(features_path)
    
    # Ensure doc_id and token_id are appropriate types
    if 'doc_id' in df.columns:
        df['doc_id'] = df['doc_id'].astype(str)
    if 'token_id' in df.columns:
        df['token_id'] = df['token_id'].astype(int)
    
    logger.info(f"Loaded {len(df)} feature rows for {df['doc_id'].nunique()} documents")
    return df

def load_anomalies(anomalies_path: str) -> set:
    """
    Load list of anomalous document IDs that should be excluded.
    
    Returns a set of document IDs to exclude.
    """
    if not os.path.exists(anomalies_path):
        logger.info(f"No anomalies file found at {anomalies_path}, proceeding without exclusions")
        return set()
    
    logger.info(f"Loading anomalies from {anomalies_path}")
    
    anomalies = set()
    try:
        df = pd.read_csv(anomalies_path)
        if 'doc_id' in df.columns:
            anomalies = set(df['doc_id'].astype(str).tolist())
        logger.info(f"Loaded {len(anomalies)} anomalous document IDs")
    except Exception as e:
        logger.warning(f"Could not parse anomalies file: {e}, proceeding without exclusions")
    
    return anomalies

def merge_datasets(
    labels: Dict[str, Any],
    features_df: pd.DataFrame,
    anomalies: set
) -> pd.DataFrame:
    """
    Merge ground truth labels with static features.
    
    For each token in each document:
    - Add a 'is_rtpurbo' boolean column indicating if the token was selected
    - Add 'attention_entropy' if available from attention stats
    - Exclude tokens from anomalous documents
    
    Returns a merged DataFrame.
    """
    logger.info(f"Starting merge: {len(labels)} documents, {len(features_df)} tokens")
    
    merged_rows = []
    excluded_count = 0
    
    # Process each document
    for doc_id in features_df['doc_id'].unique():
        # Check if document is anomalous
        if doc_id in anomalies:
            excluded_count += len(features_df[features_df['doc_id'] == doc_id])
            logger.info(f"Excluding anomalous document: {doc_id}")
            continue
        
        # Get ground truth for this document
        if doc_id not in labels:
            logger.warning(f"No ground truth found for document {doc_id}, skipping")
            continue
        
        doc_labels = labels[doc_id]
        rtpurbo_indices = set(doc_labels['rtpurbo_indices'])
        attention_stats = doc_labels['attention_stats']
        
        # Get document features
        doc_features = features_df[features_df['doc_id'] == doc_id]
        
        for _, row in doc_features.iterrows():
            token_id = int(row['token_id'])
            
            # Create merged row
            merged_row = row.to_dict()
            merged_row['is_rtpurbo'] = token_id in rtpurbo_indices
            
            # Add attention stats if available
            for key, value in attention_stats.items():
                merged_row[f'attention_{key}'] = value
            
            merged_rows.append(merged_row)
    
    merged_df = pd.DataFrame(merged_rows)
    
    logger.info(f"Merge complete: {len(merged_df)} rows, excluded {excluded_count} rows from anomalies")
    
    if len(merged_df) == 0:
        raise ValueError("Merged dataset is empty. Check input data and anomaly exclusions.")
    
    return merged_df

def save_merged_dataset(df: pd.DataFrame, output_path: str):
    """
    Save merged dataset to CSV.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    logger.info(f"Saving merged dataset to {output_path}")
    
    df.to_csv(output_path, index=False)
    
    # Log summary statistics
    logger.info(f"Saved {len(df)} rows to {output_path}")
    logger.info(f"Columns: {list(df.columns)}")
    logger.info(f"RTPurbo selection rate: {df['is_rtpurbo'].mean():.4f}")

def main():
    """
    Main entry point for dataset merging.
    """
    parser = argparse.ArgumentParser(description='Merge ground truth labels with static features')
    parser.add_argument('--attention-maps', type=str, default=ATTENTION_MAPS_PATH,
                      help='Path to attention maps HDF5 file')
    parser.add_argument('--features', type=str, default=FEATURES_PATH,
                      help='Path to static features CSV file')
    parser.add_argument('--anomalies', type=str, default=ANOMALIES_PATH,
                      help='Path to anomalies CSV file')
    parser.add_argument('--output', type=str, default=OUTPUT_PATH,
                      help='Output path for merged dataset')
    
    args = parser.parse_args()
    
    try:
        # Load inputs
        labels = load_ground_truth_labels(args.attention_maps)
        features_df = load_static_features(args.features)
        anomalies = load_anomalies(args.anomalies)
        
        # Merge datasets
        merged_df = merge_datasets(labels, features_df, anomalies)
        
        # Save output
        save_merged_dataset(merged_df, args.output)
        
        logger.info("Dataset merge completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during merge: {e}")
        raise

if __name__ == '__main__':
    main()
