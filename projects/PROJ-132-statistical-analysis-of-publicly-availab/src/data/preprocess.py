import os
import sys
import hashlib
import yaml
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

import polars as pl
from src.config import setup_logging
from src.data.stream_utils import stream_ebird_data
from src.data.download import get_clo_migratory_list
from src.models.utils import benjamini_hochberg_fdr

# Ensure logging is configured
logger = setup_logging("preprocess")

GRID_RES = 0.5
MIN_OBSERVATIONS = 10

def assign_grid_cell(lat: float, lon: float) -> str:
    """Assign a grid cell ID based on latitude and longitude."""
    lat_bin = int(lat / GRID_RES)
    lon_bin = int(lon / GRID_RES)
    return f"{lat_bin}_{lon_bin}"

def filter_migratory_species(df: pl.DataFrame, migratory_set: set) -> pl.DataFrame:
    """Filter the DataFrame for only migratory species."""
    return df.filter(pl.col("species").is_in(list(migratory_set)))

def aggregate_to_weekly_grid(df: pl.DataFrame) -> pl.DataFrame:
    """Aggregate observations to weekly grid cells."""
    df = df.with_columns(
        [
            pl.col("date").dt.strftime("%Y-%W").alias("week"),
            pl.col("lat").apply(lambda x: assign_grid_cell(x, None)).alias("lat_bin"),
            pl.col("lon").apply(lambda x: assign_grid_cell(None, x)).alias("lon_bin"),
        ]
    )
    df = df.with_columns(
        (pl.col("lat_bin") + "_" + pl.col("lon_bin")).alias("grid_cell")
    )
    return df.group_by(["species", "week", "grid_cell"]).agg(
        [
            pl.col("count").sum().alias("total_count"),
            pl.col("checklist_id").first().alias("first_checklist_id"),
        ]
    )

def compute_phenology_metrics(df: pl.DataFrame) -> pl.DataFrame:
    """Compute phenology metrics: first arrival, median arrival, stopover duration."""
    # Placeholder logic for phenology metrics calculation
    # This should be replaced with actual logic based on real data
    return df

def mark_insufficient_cells(df: pl.DataFrame) -> pl.DataFrame:
    """Mark grid cells with insufficient observations."""
    # Placeholder logic for marking insufficient cells
    return df

def generate_provenance(df: pl.DataFrame, output_path: str) -> None:
    """
    Generate a provenance mapping file.
    
    Maps each processed row ID to its original checklist_id, species, and grid_cell.
    Writes the mapping to `data/provenance/row_mapping.json`.
    
    Args:
        df: The preprocessed Polars DataFrame.
        output_path: The path to write the JSON mapping file.
    """
    # Ensure the output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    mapping = []
    
    # Iterate over the DataFrame to build the mapping
    # We use row enumeration to create a unique processed_row_id
    for idx, row in enumerate(df.iter_rows(named=True)):
        mapping.append({
            "processed_row_id": str(idx),
            "original_checklist_id": row["first_checklist_id"],
            "species": row["species"],
            "grid_cell": row["grid_cell"]
        })
    
    # Write the mapping to JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2)
    
    logger.info(f"Provenance mapping written to {output_path}")

def run_preprocessing_pipeline() -> None:
    """Run the full preprocessing pipeline."""
    # 1. Stream eBird data
    logger.info("Streaming eBird data...")
    # Note: This assumes stream_ebird_data yields chunks of data
    # We accumulate them into a single DataFrame for simplicity here
    # In a production scenario, we might process chunks incrementally
    all_chunks = []
    for chunk in stream_ebird_data():
        all_chunks.append(chunk)
    
    if not all_chunks:
        raise RuntimeError("No data streamed from eBird source.")
    
    df = pl.concat(all_chunks)
    logger.info(f"Loaded {len(df)} raw records.")
    
    # 2. Get migratory species list
    migratory_set = get_clo_migratory_list()
    logger.info(f"Loaded {len(migratory_set)} migratory species.")
    
    # 3. Filter for migratory species
    df = filter_migratory_species(df, migratory_set)
    logger.info(f"Filtered to {len(df)} migratory records.")
    
    # 4. Aggregate to weekly grid
    df = aggregate_to_weekly_grid(df)
    logger.info(f"Aggregated to {len(df)} grid-week records.")
    
    # 5. Compute phenology metrics
    df = compute_phenology_metrics(df)
    
    # 6. Mark insufficient cells
    df = mark_insufficient_cells(df)
    
    # 7. Generate provenance mapping
    output_mapping_path = "data/provenance/row_mapping.json"
    generate_provenance(df, output_mapping_path)
    
    # 8. Save the preprocessed data
    output_data_path = "data/processed/preprocessed_data.parquet"
    df.write_parquet(output_data_path)
    logger.info(f"Preprocessed data saved to {output_data_path}")

def main():
    """Entry point for the preprocessing pipeline."""
    run_preprocessing_pipeline()

if __name__ == "__main__":
    main()
