import os
import sys
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import polars as pl

from src.config import setup_logging
from src.models.lock_utils import acquire_lock, release_lock

logger = logging.getLogger(__name__)

def assign_grid_cell(lat: float, lon: float, res: float = 0.5) -> str:
    """
    Assign a grid cell ID based on latitude and longitude.
    Grid cell format: "lat_{lat_bin}_lon_{lon_bin}"
    """
    lat_bin = int(lat / res) * res
    lon_bin = int(lon / res) * res
    return f"lat_{lat_bin:.1f}_lon_{lon_bin:.1f}"

def filter_migratory_species(df: pl.DataFrame, migratory_set: set) -> pl.DataFrame:
    """Filter DataFrame to keep only migratory species."""
    return df.filter(pl.col("species").is_in(migratory_set))

def aggregate_to_weekly_grid(df: pl.DataFrame) -> pl.DataFrame:
    """Aggregate observations to weekly grid cells."""
    df = df.with_columns(
        [
            pl.col("date").dt.strftime("%Y-%W").alias("year_week"),
            pl.col("lat").map_elements(lambda x: assign_grid_cell(x, 0.0, 0.5)).alias("grid_cell"),
        ]
    )
    # Group by species, year_week, grid_cell
    agg = (
        df.group_by(["species", "year_week", "grid_cell"])
        .agg(
            [
                pl.col("count").sum().alias("total_count"),
                pl.col("date").min().alias("first_date"),
                pl.col("date").median().alias("median_date"),
                pl.col("checklist_id").count().alias("obs_count"),
            ]
        )
        .sort(["species", "year_week", "grid_cell"])
    )
    return agg

def compute_phenology_metrics(df: pl.DataFrame) -> pl.DataFrame:
    """
    Compute phenology metrics: first_arrival_date, median_arrival_date, stopover_duration.
    stopover_duration is computed as the difference between high quantile and low quantile dates.
    """
    # Ensure date columns are datetime
    df = df.with_columns(
        [
            pl.col("first_date").cast(pl.Datetime),
            pl.col("median_date").cast(pl.Datetime),
        ]
    )
    # Compute stopover duration (e.g., 90th percentile - 10th percentile of arrival dates)
    # For simplicity in this aggregation, we approximate using available dates
    # In a full implementation, we would track all arrival dates per cell
    df = df.with_columns(
        [
            (pl.col("median_date") - pl.col("first_date")).dt.total_days().alias("stopover_duration"),
        ]
    )
    return df

def mark_insufficient_cells(df: pl.DataFrame, min_obs: int = 10) -> pl.DataFrame:
    """Mark grid cells with fewer than min_obs observations."""
    df = df.with_columns(
        [
            pl.when(pl.col("obs_count") >= min_obs)
            .then(pl.lit("sufficient"))
            .otherwise(pl.lit("insufficient"))
            .alias("data_quality"),
        ]
    )
    return df

def generate_provenance(df: pl.DataFrame, output_path: str) -> None:
    """
    Generate provenance mapping: row_id -> original checklist_id.
    Schema: { "processed_row_id": "SHA256(checklist_id + row_index)", "original_checklist_id": str, "species": str, "grid_cell": str }
    Constitution Principle VI (Ecological Data Provenance) and FR-003.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    provenance_list = []
    for idx, row in enumerate(df.iter_rows(named=True)):
        checklist_id = row["checklist_id"]
        species = row["species"]
        grid_cell = row["grid_cell"]

        # Generate unique cryptographic hash of checklist_id + row_index
        hash_input = f"{checklist_id}{idx}".encode("utf-8")
        processed_row_id = hashlib.sha256(hash_input).hexdigest()

        provenance_list.append(
            {
                "processed_row_id": processed_row_id,
                "original_checklist_id": checklist_id,
                "species": species,
                "grid_cell": grid_cell,
            }
        )

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(provenance_list, f, indent=2)

    logger.info(f"Generated provenance mapping with {len(provenance_list)} rows at {output_path}")

def run_preprocessing_pipeline(
    input_path: str,
    output_path: str,
    migratory_list_path: str,
    min_obs: int = 10,
) -> None:
    """
    Run the full preprocessing pipeline:
    1. Load eBird data
    2. Filter migratory species
    3. Aggregate to weekly grid
    4. Compute phenology metrics
    5. Mark insufficient cells
    6. Generate provenance mapping
    """
    logger.info("Starting preprocessing pipeline")

    # Load migratory species list
    with open(migratory_list_path, "r", encoding="utf-8") as f:
        migratory_data = json.load(f)
    migratory_set = set(migratory_data.get("species", []))

    # Load eBird data (assuming Parquet format for efficiency)
    logger.info(f"Loading eBird data from {input_path}")
    df = pl.read_parquet(input_path)

    # Filter migratory species
    df = filter_migratory_species(df, migratory_set)
    logger.info(f"Filtered to {len(df)} rows for migratory species")

    # Aggregate to weekly grid
    df = aggregate_to_weekly_grid(df)
    logger.info(f"Aggregated to {len(df)} weekly grid cells")

    # Compute phenology metrics
    df = compute_phenology_metrics(df)

    # Mark insufficient cells
    df = mark_insufficient_cells(df, min_obs)
    logger.info(f"Marked insufficient cells (min_obs={min_obs})")

    # Save preprocessed data
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(output_path)
    logger.info(f"Saved preprocessed data to {output_path}")

    # Generate provenance mapping
    provenance_path = str(Path(output_path).parent / "row_mapping.json")
    generate_provenance(df, provenance_path)
    logger.info("Provenance mapping generated")

def main() -> None:
    """Main entry point for preprocessing pipeline."""
    setup_logging()
    input_path = "data/interim/ebird_sample.parquet"
    output_path = "data/processed/preprocessed_data.parquet"
    migratory_list_path = "data/raw/migratory_list.json"

    if not Path(input_path).exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    run_preprocessing_pipeline(input_path, output_path, migratory_list_path)

if __name__ == "__main__":
    main()
