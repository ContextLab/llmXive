import os
import csv
import logging
import argparse
import h5py
import pandas as pd
from typing import List, Set, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_ground_truth_labels(path: str = "data/intermediate/rtpurbo_labels.parquet") -> pd.DataFrame:
    """Load ground truth labels from Parquet file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Ground truth labels file not found: {path}")
    logger.info(f"Loading ground truth labels from {path}")
    df = pd.read_parquet(path)
    logger.info(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
    return df

def load_static_features(path: str = "data/intermediate/static_features.csv") -> pd.DataFrame:
    """Load static features from CSV file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Static features file not found: {path}")
    logger.info(f"Loading static features from {path}")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
    return df

def load_anomalies(path: str = "data/logs/anomalies.csv") -> Set[str]:
    """Load anomaly document IDs from CSV file."""
    anomaly_ids = set()
    if not os.path.exists(path):
        logger.warning(f"Anomalies file not found: {path}. Proceeding without exclusion.")
        return anomaly_ids
    
    logger.info(f"Loading anomalies from {path}")
    try:
        with open(path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Assume column name is 'document_id' or similar; handle variations
                doc_id = row.get('document_id') or row.get('id') or row.get('doc_id')
                if doc_id:
                    anomaly_ids.add(str(doc_id))
        logger.info(f"Loaded {len(anomaly_ids)} anomaly document IDs")
    except Exception as e:
        logger.warning(f"Could not parse anomalies file {path}: {e}")
    
    return anomaly_ids

def merge_datasets(
    ground_truth: pd.DataFrame,
    static_features: pd.DataFrame,
    anomaly_ids: Optional[Set[str]] = None
) -> pd.DataFrame:
    """
    Merge ground truth labels with static features, excluding anomalies.
    
    Args:
        ground_truth: DataFrame with RTPurbo labels (must have 'document_id' column)
        static_features: DataFrame with static features (must have 'document_id' column)
        anomaly_ids: Set of document IDs to exclude from the merge
    
    Returns:
        Merged DataFrame
    """
    if anomaly_ids is None:
        anomaly_ids = set()
    
    logger.info(f"Excluding {len(anomaly_ids)} anomaly documents")
    
    # Filter out anomalies from both datasets
    if anomaly_ids:
        gt_filtered = ground_truth[~ground_truth['document_id'].isin(anomaly_ids)].copy()
        sf_filtered = static_features[~static_features['document_id'].isin(anomaly_ids)].copy()
    else:
        gt_filtered = ground_truth.copy()
        sf_filtered = static_features.copy()
    
    logger.info(f"After filtering anomalies: GT={len(gt_filtered)}, SF={len(sf_filtered)}")
    
    # Merge on document_id
    # We expect a 1-to-1 or 1-to-many relationship; assuming 1-to-1 based on token-level data
    # If static_features has one row per token and ground_truth has one row per token, merge directly
    # If ground_truth is at doc-level and features are at token-level, we might need to broadcast
    # Based on T012/T013 outputs, both should be token-level or doc-level aligned.
    # Assuming token-level alignment on 'document_id' and 'token_index' if present.
    
    merge_keys = ['document_id']
    if 'token_index' in gt_filtered.columns and 'token_index' in sf_filtered.columns:
        merge_keys.append('token_index')
    
    merged = pd.merge(
        gt_filtered,
        sf_filtered,
        on=merge_keys,
        how='inner'
    )
    
    logger.info(f"Merged dataset shape: {merged.shape}")
    logger.info(f"Merged columns: {list(merged.columns)}")
    
    return merged

def save_merged_dataset(df: pd.DataFrame, path: str = "data/intermediate/merged_dataset.csv") -> None:
    """Save merged dataset to CSV."""
    os.makedirs(os.dirname(path), exist_ok=True)
    logger.info(f"Saving merged dataset to {path}")
    df.to_csv(path, index=False)
    logger.info(f"Saved {len(df)} rows to {path}")

def main():
    parser = argparse.ArgumentParser(description="Merge ground truth and static features")
    parser.add_argument("--gt-path", default="data/intermediate/rtpurbo_labels.parquet", help="Path to ground truth parquet")
    parser.add_argument("--sf-path", default="data/intermediate/static_features.csv", help="Path to static features CSV")
    parser.add_argument("--anomaly-path", default="data/logs/anomalies.csv", help="Path to anomalies CSV")
    parser.add_argument("--output-path", default="data/intermediate/merged_dataset.csv", help="Output path for merged dataset")
    args = parser.parse_args()
    
    try:
        ground_truth = load_ground_truth_labels(args.gt_path)
        static_features = load_static_features(args.sf_path)
        anomaly_ids = load_anomalies(args.anomaly_path)
        
        merged = merge_datasets(ground_truth, static_features, anomaly_ids)
        save_merged_dataset(merged, args.output_path)
        
        logger.info("Merge completed successfully.")
    except Exception as e:
        logger.error(f"Merge failed: {e}")
        raise

if __name__ == "__main__":
    main()
