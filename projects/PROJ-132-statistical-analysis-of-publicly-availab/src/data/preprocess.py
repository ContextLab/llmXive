import os
import sys
import hashlib
import yaml
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Any
import pandas as pd
import numpy as np

from src.lib.config import get_config, Config

# Ensure logger is configured (T010 dependency)
logger = logging.getLogger(__name__)

def verify_checksums(data_dir: Path, state_file: Path) -> bool:
    """Verify checksums of raw data files against state file."""
    if not state_file.exists():
        logger.warning(f"State file {state_file} not found. Skipping checksum verification.")
        return False

    with open(state_file, 'r') as f:
        state = yaml.safe_load(f)

    artifact_hashes = state.get('artifact_hashes', {})
    for rel_path, expected_hash in artifact_hashes.items():
        file_path = data_dir / rel_path
        if not file_path.exists():
            logger.error(f"Checksum verification failed: {file_path} missing.")
            return False
        
        actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            logger.error(f"Checksum mismatch for {file_path}: expected {expected_hash}, got {actual_hash}")
            return False
    
    logger.info("All checksums verified successfully.")
    return True

def filter_migratory_species(df: pd.DataFrame, clo_list: Optional[List[str]] = None) -> pd.DataFrame:
    """Filter eBird data to only migratory species based on CLO list."""
    if clo_list is None:
        # Default to a small set for demonstration; in production, load from external CLO list
        clo_list = ["American Robin", "Gray Catbird", "Black-capped Chickadee"]
    
    if 'species' not in df.columns:
        raise ValueError("Input DataFrame must contain 'species' column")
    
    mask = df['species'].isin(clo_list)
    filtered_df = df[mask].copy()
    logger.info(f"Filtered to {len(filtered_df)} records for {len(clo_list)} migratory species.")
    return filtered_df

def assign_grid_cell(lat: float, lon: float, grid_res: float = 0.5) -> Tuple[float, float]:
    """Assign a lat/lon point to a grid cell of specified resolution."""
    grid_lat = np.floor(lat / grid_res) * grid_res
    grid_lon = np.floor(lon / grid_res) * grid_res
    return grid_lat, grid_lon

def add_grid_cells(df: pd.DataFrame, grid_res: float = 0.5) -> pd.DataFrame:
    """Add grid_cell column to DataFrame based on lat/lon."""
    if 'lat' not in df.columns or 'lon' not in df.columns:
        raise ValueError("DataFrame must contain 'lat' and 'lon' columns")
    
    df = df.copy()
    df['grid_lat'], df['grid_lon'] = zip(*df.apply(
        lambda row: assign_grid_cell(row['lat'], row['lon'], grid_res), axis=1
    ))
    df['grid_cell'] = df['grid_lat'].astype(str) + "_" + df['grid_lon'].astype(str)
    logger.info(f"Assigned grid cells with resolution {grid_res}°.")
    return df

