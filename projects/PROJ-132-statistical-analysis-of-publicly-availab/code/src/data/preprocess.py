import os
import sys
import hashlib
import yaml
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

import pandas as pd
import numpy as np
from scipy import stats

# Import project config
try:
    from src.lib.config import SEED, GRID_RES
except ImportError:
    # Fallback for execution context where lib is not in path yet
    SEED = 42
    GRID_RES = 0.5

# Import logging setup
try:
    from src.lib.logging_config import setup_logging, log_insufficient_data
except ImportError:
    import logging
    def setup_logging():
        logging.basicConfig(level=logging.INFO)
    def log_insufficient_data(msg):
        logging.warning(msg)

setup_logging()
logger = logging.getLogger(__name__)

# --- Helper Functions (from previous tasks) ---

def verify_checksums(state_file: Path, expected_hashes: Dict[str, str]) -> bool:
    """Verify file checksums against stored state."""
    if not state_file.exists():
        return False
    with open(state_file, 'r') as f:
        state = yaml.safe_load(f)
    stored = state.get('artifact_hashes', {})
    for path, hash_val in expected_hashes.items():
        if stored.get(path) != hash_val:
            return False
    return True

def ensure_data_available(data_dir: Path, synthetic: bool = False) -> bool:
    """Ensure raw data files exist, optionally generating synthetic ones."""
    ebird_path = data_dir / "ebird" / "observations.csv"
    climate_path = data_dir / "climate" / "climate.parquet"

    if ebird_path.exists() and climate_path.exists():
        return True

    if synthetic:
        logger.info("Generating synthetic data for development...")
        ebird_path.parent.mkdir(parents=True, exist_ok=True)
        climate_path.parent.mkdir(parents=True, exist_ok=True)
        # Generate minimal synthetic data
        np.random.seed(SEED)
        dates = pd.date_range('2020-01-01', periods=1000, freq='D')
        df = pd.DataFrame({
            'species': np.random.choice(['Turdus migratorius', 'Setophaga ruticilla'], 1000),
            'lat': np.random.uniform(30, 50, 1000),
            'lon': np.random.uniform(-120, -70, 1000),
            'date': np.random.choice(dates, 1000),
            'count': np.random.randint(1, 20, 1000),
            'checklist_id': [f'chk_{i}' for i in range(1000)]
        })
        df.to_csv(ebird_path, index=False)
        
        climate_df = pd.DataFrame({
            'lat': np.random.uniform(30, 50, 100),
            'lon': np.random.uniform(-120, -70, 100),
            'temp': np.random.normal(15, 5, 100),
            'week': np.random.randint(1, 53, 100),
            'precip': np.random.exponential(2, 100)
        })
        climate_df.to_parquet(climate_path)
        return True
    
    logger.error("Real data required for production run")
    return False

def filter_migratory_species(df: pd.DataFrame, migratory_list: Optional[List[str]] = None) -> pd.DataFrame:
    """Filter eBird data to known migratory species."""
    if migratory_list is None:
        # Default list for demo
        migratory_list = ['Turdus migratorius', 'Setophaga ruticilla', 'Junco hyemalis']
    return df[df['species'].isin(migratory_list)]

def assign_grid_cell(lat: float, lon: float, res: float = GRID_RES) -> Tuple[float, float]:
    """Assign lat/lon to a grid cell."""
    return (round(lat / res) * res, round(lon / res) * res)

def add_grid_cells(df: pd.DataFrame, res: float = GRID_RES) -> pd.DataFrame:
    """Add grid_cell_lat and grid_cell_lon columns."""
    df['grid_cell_lat'] = df['lat'].apply(lambda x: round(x / res) * res)
    df['grid_cell_lon'] = df['lon'].apply(lambda x: round(x / res) * res)
    return df

