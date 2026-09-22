"""
Dataset Merger for US1.

Joins ground truth labels (from T012) with static features (from T013),
filtering out documents listed in the anomaly log.
"""
import os
import csv
import logging
import argparse
import h5py
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths relative to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
INTERMEDIATE_DIR = os.path.join(DATA_DIR, "intermediate")
LOGS_DIR = os.path.join(DATA_DIR, "logs")

# Input files (produced by T012 and T013)
GROUND_TRUTH_PATH = os.path.join(INTERMEDIATE_DIR, "rtpurbo_labels.parquet")
ATTENTION_MAPS_PATH = os.path.join(INTERMEDIATE_DIR, "attention_maps.h5")
STATIC_FEATURES_PATH = os.path.join(INTERMEDIATE_DIR, "static_features.csv")
ANOMALY_LOG_PATH = os.path.join(LOGS_DIR, "anomalies.csv")

# Output file
MERGED_OUTPUT_PATH = os.path.join(INTERMEDIATE_DIR, "merged_dataset.csv")


def load_ground_truth_labels() -> pd.DataFrame:
    """
    Load RTPurbo ground truth labels from Parquet.
    Expected columns: ['document_id', 'token_id', 'is_selected', ...]
    """
    if not os.path.exists(GROUND_TRUTH_PATH):
        raise FileNotFoundError(f"Ground truth labels not found at {GROUND_TRUTH_PATH}. "
                                "Ensure T012 has completed successfully.")
    
    logger.info(f"Loading ground truth labels from {GROUND_TRUTH_PATH}")
    df_gt = pd.read_parquet(GROUND_TRUTH_PATH)
    
    # Ensure document_id is string for consistent merging
    if 'document_id' in df_gt.columns:
        df_gt['document_id'] = df_gt['document_id'].astype(str)
    
    logger.info(f"Loaded {len(df_gt)} ground truth records.")
    return df_gt


def load_static_features() -> pd.DataFrame:
    """
    Load static features computed by T013.
    Expected columns: ['document_id', 'token_id', 'entropy', 'pos_tag', 'position', 'perplexity', ...]
    """
    if not os.path.exists(STATIC_FEATURES_PATH):
        raise FileNotFoundError(f"Static features not found at {STATIC_FEATURES_PATH}. "
                                "Ensure T013 has completed successfully.")
    
    logger.info(f"Loading static features from {STATIC_FEATURES_PATH}")
    df_features = pd.read_csv(STATIC_FEATURES_PATH)
    
    # Ensure document_id is string for consistent merging
    if 'document_id' in df_features.columns:
        df_features['document_id'] = df_features['document_id'].astype(str)
    
    logger.info(f"Loaded {len(df_features)} static feature records.")
    return df_features


def load_anomalies() -> set:
    """
    Load the list of anomalous document IDs to exclude.
    Returns a set of document_id strings.
    """
    if not os.path.exists(ANOMALY_LOG_PATH):
        logger.warning(f"Anomaly log not found at {ANOMALY_LOG_PATH}. "
                       "Proceeding without anomaly exclusion (assuming no anomalies).")
        return set()
    
    logger.info(f"Loading anomaly list from {ANOMALY_LOG_PATH}")
    df_anomalies = pd.read_csv(ANOMALY_LOG_PATH)
    
    # Assume the column containing document IDs is named 'document_id' or the first column
    if 'document_id' in df_anomalies.columns:
        anomaly_ids = set(df_anomalies['document_id'].astype(str).tolist())
    else:
        # Fallback to first column if 'document_id' is missing
        col_name = df_anomalies.columns[0]
        anomaly_ids = set(df_anomalies[col_name].astype(str).tolist())
    
    logger.info(f"Loaded {len(anomaly_ids)} anomalous document IDs.")
    return anomaly_ids


def merge_datasets(df_gt: pd.DataFrame, df_features: pd.DataFrame, anomaly_ids: set) -> pd.DataFrame:
    """
    Merge ground truth and features, excluding anomalous documents.
    
    Performs an inner join on (document_id, token_id).
    """
    logger.info("Starting dataset merge...")
    
    # Filter out anomalies from both dataframes before merging
    # This ensures we don't waste memory merging rows we will discard
    logger.info(f"Filtering out {len(anomaly_ids)} anomalous documents.")
    
    df_gt_clean = df_gt[~df_gt['document_id'].isin(anomaly_ids)]
    df_features_clean = df_features[~df_features['document_id'].isin(anomaly_ids)]
    
    logger.info(f"Filtered Ground Truth: {len(df_gt)} -> {len(df_gt_clean)}")
    logger.info(f"Filtered Features: {len(df_features)} -> {len(df_features_clean)}")
    
    if df_gt_clean.empty or df_features_clean.empty:
        logger.warning("One of the filtered datasets is empty. Merging will result in an empty dataframe.")
    
    # Merge on document_id and token_id
    # We use an inner join to ensure we only keep tokens that exist in both
    merged_df = pd.merge(
        df_gt_clean,
        df_features_clean,
        on=['document_id', 'token_id'],
        how='inner'
    )
    
    logger.info(f"Merged dataset size: {len(merged_df)} rows.")
    return merged_df


def save_merged_dataset(df: pd.DataFrame, output_path: str):
    """
    Save the merged dataset to CSV.
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    logger.info(f"Saving merged dataset to {output_path}")
    df.to_csv(output_path, index=False)
    
    # Log a sample of the output
    logger.info(f"Output columns: {list(df.columns)}")
    if not df.empty:
        logger.info(f"Sample row:\n{df.head(1).to_string()}")


def main():
    """
    Main entry point for the dataset merger.
    """
    logger.info("=== Starting Dataset Merger (T014) ===")
    
    try:
        # 1. Load inputs
        df_gt = load_ground_truth_labels()
        df_features = load_static_features()
        anomaly_ids = load_anomalies()
        
        # 2. Merge and filter
        merged_df = merge_datasets(df_gt, df_features, anomaly_ids)
        
        # 3. Save output
        save_merged_dataset(merged_df, MERGED_OUTPUT_PATH)
        
        logger.info("=== Dataset Merger (T014) Completed Successfully ===")
        print(f"Success: Merged dataset saved to {MERGED_OUTPUT_PATH}")
        
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during merge: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()