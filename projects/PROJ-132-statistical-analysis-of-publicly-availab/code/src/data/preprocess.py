import os
import sys
import hashlib
import yaml
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import polars as pl
from datetime import datetime, timezone

from src.config import setup_logging
from src.models.lock_utils import managed_lock
from src.data.stream_utils import stream_ebird_data

# Configure logging
logger = setup_logging(__name__)

def assign_grid_cell(lat: float, lon: float, grid_res: float = 0.5) -> str:
    """
    Assign a grid cell ID based on latitude and longitude.
    Formula: floor(lat / res) * 1000 + floor(lon / res)
    Returns a string ID like "grid_123_456".
    """
    lat_bin = int(lat // grid_res)
    lon_bin = int(lon // grid_res)
    return f"grid_{lat_bin}_{lon_bin}"

def filter_migratory_species(df: pl.DataFrame, valid_species: List[str]) -> pl.DataFrame:
    """
    Filter the dataframe to only include rows where the species is in the valid list.
    """
    return df.filter(pl.col("species").is_in(valid_species))

def aggregate_to_weekly_grid(df: pl.DataFrame) -> pl.DataFrame:
    """
    Aggregate observations to weekly grid cells.
    Assumes 'date' is a date/datetime column.
    Computes: count, first_arrival (min date), median_arrival (median date).
    """
    # Extract week number
    df = df.with_columns(pl.col("date").dt.week().alias("week"))
    
    # Group by species, year, week, grid_cell
    aggregated = df.group_by(["species", "date.year", "week", "grid_cell"]).agg(
        pl.col("count").sum().alias("total_count"),
        pl.col("date").min().alias("first_arrival_date"),
        pl.col("date").median().alias("median_arrival_date"),
        pl.col("checklist_id").first().alias("checklist_id_sample")
    )
    return aggregated

def compute_phenology_metrics(df: pl.DataFrame) -> pl.DataFrame:
    """
    Compute phenology metrics: first_arrival, median_arrival, stopover_duration.
    stopover_duration = high_quantile_date - low_quantile_date (e.g., 90th - 10th).
    """
    # Calculate stopover duration as difference between 90th and 10th percentile dates
    # Since Polars doesn't support date percentiles directly in group_by, we approximate
    # by converting to ordinal or using quantile on a numeric representation if needed.
    # For this implementation, we assume 'date' is a date type and compute quantiles on it.
    
    # Note: Polars date quantiles require converting to integer (ordinal) or using a specific method.
    # Here we use the 'quantile' on the date column directly if supported, else ordinal.
    # Assuming Polars version supports date quantiles or we convert to ordinal.
    
    df = df.with_columns(
        pl.col("date").dt.ordinal_day().alias("ordinal_day")
    )
    
    # Group by species, year, grid_cell to compute metrics if not already aggregated
    # If already aggregated by week, we might need to re-aggregate or compute on the fly.
    # For this task, we assume we are computing on the aggregated weekly data or raw data.
    # Let's assume we are computing on the raw data grouped by species, year, grid_cell.
    
    # Re-group to ensure we have the full set of dates per species/year/grid
    metrics = df.group_by(["species", "date.year", "grid_cell"]).agg(
        pl.col("date").min().alias("first_arrival_date"),
        pl.col("date").median().alias("median_arrival_date"),
        pl.col("ordinal_day").quantile(0.90).alias("q90"),
        pl.col("ordinal_day").quantile(0.10).alias("q10")
    )
    
    metrics = metrics.with_columns(
        (pl.col("q90") - pl.col("q10")).alias("stopover_duration")
    )
    
    # Drop ordinal helper columns
    metrics = metrics.drop(["q90", "q10"])
    
    return metrics

def mark_insufficient_cells(df: pl.DataFrame, min_observations: int = 10) -> pl.DataFrame:
    """
    Mark grid cells with fewer than min_observations as data_quality="insufficient".
    """
    # Count observations per species, year, grid_cell
    counts = df.group_by(["species", "date.year", "grid_cell"]).agg(
        pl.col("checklist_id").count().alias("observation_count")
    )
    
    # Mark insufficient
    counts = counts.with_columns(
        pl.when(pl.col("observation_count") < min_observations)
        .then(pl.lit("insufficient"))
        .otherwise(pl.lit("sufficient"))
        .alias("data_quality")
    )
    
    # Join back to main dataframe (or return counts if that's the output)
    # For this task, we update the main dataframe or a processed version.
    # We'll assume we are updating a processed dataframe.
    # Since we are returning a modified df, we join counts back.
    df = df.join(counts, on=["species", "date.year", "grid_cell"], how="left")
    
    return df

def generate_provenance(df: pl.DataFrame, output_path: str) -> None:
    """
    Generate provenance mapping: data/provenance/row_mapping.json.
    Maps each processed row ID to its original checklist_id.
    Schema: { "processed_row_id": "SHA256(checklist_id + row_index)", "original_checklist_id": str, "species": str, "grid_cell": str }
    
    This function implements Constitution Principle VI (Ecological Data Provenance) and FR-003.
    """
    logger.info(f"Generating provenance mapping for {df.shape[0]} rows.")
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a list to hold the mapping records
    mapping_records = []
    
    # Iterate over the dataframe rows
    # We use a chunked approach if the dataframe is large, but for this implementation,
    # we assume it fits in memory or we use Polars' efficient iteration.
    # Polars does not support row iteration efficiently, so we use with_row_index and map.
    
    # Add row index
    df_with_idx = df.with_row_index("row_index")
    
    # Generate processed_row_id as SHA256(checklist_id + str(row_index))
    # We do this by creating a temporary column with the concatenated string
    df_with_idx = df_with_idx.with_columns(
        (pl.col("checklist_id").cast(str) + pl.col("row_index").cast(str)).alias("concat_key")
    )
    
    # Hash the concatenation
    # Polars doesn't have a built-in SHA256 for strings, so we use a UDF or process in chunks.
    # For simplicity and performance, we'll use a Python UDF.
    def sha256_hash(s: str) -> str:
        return hashlib.sha256(s.encode('utf-8')).hexdigest()
    
    df_with_idx = df_with_idx.with_columns(
        pl.col("concat_key").map_elements(sha256_hash, return_dtype=pl.Utf8).alias("processed_row_id")
    )
    
    # Select required columns
    mapping_df = df_with_idx.select([
        "processed_row_id",
        "checklist_id",
        "species",
        "grid_cell"
    ])
    
    # Convert to list of dicts
    mapping_records = mapping_df.to_dicts()
    
    # Write to JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(mapping_records, f, indent=2)
    
    logger.info(f"Provenance mapping written to {output_path}")

def run_preprocessing_pipeline(
    input_path: str,
    output_path: str,
    species_list_path: str,
    min_observations: int = 10,
    grid_res: float = 0.5
) -> None:
    """
    Run the full preprocessing pipeline:
    1. Load species list.
    2. Stream eBird data.
    3. Filter migratory species.
    4. Assign grid cells.
    5. Aggregate to weekly grid.
    6. Compute phenology metrics.
    7. Mark insufficient cells.
    8. Generate provenance mapping.
    """
    logger.info("Starting preprocessing pipeline.")
    
    # Load species list
    with open(species_list_path, 'r') as f:
        valid_species = json.load(f)
    
    # Stream eBird data (assuming stream_ebird_data yields a Polars DataFrame)
    # We'll assume it returns a single DataFrame for simplicity, or we combine chunks.
    # For this implementation, we assume stream_ebird_data returns a Polars DataFrame.
    df = stream_ebird_data(input_path)
    
    # Filter migratory species
    df = filter_migratory_species(df, valid_species)
    
    # Assign grid cells
    df = df.with_columns(
        pl.map_groups(["lat", "lon"], lambda x: assign_grid_cell(x[0], x[1], grid_res), return_dtype=pl.Utf8).alias("grid_cell")
    )
    
    # Aggregate to weekly grid (optional, depending on downstream needs)
    # For this task, we might skip aggregation if we are computing phenology on raw data.
    # But the task description says "aggregate to coarse-resolution grid cells".
    # We'll do a preliminary aggregation to weekly grid.
    df_weekly = aggregate_to_weekly_grid(df)
    
    # Compute phenology metrics on the weekly aggregated data or raw data?
    # The task says "compute phenology metrics" after aggregation.
    # We'll compute on the weekly aggregated data.
    df_metrics = compute_phenology_metrics(df_weekly)
    
    # Mark insufficient cells
    df_final = mark_insufficient_cells(df_metrics, min_observations)
    
    # Write preprocessed data
    df_final.write_parquet(output_path)
    
    # Generate provenance mapping
    provenance_path = str(Path(output_path).parent / "row_mapping.json")
    generate_provenance(df_final, provenance_path)
    
    logger.info("Preprocessing pipeline completed.")

def main():
    """
    Main entry point for the preprocessing pipeline.
    """
    # Example usage (adjust paths as needed)
    input_path = "data/raw/ebird_sample/ebird_data.parquet"
    output_path = "data/processed/preprocessed_data.parquet"
    species_list_path = "data/raw/migratory_list.json"
    
    run_preprocessing_pipeline(input_path, output_path, species_list_path)

if __name__ == "__main__":
    main()