import os
import sys
import hashlib
import yaml
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import polars as pl
import numpy as np
from datetime import datetime, timezone

from src.config import setup_logging
from src.data.stream_utils import stream_ebird_data
from src.data.impute import run_imputation_pipeline
from src.models.lock_utils import managed_lock

logger = setup_logging(__name__)

GRID_RES = 0.5
MIN_OBSERVATIONS = 10
RANDOM_SEED = 42

def assign_grid_cell(lat: float, lon: float) -> str:
    """
    Assign a grid cell string based on latitude and longitude.
    Format: "{lat_bin}_{lon_bin}" where bin = floor(coord / GRID_RES) * GRID_RES
    """
    lat_bin = np.floor(lat / GRID_RES) * GRID_RES
    lon_bin = np.floor(lon / GRID_RES) * GRID_RES
    return f"{lat_bin:.1f}_{lon_bin:.1f}"

def filter_migratory_species(df: pl.DataFrame, migratory_list: List[str]) -> pl.DataFrame:
    """
    Filter the DataFrame to keep only rows where 'species' is in the migratory list.
    """
    if not migratory_list:
        logger.warning("Migratory list is empty; returning original DataFrame.")
        return df
    return df.filter(pl.col("species").is_in(migratory_list))

def aggregate_to_weekly_grid(df: pl.DataFrame) -> pl.DataFrame:
    """
    Aggregate data to a weekly grid resolution.
    Creates 'week' column (ISO week number) and 'grid_cell'.
    """
    # Ensure date is datetime
    if not isinstance(df.schema["date"], pl.Date):
        df = df.with_columns(pl.col("date").cast(pl.Date))

    df = df.with_columns(
        pl.col("date").dt.iso_year().alias("year"),
        pl.col("date").dt.week().alias("week"),
        pl.struct(["lat", "lon"]).map_elements(
            lambda row: assign_grid_cell(row["lat"], row["lon"]),
            return_dtype=pl.Utf8
        ).alias("grid_cell")
    )
    return df

def compute_phenology_metrics(df: pl.DataFrame) -> pl.DataFrame:
    """
    Compute phenology metrics: first_arrival, median_arrival, stopover_duration.
    Aggregated by species, grid_cell, year, week.
    """
    # Convert date to numeric for percentile calculation (days since epoch)
    df = df.with_columns(
        (pl.col("date") - pl.lit(datetime(1970, 1, 1))).dt.total_days().alias("date_numeric")
    )

    agg_expr = [
        pl.col("date_numeric").min().alias("first_arrival_numeric"),
        pl.col("date_numeric").median().alias("median_arrival_numeric"),
        (pl.col("date_numeric").quantile(0.9, interpolation="nearest") -
         pl.col("date_numeric").quantile(0.1, interpolation="nearest")).alias("stopover_duration"),
        pl.col("count").sum().alias("total_count")
    ]

    grouped = df.group_by(["species", "grid_cell", "year", "week"]).agg(agg_expr)

    # Convert back to dates
    base_date = datetime(1970, 1, 1)
    grouped = grouped.with_columns(
        pl.col("first_arrival_numeric").map_elements(
            lambda x: (base_date + timedelta(days=x)).date() if x is not None else None,
            return_dtype=pl.Date
        ).alias("first_arrival"),
        pl.col("median_arrival_numeric").map_elements(
            lambda x: (base_date + timedelta(days=x)).date() if x is not None else None,
            return_dtype=pl.Date
        ).alias("median_arrival")
    ).drop(["first_arrival_numeric", "median_arrival_numeric"])

    return grouped

def mark_insufficient_cells(df: pl.DataFrame) -> pl.DataFrame:
    """
    Mark grid cells with fewer than MIN_OBSERVATIONS as data_quality='insufficient'.
    """
    # Count observations per grid cell
    counts = df.group_by("grid_cell").agg(pl.count().alias("obs_count"))
    insufficient_cells = counts.filter(pl.col("obs_count") < MIN_OBSERVATIONS).select("grid_cell")

    # Mark in main dataframe
    df = df.join(insufficient_cells, on="grid_cell", how="left")
    df = df.with_columns(
        pl.when(pl.col("grid_cell").is_in(insufficient_cells["grid_cell"]))
        .then(pl.lit("insufficient"))
        .otherwise(pl.lit("sufficient"))
        .alias("data_quality")
    ).drop("obs_count") # Keep logic clean

    return df

