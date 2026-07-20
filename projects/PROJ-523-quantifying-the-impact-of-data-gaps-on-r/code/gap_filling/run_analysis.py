"""
Main analysis runner with convergence failure handling.

This script orchestrates the gap-filling algorithms and handles convergence failures
according to FR-008. It wraps the individual algorithm implementations and ensures
that failures are logged, recorded, and excluded from downstream analysis.
"""
import os
import sys
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Import from existing project modules
from config import (
    DATA_DERIVED_DIR,
    DATA_RESULTS_DIR,
    N_SIDE,
    GAP_FRACTIONS,
    GAP_MORPHOLOGIES,
    get_dtype
)
from data_io import load_map_from_fits, load_mask_from_fits, save_metadata
from simulation.utils import get_available_gap_fractions
from gap_filling.failure_handler import (
    handle_convergence_failure,
    is_realization_excluded,
    get_excluded_realization_ids
)

# Import algorithm implementations
from gap_filling.harmonic_interp import apply_harmonic_filling
from gap_filling.wiener_filter import apply_wiener_filling
from gap_filling.iterative_synthesis import apply_iterative_filling

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Available algorithms
ALGORITHMS = {
    "harmonic_interpolation": apply_harmonic_filling,
    "wiener_filter": apply_wiener_filling,
    "iterative_synthesis": apply_iterative_filling
}


def run_single_algorithm(
    realization_id: str,
    algo_name: str,
    gap_fraction: float,
    gap_morphology: str,
    map_path: Path,
    mask_path: Path
) -> Optional[Dict[str, Any]]:
    """
    Run a single gap-filling algorithm on a masked map.
    
    This function handles convergence failures according to FR-008:
    - Logs the failure with full context
    - Records the exclusion
    - Returns None for failed cases (excluded from analysis)
    
    Args:
        realization_id: Unique identifier for the realization
        algo_name: Name of the algorithm to run
        gap_fraction: Target gap fraction
        gap_morphology: Type of gap morphology
        map_path: Path to the CMB map file
        mask_path: Path to the gap mask file
    
    Returns:
        Dictionary with results if successful, None if failed/excluded
    """
    # Check if this realization is already excluded
    if is_realization_excluded(realization_id):
        logger.info(f"Skipping excluded realization: {realization_id}")
        return None
    
    logger.info(
        f"Running {algo_name} on {realization_id} "
        f"(gap={gap_fraction}, morphology={gap_morphology})"
    )
    
    start_time = time.time()
    
    try:
        # Load the map and mask
        cmb_map = load_map_from_fits(map_path)
        mask = load_mask_from_fits(mask_path)
        
        # Get the appropriate algorithm function
        algo_func = ALGORITHMS.get(algo_name)
        if algo_func is None:
            raise ValueError(f"Unknown algorithm: {algo_name}")
        
        # Run the algorithm
        filled_map, metadata = algo_func(cmb_map, mask)
        
        exec_time = time.time() - start_time
        
        logger.info(
            f"Successfully completed {algo_name} for {realization_id} "
            f"in {exec_time:.2f}s"
        )
        
        return {
            "status": "SUCCESS",
            "realization_id": realization_id,
            "algorithm": algo_name,
            "gap_fraction": gap_fraction,
            "gap_morphology": gap_morphology,
            "execution_time_sec": exec_time,
            "filled_map": filled_map,
            "metadata": metadata
        }
    
    except Exception as e:
        exec_time = time.time() - start_time
        
        # Handle the convergence failure
        failure_result = handle_convergence_failure(
            exception=e,
            realization_id=realization_id,
            algo_name=algo_name,
            gap_fraction=gap_fraction,
            gap_morphology=gap_morphology,
            exec_time_sec=exec_time
        )
        
        logger.error(
            f"Convergence failure for {algo_name} on {realization_id}: {str(e)}"
        )
        
        return None


def run_full_analysis(
    realization_ids: List[str],
    gap_fractions: Optional[List[float]] = None,
    gap_morphologies: Optional[List[str]] = None,
    algorithms: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Run the full gap-filling analysis across all configurations.
    
    Args:
        realization_ids: List of realization IDs to process
        gap_fractions: List of gap fractions to test (default: all available)
        gap_morphologies: List of morphologies to test (default: all available)
        algorithms: List of algorithms to run (default: all available)
    
    Returns:
        List of successful results (excludes failed cases)
    """
    if gap_fractions is None:
        gap_fractions = get_available_gap_fractions()
    
    if gap_morphologies is None:
        gap_morphologies = GAP_MORPHOLOGIES
    
    if algorithms is None:
        algorithms = list(ALGORITHMS.keys())
    
    results = []
    total_configs = len(realization_ids) * len(gap_fractions) * len(algorithms)
    current = 0
    
    for realization_id in realization_ids:
        for gap_fraction in gap_fractions:
            for algo_name in algorithms:
                current += 1
                
                # Determine mask path (assuming standard naming convention)
                # In a real implementation, this would be more robust
                mask_path = Path(
                    f"data/derived/masks/{realization_id}_gap_{gap_fraction:.2f}.fits"
                )
                map_path = Path(
                    f"data/derived/maps/{realization_id}_cmb.fits"
                )
                
                # Check if files exist
                if not mask_path.exists() or not map_path.exists():
                    logger.warning(
                        f"Skipping {realization_id}: missing map or mask files"
                    )
                    continue
                
                result = run_single_algorithm(
                    realization_id=realization_id,
                    algo_name=algo_name,
                    gap_fraction=gap_fraction,
                    gap_morphology="random",  # Could be parameterized
                    map_path=map_path,
                    mask_path=mask_path
                )
                
                if result is not None:
                    results.append(result)
                
                logger.info(f"Progress: {current}/{total_configs}")
    
    logger.info(
        f"Analysis complete: {len(results)} successful, "
        f"{total_configs - len(results)} failed/skipped"
    )
    
    return results


def save_analysis_results(results: List[Dict[str, Any]], output_path: Path):
    """
    Save analysis results to a JSON file.
    
    Args:
        results: List of result dictionaries
        output_path: Path to output file
    """
    # Remove non-serializable data (e.g., numpy arrays)
    serializable_results = []
    for result in results:
        serializable_result = result.copy()
        if "filled_map" in serializable_result:
            # Convert numpy array to list for JSON serialization
            serializable_result["filled_map"] = (
                serializable_result["filled_map"].tolist()
            )
        serializable_results.append(serializable_result)
    
    with open(output_path, 'w') as f:
        json.dump(serializable_results, f, indent=2)
    
    logger.info(f"Saved {len(results)} results to {output_path}")


def main():
    """Command-line entry point for the analysis runner."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run gap-filling analysis with failure handling"
    )
    parser.add_argument(
        "--realizations",
        nargs="+",
        default=None,
        help="List of realization IDs to process"
    )
    parser.add_argument(
        "--output",
        default="data/results/analysis_results.json",
        help="Output file path"
    )
    
    args = parser.parse_args()
    
    # Default realization IDs (in a real implementation, these would be loaded)
    realization_ids = args.realizations or ["sim_001", "sim_002", "sim_003"]
    
    logger.info(f"Starting analysis for {len(realization_ids)} realizations")
    
    # Run the analysis
    results = run_full_analysis(realization_ids)
    
    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_analysis_results(results, output_path)
    
    # Print summary
    excluded_count = len(get_excluded_realization_ids())
    logger.info(f"Analysis complete: {len(results)} success, {excluded_count} excluded")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())