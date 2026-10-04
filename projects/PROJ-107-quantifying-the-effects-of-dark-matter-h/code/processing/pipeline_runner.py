import os
import gc
import logging
import time
import json
import csv
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from utils.config import get_project_root, get_data_processed_path, get_data_raw_path, get_project_root
from utils.logging import get_pipeline_logger, log_task_start, log_task_end, log_error, log_metric
from utils.io import write_csv_with_associational_flag, write_json_with_associational_flag, iter_hdf5_groups
from processing.inertia_tensor import compute_reduced_inertia_tensor, compute_eigenvalues_and_eigenvectors, compute_shape_from_inertia
from processing.shape_metrics import compute_axial_ratios, compute_triaxiality, validate_shape_metrics, filter_halo_by_particle_count, get_exclusion_reason

logger = get_pipeline_logger(__name__)

# Constants for validation
MIN_PARTICLE_COUNT = 10000
VALIDATION_ERROR_TOLERANCE = 1e-6

def iterate_haloes(snapshot_path: Path) -> List[Dict[str, Any]]:
    """
    Iterates over halo files in the snapshot directory.
    In a real streaming scenario, this would yield halo IDs or file paths
    one by one to avoid loading the full list into memory.
    For this implementation, we assume a list of halo IDs is available
    or generated from the file structure.
    """
    # Placeholder: In a real scenario, this would read from the TNG API or HDF5 structure
    # to get a list of halo IDs. For now, we simulate a list of IDs.
    # In the actual pipeline, this would be replaced with a real iterator.
    # We will use a small set of IDs for demonstration if no real data is present,
    # but the logic is designed to handle a large list.
    # NOTE: The task requires real data. If no real data source is found, this will fail loudly.
    # We assume the TNG data has been downloaded to data/raw/tng/snapshot_000/
    
    # Attempt to discover halo files if they exist
    halo_files = []
    if snapshot_path.exists():
        for f in snapshot_path.glob("halo_*.hdf5"):
            halo_files.append(f)
    
    if not halo_files:
        # If no files found, we cannot proceed with real data.
        # The task requires real data, so we raise an error.
        raise FileNotFoundError(f"No halo files found in {snapshot_path}. Ensure TNG data is downloaded.")

    # Extract halo IDs from filenames (e.,g., halo_000.hdf5 -> 0)
    halo_ids = []
    for f in halo_files:
        try:
            # Simple parsing: assume filename is halo_<id>.hdf5
            halo_id = int(f.stem.split('_')[1])
            halo_ids.append(halo_id)
        except (IndexError, ValueError):
            continue
    
    return halo_ids

def process_halo_chunk(halo_id: int, snapshot_path: Path) -> Optional[Dict[str, Any]]:
    """
    Processes a single halo to compute shape metrics.
    Returns a dictionary with shape metrics or None if the halo is excluded.
    """
    halo_file = snapshot_path / f"halo_{halo_id}.hdf5"
    
    if not halo_file.exists():
        logger.warning(f"Halo file not found: {halo_file}")
        return None

    try:
        # In a real implementation, we would load particle data from the HDF5 file.
        # Since we are constrained by memory, we assume the inertia tensor 
        # or particle positions are available. 
        # For this task, we assume the inertia tensor is pre-calculated or 
        # we load the necessary particle subset.
        
        # Simulate loading inertia tensor components from the file
        # In reality, this would be:
        # with h5py.File(halo_file, 'r') as f:
        #     pos = f['Particles/Type1/Coordinates'][:]
        #     mass = f['Particles/Type1/Mass'][:]
        #     inertia = compute_reduced_inertia_tensor(pos, mass)
        
        # Placeholder for real data loading:
        # We will assume the file contains the necessary data and attempt to read it.
        # If the structure is different, this will raise an error, which is desired.
        
        # Check if the file has the expected structure
        import h5py
        with h5py.File(halo_file, 'r') as f:
            if 'Particles' not in f:
                raise ValueError(f"Halo file {halo_file} does not contain 'Particles' group.")
            
            # Attempt to get particle count
            # Assuming Type 1 (dark matter) particles
            if 'Type1' not in f['Particles']:
                # Try other types if Type1 is missing
                particle_types = [key for key in f['Particles'].keys() if key.startswith('Type')]
                if not particle_types:
                    raise ValueError(f"No particle types found in {halo_file}")
                # Use the first available type
                p_type = particle_types[0]
            else:
                p_type = 'Type1'
                
            pos = f['Particles'][p_type]['Coordinates'][:]
            mass = f['Particles'][p_type]['Mass'][:]
            
            if len(pos) < MIN_PARTICLE_COUNT:
                return None

            # Compute inertia tensor
            inertia = compute_reduced_inertia_tensor(pos, mass)
            eigenvalues, _ = compute_eigenvalues_and_eigenvectors(inertia)
            
            # Compute shape metrics
            b_a, c_a = compute_axial_ratios(eigenvalues)
            triaxiality = compute_triaxiality(eigenvalues)
            
            # Mass of the halo (sum of particle masses)
            halo_mass = np.sum(mass)
            
            return {
                "halo_id": halo_id,
                "mass": float(halo_mass),
                "b_a_ratio": float(b_a),
                "c_a_ratio": float(c_a),
                "triaxiality": float(triaxiality),
                "particle_count": len(mass)
            }

    except Exception as e:
        logger.error(f"Error processing halo {halo_id}: {e}")
        return None

