import os
import sys
import hashlib
import yaml
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime

# Import existing utilities from project
from src.config import setup_logging
from src.data.download import get_clo_migratory_list, check_real_data_available
from src.data.impute import run_imputation_pipeline

logger = logging.getLogger(__name__)

# Constants (matching T010a)
SEED: int = 42
GRID_RES: float = 0.5
PERMUTATIONS: int = 10000

def load_ebird_data(data_path: str) -> pd.DataFrame:
    """Load eBird data from parquet or csv."""
    path = Path(data_path)
    if path.suffix == '.parquet':
        return pd.read_parquet(path)
    elif path.suffix == '.csv':
        return pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")

def filter_migratory_species(df: pd.DataFrame, migratory_list_path: str) -> pd.DataFrame:
    """Filter eBird records to migratory species using CLO list."""
    migratory_species = get_clo_migratory_list(migratory_list_path)
    return df[df['species'].isin(migratory_species)]

def filter_date_range(df: pd.DataFrame, start_year: int = 2020, end_year: int = 2024) -> pd.DataFrame:
    """Filter records to specified date range."""
    df['date'] = pd.to_datetime(df['date'])
    return df[(df['date'].dt.year >= start_year) & (df['date'].dt.year <= end_year)]

def assign_grid_cell(df: pd.DataFrame, grid_res: float = GRID_RES) -> pd.DataFrame:
    """Assign grid cell to each record based on lat/lon."""
    df['grid_cell'] = (
        df['lat'].round(grid_res) * 100 + df['lon'].round(grid_res)
    ).astype(int)
    return df

