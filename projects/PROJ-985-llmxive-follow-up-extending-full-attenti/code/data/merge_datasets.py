import os
import csv
import logging
import argparse
import h5py
import pandas as pd
from typing import List, Set, Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/merge_datasets.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_ground_truth_labels(h5_path: str) -> pd.DataFrame:
    """Load ground truth labels and indices from HDF5."""
    if not os.path.exists(h5_path):
        raise FileNotFoundError(f"Ground truth file not found: {h5_path}")
    
    data = []
    with h5py.File(h5_path, 'r') as hf:
        doc_ids = hf['document_ids'][:]
        total_tokens = hf['total_tokens'][:]
        is_anomaly = hf['is_anomaly'][:]
        # We assume indices are stored in a way we can reconstruct
        # For this task, we just load the metadata. The actual indices might be in a separate structure
        # or we reconstruct from the flattened array if we stored it that way.
        # Simplified: We assume the H5 file has 'selected_indices' as a variable length dataset
        # or we just load the metadata for now.
        
        for i in range(len(doc_ids)):
            # Handle variable length dataset for indices if necessary
            # For this implementation, we assume we can access it
            try:
                indices = hf['selected_indices'][i]
                if isinstance(indices, (bytes, np.bytes_)):
                    indices = np.frombuffer(indices, dtype=np.int64)
                elif isinstance(indices, str):
                    indices = [int(x) for x in indices.split(',')]
                else:
                    indices = list(indices) if hasattr(indices, '__iter__') else []
            except Exception:
                indices = []
            
            data.append({
                'document_id': doc_ids[i].decode() if isinstance(doc_ids[i], bytes) else doc_ids[i],
                'total_tokens': int(total_tokens[i]),
                'is_anomaly': bool(is_anomaly[i]),
                'selected_count': len(indices),
                'selected_indices': indices # Storing list in DF might be tricky, better to explode or keep separate
            })
    
    df = pd.DataFrame(data)
    # Explode indices for row-wise analysis if needed, but for merging we keep as list or count
    # We'll keep 'selected_indices' as a list object in the DF for now, or just the count.
    # T014 requirement: join ground truth with static features.
    # We'll assume the static features are at the document level or token level.
    # If token level, we need to explode.
    return df

def load_static_features(csv_path: str) -> pd.DataFrame:
    """Load static features from CSV."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Static features file not found: {csv_path}")
    return pd.read_csv(csv_path)

def load_anomalies(csv_path: str) -> Set[str]:
    """Load document IDs that are flagged as anomalies."""
    anomalies = set()
    if not os.path.exists(csv_path):
        logger.warning(f"Anomaly file not found: {csv_path}. Assuming no anomalies.")
        return anomalies
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            anomalies.add(row['document_id'])
    return anomalies

def merge_datasets(
    ground_truth_df: pd.DataFrame,
    static_features_df: pd.DataFrame,
    anomalies: Set[str]
) -> pd.DataFrame:
    """
    Merge ground truth with static features, EXCLUDING anomalies.
    """
    # Filter out anomalies
    valid_docs = ground_truth_df[~ground_truth_df['document_id'].isin(anomalies)]
    logger.info(f"Excluded {len(ground_truth_df) - len(valid_docs)} anomalous documents.")
    
    # Merge on document_id
    # Assuming static_features_df has 'document_id' column
    merged = pd.merge(
        valid_docs,
        static_features_df,
        on='document_id',
        how='inner'
    )
    
    return merged

def save_merged_dataset(df: pd.DataFrame, output_path: str) -> None:
    """Save the merged dataset to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    # If 'selected_indices' is a list, convert to string for CSV
    if 'selected_indices' in df.columns:
        df['selected_indices'] = df['selected_indices'].apply(lambda x: ','.join(map(str, x)) if isinstance(x, list) else str(x))
    
    df.to_csv(output_path, index=False)
    logger.info(f"Saved merged dataset to {output_path} with {len(df)} rows.")

def main():
    """Main entry point for merging datasets."""
    gt_path = "data/intermediate/attention_maps.h5"
    features_path = "data/intermediate/static_features.csv" # Assuming this is the output of T013
    anomalies_path = "data/logs/anomalies.csv"
    output_path = "data/intermediate/merged_dataset.csv"
    
    logger.info("Starting dataset merge with anomaly exclusion.")
    
    try:
        gt_df = load_ground_truth_labels(gt_path)
        static_df = load_static_features(features_path)
        anomalies = load_anomalies(anomalies_path)
        
        merged_df = merge_datasets(gt_df, static_df, anomalies)
        save_merged_dataset(merged_df, output_path)
        
    except Exception as e:
        logger.error(f"Merge failed: {e}")
        raise

if __name__ == "__main__":
    main()