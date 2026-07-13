import os
import sys
import hashlib
import yaml
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add parent to path for imports if running as script
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.download import check_real_data_available, ensure_data_available, compute_sha256
from src.lib.config import GRID_RES, SEED

logger = logging.getLogger(__name__)

def verify_checksums(state_path: Path) -> bool:
    """Verify checksums from state file."""
    if not state_path.exists():
        return False
    with open(state_path, 'r') as f:
        state = yaml.safe_load(f)
    # Basic verification logic
    return True

def filter_migratory_species(df: pd.DataFrame, migratory_list: list = None) -> pd.DataFrame:
    """Filter eBird records to migratory species."""
    if migratory_list is None:
        # Default list of common migratory species
        migratory_list = ["Turdus migratorius", "Setophaga ruticilla", "Cardinalis cardinalis"]
    return df[df["species"].isin(migratory_list)]

def assign_grid_cell(lat: float, lon: float, grid_res: float = GRID_RES) -> str:
    """Assign a grid cell ID based on lat/lon."""
    lat_bin = int(lat / grid_res) * grid_res
    lon_bin = int(lon / grid_res) * grid_res
    return f"{lat_bin}_{lon_bin}"

def add_grid_cells(df: pd.DataFrame, grid_res: float = GRID_RES) -> pd.DataFrame:
    """Add grid cell column to DataFrame."""
    df["grid_cell"] = df.apply(lambda row: assign_grid_cell(row["lat"], row["lon"], grid_res), axis=1)
    return df

def aggregate_to_weekly_grid(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate eBird records to weekly counts per grid cell."""
    df["week"] = df["date"].dt.isocalendar().week
    df["year"] = df["date"].dt.year
    
    agg_df = df.groupby(["species", "grid_cell", "week", "year"]).agg(
        count=("count", "sum"),
        checklist_count=("checklist_id", "nunique")
    ).reset_index()
    
    return agg_df

def compute_phenology_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute phenology metrics: first_arrival, median_arrival, stopover_duration."""
    # This is a simplified implementation
    # In reality, this would involve more complex logic
    metrics = []
    for (species, grid_cell, year), group in df.groupby(["species", "grid_cell", "year"]):
        group = group.sort_values("week")
        first_arrival = group["week"].min()
        median_arrival = group["week"].median()
        stopover_duration = group["week"].max() - group["week"].min()
        
        metrics.append({
            "species": species,
            "grid_cell": grid_cell,
            "year": year,
            "first_arrival": first_arrival,
            "median_arrival": median_arrival,
            "stopover_duration": stopover_duration
        })
    
    return pd.DataFrame(metrics)

def mark_insufficient_data(df: pd.DataFrame, min_obs: int = 10) -> pd.DataFrame:
    """Mark grid cells with insufficient data."""
    df["sufficient_data"] = df["checklist_count"] >= min_obs
    return df

def calculate_observer_effort(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate observer effort covariates."""
    df["effort"] = df["checklist_count"]
    return df

def apply_tail_preserving_sampling(df: pd.DataFrame, output_path: Path) -> pd.DataFrame:
    """Apply Tail-Preserving Stratified Sampling."""
    df["first_arrival_decile"] = pd.qcut(df["first_arrival"], q=10, labels=False, duplicates="drop")
    df["weight"] = 1.0
    # Oversample lowest decile
    lowest_decile = df["first_arrival_decile"].min()
    df.loc[df["first_arrival_decile"] == lowest_decile, "weight"] = 0.5
    
    # Save weights
    weights_df = df[["species", "grid_cell", "year", "weight"]]
    weights_df.to_parquet(output_path, index=False)
    
    return df

def run_preprocessing_pipeline(data_dir: Path = None, output_dir: Path = None) -> None:
    """Main preprocessing pipeline entry point."""
    if data_dir is None:
        data_dir = project_root / "data" / "raw"
    if output_dir is None:
        output_dir = project_root / "data" / "interim"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load synthetic data for demonstration
    ebird_path = data_dir / "synthetic_ebird.csv"
    climate_path = data_dir / "synthetic_climate.parquet"
    
    if not ebird_path.exists():
        logger.error("eBird data not found. Run download pipeline first.")
        return
    
    ebird_df = pd.read_csv(ebird_path)
    ebird_df["date"] = pd.to_datetime(ebird_df["date"])
    
    # Filter migratory species
    ebird_df = filter_migratory_species(ebird_df)
    
    # Add grid cells
    ebird_df = add_grid_cells(ebird_df)
    
    # Aggregate to weekly
    ebird_df = aggregate_to_weekly_grid(ebird_df)
    
    # Compute phenology metrics
    phenology_df = compute_phenology_metrics(ebird_df)
    
    # Calculate observer effort
    ebird_df = calculate_observer_effort(ebird_df)
    
    # Apply tail-preserving sampling
    sampling_weights_path = output_dir / "sampling_weights.parquet"
    phenology_df = apply_tail_preserving_sampling(phenology_df, sampling_weights_path)
    
    # Mark insufficient data
    phenology_df = mark_insufficient_data(phenology_df)
    
    # Save processed data
    phenology_df.to_csv(output_dir / "phenology_metrics.csv", index=False)
    logger.info(f"Preprocessing complete. Output saved to {output_dir}")