def aggregate_to_weekly_grid(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate records to weekly counts per grid cell."""
    df['week'] = df['date'].dt.isocalendar().week
    df['year'] = df['date'].dt.year
    
    aggregated = df.groupby(['species', 'grid_cell', 'year', 'week']).agg({
        'count': 'sum',
        'checklist_id': 'first'  # Keep one checklist_id for provenance
    }).reset_index()
    
    return aggregated

def compute_phenology_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute phenology metrics: first_arrival, median_arrival, stopover_duration."""
    # Group by species, grid_cell, year
    result = []
    
    for (species, grid_cell, year), group in df.groupby(['species', 'grid_cell', 'year']):
        sorted_group = group.sort_values('week')
        
        first_arrival = sorted_group['week'].min()
        median_arrival = sorted_group['week'].median()
        
        # Stopover duration: 90th percentile - 10th percentile
        weeks = sorted_group['week'].values
        low_pct = int(np.percentile(weeks, 10))
        high_pct = int(np.percentile(weeks, 90))
        stopover_duration = high_pct - low_pct
        
        result.append({
            'species': species,
            'grid_cell': grid_cell,
            'year': year,
            'first_arrival': first_arrival,
            'median_arrival': median_arrival,
            'stopover_duration': stopover_duration
        })
    
    return pd.DataFrame(result)

def mark_insufficient_cells(df: pd.DataFrame, min_count: int = 5) -> pd.DataFrame:
    """Mark grid cells with insufficient data."""
    df['data_quality'] = 'sufficient'
    insufficient_mask = df['count'] < min_count
    df.loc[insufficient_mask, 'data_quality'] = 'insufficient'
    
    # Log insufficient cells
    insufficient_cells = df[insufficient_mask][['species', 'grid_cell', 'count']]
    if not insufficient_cells.empty:
        logger.warning(f"Marked {len(insufficient_cells)} cells as insufficient data")
    
    return df

def merge_climate_data(df: pd.DataFrame, climate_data: pd.DataFrame) -> pd.DataFrame:
    """Merge climate data with eBird aggregated data."""
    # Ensure grid_cell is same type
    df['grid_cell'] = df['grid_cell'].astype(int)
    climate_data['grid_cell'] = climate_data['grid_cell'].astype(int)
    
    merged = pd.merge(
        df,
        climate_data[['grid_cell', 'year', 'temp_avg', 'precip_total', 'is_imputed']],
        on=['grid_cell', 'year'],
        how='left'
    )
    
    return merged

def generate_provenance(processed_df: pd.DataFrame, raw_df: pd.DataFrame, output_path: str) -> None:
    """
    Generate provenance mapping from processed rows back to original checklist_ids.
    
    Args:
        processed_df: The processed/aggregated DataFrame
        raw_df: The original raw eBird DataFrame
        output_path: Path to write the JSON mapping file
    """
    logger.info("Generating provenance mapping...")
    
    # Create mapping: processed row -> original checklist_ids
    mapping = []
    
    for idx, row in processed_df.iterrows():
        species = row['species']
        grid_cell = row['grid_cell']
        year = row['year']
        week = row['week']
        
        # Find matching checklist_ids in raw data
        # Note: In aggregated data, we kept 'checklist_id' from first record
        # For full provenance, we'd need to track all contributing checklists
        # Here we use the stored checklist_id from aggregation
        checklist_id = row.get('checklist_id')
        
        if pd.notna(checklist_id):
            mapping.append({
                'processed_row_idx': int(idx),
                'species': species,
                'grid_cell': int(grid_cell),
                'year': int(year),
                'week': int(week),
                'original_checklist_id': str(checklist_id)
            })
    
    # Verify integrity: all checklist_ids in mapping exist in raw data
    if raw_df is not None and 'checklist_id' in raw_df.columns:
        raw_checklist_ids = set(raw_df['checklist_id'].astype(str))
        mapping_checklist_ids = set(m['original_checklist_id'] for m in mapping)
        
        missing = mapping_checklist_ids - raw_checklist_ids
        if missing:
            logger.warning(f"Found {len(missing)} checklist_ids in mapping not in raw data")
        else:
            logger.info("Provenance integrity verified: all checklist_ids exist in raw data")
    
    # Write mapping to JSON
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(mapping, f, indent=2)
    
    logger.info(f"Provenance mapping written to {output_path}")

def run_preprocessing_pipeline(
    ebird_data_path: str,
    climate_data_path: str,
    migratory_list_path: str,
    output_path: str,
    provenance_path: str
) -> pd.DataFrame:
    """
    Run the full preprocessing pipeline.
    
    Args:
        ebird_data_path: Path to raw eBird data
        climate_data_path: Path to climate data
        migratory_list_path: Path to CLO migratory species list
        output_path: Path to write processed data
        provenance_path: Path to write provenance mapping
        
    Returns:
        Processed DataFrame
    """
    logger.info("Starting preprocessing pipeline...")
    
    # 1. Load raw data
    raw_df = load_ebird_data(ebird_data_path)
    logger.info(f"Loaded {len(raw_df)} raw eBird records")
    
    # 2. Filter to migratory species
    df = filter_migratory_species(raw_df, migratory_list_path)
    logger.info(f"Filtered to {len(df)} migratory species records")
    
    # 3. Filter date range
    df = filter_date_range(df)
    logger.info(f"Filtered to date range: {len(df)} records")
    
    # 4. Assign grid cells
    df = assign_grid_cell(df)
    
    # 5. Aggregate to weekly grid
    aggregated = aggregate_to_weekly_grid(df)
    logger.info(f"Aggregated to {len(aggregated)} weekly grid cells")
    
    # 6. Mark insufficient cells
    aggregated = mark_insufficient_cells(aggregated)
    
    # 7. Merge climate data
    climate_df = load_ebird_data(climate_data_path)
    final_df = merge_climate_data(aggregated, climate_df)
    
    # 8. Compute phenology metrics
    phenology_df = compute_phenology_metrics(final_df)
    
    # 9. Generate provenance mapping
    generate_provenance(phenology_df, raw_df, provenance_path)
    
    # 10. Write output
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    phenology_df.to_parquet(output_path, index=False)
    
    logger.info(f"Preprocessing complete. Output written to {output_path}")
    return phenology_df

def main():
    """Main entry point for preprocessing pipeline."""
    logger = setup_logging()
    
    # Paths (adjust based on actual project structure)
    base_path = Path(__file__).parent.parent.parent
    ebird_path = base_path / "data" / "raw" / "ebird_sample.parquet"
    climate_path = base_path / "data" / "raw" / "climate.parquet"
    migratory_path = base_path / "data" / "raw" / "clo_migratory_list.csv"
    output_path = base_path / "data" / "processed" / "phenology_metrics.parquet"
    provenance_path = base_path / "data" / "provenance" / "row_mapping.json"
    
    # Verify data availability
    if not check_real_data_available(ebird_path):
        logger.error(f"eBird data not found at {ebird_path}")
        sys.exit(1)
    
    # Run pipeline
    run_preprocessing_pipeline(
        ebird_data_path=str(ebird_path),
        climate_data_path=str(climate_path),
        migratory_list_path=str(migratory_path),
        output_path=str(output_path),
        provenance_path=str(provenance_path)
    )

if __name__ == "__main__":
    main()
