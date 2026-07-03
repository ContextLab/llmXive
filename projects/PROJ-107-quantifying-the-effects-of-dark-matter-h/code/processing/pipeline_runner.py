"""
Pipeline runner for chunked halo shape processing.

Implements chunked loop logic to read input chunks, iterate over haloes,
compute shape metrics, and yield processed records. Includes aggregation
and validation logic for final output generation.
"""
import os
import gc
import logging
import time
from pathlib import Path
from typing import Generator, Dict, Any, List, Optional
import pandas as pd
import numpy as np

# Import from existing project modules
from utils.config import get_project_root, get_data_raw_path, get_data_processed_path, load_config
from utils.io import iter_hdf5_groups, process_halo_chunk, get_file_size_mb
from utils.logging import get_pipeline_logger, log_pipeline_start, log_pipeline_end, log_error, log_metric
from processing.inertia_tensor import process_halo_inertia
from processing.shape_metrics import (
    filter_halo_by_particle_count,
    validate_shape_metrics,
    process_halo_shape
)

logger = get_pipeline_logger("pipeline_runner")

def iterate_haloes(chunk_size: int = 100) -> Generator[Dict[str, Any], None, None]:
    """
    Iterate over haloes from TNG-100 data in chunks.
    
    Args:
        chunk_size: Number of haloes to process per chunk.
        
    Yields:
        Dictionary containing processed halo shape metrics.
    """
    config = load_config()
    raw_path = get_data_raw_path()
    
    # Get list of HDF5 files (simulated for this implementation based on T011)
    # In a real scenario, this would come from the TNG API or a manifest file
    hdf5_files = list(Path(raw_path).glob("tng100_snapshot_000_halo_*.hdf5"))
    
    if not hdf5_files:
        logger.warning(f"No HDF5 files found in {raw_path}. Check T011 download status.")
        return

    logger.info(f"Found {len(hdf5_files)} HDF5 files to process.")
    
    processed_count = 0
    skipped_count = 0
    error_count = 0

    for file_idx, hdf5_file in enumerate(hdf5_files):
        logger.info(f"Processing file {file_idx + 1}/{len(hdf5_files)}: {hdf5_file.name}")
        
        try:
            # Process chunks within the file
            for chunk_data in process_halo_chunk(hdf5_file, chunk_size=chunk_size):
                if not chunk_data or 'halo_ids' not in chunk_data:
                    continue
                
                halo_ids = chunk_data['halo_ids']
                positions = chunk_data.get('positions', [])
                masses = chunk_data.get('masses', [])
                vel = chunk_data.get('velocities', [])
                
                # Process each halo in the chunk
                for i, halo_id in enumerate(halo_ids):
                    try:
                        # Extract data for this halo
                        halo_positions = positions[i] if i < len(positions) else None
                        halo_masses = masses[i] if i < len(masses) else None
                        halo_vel = vel[i] if i < len(vel) else None
                        
                        if halo_positions is None or len(halo_positions) == 0:
                            skipped_count += 1
                            continue
                        
                        # Step 1: Filter by particle count (T014 logic)
                        n_particles = len(halo_positions)
                        if not filter_halo_by_particle_count(n_particles, min_particles=10000):
                            skipped_count += 1
                            continue
                        
                        # Step 2: Compute reduced inertia tensor (T012 logic)
                        inertia_result = process_halo_inertia(
                            positions=halo_positions,
                            masses=halo_masses,
                            velocities=halo_vel,
                            halo_id=halo_id
                        )
                        
                        if inertia_result is None or 'eigenvalues' not in inertia_result:
                            error_count += 1
                            continue
                        
                        # Step 3: Compute shape metrics (T013 logic)
                        shape_result = process_halo_shape(
                            inertia_result=inertia_result,
                            halo_id=halo_id
                        )
                        
                        # Step 4: Validate shape metrics (T017 logic)
                        if not validate_shape_metrics(shape_result):
                            skipped_count += 1
                            continue
                        
                        # Yield the processed record
                        yield shape_result
                        processed_count += 1
                        
                    except Exception as e:
                        log_error(logger, f"Error processing halo {halo_id}: {str(e)}")
                        error_count += 1
                        continue
                        
        except Exception as e:
            log_error(logger, f"Error processing file {hdf5_file.name}: {str(e)}")
            continue
        
        # Force garbage collection after each file
        gc.collect()
    
    logger.info(f"Chunked iteration complete. Processed: {processed_count}, Skipped: {skipped_count}, Errors: {error_count}")
    log_metric(logger, "haloes_processed", processed_count)
    log_metric(logger, "haloes_skipped", skipped_count)
    log_metric(logger, "haloes_error", error_count)

