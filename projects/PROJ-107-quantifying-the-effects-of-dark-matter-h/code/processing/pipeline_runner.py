import os
import gc
import logging
import time
from pathlib import Path
from typing import Generator, Dict, Any, List, Optional
import pandas as pd
import numpy as np

from utils.config import get_project_root, get_data_processed_path, get_data_raw_path
from utils.logging import get_pipeline_logger, log_task_start, log_task_end, log_metric, log_error
from utils.io import process_halo_chunk, iter_hdf5_groups
from ingestion.tng_loader import fetch_tng_halo_data, download_file, fetch_halos_list
from processing.inertia_tensor import compute_reduced_inertia_tensor, compute_eigenvalues_and_eigenvectors
from processing.shape_metrics import (
    compute_axial_ratios,
    compute_triaxiality,
    filter_halo_by_particle_count,
    validate_shape_metrics,
    process_halo_shape
)

logger = get_pipeline_logger("pipeline_runner")

# Constants for validation
MIN_PARTICLE_COUNT = 10000
OUTPUT_FILE_NAME = "halo_shapes.csv"
EXCLUDED_LOG_NAME = "excluded_haloes.log"

def iterate_haloes(
    snapshot_id: int = 0,
    chunk_size: int = 100
) -> Generator[Dict[str, Any], None, None]:
    """
    Generator that iterates over haloes in the TNG-100 dataset.
    Handles chunked processing to stay within memory constraints.
    
    Args:
        snapshot_id: The snapshot ID (default 0 for TNG-100)
        chunk_size: Number of haloes to process in a chunk
    
    Yields:
        Dictionary containing processed halo shape metrics
    """
    log_task_start(logger, "iterate_haloes", f"Snapshot {snapshot_id}")
    
    try:
        # Fetch the list of haloes for the snapshot
        logger.info(f"Fetching halo list for snapshot {snapshot_id}")
        halos_list = fetch_halos_list(snapshot_id)
        
        if not halos_list:
            logger.warning(f"No haloes found for snapshot {snapshot_id}")
            return

        total_haloes = len(halos_list)
        logger.info(f"Found {total_haloes} haloes to process")

        processed_count = 0
        excluded_count = 0
        chunk_buffer = []

        for i, halo_info in enumerate(halos_list):
            try:
                # Fetch halo data
                halo_data = fetch_tng_halo_data(halo_info)
                
                if halo_data is None:
                    logger.warning(f"Failed to fetch data for halo {halo_info.get('id', 'unknown')}")
                    excluded_count += 1
                    continue

                # Filter by particle count
                particle_count = halo_data.get('num_particles', 0)
                if not filter_halo_by_particle_count(particle_count, MIN_PARTICLE_COUNT):
                    logger.debug(f"Excluding halo {halo_info.get('id', 'unknown')}: particle count {particle_count} < {MIN_PARTICLE_COUNT}")
                    excluded_count += 1
                    continue

                # Compute inertia tensor
                positions = halo_data.get('positions')
                masses = halo_data.get('masses')
                
                if positions is None or masses is None:
                    logger.warning(f"Missing position/mass data for halo {halo_info.get('id', 'unknown')}")
                    excluded_count += 1
                    continue

                inertia_tensor = compute_reduced_inertia_tensor(positions, masses)
                
                if inertia_tensor is None:
                    logger.warning(f"Singular inertia tensor for halo {halo_info.get('id', 'unknown')}")
                    excluded_count += 1
                    continue

                # Compute eigenvalues
                eigenvalues, eigenvectors = compute_eigenvalues_and_eigenvectors(inertia_tensor)
                
                if eigenvalues is None or len(eigenvalues) != 3:
                    logger.warning(f"Invalid eigenvalues for halo {halo_info.get('id', 'unknown')}")
                    excluded_count += 1
                    continue

                # Compute shape metrics
                axial_ratios = compute_axial_ratios(eigenvalues)
                triaxiality = compute_triaxiality(eigenvalues)
                
                # Validate shape metrics
                is_valid, validation_error = validate_shape_metrics(axial_ratios, triaxiality)
                
                if not is_valid:
                    logger.debug(f"Excluding halo {halo_info.get('id', 'unknown')}: {validation_error}")
                    excluded_count += 1
                    continue

                # Build result record
                result = {
                    'halo_id': halo_info.get('id'),
                    'snapshot_id': snapshot_id,
                    'particle_count': particle_count,
                    'eigenvalue_1': float(eigenvalues[0]),
                    'eigenvalue_2': float(eigenvalues[1]),
                    'eigenvalue_3': float(eigenvalues[2]),
                    'b_a_ratio': float(axial_ratios['b_a']),
                    'c_a_ratio': float(axial_ratios['c_a']),
                    'triaxiality': float(triaxiality),
                    'is_valid': True
                }

                chunk_buffer.append(result)
                processed_count += 1

                # Yield chunk if size reached
                if len(chunk_buffer) >= chunk_size:
                    for record in chunk_buffer:
                        yield record
                    chunk_buffer = []
                    gc.collect()

            except Exception as e:
                log_error(logger, f"Error processing halo {halo_info.get('id', 'unknown')}", e)
                excluded_count += 1
                continue

        # Yield remaining records
        if chunk_buffer:
            for record in chunk_buffer:
                yield record
            chunk_buffer = []

        # Log summary
        log_metric(logger, "iterate_haloes_processed", processed_count)
        log_metric(logger, "iterate_haloes_excluded", excluded_count)
        logger.info(f"Finished iterating haloes. Processed: {processed_count}, Excluded: {excluded_count}")

    except Exception as e:
        log_error(logger, "Error in iterate_haloes", e)
        raise
    finally:
        log_task_end(logger, "iterate_haloes")

