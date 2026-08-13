import os
import sys
import hashlib
import yaml
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd
import polars as pl

from src.config import setup_logging
from src.data.stream_utils import stream_ebird_data, process_streamed_chunks
from src.models.lock_utils import managed_lock, acquire_lock, release_lock

logger = logging.getLogger(__name__)

# Constants from config (imported or defined locally if not exported)
GRID_RES = 0.5
MIN_OBSERVATIONS = 10
RANDOM_SEED = 42

def assign_grid_cell(lat: float, lon: float, resolution: float = GRID_RES) -> str:
    """
    Assign a grid cell ID based on latitude and longitude.
    Returns a string like "lat_40.0_lon_-75.0".
    """
    lat_bin = round(lat / resolution) * resolution
    lon_bin = round(lon / resolution) * resolution
    return f"lat_{lat_bin}_lon_{lon_bin}"

def filter_migratory_species(df: pd.DataFrame, species_set: set) -> pd.DataFrame:
    """
    Filter the DataFrame to keep only rows where 'species' is in the provided set.
    """
    if 'species' not in df.columns:
        raise ValueError("DataFrame must contain 'species' column")
    return df[df['species'].isin(species_set)]

def aggregate_to_weekly_grid(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate observations to weekly grid cells.
    Assumes 'date' is datetime. Computes min, median, and percentiles for phenology.
    """
    if 'date' not in df.columns:
        raise ValueError("DataFrame must contain 'date' column")

    df['week'] = df['date'].dt.to_period('W').dt.start_time
    df['grid_cell'] = df.apply(lambda row: assign_grid_cell(row['lat'], row['lon']), axis=1)

    # Group by species, grid_cell, and week
    agg_df = df.groupby(['species', 'grid_cell', 'week']).agg(
        first_arrival_date=('date', 'min'),
        median_arrival_date=('date', 'median'),
        p10_date=('date', lambda x: x.quantile(0.1)),
        p90_date=('date', lambda x: x.quantile(0.9)),
        count=('count', 'sum'),
        checklist_ids=('checklist_id', list) # Keep list for provenance
    ).reset_index()

    # Compute stopover duration
    agg_df['stopover_duration'] = (agg_df['p90_date'] - agg_df['p10_date']).dt.days

    # Drop intermediate columns
    agg_df = agg_df.drop(columns=['p10_date', 'p90_date'])

    return agg_df

def compute_phenology_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure phenology metrics are present. This is a wrapper for clarity.
    """
    return df

def mark_insufficient_cells(df: pd.DataFrame) -> pd.DataFrame:
    """
    Mark grid cells with fewer than MIN_OBSERVATIONS as 'insufficient'.
    """
    # Count observations per grid cell (could be per species-year-week depending on granularity)
    # Here we assume the input is already aggregated to a level where count represents total obs
    df['data_quality'] = 'sufficient'
    if 'count' in df.columns:
        df.loc[df['count'] < MIN_OBSERVATIONS, 'data_quality'] = 'insufficient'
    return df

def generate_provenance(df: pd.DataFrame, output_path: str) -> None:
    """
    Generate provenance mapping for each processed row.
    Schema: { "processed_row_id": "SHA256(checklist_id + row_index)", "original_checklist_id": str, "species": str, "grid_cell": str }
    
    This function explicitly references Constitution Principle VI (Ecological Data Provenance) and FR-003.
    """
    logger.info(f"Generating provenance mapping for {len(df)} rows to {output_path}")
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    mapping = []

    # The input df is expected to have a column 'checklist_ids' which is a list of original IDs
    # If the df is aggregated, we need to map each aggregated row back to its constituent checklist IDs.
    # However, the task description implies a row-to-row mapping. 
    # If 'checklist_ids' is a list, we iterate through it.
    # If the df is not aggregated yet, we assume 'checklist_id' exists directly.
    
    has_list_ids = 'checklist_ids' in df.columns
    has_single_id = 'checklist_id' in df.columns

    if not has_list_ids and not has_single_id:
        raise ValueError("DataFrame must contain either 'checklist_id' or 'checklist_ids' column for provenance.")

    for row_idx, row in df.iterrows():
        checklist_ids = row['checklist_ids'] if has_list_ids else [row['checklist_id']]
        species = row['species']
        grid_cell = row['grid_cell']

        for local_idx, checklist_id in enumerate(checklist_ids):
            # Create unique hash: SHA256(checklist_id + row_index)
            # Note: row_idx is the index in the processed/aggregated DataFrame.
            # We combine it with the local index within the list to ensure uniqueness if multiple checklists per row.
            unique_str = f"{checklist_id}_{row_idx}_{local_idx}"
            processed_id = hashlib.sha256(unique_str.encode('utf-8')).hexdigest()

            mapping.append({
                "processed_row_id": processed_id,
                "original_checklist_id": checklist_id,
                "species": species,
                "grid_cell": grid_cell
            })

    # Write to JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, indent=2)
    
    logger.info(f"Provenance mapping written to {output_path} with {len(mapping)} entries.")

def run_preprocessing_pipeline(species_list_path: Optional[str] = None) -> pd.DataFrame:
    """
    Main entry point for the preprocessing pipeline.
    """
    # 1. Load Species List
    if species_list_path and os.path.exists(species_list_path):
        with open(species_list_path, 'r') as f:
            species_data = json.load(f)
        migratory_species = set(species_data.get('species', []))
    else:
        # Fallback or error if list is missing but required
        logger.warning("Species list not found. Proceeding without filtering.")
        migratory_species = set()

    # 2. Stream and Process Data
    # We use polars for streaming efficiency as per T015b requirements
    # Note: The actual streaming logic might be in stream_utils, we adapt here.
    
    # For this implementation, we assume the streaming yields chunks that we collect or process in memory
    # if the dataset fits, or we write intermediate parquet files.
    # Given the constraint of T015b, we assume the data is available in data/raw/ebird_sample/
    
    raw_data_path = Path("data/raw/ebird_sample")
    if not raw_data_path.exists():
        raise FileNotFoundError("Raw eBird sample data not found. Run T005b first.")

    # Collect all parquet or csv files in the raw directory
    all_files = list(raw_data_path.glob("*.parquet")) + list(raw_data_path.glob("*.csv"))
    
    if not all_files:
        raise FileNotFoundError("No data files found in raw directory.")

    chunks = []
    for file_path in all_files:
        logger.info(f"Reading {file_path}")
        if file_path.suffix == '.parquet':
            df_chunk = pl.read_parquet(file_path).to_pandas()
        else:
            df_chunk = pd.read_csv(file_path)
        
        if migratory_species:
            df_chunk = filter_migratory_species(df_chunk, migratory_species)
        
        chunks.append(df_chunk)

    if not chunks:
        logger.warning("No data remaining after filtering.")
        return pd.DataFrame()

    full_df = pd.concat(chunks, ignore_index=True)
    
    # 3. Aggregate
    aggregated_df = aggregate_to_weekly_grid(full_df)
    
    # 4. Compute Phenology (already done in aggregate step, but kept for interface)
    aggregated_df = compute_phenology_metrics(aggregated_df)
    
    # 5. Mark Insufficient Data
    aggregated_df = mark_insufficient_cells(aggregated_df)

    # 6. Generate Provenance
    output_path = "data/provenance/row_mapping.json"
    generate_provenance(aggregated_df, output_path)

    # 7. Save Preprocessed Data
    processed_path = "data/processed/preprocessed_data.parquet"
    processed_dir = Path(processed_path).parent
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Use lock for writing
    with managed_lock("data/interim/pipeline.lock"):
        aggregated_df.to_parquet(processed_path)
    
    logger.info(f"Preprocessing complete. Output: {processed_path}")
    return aggregated_df

def main():
    setup_logging()
    try:
        run_preprocessing_pipeline()
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()