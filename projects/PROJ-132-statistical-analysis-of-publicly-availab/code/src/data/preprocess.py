import os
import sys
import hashlib
import yaml
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from datasets import load_dataset

# Import existing utilities from project
from src.config import setup_logging
from src.data.download import get_clo_migratory_list
from src.data.stream_utils import stream_ebird_data
from src.data.scope_documentation import determine_scope_status

logger = logging.getLogger(__name__)

GRID_RES = 0.5  # From T010a config

def assign_grid_cell(lat: float, lon: float) -> str:
    """
    Assign a grid cell ID based on latitude and longitude.
    Grid resolution is defined by GRID_RES.
    Returns a string like "lat_45.0_lon_-122.5".
    """
    lat_bin = round(lat / GRID_RES) * GRID_RES
    lon_bin = round(lon / GRID_RES) * GRID_RES
    return f"lat_{lat_bin}_lon_{lon_bin}"

def filter_migratory_species(df: pd.DataFrame, migratory_list: List[str]) -> pd.DataFrame:
    """
    Filter the dataframe to include only migratory species found in the provided list.
    """
    if not migratory_list:
        logger.warning("Migratory list is empty. Returning full dataframe.")
        return df
    
    # Ensure species column is string for safe comparison
    df = df.copy()
    df['species'] = df['species'].astype(str)
    
    # Filter
    filtered_df = df[df['species'].isin(migratory_list)]
    logger.info(f"Filtered {len(df)} records to {len(filtered_df)} migratory records.")
    return filtered_df

