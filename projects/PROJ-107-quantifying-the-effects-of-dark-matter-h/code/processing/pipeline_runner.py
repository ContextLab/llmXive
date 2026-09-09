import os
import gc
import logging
import time
from pathlib import Path
from typing import Generator, Dict, Any, List, Optional
import pandas as pd
import numpy as np

from utils.config import get_project_root, get_data_processed_path, get_output_path
from utils.logging import get_pipeline_logger, log_metric, log_error, log_chunk_info
from utils.io import iter_hdf5_groups, process_halo_chunk
from ingestion.tng_loader import fetch_tng_halo_data
from processing.inertia_tensor import process_halo_inertia
from processing.shape_metrics import (
    filter_halo_by_particle_count,
    validate_shape_metrics,
    process_halo_shape,
    compute_shape_metrics_from_halo
)

logger = get_pipeline_logger("pipeline_runner")

def iterate_haloes(snap_id: int = 0, chunk_size: int = 100) -> Generator[Dict[str, Any], None, None]:
    """
    Generator that yields processed halo records in chunks.
    Handles the full pipeline for a subset of haloes to manage memory.
    """
    root = get_project_root()
    data_processed = get_data_processed_path()
    
    # Fetch the list of halos for the snapshot
    # Note: In a real run, this would fetch the full list and iterate.
    # For the MVP/US1, we assume the tng_loader returns a list of halo indices or IDs.
    try:
        halo_indices = fetch_tng_halo_data(snap_id, return_indices_only=True)
    except Exception as e:
        log_error(logger, f"Failed to fetch halo indices: {e}")
        raise

    total_halos = len(halo_indices)
    logger.info(f"Found {total_halos} halos to process for Snapshot {snap_id}")

    for start_idx in range(0, total_halos, chunk_size):
        end_idx = min(start_idx + chunk_size, total_halos)
        current_chunk_indices = halo_indices[start_idx:end_idx]
        
        log_chunk_info(logger, "Processing chunk", {
            "start": start_idx,
            "end": end_idx,
            "size": len(current_chunk_indices)
        })

        chunk_results = []
        for halo_idx in current_chunk_indices:
            try:
                # 1. Load Halo Data (Particle positions/masses)
                # This is a placeholder for the actual HDF5 read logic which depends on tng_loader internals
                # Assuming process_halo_chunk or similar handles the heavy lifting of reading specific particles
                halo_data = process_halo_chunk(snap_id, halo_idx)
                
                if halo_data is None:
                    continue

                # 2. Filter by Particle Count (N >= 10,000)
                if not filter_halo_by_particle_count(halo_data, min_particles=10000):
                    continue

                # 3. Compute Reduced Inertia Tensor
                inertia_result = process_halo_inertia(halo_data)
                if inertia_result is None or not inertia_result.get("valid", False):
                    continue

                # 4. Compute Shape Metrics (Axial Ratios, Triaxiality)
                shape_metrics = compute_shape_metrics_from_halo(inertia_result)
                
                # 5. Validate Shape Metrics (0 < b/a <= 1, 0 < c/a <= 1)
                is_valid, reason = validate_shape_metrics(shape_metrics)
                
                if not is_valid:
                    logger.warning(f"Halo {halo_idx} excluded: {reason}")
                    continue

                # 6. Construct Record
                record = {
                    "halo_id": halo_idx,
                    "snapshot": snap_id,
                    "num_particles": halo_data.get("num_particles", 0),
                    "mass": halo_data.get("mass", 0.0),
                    "eigenvalues": inertia_result.get("eigenvalues", []),
                    "b_a_ratio": shape_metrics.get("b_a_ratio"),
                    "c_a_ratio": shape_metrics.get("c_a_ratio"),
                    "triaxiality": shape_metrics.get("triaxiality"),
                    "valid": True
                }
                chunk_results.append(record)

            except Exception as e:
                log_error(logger, f"Error processing halo {halo_idx}: {e}")
                # Continue to next halo instead of failing the whole chunk
                continue

        # Yield the processed chunk
        if chunk_results:
            yield chunk_results

        # Force garbage collection between chunks to manage memory
        gc.collect()

def run_pipeline(snap_id: int = 0, output_filename: str = "halo_shapes.csv", chunk_size: int = 100):
    """
    Orchestrates the full pipeline:
    1. Iterates haloes in chunks.
    2. Aggregates results.
    3. Validates final output constraints.
    4. Writes to data/processed/halo_shapes.csv.
    """
    root = get_project_root()
    data_processed = get_data_processed_path()
    
    # Ensure output directory exists
    data_processed.mkdir(parents=True, exist_ok=True)
    output_path = data_processed / output_filename

    logger.info(f"Starting pipeline for Snapshot {snap_id}")
    logger.info(f"Output path: {output_path}")

    all_records = []
    start_time = time.time()
    processed_count = 0
    excluded_count = 0

    try:
        for chunk in iterate_haloes(snap_id=snap_id, chunk_size=chunk_size):
            all_records.extend(chunk)
            processed_count += len(chunk)
            logger.info(f"Processed {processed_count} valid haloes so far...")
    except Exception as e:
        log_error(logger, f"Pipeline iteration failed: {e}")
        raise

    if not all_records:
        logger.warning("No valid haloes were processed. Output file will be empty.")
        # Still create the file with headers if no data
        df = pd.DataFrame()
    else:
        # Convert to DataFrame
        df = pd.DataFrame(all_records)

        # Final Aggregation & Validation Pass
        # Ensure 0 < b/a <= 1 and 0 < c/a <= 1 strictly
        valid_mask = (
            (df["b_a_ratio"] > 0) & (df["b_a_ratio"] <= 1) &
            (df["c_a_ratio"] > 0) & (df["c_a_ratio"] <= 1)
        )
        
        invalid_indices = df.index[~valid_mask]
        if len(invalid_indices) > 0:
            excluded_count += len(invalid_indices)
            logger.warning(f"Excluding {len(invalid_indices)} haloes due to final validation failure.")
            df = df[valid_mask]

        # Log triaxiality range
        if not df.empty:
            log_metric(logger, "min_triaxiality", df["triaxiality"].min())
            log_metric(logger, "max_triaxiality", df["triaxiality"].max())
            log_metric(logger, "mean_triaxiality", df["triaxiality"].mean())

    # Write to CSV
    df.to_csv(output_path, index=False)
    
    elapsed = time.time() - start_time
    logger.info(f"Pipeline completed in {elapsed:.2f} seconds.")
    logger.info(f"Total valid haloes written: {len(df)}")
    logger.info(f"Output saved to: {output_path}")

    return output_path

def main():
    """Entry point for the pipeline runner script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run TNG-100 Halo Shape Pipeline")
    parser.add_argument("--snap", type=int, default=0, help="Snapshot ID (default: 0)")
    parser.add_argument("--chunk", type=int, default=100, help="Chunk size for processing")
    parser.add_argument("--output", type=str, default="halo_shapes.csv", help="Output filename")
    
    args = parser.parse_args()
    
    try:
        run_pipeline(
            snap_id=args.snap,
            chunk_size=args.chunk,
            output_filename=args.output
        )
    except Exception as e:
        logger.critical(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()