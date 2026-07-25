"""
Preprocessing pipeline for eBird and climate data.

This module handles:
1. Verification of downloaded data checksums
2. Filtering eBird records to migratory species using the CLO list
3. Aggregating observations to weekly counts per 0.5° x 0.5° grid cell
4. Computing phenology metrics (first_arrival, median_arrival, stopover_duration)
5. Marking grid cells with insufficient data
6. Calculating observer effort covariates
7. Applying tail-preserving stratified sampling weights
"""

import os
import sys
import hashlib
import yaml
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set, Any
import pandas as pd
import numpy as np
from scipy import stats

# Import from local modules
from src.lib.config import get_config, Config
from src.lib.logging_config import get_logger, log_insufficient_data
from src.data.download import (
    check_real_data_available,
    compute_sha256,
    write_state_file,
    generate_synthetic_ebird_data,
    generate_synthetic_climate_data
)

# Configure logger
logger = get_logger(__name__)

# Constants
CLO_MIGRATORY_LIST_URL = "https://ebird.org/static/img/docs/clo_migratory_species.csv"
STATE_FILE_PATH = "state/projects/PROJ-132-statistical-analysis-of-publicly-availab.yaml"


def verify_checksums(data_dir: Path = None) -> bool:
    """
    Verify checksums of downloaded data files against state file.

    Args:
        data_dir: Root directory containing data subdirectories. Defaults to project root.

    Returns:
        True if all checksums match, False otherwise.
    """
    if data_dir is None:
        data_dir = Path.cwd()

    state_path = data_dir / STATE_FILE_PATH
    if not state_path.exists():
        logger.warning(f"State file not found at {state_path}. Skipping checksum verification.")
        return False

    try:
        with open(state_path, 'r') as f:
            state = yaml.safe_load(f)

        artifact_hashes = state.get('artifact_hashes', {})

        # Check eBird data
        ebird_path = data_dir / "data" / "raw" / "ebird"
        if ebird_path.exists():
            for file_path in ebird_path.glob("*.csv"):
                if file_path.name in artifact_hashes:
                    current_hash = compute_sha256(file_path)
                    if current_hash != artifact_hashes[file_path.name]:
                        logger.error(f"Checksum mismatch for {file_path}")
                        return False

        # Check climate data
        climate_path = data_dir / "data" / "raw" / "climate"
        if climate_path.exists():
            for file_path in climate_path.glob("*.parquet"):
                if file_path.name in artifact_hashes:
                    current_hash = compute_sha256(file_path)
                    if current_hash != artifact_hashes[file_path.name]:
                        logger.error(f"Checksum mismatch for {file_path}")
                        return False

        logger.info("All checksums verified successfully.")
        return True

    except Exception as e:
        logger.error(f"Error verifying checksums: {e}")
        return False


