import os
import gc
import logging
import time
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator, Tuple

import numpy as np
import pandas as pd

# Import from existing API surface
from utils.config import get_project_root, get_data_raw_path, get_data_processed_path
from utils.logging import get_pipeline_logger, log_task_start, log_task_end, log_error, log_metric
from utils.io import iter_csv_chunks, save_dataframe_chunked
from processing.inertia_tensor import process_halo_inertia
from processing.shape_metrics import (
    compute_shape_metrics_from_eigenvalues,
    filter_halo_by_particle_count,
    validate_shape_metrics,
    get_exclusion_reason
)
from ingestion.tng_loader import fetch_tng_halo_data

logger = get_pipeline_logger("pipeline_runner")

# Constants
MIN_PARTICLE_COUNT = 10000
OUTPUT_HALO_SHAPES = "data/processed/halo_shapes.csv"
OUTPUT_EXCLUSION_LOG = "data/processed/exclusion_log.json"

def iterate_haloes(
    snapshot_id: int = 0,
    chunk_size: int = 1000
) -> Generator[Tuple[Dict[str, Any], int], None, None]:
    """
    Iterates over haloes from the TNG-100 dataset in chunks.
    Yields (halo_data_dict, halo_id).
    """
    logger.info(f"Starting halo iteration for snapshot {snapshot_id}, chunk_size={chunk_size}")
    
    # Fetch halo list metadata
    try:
        halo_list = fetch_tng_halo_data(snapshot_id, limit=None)
    except Exception as e:
        logger.error(f"Failed to fetch halo list: {e}")
        raise

    total_haloes = len(halo_list)
    processed = 0
    
    # Process in chunks to manage memory
    for i in range(0, total_haloes, chunk_size):
        chunk = halo_list[i : i + chunk_size]
        chunk_haloes = []
        
        for halo_info in chunk:
            halo_id = halo_info['id']
            try:
                # Fetch full data for this halo
                # Note: In a real scenario, this might fetch specific HDF5 groups
                halo_data = fetch_tng_halo_data(snapshot_id, halo_id=halo_id)
                if halo_data:
                    chunk_haloes.append((halo_data, halo_id))
            except Exception as e:
                logger.warning(f"Skipping halo {halo_id} due to fetch error: {e}")
                continue
        
        processed += len(chunk_haloes)
        log_metric("haloes_processed", processed)
        
        for halo_data, halo_id in chunk_haloes:
            yield halo_data, halo_id
        
        # Force garbage collection after each chunk
        gc.collect()

def validate_shape_metrics_chunk(
    metrics: Dict[str, Any],
    particle_count: int
) -> Tuple[bool, Optional[str]]:
    """
    Validates computed shape metrics against physical constraints.
    Returns (is_valid, exclusion_reason).
    """
    if particle_count < MIN_PARTICLE_COUNT:
        return False, f"Particle count {particle_count} < {MIN_PARTICLE_COUNT}"

    b_a = metrics.get('b_a_ratio')
    c_a = metrics.get('c_a_ratio')

    if b_a is None or c_a is None:
        return False, "Missing axial ratios"

    # Validate 0 < b/a <= 1
    if not (0 < b_a <= 1):
        return False, f"Invalid b/a ratio: {b_a}"

    # Validate 0 < c/a <= 1
    if not (0 < c_a <= 1):
        return False, f"Invalid c/a ratio: {c_a}"

    triaxiality = metrics.get('triaxiality')
    if triaxiality is None or not (0 <= triaxiality <= 1):
        return False, f"Invalid triaxiality: {triaxiality}"

    return True, None

