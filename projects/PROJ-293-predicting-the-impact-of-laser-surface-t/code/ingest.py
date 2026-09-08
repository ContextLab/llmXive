import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging
import pandas as pd
import numpy as np

from seed import set_seed, ensure_seed_set
from hygiene import calculate_md5, update_artifact_hash, save_artifact_hashes
from config.loader import load_schema_map, get_target_columns, get_source_columns_for_target
from models import NormalizationMethod

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Predictor columns that MUST be present for normalization
# These are the independent variables used to predict wear
PREDICTOR_COLUMNS = [
    'pulse_duration', 'power', 'scanning_speed', 'pattern_geometry',
    'hardness', 'elastic_modulus'
]

# Columns required for Archard's Law normalization
NORMALIZATION_REQUIRED_COLUMNS = [
    'contact_load', 'sliding_speed', 'wear_rate'
]

def parse_research_md(research_md_path: str) -> Dict[str, Any]:
    """
    Parse research.md to extract static data source URLs/IDs.
    Raises ValueError if file is missing or contains dynamic logic.
    """
    path = Path(research_md_path)
    if not path.exists():
        raise FileNotFoundError(f"research.md not found at {path}")
    
    content = path.read_text()
    # Basic check for dynamic search logic (placeholder for more complex validation)
    if 'search(' in content or 'find_all(' in content:
        raise ValueError("research.md contains dynamic search logic, which is forbidden.")
    
    # Extract simple key-value pairs or URLs
    # This is a simplified parser; actual implementation would be more robust
    sources = {}
    lines = content.split('\n')
    for line in lines:
        if line.startswith('# Source:'):
            parts = line.split(':', 1)
            if len(parts) == 2:
                key = parts[0].replace('# Source:', '').strip()
                value = parts[1].strip()
                sources[key] = value
    
    return sources

def fetch_openml_data(dataset_id: int) -> pd.DataFrame:
    """
    Fetch data from OpenML using a specific dataset ID.
    Raises error if fetch fails.
    """
    try:
        import openml
        dataset = openml.datasets.get_dataset(dataset_id)
        X, y, categorical, attribute_names = dataset.get_data(
            dataset_format='dataframe', 
            target=dataset.default_target_attribute
        )
        logger.info(f"Fetched OpenML dataset {dataset_id}: {X.shape}")
        return X
    except Exception as e:
        logger.error(f"Failed to fetch OpenML dataset {dataset_id}: {e}")
        raise

def fetch_huggingface_data(dataset_id: str, split: str = 'train') -> pd.DataFrame:
    """
    Fetch data from HuggingFace using a specific dataset ID.
    Raises error if fetch fails.
    """
    try:
        from datasets import load_dataset
        dataset = load_dataset(dataset_id, split=split)
        df = dataset.to_pandas()
        logger.info(f"Fetched HuggingFace dataset {dataset_id}: {df.shape}")
        return df
    except Exception as e:
        logger.error(f"Failed to fetch HuggingFace dataset {dataset_id}: {e}")
        raise

def fetch_literature_data(url: str) -> pd.DataFrame:
    """
    Fetch data from a literature supplement URL (CSV/Excel).
    Raises error if fetch fails.
    """
    try:
        if url.endswith('.csv'):
            df = pd.read_csv(url)
        elif url.endswith('.xlsx') or url.endswith('.xls'):
            df = pd.read_excel(url)
        else:
            raise ValueError(f"Unsupported file format for URL: {url}")
        
        logger.info(f"Fetched literature data from {url}: {df.shape}")
        return df
    except Exception as e:
        logger.error(f"Failed to fetch literature data from {url}: {e}")
        raise