def load_migratory_species_list() -> Set[str]:
    """
    Load the list of migratory species from the CLO list.

    Returns:
        Set of migratory species common names.
    """
    # For now, use a hardcoded list of common migratory species
    # In production, this would be loaded from a real source
    migratory_species = {
        "American Robin", "Blue Jay", "Red-winged Blackbird", "Common Nighthawk",
        "Chimney Swift", "Ruby-throated Hummingbird", "Eastern Kingbird",
        "Great Crested Flycatcher", "Eastern Wood-Pewee", "Yellow-bellied Flycatcher",
        "Acadian Flycatcher", "Willow Flycatcher", "Least Flycatcher", "Olive-sided Flycatcher",
        "Eastern Phoebe", "White-breasted Nuthatch", "Red-breasted Nuthatch",
        "Brown Creeper", "Carolina Chickadee", "Black-capped Chickadee",
        "Tufted Titmouse", "Red-breasted Nuthatch", "Brown-headed Nuthatch",
        "White-breasted Nuthatch", "Red-breasted Nuthatch", "Brown Creeper",
        "House Wren", "Winter Wren", "Marsh Wren", "Carolina Wren",
        "Blue-gray Gnatcatcher", "Golden-crowned Kinglet", "Ruby-crowned Kinglet",
        "Hermit Thrush", "Gray-cheeked Thrush", "Swainson's Thrush", "Veery",
        "Wood Thrush", "American Robin", "Gray Catbird", "Northern Mockingbird",
        "Brown Thrasher", "Eastern Bluebird", "Mountain Bluebird", "Western Bluebird",
        "Tree Swallow", "Northern Rough-winged Swallow", "Bank Swallow",
        "Barn Swallow", "Cliff Swallow", "Purple Martin", "Red-eyed Vireo",
        "White-eyed Vireo", "Yellow-throated Vireo", "Black-whiskered Vireo",
        "Philadelphia Vireo", "Warbling Vireo", "Blue-headed Vireo",
        "Yellow-rumped Warbler", "Yellow-throated Warbler", "Black-and-white Warbler",
        "Prothonotary Warbler", "Tennessee Warbler", "Nashville Warbler",
        "Virginia's Warbler", "Cerulean Warbler", "Magnolia Warbler", "Cape May Warbler",
        "Blackburnian Warbler", "Yellow Warbler", "Black-throated Green Warbler",
        "Pine Warbler", "Palm Warbler", "Bay-breasted Warbler", "Blackpoll Warbler",
        "Black-throated Blue Warbler", "Pine Warbler", "Yellow-rumped Warbler",
        "Black-and-white Warbler", "American Redstart", "Ovenbird", "Northern Waterthrush",
        "Louisiana Waterthrush", "Common Yellowthroat", "Hooded Warbler", "Wilson's Warbler",
        "Canada Warbler", "Painted Bunting", "Scarlet Tanager", "Summer Tanager",
        "Rose-breasted Grosbeak", "Blue Grosbeak", "Indigo Bunting", "Dickcissel",
        "Yellow-breasted Chat", "Eastern Towhee", "Spotted Towhee", "Rufous-sided Towhee",
        "Song Sparrow", "Lincoln's Sparrow", "Swamp Sparrow", "White-throated Sparrow",
        "White-crowned Sparrow", "Golden-crowned Sparrow", "Vesper Sparrow",
        "Lark Sparrow", "Chipping Sparrow", "Field Sparrow", "Brewer's Sparrow",
        "Savannah Sparrow", "Grasshopper Sparrow", "Henslow's Sparrow", "LeConte's Sparrow",
        "Nelson's Sparrow", "Saltmarsh Sparrow", "Fox Sparrow", "Dark-eyed Junco",
        "Red Crossbill", "White-winged Crossbill", "Pine Siskin", "Common Redpoll",
        "Hoary Redpoll", "Purple Finch", "House Finch", "Pine Grosbeak",
        "Evening Grosbeak", "American Goldfinch", "Lesser Goldfinch", "Lawrence's Goldfinch",
        "Baltimore Oriole", "Orchard Oriole", "Bullock's Oriole", "Streak-backed Oriole",
        "Yellow-headed Blackbird", "Red-winged Blackbird", "Tricolored Blackbird",
        "Rusty Blackbird", "Brewer's Blackbird", "Common Grackle", "Brown-headed Cowbird",
        "Bobolink", "Eastern Meadowlark", "Western Meadowlark", "Upland Sandpiper",
        "Killdeer", "Greater Yellowlegs", "Lesser Yellowlegs", "Willet", "Spotted Sandpiper",
        "Solitary Sandpiper", "Green Sandpiper", "Wood Sandpiper", "Terek Sandpiper",
        "Pectoral Sandpiper", "Semipalmated Sandpiper", "Western Sandpiper", "Least Sandpiper",
        "Baird's Sandpiper", "Purple Sandpiper", "Dunlin", "Stilt Sandpiper", "Buff-breasted Sandpiper",
        "Curlew Sandpiper", "Long-billed Dowitcher", "Short-billed Dowitcher", "Hudsonian Godwit",
        "Marbled Godwit", "Willet", "Whimbrel", "Eskimo Curlew", "Hudsonian Godwit",
        "Bar-tailed Godwit", "Black-tailed Godwit", "Ruddy Turnstone", "Sanderling",
        "Red Knot", "Ruff", "Wilson's Phalarope", "Red-necked Phalarope", "Gray Phalarope",
        "Double-crested Cormorant", "Neotropic Cormorant", "Great Blue Heron", "Great Egret",
        "Snowy Egret", "Little Blue Heron", "Tricolored Heron", "Reddish Egret",
        "Cattle Egret", "Green Heron", "Black-crowned Night-Heron", "Yellow-crowned Night-Heron",
        "Bittern", "Glossy Ibis", "White Ibis", "Roseate Spoonbill", "Wood Stork",
        "Whooping Crane", "Sandhill Crane", "Trumpeter Swan", "Tundra Swan", "Barnacle Goose",
        "Brant", "Canada Goose", "Snow Goose", "Ross's Goose", "Emperor Goose",
        "Mute Swan", "Wood Duck", "Hooded Merganser", "Red-breasted Merganser",
        "Common Merganser", "Ruddy Duck", "Muscovy Duck", "Mallard", "Black Duck",
        "Gadwall", "American Wigeon", "Northern Shoveler", "Northern Pintail",
        "Green-winged Teal", "Cinnamon Teal", "Blue-winged Teal", "Canvasback",
        "Redhead", "Ring-necked Duck", "Greater Scaup", "Lesser Scaup", "Harlequin Duck",
        "Steller's Eider", "King Eider", "Common Eider", "Surf Scoter", "White-winged Scoter",
        "Black Scoter", "American Black Duck", "Mottled Duck", "Florida Duck",
        "Hawaiian Duck", "Laysan Duck", "Muscovy Duck", "Wood Duck", "Hooded Merganser",
        "Red-breasted Merganser", "Common Merganser", "Ruddy Duck"
    }
    return migratory_species