def run_pipeline(
    snapshot_id: int = 0,
    output_dir: Optional[Path] = None,
    chunk_size: int = 100
) -> Path:
    """
    Main pipeline execution function that orchestrates the full process:
    1. Iterate over haloes
    2. Compute shape metrics
    3. Validate results
    4. Aggregate and save to CSV
    
    Args:
        snapshot_id: The snapshot ID to process
        output_dir: Optional output directory (defaults to data/processed/)
        chunk_size: Number of haloes to process in a chunk
    
    Returns:
        Path to the output CSV file
    """
    log_task_start(logger, "run_pipeline", f"Snapshot {snapshot_id}")
    
    project_root = get_project_root()
    if output_dir is None:
        output_dir = get_data_processed_path(project_root)
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / OUTPUT_FILE_NAME
    excluded_log_file = output_dir / EXCLUDED_LOG_NAME
    
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Output file: {output_file}")
    
    all_results = []
    excluded_haloes = []
    start_time = time.time()
    
    try:
        # Iterate and collect results
        logger.info("Starting halo iteration and processing...")
        for result in iterate_haloes(snapshot_id, chunk_size):
            all_results.append(result)
        
        logger.info(f"Collected {len(all_results)} valid halo records")
        
        # Create DataFrame and save
        if all_results:
            df = pd.DataFrame(all_results)
            
            # Final validation pass
            valid_mask = (
                (df['b_a_ratio'] > 0) & 
                (df['b_a_ratio'] <= 1) & 
                (df['c_a_ratio'] > 0) & 
                (df['c_a_ratio'] <= 1)
            )
            
            invalid_count = (~valid_mask).sum()
            if invalid_count > 0:
                logger.warning(f"Found {invalid_count} records failing final validation. Excluding them.")
                df = df[valid_mask]
                excluded_haloes.extend(df[~valid_mask]['halo_id'].tolist())
            
            # Sort by halo_id for consistent output
            df = df.sort_values('halo_id')
            
            # Save to CSV
            df.to_csv(output_file, index=False)
            logger.info(f"Saved {len(df)} records to {output_file}")
        else:
            # Create empty CSV with headers
            df = pd.DataFrame(columns=[
                'halo_id', 'snapshot_id', 'particle_count',
                'eigenvalue_1', 'eigenvalue_2', 'eigenvalue_3',
                'b_a_ratio', 'c_a_ratio', 'triaxiality', 'is_valid'
            ])
            df.to_csv(output_file, index=False)
            logger.warning("No valid records found. Created empty CSV with headers.")
        
        # Log excluded haloes
        with open(excluded_log_file, 'w') as f:
            f.write(f"# Excluded Haloes Log\n")
            f.write(f"# Snapshot: {snapshot_id}\n")
            f.write(f"# Total Excluded: {len(excluded_haloes)}\n\n")
            for halo_id in excluded_haloes:
                f.write(f"{halo_id}\n")
        
        logger.info(f"Excluded haloes log saved to {excluded_log_file}")
        
        # Log metrics
        elapsed_time = time.time() - start_time
        log_metric(logger, "pipeline_total_time", elapsed_time)
        log_metric(logger, "pipeline_valid_haloes", len(df))
        log_metric(logger, "pipeline_excluded_haloes", len(excluded_haloes))
        
        logger.info(f"Pipeline completed successfully in {elapsed_time:.2f} seconds")
        
    except Exception as e:
        log_error(logger, "Error in run_pipeline", e)
        raise
    finally:
        log_task_end(logger, "run_pipeline")
    
    return output_file

def main():
    """
    Entry point for the pipeline runner script.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run the halo shape processing pipeline")
    parser.add_argument("--snapshot", type=int, default=0, help="Snapshot ID to process")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory")
    parser.add_argument("--chunk-size", type=int, default=100, help="Number of haloes per chunk")
    
    args = parser.parse_args()
    
    output_path = run_pipeline(
        snapshot_id=args.snapshot,
        output_dir=args.output_dir,
        chunk_size=args.chunk_size
    )
    
    print(f"Pipeline completed. Output saved to: {output_path}")

if __name__ == "__main__":
    main()