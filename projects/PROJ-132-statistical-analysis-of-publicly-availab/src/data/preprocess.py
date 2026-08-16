import os
import sys
import hashlib
import yaml
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import polars as pl

from src.config import setup_logging
from src.data.stream_utils import stream_ebird_data
from src.data.impute import run_imputation_pipeline
from src.models.lock_utils import managed_lock

logger = logging.getLogger(__name__)

GRID_RES = 0.5
MIN_OBSERVATIONS = 10

def assign_grid_cell(lat: float, lon: float) -> str:
    """Assign a grid cell string based on lat/lon."""
    grid_lat = float(int(lat / GRID_RES) * GRID_RES)
    grid_lon = float(int(lon / GRID_RES) * GRID_RES)
    return f"{grid_lat:.1f}_{grid_lon:.1f}"

def filter_migratory_species(df: pl.DataFrame, valid_species: set) -> pl.DataFrame:
    """Filter dataframe for valid migratory species."""
    return df.filter(pl.col("species").is_in(list(valid_species)))

def aggregate_to_weekly_grid(df: pl.DataFrame) -> pl.DataFrame:
    """Aggregate observations to weekly grid cells."""
    df = df.with_columns(
        [
            pl.col("date").dt.strftime("%Y-%W").alias("week"),
            pl.col("lat").apply(lambda x: assign_grid_cell(x, None)).alias("grid_cell_temp"),
        ]
    )
    # Re-calculate grid cell properly using lat/lon columns
    df = df.with_columns(
        [
            pl.col("lat").apply(lambda x: assign_grid_cell(x, 0)).alias("grid_lat"),
            pl.col("lon").apply(lambda x: assign_grid_cell(0, x)).alias("grid_lon"),
        ]
    )
    df = df.with_columns(
        (pl.col("grid_lat") + "_" + pl.col("grid_lon")).alias("grid_cell")
    )
    
    return df.group_by(["species", "grid_cell", "year", "week"]).agg(
        [
            pl.col("date").min().alias("first_arrival"),
            pl.col("date").median().alias("median_arrival"),
            pl.col("date").quantile(0.9).alias("p90_date"),
            pl.col("date").quantile(0.1).alias("p10_date"),
            pl.col("count").sum().alias("total_count"),
            pl.col("checklist_id").count().alias("obs_count"),
        ]
    ).with_columns(
        (pl.col("p90_date") - pl.col("p10_date")).dt.total_days().alias("stopover_duration")
    ).drop(["grid_lat", "grid_lon", "p90_date", "p10_date"])

def compute_phenology_metrics(df: pl.DataFrame) -> pl.DataFrame:
    """Compute final phenology metrics."""
    return df

def mark_insufficient_cells(df: pl.DataFrame) -> pl.DataFrame:
    """Mark grid cells with insufficient observations."""
    return df.with_columns(
        pl.when(pl.col("obs_count") < MIN_OBSERVATIONS)
        .then(pl.lit("insufficient"))
        .otherwise(pl.lit("sufficient"))
        .alias("data_quality")
    )

def generate_provenance(df: pl.DataFrame, output_path: str) -> None:
    """
    Generate provenance mapping: processed_row_id -> original checklist_id.
    
    Implements Constitution Principle VI (Ecological Data Provenance) and FR-003.
    processed_row_id = SHA256(checklist_id + row_index)
    """
    logger.info(f"Generating provenance mapping for {len(df)} rows...")
    
    mapping_records = []
    
    # Ensure we have a row index
    df_with_idx = df.with_row_index("row_index")
    
    for row in df_with_idx.iter_rows(named=True):
        checklist_id = str(row.get("checklist_id", ""))
        row_index = row["row_index"]
        species = row.get("species", "")
        grid_cell = row.get("grid_cell", "")
        
        # Create unique hash: SHA256(checklist_id + row_index)
        hash_input = f"{checklist_id}{row_index}"
        processed_row_id = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()
        
        mapping_records.append({
            "processed_row_id": processed_row_id,
            "original_checklist_id": checklist_id,
            "species": species,
            "grid_cell": grid_cell
        })
    
    # Write to JSON
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(mapping_records, f, indent=2)
    
    logger.info(f"Provenance mapping written to {output_path}")

def run_preprocessing_pipeline(
    ebird_path: str = "data/raw/ebird_sample",
    climate_path: str = "data/raw/daymet",
    migratory_list_path: str = "data/raw/migratory_list.json",
    output_path: str = "data/processed/preprocessed_data.parquet",
    provenance_path: str = "data/provenance/row_mapping.json"
) -> None:
    """Run the full preprocessing pipeline."""
    setup_logging()
    
    logger.info("Starting preprocessing pipeline...")
    
    # Load migratory species list
    with open(migratory_list_path, "r") as f:
        valid_species = set(json.load(f))
    
    # Stream and process eBird data
    df = stream_ebird_data(ebird_path)
    
    # Filter for migratory species
    df = filter_migratory_species(df, valid_species)
    
    # Aggregate to weekly grid
    df = aggregate_to_weekly_grid(df)
    
    # Compute phenology metrics
    df = compute_phenology_metrics(df)
    
    # Mark insufficient cells
    df = mark_insufficient_cells(df)
    
    # Generate provenance mapping BEFORE writing final output
    generate_provenance(df, provenance_path)
    
    # Write final output
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(output_path)
    
    logger.info(f"Preprocessing pipeline complete. Output: {output_path}")

def main():
    """Entry point for preprocessing pipeline."""
    run_preprocessing_pipeline()

if __name__ == "__main__":
    main()
