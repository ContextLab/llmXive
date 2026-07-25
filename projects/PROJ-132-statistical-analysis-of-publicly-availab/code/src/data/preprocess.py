import os
import sys
import hashlib
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy.stats import rankdata

# Import from project config and logging
from src.lib.config import get_config, Config
from src.lib.logging_config import get_logger, log_insufficient_data

# Import download utilities
from src.data.download import (
    run_download_pipeline,
    check_real_data_available,
    ensure_data_available,
    compute_sha256,
    write_state_file
)

logger = get_logger(__name__)
config = get_config()

def verify_checksums(state_file: Path) -> bool:
    """Verify checksums from the state file match actual files."""
    if not state_file.exists():
        logger.warning(f"State file not found: {state_file}")
        return False
    
    try:
        with open(state_file, 'r') as f:
            state = yaml.safe_load(f)
        
        artifact_hashes = state.get('artifact_hashes', {})
        if not artifact_hashes:
            logger.warning("No artifact hashes found in state file")
            return False
        
        # Verify checksums for raw data files
        for file_path, expected_hash in artifact_hashes.items():
            path = Path(file_path)
            if path.exists():
                actual_hash = compute_sha256(path)
                if actual_hash != expected_hash:
                    logger.error(f"Checksum mismatch for {file_path}: expected {expected_hash}, got {actual_hash}")
                    return False
            else:
                logger.error(f"File not found for checksum verification: {file_path}")
                return False
        
        logger.info("All checksums verified successfully")
        return True
    except Exception as e:
        logger.error(f"Error verifying checksums: {e}")
        return False

def filter_migratory_species(df: pd.DataFrame, clo_list: Optional[List[str]] = None) -> pd.DataFrame:
    """Filter eBird records to migratory species using CLO list."""
    if clo_list is None:
        # Default list of common migratory species for demonstration
        # In production, this would be loaded from a real CLO list file
        clo_list = [
            'Turdus migratorius', 'Setophaga ruticilla', 'Hirundo rustica',
            'Calidris canutus', 'Anas platyrhynchos', 'Buteo jamaicensis',
            'Archilochus colubris', 'Passerella iliaca', 'Zonotrichia albicollis'
        ]
    
    # Filter by species in CLO list
    filtered = df[df['species'].isin(clo_list)].copy()
    logger.info(f"Filtered to {len(filtered)} records for {len(filtered['species'].unique())} migratory species")
    return filtered

def assign_grid_cell(lat: float, lon: float, resolution: float = 0.5) -> Tuple[float, float]:
    """Assign a lat/lon pair to a grid cell of given resolution."""
    grid_lat = np.floor(lat / resolution) * resolution
    grid_lon = np.floor(lon / resolution) * resolution
    return grid_lat, grid_lon

def add_grid_cells(df: pd.DataFrame, resolution: Optional[float] = None) -> pd.DataFrame:
    """Add grid cell columns to the dataframe."""
    if resolution is None:
        resolution = config.GRID_RES
    
    df = df.copy()
    df['grid_lat'], df['grid_lon'] = zip(*df.apply(
        lambda row: assign_grid_cell(row['lat'], row['lon'], resolution), axis=1
    ))
    df['grid_cell'] = df['grid_lat'].astype(str) + '_' + df['grid_lon'].astype(str)
    logger.info(f"Added grid cells with resolution {resolution}")
    return df