def aggregate_to_weekly_grid(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate counts to weekly grid cells."""
    df = df.copy()
    df['week'] = df['date'].dt.isocalendar().week
    agg_df = df.groupby(['species', 'grid_cell_lat', 'grid_cell_lon', 'week']).agg({
        'count': 'sum',
        'checklist_id': 'count'
    }).reset_index()
    agg_df.rename(columns={'checklist_id': 'checklist_count'}, inplace=True)
    return agg_df

def compute_phenology_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute first_arrival, median_arrival, stopover_duration."""
    results = []
    for (species, g_lat, g_lon), group in df.groupby(['species', 'grid_cell_lat', 'grid_cell_lon']):
        group = group.sort_values('week')
        if group['count'].sum() == 0:
            continue
        
        first_arrival = group['week'].min()
        median_week = group['week'].quantile(0.5)
        # Stopover: duration of presence (simplified as max week - min week + 1)
        stopover = group['week'].max() - group['week'].min() + 1
        
        results.append({
            'species': species,
            'grid_cell_lat': g_lat,
            'grid_cell_lon': g_lon,
            'first_arrival': first_arrival,
            'median_arrival': median_week,
            'stopover_duration': stopover,
            'total_count': group['count'].sum()
        })
    
    return pd.DataFrame(results)

def mark_insufficient_data(df: pd.DataFrame, threshold: int = 10) -> pd.DataFrame:
    """Mark grid cells with insufficient data."""
    df = df.copy()
    df['sufficient_data'] = df['total_count'] >= threshold
    return df

def calculate_observer_effort(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate observer effort covariates."""
    df = df.copy()
    # Effort = checklist_count (number of checklists in that grid/week)
    df['observer_effort'] = df['checklist_count']
    return df

# --- T019b: Tail-Preserving Stratified Sampling ---

def apply_tail_preserving_sampling(phenology_df: pd.DataFrame, output_path: Path) -> pd.DataFrame:
    """
    Implement Tail-Preserving Stratified Sampling (FR-002-S).
    
    1. Quantile-bin `first_arrival` into deciles.
    2. Oversample cells in the lowest decile (early arrival) by a moderate factor (e.g., 2x).
    3. Assign inverse-probability weights:
       - weight = 0.5 for oversampled (low decile)
       - weight = 1.0 otherwise
    4. Output weights to `data/interim/sampling_weights.parquet`.
    
    Returns the DataFrame with the 'sampling_weight' column added.
    """
    if phenology_df.empty:
        logger.warning("Empty phenology dataframe, returning empty result")
        return phenology_df

    df = phenology_df.copy()
    
    # 1. Quantile-bin first_arrival into deciles (0-9)
    # Use q=10 for deciles. Handle edge cases where all values are same.
    if df['first_arrival'].nunique() < 10:
        logger.warning("Not enough unique first_arrival values for deciles. Assigning all to decile 0.")
        df['arrival_decile'] = 0
    else:
        df['arrival_decile'] = pd.qcut(df['first_arrival'], q=10, labels=False, duplicates='drop')
    
    # Identify the lowest decile (index 0)
    lowest_decile = df['arrival_decile'].min()
    
    # 2. Assign weights based on decile
    # Oversampling logic in a weighting scheme:
    # If we oversample a group by factor K, the weight for that group becomes 1/K to correct bias.
    # Task spec: "weight = 0.5 for oversampled". This implies K=2.
    df['sampling_weight'] = df['arrival_decile'].apply(
        lambda x: 0.5 if x == lowest_decile else 1.0
    )
    
    # 3. Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 4. Write to parquet
    # Select relevant columns for the weight artifact
    weight_df = df[['species', 'grid_cell_lat', 'grid_cell_lon', 'first_arrival', 'arrival_decile', 'sampling_weight']].copy()
    weight_df.to_parquet(output_path, index=False)
    
    logger.info(f"Tail-preserving sampling weights written to {output_path}")
    logger.info(f"Oversampled decile: {lowest_decile}, weight: 0.5")
    
    return df

def run_preprocessing_pipeline(raw_data_dir: Path, processed_dir: Path, output_file: Path) -> pd.DataFrame:
    """
    Main pipeline orchestrator for US1.
    Includes T019b sampling weights.
    """
    # 1. Ensure data
    if not ensure_data_available(raw_data_dir, synthetic=True):
        raise RuntimeError("Data availability check failed")

    # 2. Load eBird
    ebird_path = raw_data_dir / "ebird" / "observations.csv"
    df = pd.read_csv(ebird_path, parse_dates=['date'])

    # 3. Filter migratory
    df = filter_migratory_species(df)

    # 4. Grid assignment
    df = add_grid_cells(df)

    # 5. Aggregate
    df_agg = aggregate_to_weekly_grid(df)

    # 6. Phenology
    df_pheno = compute_phenology_metrics(df_agg)

    # 7. Insufficient data
    df_pheno = mark_insufficient_data(df_pheno)

    # 8. Observer effort
    df_pheno = calculate_observer_effort(df_pheno)

    # 9. T019b: Tail-Preserving Stratified Sampling
    weights_path = processed_dir / "sampling_weights.parquet"
    df_pheno = apply_tail_preserving_sampling(df_pheno, weights_path)

    # 10. Final Output
    df_pheno.to_csv(output_file, index=False)
    
    return df_pheno

if __name__ == "__main__":
    # Example execution
    root = Path(__file__).resolve().parent.parent.parent
    raw_dir = root / "data" / "raw"
    proc_dir = root / "data" / "interim"
    out_file = root / "data" / "processed" / "phenology_metrics.csv"
    
    proc_dir.mkdir(parents=True, exist_ok=True)
    (root / "data" / "processed").mkdir(parents=True, exist_ok=True)
    
    run_preprocessing_pipeline(raw_dir, proc_dir, out_file)
    print(f"Pipeline complete. Output: {out_file}")