def standardize_schema(df: pd.DataFrame, schema_map_path: str) -> pd.DataFrame:
    """
    Map source columns to canonical target columns using schema_map.json.
    """
    schema_map = load_schema_map(schema_map_path)
    target_columns = get_target_columns(schema_map)
    
    # Create a mapping from source to target
    source_to_target = {}
    for target, sources in schema_map.items():
        for source in sources:
            source_to_target[source] = target
    
    # Rename columns
    existing_cols = set(df.columns)
    rename_map = {}
    for source, target in source_to_target.items():
        if source in existing_cols:
            rename_map[source] = target
    
    df_renamed = df.rename(columns=rename_map)
    
    # Ensure all target columns are present (some might be missing entirely)
    for col in target_columns:
        if col not in df_renamed.columns:
            df_renamed[col] = np.nan
            logger.warning(f"Target column '{col}' not found in source data, filled with NaN.")
    
    return df_renamed

def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Implement missing value handling per FR-002:
    1. DROP records with missing predictors (pulse_duration, power, scanning_speed, 
       pattern_geometry, hardness, elastic_modulus).
    2. RETAIN records with missing contact_load/sliding_speed but set 
       normalization_method='raw'.
    3. Ensure 'wear_rate' is present (it is the target, so if missing, drop record).
    
    Returns:
        pd.DataFrame: Cleaned dataframe with 'normalization_method' column added.
    """
    logger.info(f"Starting missing value handling. Original shape: {df.shape}")
    
    # Initialize normalization_method column
    df['normalization_method'] = 'normalized'
    
    # Identify predictor columns that must NOT have missing values
    # These are features used for prediction
    predictors_to_drop = [col for col in PREDICTOR_COLUMNS if col in df.columns]
    
    # Identify columns needed for normalization (Archard's Law)
    normalization_cols = [col for col in NORMALIZATION_REQUIRED_COLUMNS if col in df.columns]
    
    # Step 1: Mark records that have missing normalization inputs
    # These records will be retained but flagged as 'raw'
    if 'contact_load' in df.columns and 'sliding_speed' in df.columns:
        mask_missing_normalization = df['contact_load'].isna() | df['sliding_speed'].isna()
        df.loc[mask_missing_normalization, 'normalization_method'] = 'raw'
        logger.info(f"Marked {mask_missing_normalization.sum()} records as 'raw' due to missing normalization inputs.")
    else:
        # If normalization columns are completely missing, all records are 'raw'
        df['normalization_method'] = 'raw'
        logger.warning("Normalization columns (contact_load, sliding_speed) missing entirely. All records set to 'raw'.")
    
    # Step 2: Drop records with missing predictors OR missing target (wear_rate)
    # Predictors are required for the model to work
    # wear_rate is the target, so it must be present
    drop_mask = pd.Series([False] * len(df), index=df.index)
    
    for col in predictors_to_drop:
        drop_mask |= df[col].isna()
    
    if 'wear_rate' in df.columns:
        drop_mask |= df['wear_rate'].isna()
    else:
        logger.error("Target column 'wear_rate' is missing. Cannot proceed without target.")
        raise ValueError("Target column 'wear_rate' is missing.")
    
    # Apply drop mask
    initial_count = len(df)
    df = df[~drop_mask].reset_index(drop=True)
    final_count = len(df)
    dropped_count = initial_count - final_count
    
    logger.info(f"Dropped {dropped_count} records due to missing predictors or target. New shape: {df.shape}")
    
    # Verify no missing predictors remain
    for col in predictors_to_drop:
        if df[col].isna().any():
            logger.error(f"Predictor column '{col}' still has missing values after dropping.")
            raise ValueError(f"Predictor column '{col}' still has missing values.")
    
    return df

def apply_archard_normalization(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute wear coefficient K using Archard's Law: K = (Wear Volume) / (Load * Sliding Distance)
    Wear Volume approximated by wear_rate * sliding_speed * time (or similar).
    For this implementation, we assume wear_rate is already a volume-based metric or proportional.
    
    K = wear_rate / (contact_load * sliding_speed)
    
    Records with 'normalization_method' == 'raw' are skipped.
    """
    logger.info("Applying Archard's Law normalization.")
    
    # Only process normalized records
    mask = df['normalization_method'] == 'normalized'
    if not mask.any():
        logger.warning("No records to normalize. All are marked as 'raw'.")
        return df
    
    subset = df.loc[mask].copy()
    
    # Check for required columns
    required_cols = ['wear_rate', 'contact_load', 'sliding_speed']
    for col in required_cols:
        if col not in subset.columns:
            logger.error(f"Required column '{col}' missing for normalization.")
            raise ValueError(f"Required column '{col}' missing for normalization.")
    
    # Calculate K
    # Avoid division by zero
    denominator = subset['contact_load'] * subset['sliding_speed']
    denominator[denominator == 0] = np.nan
    
    subset['wear_coefficient_K'] = subset['wear_rate'] / denominator
    
    # Update main dataframe
    df.loc[mask, 'wear_coefficient_K'] = subset['wear_coefficient_K']
    
    # Flag records where calculation failed (e.g., division by zero)
    failed_mask = mask & df['wear_coefficient_K'].isna()
    if failed_mask.any():
        logger.warning(f"{failed_mask.sum()} records failed normalization due to zero/NaN in denominator.")
        df.loc[failed_mask, 'normalization_method'] = 'raw'
    
    return df

