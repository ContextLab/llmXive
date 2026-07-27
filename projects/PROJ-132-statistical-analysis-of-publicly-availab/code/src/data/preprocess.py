import os
import sys
import hashlib
import yaml
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
import pandas as pd
import numpy as np

# Import logging helpers from existing infrastructure
from src.lib.logging_config import log_insufficient_data, get_logger

# Import config for threshold (though task specifies < 5, we use config for flexibility)
from src.lib.config import get_config

logger = get_logger(__name__)

def verify_checksums(data_dir: Path, state_file: Path) -> bool:
    """Verify data checksums against stored state."""
    if not state_file.exists():
        logger.warning(f"State file not found: {state_file}")
        return False
    
    with open(state_file, 'r') as f:
        state = yaml.safe_load(f)
    
    artifact_hashes = state.get('artifact_hashes', {})
    for name, expected_hash in artifact_hashes.items():
        file_path = data_dir / name
        if not file_path.exists():
            logger.error(f"Missing file for checksum verification: {file_path}")
            return False
        
        with open(file_path, 'rb') as f:
            actual_hash = hashlib.sha256(f.read()).hexdigest()
        
        if actual_hash != expected_hash:
            logger.error(f"Checksum mismatch for {name}: expected {expected_hash}, got {actual_hash}")
            return False
    
    logger.info("All checksums verified successfully.")
    return True

def filter_migratory_species(df: pd.DataFrame, migratory_list: List[str]) -> pd.DataFrame:
    """Filter eBird data to only include migratory species."""
    if 'species' not in df.columns:
        raise ValueError("DataFrame must contain 'species' column")
    
    return df[df['species'].isin(migratory_list)].copy()

def assign_grid_cell(lat: float, lon: float, grid_res: float = 0.5) -> Tuple[float, float]:
    """Assign a grid cell ID based on latitude and longitude."""
    grid_lat = np.floor(lat / grid_res) * grid_res
    grid_lon = np.floor(lon / grid_res) * grid_res
    return grid_lat, grid_lon

def add_grid_cells(df: pd.DataFrame, grid_res: float = 0.5) -> pd.DataFrame:
    """Add grid cell columns to the DataFrame."""
    if 'lat' not in df.columns or 'lon' not in df.columns:
        raise ValueError("DataFrame must contain 'lat' and 'lon' columns")
    
    df['grid_cell'] = df.apply(
        lambda row: f"{assign_grid_cell(row['lat'], row['lon'], grid_res)[0]}_{assign_grid_cell(row['lat'], row['lon'], grid_res)[1]}",
        axis=1
    )
    return df