def validate_shape_metrics_chunk(metrics: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validates the computed shape metrics.
    Returns (is_valid, error_message).
    """
    if metrics is None:
        return False, "Metrics is None"

    b_a = metrics.get("b_a_ratio")
    c_a = metrics.get("c_a_ratio")
    tri = metrics.get("triaxiality")
    p_count = metrics.get("particle_count")

    # Validate particle count
    if p_count is None or p_count < MIN_PARTICLE_COUNT:
        return False, get_exclusion_reason("particle_count")

    # Validate axial ratios
    if b_a is None or not (0 < b_a <= 1):
        return False, get_exclusion_reason("b_a_ratio")
    if c_a is None or not (0 < c_a <= 1):
        return False, get_exclusion_reason("c_a_ratio")

    # Validate triaxiality
    if tri is None or not (0 <= tri <= 1):
        return False, get_exclusion_reason("triaxiality")

    return True, None

def save_halo_shapes_chunk(results: List[Dict[str, Any]], output_path: Path):
    """
    Saves a chunk of validated halo shape results to CSV.
    """
    if not results:
        return

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write CSV with associational flag
    # The utility function handles the flag injection
    write_csv_with_associational_flag(
        output_path,
        results,
        columns=["halo_id", "mass", "b_a_ratio", "c_a_ratio", "triaxiality", "particle_count"]
    )
    logger.info(f"Saved chunk to {output_path}")

def write_exclusion_log(excluded_haloes: List[Dict[str, Any]], output_path: Path):
    """
    Writes the log of excluded haloes to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_json_with_associational_flag(output_path, excluded_haloes)
    logger.info(f"Saved exclusion log to {output_path}")

def run_pipeline(snapshot_path: Optional[Path] = None):
    """
    Main pipeline function to process all haloes, validate metrics, and save results.
    """
    if snapshot_path is None:
        # Default path
        snapshot_path = get_data_raw_path() / "tng" / "snapshot_000"
    
    log_task_start("T017 - Aggregation and Validation")
    start_time = time.time()

    # 1. Iterate over haloes
    try:
        halo_ids = iterate_haloes(snapshot_path)
    except FileNotFoundError as e:
        log_error(str(e))
        raise

    logger.info(f"Found {len(halo_ids)} haloes to process.")

    valid_results = []
    excluded_haloes = []

    # 2. Process each halo (Streaming logic)
    for halo_id in halo_ids:
        # Process chunk
        metrics = process_halo_chunk(halo_id, snapshot_path)
        
        if metrics is None:
            # If processing failed or particle count < 10k, it's excluded
            excluded_haloes.append({
                "halo_id": halo_id,
                "reason": "Processing failed or particle count < 10k"
            })
            continue

        # 3. Validate metrics
        is_valid, error_msg = validate_shape_metrics_chunk(metrics)
        
        if is_valid:
            valid_results.append(metrics)
        else:
            excluded_haloes.append({
                "halo_id": halo_id,
                "reason": error_msg
            })

        # Optional: Log progress every 100 haloes
        if halo_id % 100 == 0:
            logger.info(f"Processed halo {halo_id}. Valid: {len(valid_results)}, Excluded: {len(excluded_haloes)}")
            gc.collect()

    # 4. Merge chunks (In this streaming case, 'valid_results' is the merged list)
    # Since we are streaming, we write directly to the final output file 
    # rather than accumulating chunks in memory if the list is too large.
    # However, for the final output, we write the accumulated valid results.
    # If the list is too large, we would write in chunks, but the task asks for a single CSV.
    # We assume the number of valid haloes fits in memory or we write in chunks.
    # For this task, we write the final CSV.
    
    output_csv_path = get_data_processed_path() / "halo_shapes.csv"
    output_json_path = get_data_processed_path() / "exclusion_log.json"

    if valid_results:
        save_halo_shapes_chunk(valid_results, output_csv_path)
    else:
        logger.warning("No valid halo shapes found.")

    if excluded_haloes:
        write_exclusion_log(excluded_haloes, output_json_path)
    else:
        # Write an empty log if no exclusions
        write_json_with_associational_flag(output_json_path, [])

    elapsed = time.time() - start_time
    log_metric("processing_time_seconds", elapsed)
    log_metric("valid_halo_count", len(valid_results))
    log_metric("excluded_halo_count", len(excluded_haloes))
    
    log_task_end("T017 - Aggregation and Validation")
    logger.info(f"Pipeline completed. Valid: {len(valid_results)}, Excluded: {len(excluded_haloes)}")

def main():
    """
    Entry point for the pipeline runner.
    """
    run_pipeline()

if __name__ == "__main__":
    main()
