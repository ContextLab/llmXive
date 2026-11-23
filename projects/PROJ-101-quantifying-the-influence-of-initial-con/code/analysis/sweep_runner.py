"""
Sweep runner module for parallel execution of trajectory generation and analysis.

This module implements parallelized trial execution using multiprocessing to
optimize performance across CPU cores.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import multiprocessing as mp
from functools import partial
from concurrent.futures import ProcessPoolExecutor, as_completed
import traceback

import numpy as np

# Import from local modules using the defined API surface
from config import get_full_config, set_simulation_seed, set_noise_levels, set_N_oscillators
from data.generator import generate_batch_trajectories, UnphysicalTrajectoryError
from data.loader import save_trajectory
from analysis.ftle import run_sliding_window_sweep, load_baseline_and_compute_ftle
from analysis.baseline import load_baseline_result, validate_and_gate_for_baseline, NonChaoticSystemError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def _worker_init(seed_offset: int):
    """Initialize worker process with unique seed offset."""
    # Each worker gets a unique seed to ensure reproducibility
    base_seed = 42  # Base seed from config
    worker_seed = base_seed + seed_offset
    np.random.seed(worker_seed)
    logger.info(f"Worker initialized with seed: {worker_seed}")

def _run_single_trial(args: Tuple[int, int, float, int]) -> Dict[str, Any]:
    """
    Run a single trial for trajectory generation and FTLE computation.
    
    This function is designed to be executed in a separate process.
    
    Args:
        args: Tuple of (trial_id, N_oscillators, sigma_noise, trial_index)
    
    Returns:
        Dictionary containing trial results or error information.
    """
    trial_id, N_oscillators, sigma_noise, trial_index = args
    
    try:
        # Set unique seed for this trial within the worker
        worker_seed = int(trial_id * 1000 + trial_index)
        np.random.seed(worker_seed)
        
        # Generate trajectory
        logger.debug(f"Worker generating trajectory: N={N_oscillators}, sigma={sigma_noise}, trial={trial_index}")
        
        trajectory_data = generate_batch_trajectories(
            N=N_oscillators,
            sigma_noise=sigma_noise,
            n_trials=1,  # Generate one trajectory at a time
            seed=worker_seed
        )
        
        if not trajectory_data or len(trajectory_data) == 0:
            return {
                "trial_id": trial_id,
                "status": "error",
                "error": "No trajectory data generated"
            }
        
        # Extract the single trajectory
        traj = trajectory_data[0]
        
        # Save trajectory to disk
        config = get_full_config()
        output_path = Path(config.simulation.output_dir) / "raw"
        output_path.mkdir(parents=True, exist_ok=True)
        
        filename = f"trajectory_N{N_oscillators}_sigma{sigma_noise:.3f}_trial{trial_index}.csv"
        filepath = output_path / filename
        
        save_trajectory(traj, filepath)
        
        # Compute FTLE if baseline exists
        ftle_result = None
        baseline_path = Path(config.analysis.baseline_dir) / f"baseline_{N_oscillators}.json"
        
        if baseline_path.exists():
            try:
                ftle_result = load_baseline_and_compute_ftle(
                    trajectory_data=[traj],
                    baseline_path=baseline_path,
                    window_sizes=[500, 1000, 5000]
                )
                
                if ftle_result and len(ftle_result) > 0:
                    ftle_result = ftle_result[0]  # Take first result
            except Exception as ftle_err:
                logger.warning(f"FTLE computation failed for trial {trial_id}: {ftle_err}")
                ftle_result = None
        else:
            logger.warning(f"Baseline not found for N={N_oscillators}, skipping FTLE")
        
        return {
            "trial_id": trial_id,
            "N": N_oscillators,
            "sigma": sigma_noise,
            "trial_index": trial_index,
            "status": "success",
            "filepath": str(filepath),
            "ftle_results": ftle_result
        }
        
    except UnphysicalTrajectoryError as e:
        logger.warning(f"Unphysical trajectory detected for trial {trial_id}: {e}")
        return {
            "trial_id": trial_id,
            "N": N_oscillators,
            "sigma": sigma_noise,
            "trial_index": trial_index,
            "status": "unphysical",
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Trial {trial_id} failed with exception: {e}")
        logger.error(traceback.format_exc())
        return {
            "trial_id": trial_id,
            "N": N_oscillators,
            "sigma": sigma_noise,
            "trial_index": trial_index,
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

def run_full_sweep(
    N_values: Optional[List[int]] = None,
    noise_levels: Optional[List[float]] = None,
    n_processes: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run the full generation and analysis sweep with parallelized trials.
    
    This function parallelizes the execution of trials across CPU cores using
    multiprocessing to significantly reduce runtime for large sweeps.
    
    Args:
        N_values: List of oscillator counts to test. Defaults to config values.
        noise_levels: List of noise levels to test. Defaults to config values.
        n_processes: Number of parallel processes. Defaults to CPU count.
    
    Returns:
        Dictionary containing all results and metadata.
    """
    config = get_full_config()
    
    # Use config values if not provided
    if N_values is None:
        N_values = config.simulation.N_values
    if noise_levels is None:
        noise_levels = config.analysis.noise_levels
    
    if n_processes is None:
        n_processes = max(1, mp.cpu_count() - 1)  # Leave one core free
    
    logger.info(f"Starting parallel sweep with {n_processes} processes")
    logger.info(f"N values: {N_values}")
    logger.info(f"Noise levels: {noise_levels}")
    
    # Prepare task arguments
    tasks = []
    trial_counter = 0
    
    for N in N_values:
        # Validate baseline exists before processing
        baseline_path = Path(config.analysis.baseline_dir) / f"baseline_{N}.json"
        if not baseline_path.exists():
            logger.warning(f"Baseline missing for N={N}, skipping this configuration")
            continue
        
        for sigma in noise_levels:
            # Determine number of trials based on noise level
            k = 50 if sigma < 0.01 else 30
            
            for t in range(k):
                tasks.append((trial_counter, N, sigma, t))
                trial_counter += 1
    
    logger.info(f"Prepared {len(tasks)} tasks for execution")
    
    # Execute tasks in parallel
    results = []
    start_time = datetime.now()
    
    with ProcessPoolExecutor(
        max_workers=n_processes,
        initializer=_worker_init,
        initargs=(0,)  # Seed offset (0 for base, workers add their own)
    ) as executor:
        # Submit all tasks
        future_to_task = {
            executor.submit(_run_single_trial, task): task 
            for task in tasks
        }
        
        # Collect results as they complete
        completed = 0
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            try:
                result = future.result()
                results.append(result)
                completed += 1
                
                if completed % 10 == 0:
                    logger.info(f"Progress: {completed}/{len(tasks)} tasks completed")
                    
            except Exception as e:
                logger.error(f"Task {task} failed: {e}")
                results.append({
                    "trial_id": task[0],
                    "status": "failed",
                    "error": str(e)
                })
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    logger.info(f"Sweep completed in {duration:.2f} seconds")
    logger.info(f"Total results: {len(results)}")
    
    # Aggregate results
    successful = sum(1 for r in results if r.get("status") == "success")
    unphysical = sum(1 for r in results if r.get("status") == "unphysical")
    failed = sum(1 for r in results if r.get("status") in ["error", "failed"])
    
    summary = {
        "total_tasks": len(tasks),
        "successful": successful,
        "unphysical": unphysical,
        "failed": failed,
        "duration_seconds": duration,
        "n_processes": n_processes,
        "N_values": N_values,
        "noise_levels": noise_levels
    }
    
    return {
        "summary": summary,
        "results": results,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat()
    }