def run_pipeline(output_path: Optional[str] = None, chunk_size: int = 100) -> str:
    """
    Run the full halo shape processing pipeline.
    
    Args:
        output_path: Optional path for the output CSV. If None, uses default from config.
        chunk_size: Number of haloes to process per chunk.
        
    Returns:
        Path to the generated CSV file.
    """
    config = load_config()
    start_time = time.time()
    
    # Set up output path
    if output_path is None:
        output_path = str(get_data_processed_path() / "halo_shapes.csv")
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting pipeline run. Output: {output_file}")
    log_pipeline_start(logger, "T015_pipeline_runner")
    
    records = []
    total_processed = 0
    
    try:
        # Iterate over haloes and collect records
        for record in iterate_haloes(chunk_size=chunk_size):
            records.append(record)
            total_processed += 1
            
            # Periodic flush to avoid memory issues
            if total_processed % 1000 == 0:
                logger.info(f"Processed {total_processed} haloes so far...")
                
        if not records:
            logger.warning("No valid halo records were processed. Creating empty output file.")
            # Create empty CSV with headers
            df_empty = pd.DataFrame(columns=[
                'halo_id', 'n_particles', 'lambda1', 'lambda2', 'lambda3',
                'b_a_ratio', 'c_a_ratio', 'triaxiality', 'is_valid'
            ])
            df_empty.to_csv(output_file, index=False)
            log_metric(logger, "output_file", str(output_file))
            return str(output_file)
        
        # Convert to DataFrame
        df = pd.DataFrame(records)
        
        # Validate final output (T017 logic)
        valid_mask = (
            (df['b_a_ratio'] > 0) & (df['b_a_ratio'] <= 1) &
            (df['c_a_ratio'] > 0) & (df['c_a_ratio'] <= 1) &
            (df['triaxiality'] >= 0) & (df['triaxiality'] <= 1)
        )
        
        valid_count = valid_mask.sum()
        invalid_count = len(df) - valid_count
        
        if invalid_count > 0:
            logger.warning(f"Removing {invalid_count} records with invalid shape metrics.")
            df = df[valid_mask]
        
        # Add metadata flag as per T026 requirement
        df['associational_only'] = True
        
        # Save to CSV
        df.to_csv(output_file, index=False)
        
        elapsed = time.time() - start_time
        logger.info(f"Pipeline completed successfully. Processed {total_processed} haloes, "
                    f"saved {len(df)} valid records to {output_file} in {elapsed:.2f}s.")
        
        log_metric(logger, "total_haloes_processed", total_processed)
        log_metric(logger, "valid_haloes_saved", len(df))
        log_metric(logger, "pipeline_duration_seconds", elapsed)
        log_metric(logger, "output_file", str(output_file))
        
        log_pipeline_end(logger, "T015_pipeline_runner", status="success")
        
    except Exception as e:
        log_error(logger, f"Pipeline failed: {str(e)}")
        log_pipeline_end(logger, "T015_pipeline_runner", status="failed")
        raise
    
    return str(output_file)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run halo shape processing pipeline")
    parser.add_argument("--chunk-size", type=int, default=100, help="Number of haloes per chunk")
    parser.add_argument("--output", type=str, default=None, help="Output CSV path")
    
    args = parser.parse_args()
    
    output_file = run_pipeline(
        output_path=args.output,
        chunk_size=args.chunk_size
    )
    print(f"Pipeline complete. Output saved to: {output_file}")