def ingest_all_data(research_md_path: str, schema_map_path: str, output_path: str) -> pd.DataFrame:
    """
    Main ingestion pipeline:
    1. Parse research.md for sources.
    2. Fetch data from each source.
    3. Standardize schema.
    4. Handle missing values.
    5. Apply Archard normalization.
    6. Save output and update hashes.
    """
    # Parse sources
    sources = parse_research_md(research_md_path)
    logger.info(f"Found {len(sources)} data sources.")
    
    all_dfs = []
    
    # Fetch and process each source
    for source_name, source_info in sources.items():
        logger.info(f"Processing source: {source_name}")
        
        try:
            if source_name.startswith('openml'):
                dataset_id = int(source_info)
                df = fetch_openml_data(dataset_id)
            elif source_name.startswith('huggingface'):
                dataset_id = source_info
                df = fetch_huggingface_data(dataset_id)
            elif source_name.startswith('literature'):
                url = source_info
                df = fetch_literature_data(url)
            else:
                logger.warning(f"Unknown source type: {source_name}, skipping.")
                continue
            
            # Standardize schema
            df = standardize_schema(df, schema_map_path)
            all_dfs.append(df)
            
        except Exception as e:
            logger.error(f"Failed to process source {source_name}: {e}")
            # Continue with other sources, but log the error
            # In a strict pipeline, we might want to fail here
            # For now, we continue but the final dataset might be incomplete
            continue
    
    if not all_dfs:
        raise ValueError("No data was successfully ingested from any source.")
    
    # Concatenate all data
    combined_df = pd.concat(all_dfs, ignore_index=True)
    logger.info(f"Combined data shape: {combined_df.shape}")
    
    # Handle missing values
    cleaned_df = handle_missing_values(combined_df)
    
    # Apply normalization
    final_df = apply_archard_normalization(cleaned_df)
    
    # Save output
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(output_path, index=False)
    logger.info(f"Saved cleaned data to {output_path}")
    
    # Update artifact hash
    update_artifact_hash(output_path)
    save_artifact_hashes()
    
    return final_df

def main():
    """
    Entry point for the ingestion script.
    """
    # Set seed for reproducibility
    set_seed(42)
    
    # Define paths
    project_root = Path(__file__).parent.parent
    research_md_path = project_root / 'specs' / 'research.md'
    schema_map_path = project_root / 'code' / 'config' / 'schema_map.json'
    output_path = project_root / 'data' / 'processed' / 'aggregated_clean.csv'
    
    # Ensure logs directory exists
    (project_root / 'logs').mkdir(exist_ok=True)
    
    try:
        df = ingest_all_data(
            research_md_path=str(research_md_path),
            schema_map_path=str(schema_map_path),
            output_path=str(output_path)
        )
        
        # Log summary
        normalized_count = (df['normalization_method'] == 'normalized').sum()
        raw_count = (df['normalization_method'] == 'raw').sum()
        logger.info(f"Ingestion complete. Normalized: {normalized_count}, Raw: {raw_count}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == '__main__':
    main()