def save_sweep_results(results: Dict[str, Any], output_path: Optional[str] = None):
    """
    Save sweep results to disk.
    
    Args:
        results: Results dictionary from run_full_sweep.
        output_path: Optional custom output path. Defaults to config.
    """
    config = get_full_config()
    
    if output_path is None:
        output_path = Path(config.analysis.output_dir) / "processed" / "sweep_results.json"
    else:
        output_path = Path(output_path)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Results saved to {output_path}")

def main():
    """Main entry point for the sweep runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run parallel sweep of chaotic system simulations")
    parser.add_argument("--N-values", type=int, nargs="+", help="Oscillator counts to test")
    parser.add_argument("--noise-levels", type=float, nargs="+", help="Noise levels to test")
    parser.add_argument("--processes", type=int, help="Number of parallel processes")
    parser.add_argument("--output", type=str, help="Output file path")
    
    args = parser.parse_args()
    
    N_values = args.N_values if args.N_values else None
    noise_levels = args.noise_levels if args.noise_levels else None
    n_processes = args.processes if args.processes else None
    output_path = args.output
    
    results = run_full_sweep(
        N_values=N_values,
        noise_levels=noise_levels,
        n_processes=n_processes
    )
    
    save_sweep_results(results, output_path)
    
    # Print summary
    summary = results["summary"]
    print(f"\n=== Sweep Summary ===")
    print(f"Total tasks: {summary['total_tasks']}")
    print(f"Successful: {summary['successful']}")
    print(f"Unphysical: {summary['unphysical']}")
    print(f"Failed: {summary['failed']}")
    print(f"Duration: {summary['duration_seconds']:.2f}s")
    print(f"Processes: {summary['n_processes']}")

if __name__ == "__main__":
    main()