def aggregate_to_weekly_grid(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate eBird records to weekly counts per spatial grid cell.
    Expects 'date' column to be datetime-like.
    """
    if df.empty:
        logger.warning("Input dataframe is empty. Returning empty aggregated dataframe.")
        return pd.DataFrame(columns=['species', 'grid_cell', 'week', 'count', 'checklist_ids'])

    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df['week'] = df['date'].dt.isocalendar().week
    df['year'] = df['date'].dt.year
    
    # Assign grid cells
    df['grid_cell'] = df.apply(lambda row: assign_grid_cell(row['lat'], row['lon']), axis=1)

    # Aggregate
    # We need to keep track of checklist_ids for provenance
    aggregated = df.groupby(['species', 'grid_cell', 'week', 'year']).agg(
        count=('checklist_id', 'count'),
        checklist_ids=('checklist_id', lambda x: list(x))
    ).reset_index()

    logger.info(f"Aggregated to {len(aggregated)} weekly grid cells.")
    return aggregated

def compute_phenology_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute phenology metrics: first_arrival, median_arrival, stopover_duration.
    Assumes 'df' is already aggregated by week and has a 'count' column.
    This is a simplified implementation assuming weekly data is available.
    """
    if df.empty:
        logger.warning("Input dataframe for phenology is empty.")
        return df

    # Calculate Day of Year (DOY) for the week start
    # Note: This is a simplification. A robust implementation would use specific dates.
    df = df.copy()
    
    # Create a dummy date for the first day of the week to calculate DOY
    # We assume 'year' and 'week' are present.
    # Using pd.to_datetime with week number requires specific formatting.
    # Here we approximate DOY as (week - 1) * 7 + 1
    df['approx_doy'] = (df['week'] - 1) * 7 + 1

    results = []
    
    for (species, grid_cell), group in df.groupby(['species', 'grid_cell']):
        if group['count'].sum() == 0:
            continue
        
        # Sort by DOY
        group = group.sort_values('approx_doy')
        
        # First arrival: first week with count > 0
        first_arrival_row = group[group['count'] > 0].iloc[0] if not group[group['count'] > 0].empty else None
        
        # Median arrival: weighted median of DOY
        total_count = group['count'].sum()
        if total_count == 0:
            continue
        
        cumulative = group['count'].cumsum()
        median_idx = cumulative >= (total_count / 2)
        median_row = group[median_idx].iloc[0] if median_idx.any() else None
        
        # Stopover duration: High percentile - Low percentile
        # Using 10th and 90th percentiles of the cumulative distribution
        low_pct_idx = cumulative >= (total_count * 0.1)
        high_pct_idx = cumulative >= (total_count * 0.9)
        
        low_doy = group[low_pct_idx].iloc[0]['approx_doy'] if low_pct_idx.any() else None
        high_doy = group[high_pct_idx].iloc[0]['approx_doy'] if high_pct_idx.any() else None
        
        stopover = None
        if low_doy is not None and high_doy is not None:
            stopover = high_doy - low_doy

        results.append({
            'species': species,
            'grid_cell': grid_cell,
            'first_arrival': first_arrival_row['approx_doy'] if first_arrival_row is not None else None,
            'median_arrival': median_row['approx_doy'] if median_row is not None else None,
            'stopover_duration': stopover,
            'total_count': total_count
        })

    result_df = pd.DataFrame(results)
    logger.info(f"Computed phenology metrics for {len(result_df)} species-grid combinations.")
    return result_df

def mark_insufficient_cells(df: pd.DataFrame, threshold: int = 5) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Mark grid cells with insufficient data (count < threshold).
    Returns the modified dataframe and a list of metadata dicts for insufficient cells.
    """
    if df.empty:
        return df, []
    
    df = df.copy()
    insufficient_cells = []
    
    # Check total_count if present, otherwise sum of counts if 'count' column exists
    count_col = 'total_count' if 'total_count' in df.columns else 'count'
    
    mask = df[count_col] < threshold
    insufficient_indices = df[mask].index
    
    for idx in insufficient_indices:
        row = df.loc[idx]
        insufficient_cells.append({
            'species': row['species'],
            'grid_cell': row['grid_cell'],
            'count': row[count_col],
            'reason': f"Count {row[count_col]} < threshold {threshold}"
        })
    
    # Flag in dataframe
    df['data_quality'] = 'sufficient'
    df.loc[mask, 'data_quality'] = 'insufficient'
    
    logger.info(f"Marked {len(insufficient_cells)} cells as insufficient data.")
    return df, insufficient_cells

def generate_provenance(processed_df: pd.DataFrame, raw_checklist_ids: List[str]) -> Dict[str, Any]:
    """
    Generate provenance mapping from processed rows back to original checklist_ids.
    
    Args:
        processed_df: The aggregated/processed dataframe containing 'checklist_ids' lists.
        raw_checklist_ids: List of all checklist_ids present in the raw source data 
                           (optional, used for integrity verification).
    
    Returns:
        A dictionary mapping processed row identifiers to their source checklist_ids.
    """
    if processed_df.empty:
        logger.warning("Processed dataframe is empty. Returning empty mapping.")
        return {}
    
    mapping = {}
    processed_checklist_ids = set()
    
    # Create a unique key for each processed row (species, grid, week, year)
    for idx, row in processed_df.iterrows():
        row_key = f"{row['species']}_{row['grid_cell']}_{row['week']}_{row.get('year', 'unknown')}"
        checklist_ids = row.get('checklist_ids', [])
        
        if isinstance(checklist_ids, list):
            mapping[row_key] = checklist_ids
            processed_checklist_ids.update(checklist_ids)
        else:
            # Handle case where it might be a string representation or single ID
            mapping[row_key] = [checklist_ids] if checklist_ids else []
            if checklist_ids:
                processed_checklist_ids.add(checklist_ids)
    
    # Integrity Verification
    if raw_checklist_ids:
        raw_set = set(raw_checklist_ids)
        missing_in_raw = processed_checklist_ids - raw_set
        if missing_in_raw:
            logger.warning(f"Found {len(missing_in_raw)} checklist_ids in processed data not found in raw source.")
            # In a strict pipeline, we might raise an error here, but we log and continue for now
    
    logger.info(f"Generated provenance mapping for {len(mapping)} processed rows.")
    return mapping

def run_preprocessing_pipeline(raw_data_path: Optional[str] = None) -> str:
    """
    Orchestrate the full preprocessing pipeline:
    1. Load raw data (or stream it)
    2. Filter migratory species
    3. Aggregate to weekly grid cells
    4. Compute phenology metrics
    5. Mark insufficient cells
    6. Generate provenance mapping
    
    Args:
        raw_data_path: Path to raw data file. If None, streams from dataset.
    
    Returns:
        Path to the processed output file.
    """
    logger.info("Starting preprocessing pipeline...")
    
    # 1. Load Data
    # Assuming T015b has already prepared the data or we stream it here.
    # For this task, we assume the input is a dataframe or we load it.
    # If raw_data_path is provided, load from there. Otherwise, stream.
    
    if raw_data_path and os.path.exists(raw_data_path):
        logger.info(f"Loading data from {raw_data_path}")
        df = pd.read_parquet(raw_data_path)
    else:
        logger.info("Streaming eBird data...")
        # Stream and convert to DF (careful with memory, but for sample it's ok)
        # In a real scenario with large data, we would process in chunks.
        # Here we assume the sample dataset fits or we take a slice.
        df = stream_ebird_data("vvud/eb-data", split="train")
        # Filter to 2020-2024 immediately to reduce size
        df['date'] = pd.to_datetime(df['date'])
        df = df[(df['date'].dt.year >= 2020) & (df['date'].dt.year <= 2024)]
    
    # 2. Filter Migratory Species
    migratory_list = get_clo_migratory_list()
    df_filtered = filter_migratory_species(df, migratory_list)
    
    # 3. Aggregate
    df_aggregated = aggregate_to_weekly_grid(df_filtered)
    
    # 4. Phenology Metrics
    df_phenology = compute_phenology_metrics(df_aggregated)
    
    # 5. Mark Insufficient
    df_final, insufficient_metadata = mark_insufficient_cells(df_phenology)
    
    # Save insufficient metadata
    if insufficient_metadata:
        insufficient_path = Path("data/processed/metadata_insufficient_cells.json")
        insufficient_path.parent.mkdir(parents=True, exist_ok=True)
        with open(insufficient_path, 'w') as f:
            json.dump(insufficient_metadata, f, indent=2)
        logger.info(f"Saved insufficient cells metadata to {insufficient_path}")
    
    # 6. Generate Provenance
    # We need the original checklist_ids from the raw data for the mapping
    # Since we aggregated, we have 'checklist_ids' in df_aggregated
    # We pass the original raw IDs if available, otherwise we use what we have
    # For the mapping, we use the checklist_ids collected during aggregation
    all_raw_ids = df['checklist_id'].unique().tolist()
    provenance_mapping = generate_provenance(df_final, all_raw_ids)
    
    # Write Provenance Mapping
    provenance_path = Path("data/provenance/row_mapping.json")
    provenance_path.parent.mkdir(parents=True, exist_ok=True)
    with open(provenance_path, 'w') as f:
        json.dump(provenance_mapping, f, indent=2)
    
    logger.info(f"Saved provenance mapping to {provenance_path}")
    
    # Save final processed data
    output_path = Path("data/processed/preprocessed_data.parquet")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_final.to_parquet(output_path, index=False)
    logger.info(f"Saved processed data to {output_path}")
    
    return str(output_path)

def main():
    """Entry point for the preprocessing script."""
    setup_logging()
    try:
        run_preprocessing_pipeline()
        logger.info("Preprocessing pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Preprocessing pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