def run_pipeline(
    snapshot_id: int = 0,
    chunk_size: int = 1000
) -> None:
    """
    Main pipeline execution:
    1. Iterate haloes
    2. Compute inertia tensors and shape metrics
    3. Validate and filter
    4. Aggregate results
    5. Write outputs
    """
    start_time = time.time()
    log_task_start("run_pipeline")
    
    project_root = get_project_root()
    processed_dir = get_data_processed_path()
    
    # Ensure output directories exist
    os.makedirs(processed_dir, exist_ok=True)
    
    output_csv_path = processed_dir / OUTPUT_HALO_SHAPES
    output_json_path = processed_dir / OUTPUT_EXCLUSION_LOG
    
    valid_records = []
    exclusion_log = []
    stats = {
        "total_processed": 0,
        "valid": 0,
        "excluded": 0,
        "errors": 0
    }

    try:
        for halo_data, halo_id in iterate_haloes(snapshot_id, chunk_size):
            stats["total_processed"] += 1
            
            try:
                # Compute inertia tensor
                inertia_result = process_halo_inertia(halo_data)
                
                if inertia_result is None:
                    raise ValueError("Inertia tensor computation failed")

                particle_count = inertia_result.get('particle_count', 0)
                eigenvalues = inertia_result.get('eigenvalues')
                
                if eigenvalues is None or len(eigenvalues) != 3:
                    raise ValueError("Invalid eigenvalues from inertia tensor")

                # Compute shape metrics
                metrics = compute_shape_metrics_from_eigenvalues(eigenvalues)
                metrics['particle_count'] = particle_count

                # Validate
                is_valid, reason = validate_shape_metrics_chunk(metrics, particle_count)
                
                if is_valid:
                    record = {
                        'halo_id': halo_id,
                        'mass': halo_data.get('mass', 0.0),
                        'b_a_ratio': round(metrics['b_a_ratio'], 6),
                        'c_a_ratio': round(metrics['c_a_ratio'], 6),
                        'triaxiality': round(metrics['triaxiality'], 6),
                        'particle_count': particle_count
                    }
                    valid_records.append(record)
                    stats["valid"] += 1
                else:
                    exclusion_log.append({
                        'halo_id': halo_id,
                        'reason': reason,
                        'particle_count': particle_count
                    })
                    stats["excluded"] += 1

            except Exception as e:
                logger.error(f"Error processing halo {halo_id}: {e}")
                exclusion_log.append({
                    'halo_id': halo_id,
                    'reason': f"Processing error: {str(e)}",
                    'particle_count': 0
                })
                stats["errors"] += 1

            # Periodic checkpointing to avoid memory bloat
            if len(valid_records) >= 10000:
                save_halo_shapes_chunk(valid_records, output_csv_path, append=True)
                valid_records.clear()
                gc.collect()

    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        raise

    # Write remaining valid records
    if valid_records:
        save_halo_shapes_chunk(valid_records, output_csv_path, append=True)
    
    # Write exclusion log
    write_exclusion_log(exclusion_log, output_json_path)
    
    end_time = time.time()
    log_metric("pipeline_duration_seconds", end_time - start_time)
    log_metric("final_valid_count", stats["valid"])
    log_metric("final_excluded_count", stats["excluded"])
    log_task_end("run_pipeline", success=True)

def save_halo_shapes_chunk(
    records: List[Dict[str, Any]],
    output_path: Path,
    append: bool = False
) -> None:
    """
    Saves a chunk of halo shape records to CSV.
    """
    mode = 'a' if append else 'w'
    header = not append

    try:
        with open(output_path, mode, newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['halo_id', 'mass', 'b_a_ratio', 'c_a_ratio', 'triaxiality', 'particle_count'])
            if header:
                writer.writeheader()
            writer.writerows(records)
        logger.info(f"Wrote {len(records)} records to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write CSV chunk: {e}")
        raise

def write_exclusion_log(
    exclusion_log: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Writes the exclusion log to a JSON file.
    """
    try:
        with open(output_path, 'w') as f:
            json.dump(exclusion_log, f, indent=2)
        logger.info(f"Wrote {len(exclusion_log)} exclusion records to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write exclusion log: {e}")
        raise

def main() -> None:
    """
    Entry point for the pipeline runner.
    """
    logger.info("Starting halo shape pipeline runner...")
    try:
        run_pipeline(snapshot_id=0, chunk_size=500)
        logger.info("Pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()