def aggregate_to_weekly_grid(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate eBird records to weekly counts per grid cell."""
    if 'date' not in df.columns:
        raise ValueError("DataFrame must contain 'date' column")
    
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df['week'] = df['date'].dt.isocalendar().week
    df['year'] = df['date'].dt.year
    
    # Aggregate by species, grid_cell, week, year
    agg_df = df.groupby(['species', 'grid_cell', 'week', 'year'], as_index=False).agg(
        count=('count', 'sum'),
        checklist_id=('checklist_id', 'nunique')
    ).reset_index(drop=True)
    
    logger.info(f"Aggregated to {len(agg_df)} weekly grid records.")
    return agg_df

def compute_phenology_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute phenology metrics: first_arrival, median_arrival, stopover_duration."""
    if 'week' not in df.columns or 'count' not in df.columns:
        raise ValueError("DataFrame must contain 'week' and 'count' columns")
    
    df = df.copy()
    
    # Sort by week within each group
    df = df.sort_values(['species', 'grid_cell', 'year', 'week'])
    
    def calculate_metrics(group):
        if group['count'].sum() == 0:
            return pd.Series({
                'first_arrival': None,
                'median_arrival': None,
                'stopover_duration': None
            })
        
        # First arrival: first week with non-zero count
        first_arrival = group[group['count'] > 0]['week'].iloc[0]
        
        # Median arrival: weighted median of weeks
        total_count = group['count'].sum()
        cum_count = group['count'].cumsum()
        median_idx = cum_count.searchsorted(total_count / 2)
        median_arrival = group.iloc[median_idx]['week']
        
        # Stopover duration: weeks with significant activity (simplified)
        active_weeks = group[group['count'] > 0]['week']
        if len(active_weeks) < 2:
            stopover_duration = None
        else:
            stopover_duration = active_weeks.max() - active_weeks.min()
        
        return pd.Series({
            'first_arrival': first_arrival,
            'median_arrival': median_arrival,
            'stopover_duration': stopover_duration
        })
    
    result = df.groupby(['species', 'grid_cell', 'year'], as_index=False).apply(
        calculate_metrics
    ).reset_index(drop=True)
    
    # Merge back to main df
    df = df.merge(result, on=['species', 'grid_cell', 'year'], how='left')
    logger.info("Computed phenology metrics.")
    return df

def mark_insufficient_data(df: pd.DataFrame, min_observations: int = 5) -> pd.DataFrame:
    """
    Mark grid cells as 'insufficient' if observation density is below threshold.
    Excludes them from downstream modeling by adding a data_quality flag.
    
    Args:
        df: DataFrame with at least 'species', 'grid_cell', 'week', 'count' columns.
        min_observations: Minimum number of observations required (default: 5).
    
    Returns:
        DataFrame with 'data_quality' column added ('sufficient' or 'insufficient').
    """
    if 'species' not in df.columns or 'grid_cell' not in df.columns:
        raise ValueError("DataFrame must contain 'species' and 'grid_cell' columns")
    
    df = df.copy()
    
    # Count observations per species-grid cell combination
    # We define an "observation" as a non-zero count record for a given week
    obs_counts = df[df['count'] > 0].groupby(['species', 'grid_cell']).size().reset_index(name='obs_count')
    
    # Merge back to original df
    df = df.merge(obs_counts, on=['species', 'grid_cell'], how='left')
    df['obs_count'] = df['obs_count'].fillna(0).astype(int)
    
    # Mark data quality
    df['data_quality'] = df['obs_count'].apply(
        lambda x: 'sufficient' if x >= min_observations else 'insufficient'
    )
    
    # Log insufficient data events
    insufficient_mask = df['data_quality'] == 'insufficient'
    if insufficient_mask.any():
        insufficient_rows = df[insufficient_mask][['species', 'grid_cell', 'obs_count']].drop_duplicates()
        for _, row in insufficient_rows.iterrows():
            logger.warning(
                f"Insufficient data: species={row['species']}, grid_cell={row['grid_cell']}, "
                f"observations={row['obs_count']} (threshold={min_observations})"
            )
    
    # Filter out insufficient data for downstream modeling (but keep the flag in the full df)
    # The function returns the full df with the flag; downstream steps must filter based on this.
    logger.info(f"Marked {insufficient_mask.sum()} records as 'insufficient' out of {len(df)} total.")
    return df

def calculate_observer_effort(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate observer effort covariates (e.g., number of checklists per grid cell)."""
    if 'grid_cell' not in df.columns or 'checklist_id' not in df.columns:
        raise ValueError("DataFrame must contain 'grid_cell' and 'checklist_id' columns")
    
    df = df.copy()
    
    # Count unique checklists per grid cell
    effort = df.groupby('grid_cell')['checklist_id'].nunique().reset_index(name='observer_effort')
    
    df = df.merge(effort, on='grid_cell', how='left')
    logger.info("Calculated observer effort covariates.")
    return df

def apply_tail_preserving_sampling(df: pd.DataFrame, target_size: Optional[int] = None) -> pd.DataFrame:
    """
    Apply tail-preserving stratified sampling to ensure representation of early arrivals.
    This is a placeholder for the actual implementation which would require real data distribution.
    """
    # For now, return the df as is; actual implementation would require distribution analysis
    logger.warning("Tail-preserving sampling not fully implemented; returning original data.")
    return df

def run_preprocessing_pipeline(
    raw_ebird_path: Path,
    raw_climate_path: Path,
    output_path: Path,
    config: Optional[Config] = None,
    min_observations: int = 5
) -> pd.DataFrame:
    """
    Run the full preprocessing pipeline:
    1. Load raw eBird data
    2. Filter to migratory species
    3. Assign grid cells
    4. Aggregate to weekly grid
    5. Compute phenology metrics
    6. Mark insufficient data
    7. Calculate observer effort
    8. Save output
    
    Args:
        raw_ebird_path: Path to raw eBird CSV file
        raw_climate_path: Path to raw climate parquet file
        output_path: Path to save processed output
        config: Configuration object (optional)
        min_observations: Minimum observations threshold for data quality (default: 5)
    
    Returns:
        Processed DataFrame
    """
    if config is None:
        config = get_config()
    
    logger.info("Starting preprocessing pipeline...")
    
    # Load eBird data
    logger.info(f"Loading eBird data from {raw_ebird_path}")
    ebird_df = pd.read_csv(raw_ebird_path)
    
    # Filter to migratory species
    ebird_df = filter_migratory_species(ebird_df)
    
    # Assign grid cells
    grid_res = config.GRID_RES if hasattr(config, 'GRID_RES') else 0.5
    ebird_df = add_grid_cells(ebird_df, grid_res=grid_res)
    
    # Aggregate to weekly grid
    ebird_df = aggregate_to_weekly_grid(ebird_df)
    
    # Compute phenology metrics
    ebird_df = compute_phenology_metrics(ebird_df)
    
    # Mark insufficient data
    ebird_df = mark_insufficient_data(ebird_df, min_observations=min_observations)
    
    # Calculate observer effort
    ebird_df = calculate_observer_effort(ebird_df)
    
    # Save output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ebird_df.to_parquet(output_path, index=False)
    logger.info(f"Preprocessing complete. Output saved to {output_path}")
    
    return ebird_df