def generate_provenance(df: pl.DataFrame, output_path: Path) -> None:
    """
    Generate provenance mapping: processed_row_id -> original_checklist_id.
    processed_row_id = SHA256(checklist_id + str(row_index))
    Schema: { "processed_row_id": str, "original_checklist_id": str, "species": str, "grid_cell": str }
    """
    logger.info(f"Generating provenance mapping for {len(df)} rows...")
    
    # Ensure we have checklist_id and row index
    if "checklist_id" not in df.columns:
        raise ValueError("DataFrame must contain 'checklist_id' column for provenance generation.")

    # Add row index
    df_with_idx = df.with_row_index("row_index")

    provenance_records = []
    
    # Iterate in chunks to manage memory if needed, though Polars is efficient
    # We'll use a simple loop for clarity and correctness
    for row in df_with_idx.iter_rows(named=True):
        checklist_id = row["checklist_id"]
        row_index = row["row_index"]
        
        # Create unique hash
        hash_input = f"{checklist_id}{row_index}".encode('utf-8')
        processed_row_id = hashlib.sha256(hash_input).hexdigest()

        record = {
            "processed_row_id": processed_row_id,
            "original_checklist_id": checklist_id,
            "species": row["species"],
            "grid_cell": row["grid_cell"]
        }
        provenance_records.append(record)

    # Write to JSON
    with open(output_path, 'w') as f:
        json.dump(provenance_records, f, indent=2)
    
    logger.info(f"Provenance mapping written to {output_path}")

def run_preprocessing_pipeline(input_dir: Path, output_dir: Path, migratory_list_path: Path) -> None:
    """
    Main entry point for the preprocessing pipeline.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Load Migratory List
    with open(migratory_list_path, 'r') as f:
        migratory_list = json.load(f)
    
    # 2. Stream and Filter eBird Data
    logger.info("Streaming eBird data...")
    df = stream_ebird_data()
    df = filter_migratory_species(df, migratory_list)
    
    # 3. Aggregate to Weekly Grid
    logger.info("Aggregating to weekly grid...")
    df = aggregate_to_weekly_grid(df)
    
    # 4. Compute Phenology Metrics
    logger.info("Computing phenology metrics...")
    df = compute_phenology_metrics(df)
    
    # 5. Mark Insufficient Cells
    logger.info("Marking insufficient cells...")
    df = mark_insufficient_cells(df)
    
    # 6. Write Intermediate Outputs
    intermediate_grid = output_dir / "grid_binned.parquet"
    intermediate_phenology = output_dir / "phenology_raw.parquet"
    df.write_parquet(intermediate_grid)
    df.write_parquet(intermediate_phenology)
    
    # 7. Generate Provenance (T016)
    provenance_path = output_dir.parent / "provenance" / "row_mapping.json"
    provenance_path.parent.mkdir(parents=True, exist_ok=True)
    generate_provenance(df, provenance_path)
    
    # 8. Final Output (Placeholder for climate join/imputation logic which might be separate)
    final_output = output_dir / "preprocessed_data.parquet"
    df.write_parquet(final_output)
    
    logger.info("Preprocessing pipeline completed.")

def main():
    """
    CLI entry point.
    """
    logger.info("Starting preprocessing pipeline main...")
    input_dir = Path("data/raw/ebird_sample")
    output_dir = Path("data/processed")
    migratory_list_path = Path("data/raw/migratory_list.json")
    
    if not migratory_list_path.exists():
        logger.error(f"Migratory list not found at {migratory_list_path}. Exiting.")
        sys.exit(1)
        
    run_preprocessing_pipeline(input_dir, output_dir, migratory_list_path)

if __name__ == "__main__":
    main()
