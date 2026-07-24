"""
Main analysis runner for gap filling algorithms.

Orchestrates the execution of all gap-filling algorithms and integrates
the NaN guard and failure handling logic.
"""
import os
import sys
import json
import logging
import time
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from gap_filling.harmonic_interp import apply_harmonic_filling
from gap_filling.wiener_filter import apply_wiener_filling
from gap_filling.iterative_synthesis import apply_iterative_filling
from gap_filling.NaN_guard import NaNPropagationError
from gap_filling.failure_handler import record_excluded_realization, handle_convergence_failure

from data_io import load_map_from_fits, load_mask_from_fits, save_map_to_fits
from analysis.metadata_recorder import record_algorithm_metadata

logger = logging.getLogger(__name__)

def run_single_algorithm(
    map_path: str,
    mask_path: str,
    algo_name: str,
    algo_func,
    realization_id: str,
    output_dir: str
) -> bool:
    """
    Runs a single gap-filling algorithm on a map.
    
    Returns:
        True if successful, False if excluded (NaN or other error).
    """
    start_time = time.time()
    logger.info(f"Starting {algo_name} for realization {realization_id}")
    
    try:
        # Load data
        input_map = load_map_from_fits(map_path)
        mask = load_mask_from_fits(mask_path)
        
        # Run algorithm (NaN guard is inside algo_func)
        filled_map = algo_func(input_map, mask, realization_id)
        
        # Save result
        output_path = os.path.join(output_dir, f"{realization_id}_{algo_name}.fits")
        save_map_to_fits(filled_map, output_path)
        
        exec_time = time.time() - start_time
        
        # Record metadata
        record_algorithm_metadata(
            realization_id=realization_id,
            algo_name=algo_name,
            algo_version="1.0.0",
            exec_time_sec=exec_time,
            gap_config={"source": mask_path}
        )
        
        logger.info(f"{algo_name} completed successfully for {realization_id} in {exec_time:.2f}s")
        return True
        
    except NaNPropagationError as e:
        # Trigger exclusion logic (T024)
        logger.error(f"NaN detected in {algo_name} for {realization_id}: {e}")
        record_excluded_realization(
            realization_id=realization_id,
            reason=f"NaN propagation in {algo_name}",
            algo_name=algo_name
        )
        return False
        
    except Exception as e:
        # Handle other convergence failures
        logger.error(f"Error in {algo_name} for {realization_id}: {e}")
        handle_convergence_failure(
            realization_id=realization_id,
            reason=str(e),
            algo_name=algo_name
        )
        return False

def run_full_analysis(
    input_map_dir: str,
    input_mask_dir: str,
    output_dir: str,
    realization_ids: list
):
    """
    Runs all gap-filling algorithms on all realizations.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    algorithms = [
        ("Harmonic Interpolation", apply_harmonic_filling),
        ("Wiener Filter", apply_wiener_filling),
        ("Iterative Synthesis", apply_iterative_filling)
    ]
    
    results = {
        "start_time": datetime.now().isoformat(),
        "realizations": {}
    }
    
    for rid in realization_ids:
        map_path = os.path.join(input_map_dir, f"{rid}.fits")
        mask_path = os.path.join(input_mask_dir, f"{rid}_mask.fits")
        
        if not os.path.exists(map_path) or not os.path.exists(mask_path):
            logger.warning(f"Missing files for {rid}, skipping.")
            continue
        
        results["realizations"][rid] = {
            "status": "success",
            "algorithms": {}
        }
        
        for algo_name, algo_func in algorithms:
            success = run_single_algorithm(
                map_path, mask_path, algo_name, algo_func, rid, output_dir
            )
            results["realizations"][rid]["algorithms"][algo_name] = "success" if success else "excluded"
            
            if not success:
                results["realizations"][rid]["status"] = "partial_failure"
    
    results["end_time"] = datetime.now().isoformat()
    return results

def save_analysis_results(results: dict, output_path: str):
    """Saves the analysis results to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Analysis results saved to {output_path}")

def main():
    """Main entry point for the gap filling analysis."""
    logging.basicConfig(level=logging.INFO)
    
    # Example paths (in production, these would come from config)
    input_map_dir = "data/derived/simulated_maps"
    input_mask_dir = "data/derived/gap_masks"
    output_dir = "data/derived/filled_maps"
    output_log = "data/results/analysis_log.json"
    
    # For testing, we might just process a few
    # In real run, this would be loaded from config or generated
    realization_ids = ["sim_001", "sim_002", "sim_003"]
    
    # Ensure directories exist
    os.makedirs(input_map_dir, exist_ok=True)
    os.makedirs(input_mask_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    # Run analysis
    results = run_full_analysis(input_map_dir, input_mask_dir, output_dir, realization_ids)
    
    # Save results
    save_analysis_results(results, output_log)
    
    print("Analysis complete.")

if __name__ == "__main__":
    main()