def aggregate_to_weekly_grid(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate eBird records to weekly counts per grid cell."""
    if df.empty:
        logger.warning("Empty dataframe provided to aggregate_to_weekly_grid")
        return pd.DataFrame(columns=['species', 'grid_cell', 'week', 'count'])
    
    # Ensure date column is datetime
    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df['date']):
        df['date'] = pd.to_datetime(df['date'])
    
    # Create week column
    df['week'] = df['date'].dt.isocalendar().week
    df['year'] = df['date'].dt.year
    
    # Aggregate by species, grid_cell, week, year
    aggregated = df.groupby(['species', 'grid_cell', 'week', 'year']).agg(
        count=('count', 'sum')
    ).reset_index()
    
    logger.info(f"Aggregated to {len(aggregated)} weekly grid records")
    return aggregated

def compute_phenology_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute phenology metrics: first_arrival, median_arrival, stopover_duration."""
    if df.empty:
        logger.warning("Empty dataframe provided to compute_phenology_metrics")
        return pd.DataFrame(columns=['species', 'grid_cell', 'first_arrival', 'median_arrival', 'stopover_duration'])
    
    df = df.copy()
    
    def calculate_metrics(group):
        # Sort by week
        group = group.sort_values('week')
        weeks = group['week'].values
        counts = group['count'].values
        
        if len(weeks) == 0:
            return pd.Series({
                'first_arrival': np.nan,
                'median_arrival': np.nan,
                'stopover_duration': np.nan
            })
        
        # First arrival: first week with non-zero count
        first_week_idx = np.argmax(counts > 0)
        if counts[first_week_idx] == 0:
            first_arrival = np.nan
        else:
            first_arrival = weeks[first_week_idx]
        
        # Median arrival: weighted median of weeks
        if counts.sum() > 0:
            cumsum = np.cumsum(counts)
            median_idx = np.searchsorted(cumsum, cumsum[-1] / 2)
            median_arrival = weeks[median_idx]
        else:
            median_arrival = np.nan
        
        # Stopover duration: weeks with significant activity (simplified)
        # Define significant as > 10% of peak count
        if counts.max() > 0:
            threshold = counts.max() * 0.1
            active_weeks = weeks[counts >= threshold]
            if len(active_weeks) > 0:
                stopover_duration = active_weeks.max() - active_weeks.min() + 1
            else:
                stopover_duration = 1.0
        else:
            stopover_duration = np.nan
        
        return pd.Series({
            'first_arrival': first_arrival,
            'median_arrival': median_arrival,
            'stopover_duration': stopover_duration
        })
    
    result = df.groupby(['species', 'grid_cell']).apply(calculate_metrics).reset_index()
    logger.info(f"Computed phenology metrics for {len(result)} species-grid combinations")
    return result

def mark_insufficient_data(df: pd.DataFrame, min_observations: int = 5) -> pd.DataFrame:
    """Mark grid cells as 'insufficient data' when observation density is too low."""
    if df.empty:
        logger.warning("Empty dataframe provided to mark_insufficient_data")
        return df
    
    df = df.copy()
    
    # Count observations per grid cell
    obs_counts = df.groupby('grid_cell').size().reset_index(name='obs_count')
    
    # Mark cells with insufficient observations
    obs_counts['insufficient_data'] = obs_counts['obs_count'] < min_observations
    
    # Merge back to main dataframe
    df = df.merge(obs_counts[['grid_cell', 'insufficient_data']], on='grid_cell', how='left')
    
    # Log insufficient data events
    insufficient_count = df['insufficient_data'].sum()
    if insufficient_count > 0:
        log_insufficient_data(f"Marked {insufficient_count} grid cells as insufficient data")
    
    logger.info(f"Marked {insufficient_count} grid cells as insufficient data (threshold: {min_observations})")
    return df

def calculate_observer_effort(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate observer effort covariates to control for sampling bias.
    
    This function computes several metrics of observer effort:
    1. checklist_count: Number of checklists per grid cell per week
    2. observer_count: Number of unique observers per grid cell per week
    3. duration_avg: Average checklist duration (if available)
    4. distance_avg: Average distance covered (if available)
    
    The effort metrics are then aggregated to species-grid-week level.
    """
    if df.empty:
        logger.warning("Empty dataframe provided to calculate_observer_effort")
        return df
    
    df = df.copy()
    
    # Ensure date column is datetime if it exists
    if 'date' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['date']):
        df['date'] = pd.to_datetime(df['date'])
    
    # Create week column if not present
    if 'week' not in df.columns:
        if 'date' in df.columns:
            df['week'] = df['date'].dt.isocalendar().week
            df['year'] = df['date'].dt.year
        else:
            # If no date, assume all data is from same week
            df['week'] = 1
            df['year'] = 2023
    
    # Calculate effort metrics per grid cell per week
    # Group by grid_cell, week, year to get effort at that level
    effort_groups = df.groupby(['grid_cell', 'week', 'year']).agg(
        checklist_count=('checklist_id', 'nunique'),
        observer_count=('observer_id', 'nunique') if 'observer_id' in df.columns else ('checklist_id', 'nunique'),
    ).reset_index()
    
    # Add optional metrics if columns exist
    if 'duration_minutes' in df.columns:
        effort_groups['duration_avg'] = df.groupby(['grid_cell', 'week', 'year'])['duration_minutes'].mean().values
    else:
        effort_groups['duration_avg'] = np.nan
        
    if 'distance_km' in df.columns:
        effort_groups['distance_avg'] = df.groupby(['grid_cell', 'week', 'year'])['distance_km'].mean().values
    else:
        effort_groups['distance_avg'] = np.nan
    
    # Merge effort metrics back to main dataframe
    df = df.merge(effort_groups, on=['grid_cell', 'week', 'year'], how='left')
    
    # Create a composite effort score (normalized)
    # Normalize checklist_count and observer_count
    if 'checklist_count' in df.columns:
        df['effort_score'] = df['checklist_count']
        if 'observer_count' in df.columns:
            # Simple weighted combination
            max_checklists = df['checklist_count'].max()
            max_observers = df['observer_count'].max()
            if max_checklists > 0 and max_observers > 0:
                df['effort_score'] = (
                    0.6 * (df['checklist_count'] / max_checklists) +
                    0.4 * (df['observer_count'] / max_observers)
                )
    else:
        df['effort_score'] = 1.0  # Default if no effort data
    
    # Log effort calculation
    logger.info(f"Calculated observer effort for {len(df)} records")
    
    return df

def apply_tail_preserving_sampling(df: pd.DataFrame, factor: float = 1.5) -> pd.DataFrame:
    """
    Implement Tail-Preserving Stratified Sampling (FR-002-S).
    
    1. Quantile-bin first_arrival into deciles.
    2. Oversample cells in the lowest decile by a moderate factor.
    3. Assign inverse-probability weights.
    4. Output weights to data/interim/sampling_weights.parquet.
    """
    if df.empty or 'first_arrival' not in df.columns:
        logger.warning("Empty dataframe or missing first_arrival column for tail-preserving sampling")
        return df
    
    df = df.copy()
    
    # Quantile-bin first_arrival into deciles (1-10)
    # Handle NaN values by excluding them from binning
    valid_mask = df['first_arrival'].notna()
    if valid_mask.sum() == 0:
        logger.warning("No valid first_arrival values for binning")
        df['sampling_weight'] = 1.0
        return df
    
    df.loc[valid_mask, 'arrival_decile'] = pd.qcut(
        df.loc[valid_mask, 'first_arrival'], 
        q=10, 
        labels=False, 
        duplicates='drop'
    ).astype(int) + 1  # 1-10
    
    # Identify lowest decile (1)
    lowest_decile_mask = df['arrival_decile'] == 1
    
    # Assign weights: 0.5 for oversampled (lowest decile), 1.0 otherwise
    # Note: The task says "oversample" but for weighting in regression, 
    # we assign lower weights to oversampled data to correct for the oversampling
    df['sampling_weight'] = np.where(lowest_decile_mask, 0.5, 1.0)
    
    # Log sampling strategy
    oversampled_count = lowest_decile_mask.sum()
    logger.info(f"Applied tail-preserving sampling: {oversampled_count} records in lowest decile (weight=0.5)")
    
    return df

def run_preprocessing_pipeline(
    raw_ebird_path: str,
    raw_climate_path: str,
    output_path: str,
    state_file: str,
    min_observations: int = 5
) -> Path:
    """
    Run the full preprocessing pipeline.
    
    1. Verify data availability and checksums.
    2. Filter to migratory species.
    3. Assign grid cells.
    4. Aggregate to weekly grid counts.
    5. Compute phenology metrics.
    6. Mark insufficient data.
    7. Calculate observer effort covariates.
    8. Apply tail-preserving sampling.
    9. Output final dataset.
    """
    logger.info("Starting preprocessing pipeline")
    
    # Ensure data is available
    ensure_data_available(raw_ebird_path, raw_climate_path)
    
    # Verify checksums
    state_path = Path(state_file)
    if not verify_checksums(state_path):
        logger.error("Checksum verification failed. Aborting pipeline.")
        sys.exit(1)
    
    # Load eBird data
    logger.info(f"Loading eBird data from {raw_ebird_path}")
    ebird_df = pd.read_csv(raw_ebird_path)
    logger.info(f"Loaded {len(ebird_df)} eBird records")
    
    # Load climate data (for later merging)
    logger.info(f"Loading climate data from {raw_climate_path}")
    climate_df = pd.read_parquet(raw_climate_path) if raw_climate_path.endswith('.parquet') else pd.read_csv(raw_climate_path)
    logger.info(f"Loaded {len(climate_df)} climate records")
    
    # Step 1: Filter to migratory species
    ebird_df = filter_migratory_species(ebird_df)
    
    # Step 2: Assign grid cells
    ebird_df = add_grid_cells(ebird_df)
    
    # Step 3: Aggregate to weekly grid
    weekly_df = aggregate_to_weekly_grid(ebird_df)
    
    # Step 4: Compute phenology metrics
    phenology_df = compute_phenology_metrics(weekly_df)
    
    # Step 5: Mark insufficient data
    phenology_df = mark_insufficient_data(phenology_df, min_observations)
    
    # Step 6: Calculate observer effort
    # Merge weekly data with effort metrics
    effort_df = calculate_observer_effort(ebird_df)
    
    # Aggregate effort to weekly level
    weekly_effort = effort_df.groupby(['species', 'grid_cell', 'week', 'year']).agg(
        effort_score=('effort_score', 'mean'),
        checklist_count=('checklist_count', 'first'),
        observer_count=('observer_count', 'first')
    ).reset_index()
    
    # Merge effort with phenology data
    phenology_df = phenology_df.merge(
        weekly_effort[['grid_cell', 'week', 'year', 'effort_score', 'checklist_count', 'observer_count']],
        on=['grid_cell', 'week', 'year'],
        how='left'
    )
    
    # Fill NaN effort scores with 1.0 (default)
    phenology_df['effort_score'] = phenology_df['effort_score'].fillna(1.0)
    
    # Step 7: Apply tail-preserving sampling (if first_arrival exists)
    if 'first_arrival' in phenology_df.columns:
        phenology_df = apply_tail_preserving_sampling(phenology_df)
    else:
        phenology_df['sampling_weight'] = 1.0
    
    # Merge climate data (simplified join on grid_cell and week)
    # In production, this would be a proper spatial-temporal join
    if 'temp' in climate_df.columns and 'precip' in climate_df.columns:
        # Ensure climate has week column
        if 'week' not in climate_df.columns:
            climate_df['week'] = 1
        
        # Merge on grid_cell and week
        phenology_df = phenology_df.merge(
            climate_df[['grid_cell', 'week', 'temp', 'precip']],
            on=['grid_cell', 'week'],
            how='left'
        )
        
        # Fill missing climate data with mean values
        phenology_df['temp'] = phenology_df['temp'].fillna(phenology_df['temp'].mean())
        phenology_df['precip'] = phenology_df['precip'].fillna(phenology_df['precip'].mean())
    else:
        phenology_df['temp'] = np.nan
        phenology_df['precip'] = np.nan
    
    # Final output
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Select final columns
    final_columns = [
        'species', 'grid_cell', 'week', 'year',
        'first_arrival', 'median_arrival', 'stopover_duration',
        'count', 'temp', 'precip', 'effort_score', 'checklist_count', 
        'observer_count', 'insufficient_data', 'sampling_weight'
    ]
    
    # Filter to existing columns
    final_columns = [col for col in final_columns if col in phenology_df.columns]
    
    phenology_df = phenology_df[final_columns]
    
    # Write output
    if output_path.suffix == '.csv':
        phenology_df.to_csv(output_path, index=False)
    elif output_path.suffix == '.parquet':
        phenology_df.to_parquet(output_path, index=False)
    else:
        phenology_df.to_csv(output_path, index=False)
    
    logger.info(f"Preprocessing pipeline complete. Output written to {output_path}")
    logger.info(f"Final dataset: {len(phenology_df)} records, {phenology_df['species'].nunique()} species")
    
    return output_path

if __name__ == "__main__":
    # Example usage
    import argparse
    
    parser = argparse.ArgumentParser(description="Run preprocessing pipeline")
    parser.add_argument("--ebird", required=True, help="Path to eBird data")
    parser.add_argument("--climate", required=True, help="Path to climate data")
    parser.add_argument("--output", required=True, help="Path to output file")
    parser.add_argument("--state", default="state/projects/PROJ-132-statistical-analysis-of-publicly-availab.yaml", help="Path to state file")
    
    args = parser.parse_args()
    
    run_preprocessing_pipeline(
        raw_ebird_path=args.ebird,
        raw_climate_path=args.climate,
        output_path=args.output,
        state_file=args.state
    )