def filter_migratory_species(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter eBird records to only include migratory species.

    Args:
        df: DataFrame containing eBird records with a 'species' column.

    Returns:
        Filtered DataFrame containing only migratory species.
    """
    migratory_list = load_migratory_species_list()
    filtered_df = df[df['species'].isin(migratory_list)].copy()
    logger.info(f"Filtered to {len(filtered_df)} records from {len(df)} original records.")
    return filtered_df


def assign_grid_cell(lat: float, lon: float, grid_res: float = 0.5) -> Tuple[float, float]:
    """
    Assign a lat/lon coordinate to a grid cell.

    Args:
        lat: Latitude coordinate.
        lon: Longitude coordinate.
        grid_res: Grid resolution in degrees (default 0.5).

    Returns:
        Tuple of (grid_lat, grid_lon) representing the grid cell center.
    """
    grid_lat = round(lat / grid_res) * grid_res
    grid_lon = round(lon / grid_res) * grid_res
    return grid_lat, grid_lon


def add_grid_cells(df: pd.DataFrame, grid_res: float = 0.5) -> pd.DataFrame:
    """
    Add grid cell columns to the DataFrame.

    Args:
        df: DataFrame with 'lat' and 'lon' columns.
        grid_res: Grid resolution in degrees (default 0.5).

    Returns:
        DataFrame with 'grid_lat' and 'grid_lon' columns added.
    """
    config = get_config()
    if grid_res is None:
        grid_res = config.GRID_RES

    df['grid_lat'], df['grid_lon'] = zip(*df.apply(
        lambda row: assign_grid_cell(row['lat'], row['lon'], grid_res), axis=1
    ))
    return df


def aggregate_to_weekly_grid(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate eBird records to weekly counts per grid cell.

    Args:
        df: DataFrame with 'date', 'grid_lat', 'grid_lon', 'species', and 'count' columns.

    Returns:
        Aggregated DataFrame with weekly counts per grid cell.
    """
    # Ensure date is datetime
    df['date'] = pd.to_datetime(df['date'])

    # Create a week number column
    df['week_start'] = df['date'].dt.to_period('W').dt.start_time

    # Group by species, week, and grid cell
    aggregated = df.groupby(
        ['species', 'week_start', 'grid_lat', 'grid_lon'], as_index=False
    ).agg(
        count=('count', 'sum'),
        checklist_id=('checklist_id', 'nunique')
    )

    logger.info(f"Aggregated to {len(aggregated)} weekly grid cell records.")
    return aggregated


def compute_phenology_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute phenology metrics for each species and grid cell.

    Metrics:
        - first_arrival: Date of first observation in the season
        - median_arrival: Median date of observation in the season
        - stopover_duration: Number of weeks between first and last observation

    Args:
        df: Aggregated DataFrame with weekly counts per grid cell.

    Returns:
        DataFrame with phenology metrics added.
    """
    phenology_results = []

    for (species, grid_lat, grid_lon), group in df.groupby(['species', 'grid_lat', 'grid_lon']):
        group = group.sort_values('week_start')

        if len(group) == 0:
            continue

        first_arrival = group['week_start'].min()
        median_arrival = group['week_start'].median()
        last_arrival = group['week_start'].max()

        # Calculate stopover duration in weeks
        stopover_duration = (last_arrival - first_arrival).days / 7

        phenology_results.append({
            'species': species,
            'grid_lat': grid_lat,
            'grid_lon': grid_lon,
            'first_arrival': first_arrival,
            'median_arrival': median_arrival,
            'stopover_duration': stopover_duration,
            'total_observations': len(group),
            'total_count': group['count'].sum()
        })

    phenology_df = pd.DataFrame(phenology_results)
    logger.info(f"Computed phenology metrics for {len(phenology_df)} species-grid combinations.")
    return phenology_df


def mark_insufficient_data(df: pd.DataFrame, min_observations: int = 5) -> pd.DataFrame:
    """
    Mark grid cells with insufficient observation density.

    Args:
        df: DataFrame with phenology metrics.
        min_observations: Minimum number of observations required.

    Returns:
        DataFrame with 'sufficient_data' boolean column added.
    """
    df['sufficient_data'] = df['total_observations'] >= min_observations

    insufficient_count = (~df['sufficient_data']).sum()
    if insufficient_count > 0:
        log_insufficient_data(f"Marked {insufficient_count} grid cells as insufficient data.")
        logger.warning(f"Marked {insufficient_count} grid cells as insufficient data.")

    return df


def calculate_observer_effort(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate observer effort covariates.

    Args:
        df: DataFrame with checklist information.

    Returns:
        DataFrame with observer effort metrics added.
    """
    # Calculate effort as number of unique checklists per grid cell per week
    effort_df = df.groupby(['grid_lat', 'grid_lon', 'week_start']).agg(
        effort=('checklist_id', 'nunique')
    ).reset_index()

    # Merge back to original dataframe
    df = df.merge(effort_df, on=['grid_lat', 'grid_lon', 'week_start'], how='left')

    logger.info("Calculated observer effort covariates.")
    return df


def apply_tail_preserving_sampling(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply tail-preserving stratified sampling to oversample early arrival events.

    Args:
        df: DataFrame with phenology metrics including 'first_arrival'.

    Returns:
        DataFrame with sampling weights added.
    """
    if len(df) == 0:
        df['weight'] = 1.0
        return df

    # Quantile-bin first_arrival into deciles
    df['arrival_decile'] = pd.qcut(
        df['first_arrival'].map(pd.Timestamp.toordinal),
        q=10,
        labels=False,
        duplicates='drop'
    )

    # Oversample lowest decile (earliest arrivals)
    df['weight'] = df['arrival_decile'].apply(lambda x: 0.5 if x == 0 else 1.0)

    logger.info("Applied tail-preserving stratified sampling.")
    return df


def run_preprocessing_pipeline(
    data_dir: Path = None,
    output_dir: Path = None,
    force_synthetic: bool = False
) -> Dict[str, Any]:
    """
    Run the complete preprocessing pipeline.

    Args:
        data_dir: Root directory containing data subdirectories.
        output_dir: Directory for processed data outputs.
        force_synthetic: If True, generate synthetic data if real data is missing.

    Returns:
        Dictionary with pipeline results and statistics.
    """
    if data_dir is None:
        data_dir = Path.cwd()

    if output_dir is None:
        output_dir = data_dir / "data" / "processed"

    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Starting preprocessing pipeline.")

    # 1. Verify data availability
    if not check_real_data_available(data_dir) and not force_synthetic:
        logger.error("Real data not available and force_synthetic=False. Aborting.")
        raise RuntimeError("Real data not available. Set force_synthetic=True to generate synthetic data.")

    # 2. Generate synthetic data if needed
    if force_synthetic and not check_real_data_available(data_dir):
        logger.info("Generating synthetic data...")
        synthetic_ebird = generate_synthetic_ebird_data(data_dir / "data" / "raw")
        synthetic_climate = generate_synthetic_climate_data(data_dir / "data" / "raw")
        write_state_file(data_dir / STATE_FILE_PATH, {
            'artifact_hashes': {
                'synthetic_ebird.csv': compute_sha256(synthetic_ebird),
                'synthetic_climate.parquet': compute_sha256(synthetic_climate)
            },
            'updated_at': datetime.now().isoformat()
        })
        ebird_path = synthetic_ebird
    else:
        # Use real data
        ebird_path = data_dir / "data" / "raw" / "ebird" / "ebird_data.csv"
        if not ebird_path.exists():
            raise FileNotFoundError(f"eBird data not found at {ebird_path}")

    # 3. Load and filter eBird data
    logger.info("Loading eBird data...")
    ebird_df = pd.read_csv(ebird_path)

    logger.info("Filtering to migratory species...")
    ebird_df = filter_migratory_species(ebird_df)

    # 4. Add grid cells
    logger.info("Assigning grid cells...")
    ebird_df = add_grid_cells(ebird_df)

    # 5. Aggregate to weekly grid
    logger.info("Aggregating to weekly grid...")
    weekly_df = aggregate_to_weekly_grid(ebird_df)

    # 6. Calculate observer effort
    logger.info("Calculating observer effort...")
    weekly_df = calculate_observer_effort(weekly_df)

    # 7. Compute phenology metrics
    logger.info("Computing phenology metrics...")
    phenology_df = compute_phenology_metrics(weekly_df)

    # 8. Mark insufficient data
    logger.info("Marking insufficient data...")
    phenology_df = mark_insufficient_data(phenology_df)

    # 9. Apply tail-preserving sampling
    logger.info("Applying tail-preserving sampling...")
    phenology_df = apply_tail_preserving_sampling(phenology_df)

    # 10. Save outputs
    phenology_path = output_dir / "phenology_metrics.csv"
    phenology_df.to_csv(phenology_path, index=False)
    logger.info(f"Saved phenology metrics to {phenology_path}")

    weekly_path = output_dir / "weekly_grid_counts.csv"
    weekly_df.to_csv(weekly_path, index=False)
    logger.info(f"Saved weekly grid counts to {weekly_path}")

    # 11. Save sampling weights
    weights_path = output_dir / "sampling_weights.parquet"
    phenology_df[['species', 'grid_lat', 'grid_lon', 'weight']].to_parquet(weights_path, index=False)
    logger.info(f"Saved sampling weights to {weights_path}")

    results = {
        'total_records': len(ebird_df),
        'migratory_records': len(ebird_df),
        'weekly_grid_records': len(weekly_df),
        'phenology_records': len(phenology_df),
        'insufficient_data_cells': (~phenology_df['sufficient_data']).sum(),
        'output_files': {
            'phenology_metrics': str(phenology_path),
            'weekly_grid_counts': str(weekly_path),
            'sampling_weights': str(weights_path)
        }
    }

    logger.info("Preprocessing pipeline completed successfully.")
    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the preprocessing pipeline.")
    parser.add_argument("--data-dir", type=str, default=None, help="Root directory for data")
    parser.add_argument("--output-dir", type=str, default=None, help="Directory for outputs")
    parser.add_argument("--force-synthetic", action="store_true", help="Force synthetic data generation")

    args = parser.parse_args()

    data_dir = Path(args.data_dir) if args.data_dir else None
    output_dir = Path(args.output_dir) if args.output_dir else None

    results = run_preprocessing_pipeline(
        data_dir=data_dir,
        output_dir=output_dir,
        force_synthetic=args.force_synthetic
    )

    print(f"Pipeline completed. Results: {results}")