def aggregate_to_weekly_grid(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate eBird data to weekly counts per grid cell."""
    if 'date' not in df.columns:
        raise ValueError("DataFrame must contain 'date' column")
    
    df['date'] = pd.to_datetime(df['date'])
    df['week'] = df['date'].dt.isocalendar().week
    df['year'] = df['date'].dt.year
    
    agg_df = df.groupby(['species', 'grid_cell', 'week', 'year']).agg({
        'count': 'sum'
    }).reset_index()
    
    return agg_df

def compute_phenology_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute phenology metrics: first_arrival, median_arrival, stopover_duration."""
    if not {'species', 'grid_cell', 'week', 'count'}.issubset(df.columns):
        raise ValueError("DataFrame must contain species, grid_cell, week, and count columns")
    
    def calculate_metrics(group):
        if group['count'].sum() == 0:
            return pd.Series({
                'first_arrival': np.nan,
                'median_arrival': np.nan,
                'stopover_duration': np.nan
            })
        
        # Weighted average for median
        weeks = group['week'].values
        counts = group['count'].values
        total = counts.sum()
        
        cumulative = np.cumsum(counts)
        median_idx = np.searchsorted(cumulative, total / 2)
        median_week = weeks[median_idx] if median_idx < len(weeks) else weeks[-1]
        
        # First arrival
        first_week = weeks[np.argmax(counts > 0)]
        
        # Stopover duration (simplified: weeks with non-zero counts)
        non_zero_weeks = weeks[counts > 0]
        duration = len(non_zero_weeks) if len(non_zero_weeks) > 0 else 0
        
        return pd.Series({
            'first_arrival': first_week,
            'median_arrival': median_week,
            'stopover_duration': duration
        })
    
    metrics_df = df.groupby(['species', 'grid_cell']).apply(calculate_metrics).reset_index()
    return metrics_df

def mark_insufficient_data(df: pd.DataFrame, min_obs: int = 5) -> pd.DataFrame:
    """
    Mark grid cells as 'insufficient' if observation density is below threshold.
    
    This function implements the logic for T018:
    - If count < 5 observations per grid cell, set data_quality='insufficient'
    - Log the species, grid cell, and reason to logs/pipeline.log
    - Return the dataframe with the new 'data_quality' column
    
    Args:
        df: DataFrame with columns including 'species', 'grid_cell', 'count' (or similar observation metric)
        min_obs: Minimum number of observations required (default 5)
    
    Returns:
        DataFrame with 'data_quality' column added
    """
    if 'count' not in df.columns and 'observation_count' not in df.columns:
        # Try to infer observation count if not explicitly named
        count_col = next((col for col in df.columns if 'count' in col.lower()), None)
        if count_col is None:
            raise ValueError("DataFrame must contain an observation count column")
    else:
        count_col = 'count' if 'count' in df.columns else 'observation_count'
    
    if 'species' not in df.columns or 'grid_cell' not in df.columns:
        raise ValueError("DataFrame must contain 'species' and 'grid_cell' columns")
    
    # Initialize data_quality column
    df['data_quality'] = 'sufficient'
    
    # Identify insufficient cells
    insufficient_mask = df[count_col] < min_obs
    insufficient_cells = df[insufficient_mask]
    
    # Log each insufficient cell
    for _, row in insufficient_cells.iterrows():
        species = row['species']
        grid_cell = row['grid_cell']
        obs_count = row[count_col]
        
        log_message = (
            f"Insufficient data: Species='{species}', Grid Cell='{grid_cell}', "
            f"Observations={obs_count} (threshold={min_obs})"
        )
        log_insufficient_data(species, grid_cell, obs_count, min_obs)
        logger.warning(log_message)
    
    # Mark insufficient cells
    df.loc[insufficient_mask, 'data_quality'] = 'insufficient'
    
    logger.info(f"Marked {insufficient_mask.sum()} grid cells as 'insufficient' data.")
    
    return df

def calculate_observer_effort(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate observer effort covariates to control for sampling bias."""
    if 'checklist_id' not in df.columns:
        logger.warning("checklist_id not found, skipping observer effort calculation")
        df['observer_effort'] = 1.0
        return df
    
    effort_by_cell = df.groupby('grid_cell')['checklist_id'].nunique().reset_index()
    effort_by_cell.columns = ['grid_cell', 'observer_effort']
    
    df = df.merge(effort_by_cell[['grid_cell', 'observer_effort']], on='grid_cell', how='left')
    return df

def run_preprocessing_pipeline(data_dir: Path, output_dir: Path, config: Optional[Dict[str, Any]] = None) -> Path:
    """
    Run the full preprocessing pipeline including T018 logic.
    
    Steps:
    1. Verify checksums
    2. Filter migratory species
    3. Assign grid cells
    4. Aggregate to weekly grid
    5. Compute phenology metrics
    6. Mark insufficient data (T018)
    7. Calculate observer effort
    8. Filter out insufficient cells for downstream modeling
    
    Returns:
        Path to the final processed dataset
    """
    logger.info("Starting preprocessing pipeline...")
    
    # Load raw data (simplified for this task; actual implementation would load from files)
    # Assuming ebird data is available at data_dir / 'ebird' / 'processed.csv'
    ebird_path = data_dir / 'ebird' / 'processed.csv'
    if not ebird_path.exists():
        raise FileNotFoundError(f"eBird data not found at {ebird_path}")
    
    df = pd.read_csv(ebird_path)
    logger.info(f"Loaded {len(df)} records from eBird data.")
    
    # Filter migratory species (simplified list)
    migratory_species = ['Turdus migratorius', 'Setophaga ruticilla', 'Archilochus colubris']
    df = filter_migratory_species(df, migratory_species)
    
    # Add grid cells
    grid_res = get_config().GRID_RES if get_config() else 0.5
    df = add_grid_cells(df, grid_res)
    
    # Aggregate to weekly grid
    df = aggregate_to_weekly_grid(df)
    
    # Compute phenology metrics
    phenology_df = compute_phenology_metrics(df)
    
    # Merge phenology metrics back
    df = df.merge(phenology_df, on=['species', 'grid_cell'], how='left')
    
    # T018: Mark insufficient data
    df = mark_insufficient_data(df, min_obs=5)
    
    # Calculate observer effort
    df = calculate_observer_effort(df)
    
    # Filter out insufficient cells for downstream modeling
    modeling_df = df[df['data_quality'] == 'sufficient'].copy()
    logger.info(f"Filtered out {len(df) - len(modeling_df)} insufficient cells. "
               f"Remaining for modeling: {len(modeling_df)}")
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save results
    output_path = output_dir / 'preprocessed_data.csv'
    modeling_df.to_csv(output_path, index=False)
    logger.info(f"Preprocessing complete. Output saved to {output_path}")
    
    return output_path

def main():
    """Main entry point for preprocessing script."""
    data_dir = Path('data/raw')
    output_dir = Path('data/processed')
    
    try:
        result_path = run_preprocessing_pipeline(data_dir, output_dir)
        print(f"Pipeline completed successfully. Output: {result_path}")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
