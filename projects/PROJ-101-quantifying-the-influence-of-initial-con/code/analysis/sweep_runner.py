"""
T045: Execution of the sliding window sweep.

Runs the FTLE algorithm (T022/T023) across the required set of T values 
({500, 1000, 5000}) and aggregates results into a structured format.

This module orchestrates the batch execution of `run_sliding_window_sweep`
from `analysis.ftle` for the defined window sizes and noise levels, 
ensuring the baseline gate (T028) is respected.
"""

import numpy as np
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from analysis.ftle import run_sliding_window_sweep, FTLEResult
from analysis.baseline import load_baseline_result, validate_and_gate_for_baseline
from analysis.shadowing import gate_for_ftle_calculation
from data.loader import load_trajectory, TrajectoryFileNotFoundError
from config import get_full_config
from utils.stability import check_numerical_validity

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Defined window sizes for the sweep (T values)
WINDOW_SIZES = [500, 1000, 5000]

def run_full_sweep(
    data_dir: Path, 
    processed_dir: Path, 
    baseline_file: str = "baseline_5.json",
    overwrite: bool = False
) -> List[Dict[str, Any]]:
    """
    Executes the sliding window sweep across all configured window sizes 
    and noise levels.
    
    Args:
        data_dir: Path to `data/raw/` where trajectory files are stored.
        processed_dir: Path to `data/processed/` for output.
        baseline_file: Filename of the baseline result JSON.
        overwrite: If True, recompute even if output exists.
    
    Returns:
        List of result dictionaries containing T, sigma, N, and lambda_max.
    """
    config = get_full_config()
    simulation_config = config.simulation
    analysis_config = config.analysis
    
    # 1. Validate Baseline (T028 Gate)
    baseline_path = processed_dir / baseline_file
    if not baseline_path.exists():
        raise FileNotFoundError(f"Baseline file not found: {baseline_path}. "
                                "Run T024 first.")
    
    baseline_data = load_baseline_result(baseline_path)
    validate_and_gate_for_baseline(baseline_data)
    logger.info(f"Baseline validation passed. Lambda_max: {baseline_data['lambda_max']:.6f}")
    
    # 2. Determine noise levels and N values to sweep
    # Using the config's defined noise levels and N values
    noise_levels = simulation_config.noise_levels  # List[float]
    n_values = simulation_config.n_oscillators     # List[int]
    
    all_results = []
    
    logger.info(f"Starting sweep for N={n_values}, sigma={noise_levels}, T={WINDOW_SIZES}")
    
    for N in n_values:
        # Ensure baseline exists for this N (or use the generic one if N is fixed to 5 in config)
        # For this implementation, we assume the baseline file provided matches the current N 
        # or is the reference for the current run.
        
        for sigma in noise_levels:
            # Construct filename pattern based on T017/T018 naming convention
            # Typically: trajectory_N{N}_sigma{sigma:.4f}.npz
            # We need to find the actual file or generate a list of files if multiple exist.
            # For this sweep, we assume one trajectory per (N, sigma) pair exists in data/raw.
            
            # Attempt to locate the trajectory file
            trajectory_files = list(data_dir.glob(f"trajectory_N{N}_sigma*.npz"))
            
            if not trajectory_files:
                logger.warning(f"No trajectory found for N={N}, sigma={sigma}. Skipping.")
                continue
            
            # If multiple files exist (e.g., different seeds), we process the first one 
            # or aggregate. For T045, we process the available trajectories.
            for traj_file in trajectory_files:
                # Extract sigma from filename if possible, or rely on filename match
                # Simple heuristic: check if filename contains the current sigma string
                sigma_str = f"{sigma:.4f}"
                if sigma_str not in traj_file.name:
                    continue
                
                logger.info(f"Processing {traj_file.name}...")
                
                try:
                    # Load trajectory
                    traj_data = load_trajectory(traj_file)
                    states = traj_data['states']  # Shape: (time_steps, N*3)
                    dt = traj_data.get('dt', 0.01)
                    
                    # Validate trajectory
                    check_numerical_validity(states)
                    
                    # Run Sliding Window Sweep for this trajectory
                    # T022/T023 logic: run_sliding_window_sweep
                    sweep_results = run_sliding_window_sweep(
                        states=states,
                        window_sizes=WINDOW_SIZES,
                        dt=dt,
                        N=N
                    )
                    
                    # Aggregate results
                    for res in sweep_results:
                        if isinstance(res, FTLEResult):
                            result_entry = {
                                "N": N,
                                "sigma_noise": sigma,
                                "window_size_T": res.window_size,
                                "lambda_max": res.lambda_max,
                                "error_estimate": res.error_estimate,
                                "file_source": str(traj_file.name)
                            }
                            all_results.append(result_entry)
                        else:
                            # Handle dict result if function returns dict
                            result_entry = {
                                "N": N,
                                "sigma_noise": sigma,
                                "window_size_T": res.get("window_size_T"),
                                "lambda_max": res.get("lambda_max"),
                                "error_estimate": res.get("error_estimate"),
                                "file_source": str(traj_file.name)
                            }
                            all_results.append(result_entry)
                            
                except Exception as e:
                    logger.error(f"Error processing {traj_file}: {e}", exc_info=True)
                    continue
    
    return all_results

def save_sweep_results(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Saves the aggregated sweep results to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Sweep results saved to {output_path}")

def main():
    """
    Entry point for T045 execution.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    data_raw = project_root / "data" / "raw"
    data_processed = project_root / "data" / "processed"
    
    if not data_raw.exists():
        raise FileNotFoundError(f"Data directory not found: {data_raw}")
    if not data_processed.exists():
        raise FileNotFoundError(f"Processed directory not found: {data_processed}")
    
    baseline_file = "baseline_5.json" # Default assumption based on config
    
    results = run_full_sweep(
        data_dir=data_raw,
        processed_dir=data_processed,
        baseline_file=baseline_file
    )
    
    output_file = data_processed / "ftle_sweep_results.json"
    save_sweep_results(results, output_file)
    
    print(f"Completed sweep. Total entries: {len(results)}")
    if results:
        print(f"Sample result: {results[0]}")

if __name__ == "__main__":
    main()
