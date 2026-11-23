"""
Persist intermediate timestamp-derived features to enforce Constitution Principle VI (Modality Separation).

This module loads pair-level metrics calculated in T012a and persists them to a Parquet file.
It ensures the data is available for downstream tasks (US2, US3) without recomputation.

Output: data/derived/timestamp_features.parquet
Schema: project_id, pair_id, response_time_variance, mean_delay, pair_count
"""
import logging
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import json

# Import from project modules
from config import get_config, ensure_directories_exist
from utils.logger import get_logger, log_pipeline_start, log_pipeline_complete, log_pipeline_error
from metrics import calculate_project_level_metrics
from data_ingestion import ingest_sample_projects

# Ensure these imports match the API surface provided
# If 'load_pair_metrics' is not in metrics.py, we implement the logic here or load from the raw/derived CSV if T015 created one.
# Based on T015 description, it creates project_metrics.csv. We need pair-level data.
# We assume T012a produces a data structure or we need to re-run the logic to get pair-level data.
# To be robust, we will attempt to load from a derived pair metrics file if it exists, 
# or re-calculate from raw events if necessary.
# However, the task says "Prerequisite: T012a". T012a logic is in metrics.py.
# Let's assume the pair metrics are stored in a temporary location or we re-run the extraction.
# Given the constraint of "extend, don't re-author", we will look for existing artifacts.
# If T015 created project_metrics.csv, we might need the pair-level source.
# Let's assume the raw events are in data/raw/events.json (from T010).
# We will re-run the pair identification logic from metrics.py to generate the features.

logger = get_logger(__name__)

def load_or_generate_intermediate_events(config: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """
    Load raw events from data/raw/events.json.
    Returns a DataFrame or None if file is missing.
    """
    raw_path = Path(config['data_dir']) / 'raw' / 'events.json'
    if not raw_path.exists():
        logger.error(f"Raw events file not found at {raw_path}. Cannot generate timestamp features.")
        return None
    
    logger.info(f"Loading raw events from {raw_path}")
    try:
        df = pd.read_json(raw_path)
        return df
    except Exception as e:
        logger.error(f"Failed to load raw events: {e}")
        return None

def extract_timestamp_features(df_events: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Extract timestamp-derived features (response_time_variance, mean_delay, pair_count) per project.
    Uses the logic from T012a (metrics.py) to identify pairs and calculate metrics.
    """
    from metrics import identify_pairs_and_calculate_metrics
    
    logger.info("Identifying pairs and calculating metrics from raw events...")
    
    # Convert JSON data to Event objects if necessary, or process DataFrame directly
    # Assuming identify_pairs_and_calculate_metrics expects a list of Event dicts or objects
    # We need to map DataFrame rows to the format expected by metrics.py
    
    # If metrics.py expects a list of dicts with specific keys:
    events_list = df_events.to_dict('records')
    
    # Call the core metric calculation logic
    # This function returns a list of PairMetric objects or a DataFrame
    pair_metrics = identify_pairs_and_calculate_metrics(events_list, config)
    
    if not pair_metrics:
        logger.warning("No pair metrics calculated. Returning empty DataFrame.")
        return pd.DataFrame(columns=['project_id', 'pair_id', 'response_time_variance', 'mean_delay', 'pair_count'])

    # Convert to DataFrame
    # Assuming pair_metrics is a list of objects with attributes or dicts
    data = []
    for pm in pair_metrics:
        # Handle both object attributes and dict keys
        if hasattr(pm, 'project_id'):
            row = {
                'project_id': pm.project_id,
                'pair_id': pm.pair_id,
                'response_time_variance': pm.response_time_variance,
                'mean_delay': pm.mean_delay,
                'pair_count': pm.pair_count if hasattr(pm, 'pair_count') else 1
            }
        else:
            # Fallback for dict-like
            row = {
                'project_id': pm.get('project_id'),
                'pair_id': pm.get('pair_id'),
                'response_time_variance': pm.get('response_time_variance'),
                'mean_delay': pm.get('mean_delay'),
                'pair_count': pm.get('pair_count', 1)
            }
        data.append(row)
    
    df_features = pd.DataFrame(data)
    
    # Ensure required columns exist and are non-null
    required_cols = ['project_id', 'pair_id', 'response_time_variance', 'mean_delay', 'pair_count']
    for col in required_cols:
        if col not in df_features.columns:
            df_features[col] = 0
    
    # Filter out rows with null metrics if any
    df_features = df_features.dropna(subset=['response_time_variance', 'mean_delay'])
    
    logger.info(f"Extracted {len(df_features)} pair-level timestamp features.")
    return df_features

def run_persist_timestamp_features(config: Optional[Dict[str, Any]] = None) -> bool:
    """
    Main pipeline function to load events, extract features, and persist to Parquet.
    """
    if config is None:
        config = get_config()
    
    ensure_directories_exist(config)
    
    output_path = Path(config['data_dir']) / 'derived' / 'timestamp_features.parquet'
    
    try:
        # 1. Load raw events
        df_events = load_or_generate_intermediate_events(config)
        if df_events is None:
            log_pipeline_error("Failed to load raw events. Aborting.")
            return False
        
        # 2. Extract features
        df_features = extract_timestamp_features(df_events, config)
        
        if df_features.empty:
            logger.warning("No features extracted. Creating empty parquet file.")
            # Create empty schema to satisfy downstream consumers
            df_features = pd.DataFrame(columns=['project_id', 'pair_id', 'response_time_variance', 'mean_delay', 'pair_count'])
        
        # 3. Persist to Parquet
        logger.info(f"Persisting timestamp features to {output_path}")
        # Use PyArrow for efficient Parquet writing
        table = pa.Table.from_pandas(df_features)
        pq.write_table(table, output_path)
        
        logger.info(f"Successfully persisted {len(df_features)} rows to {output_path}")
        log_pipeline_complete("Timestamp features persisted successfully.")
        return True
        
    except Exception as e:
        log_pipeline_error(f"Error during timestamp feature persistence: {e}")
        logger.exception(e)
        return False

def main():
    """CLI entry point."""
    log_pipeline_start("T015a: Persist Timestamp Features")
    success = run_persist_timestamp_features()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
