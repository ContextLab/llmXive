import logging
import time
import json
import csv
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import asdict, dataclass
from datetime import datetime
import numpy as np
from scipy import stats

from config import Solvent, SimulationConfig, AnalysisConfig
from data_models.bootstrap_stats import BootstrapStats
from utils.logging import get_logger

logger = get_logger(__name__)

# Configuration constants
DEFAULT_ITERATIONS = 1000
FALLBACK_ITERATIONS = 100
WALL_CLOCK_TIMEOUT_SECONDS = 5.5 * 3600  # 5.5 hours in seconds
CI_LEVEL = 0.95

@dataclass
class BootstrapIterationResult:
    solvent: str
    timescale: str
    mean_mae: float
    std_mae: float
    ci_lower: float
    ci_upper: float
    iterations_used: int
    fallback_triggered: bool
    timestamp: str

def load_mae_distribution(
    data_dir: Path,
    solvent: str,
    timescale: str
) -> List[float]:
    """
    Load the MAE distribution for a specific solvent and timescale.
    Expects a JSON file at: data/processed/<solvent>_<timescale>_mae_distribution.json
    """
    file_path = data_dir / f"{solvent}_{timescale}_mae_distribution.json"
    if not file_path.exists():
        raise FileNotFoundError(
            f"MAE distribution file not found: {file_path}. "
            "Ensure the main pipeline has generated diffusion results and MAE distributions."
        )
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    if 'mae_values' not in data:
        raise ValueError(f"Invalid MAE distribution file {file_path}: missing 'mae_values' key")
    
    return data['mae_values']

def perform_bootstrap(
    mae_values: List[float],
    n_iterations: int,
    ci_level: float = CI_LEVEL
) -> Tuple[float, float, float, float]:
    """
    Perform bootstrap resampling on the MAE distribution.
    
    Returns:
        Tuple of (mean, std, ci_lower, ci_upper)
    """
    if not mae_values:
        raise ValueError("MAE values list is empty; cannot perform bootstrap.")
    
    mae_array = np.array(mae_values)
    n_samples = len(mae_array)
    
    bootstrap_means = []
    
    for _ in range(n_iterations):
        # Resample with replacement
        resample = np.random.choice(mae_array, size=n_samples, replace=True)
        bootstrap_means.append(np.mean(resample))
    
    bootstrap_means = np.array(bootstrap_means)
    mean_mae = np.mean(bootstrap_means)
    std_mae = np.std(bootstrap_means)
    
    # Percentile method for confidence intervals
    alpha = 1 - ci_level
    ci_lower = np.percentile(bootstrap_means, 100 * alpha / 2)
    ci_upper = np.percentile(bootstrap_means, 100 * (1 - alpha / 2))
    
    return mean_mae, std_mae, ci_lower, ci_upper

def run_bootstrap_analysis(
    solvent: str,
    timescale: str,
    data_dir: Path,
    max_iterations: int = DEFAULT_ITERATIONS,
    fallback_iterations: int = FALLBACK_ITERATIONS,
    timeout_seconds: float = WALL_CLOCK_TIMEOUT_SECONDS
) -> BootstrapIterationResult:
    """
    Run bootstrap analysis for a single solvent-timescale combination.
    Implements fallback logic if wall-clock time exceeds threshold.
    """
    start_time = time.time()
    fallback_triggered = False
    iterations_to_use = max_iterations
    
    logger.info(f"Starting bootstrap analysis for {solvent} at {timescale}")
    
    try:
        mae_values = load_mae_distribution(data_dir, solvent, timescale)
    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    
    # Check if we can afford the full iteration count
    # Estimate time per iteration based on a small sample if needed, 
    # but for safety we'll just run and check time periodically.
    # However, the requirement is to fallback if TOTAL time > 5.5h.
    # Since 1000 iterations is usually fast, we start with that.
    # If the system is extremely slow, we might need to check mid-run.
    # For simplicity and robustness, we'll check time after a small batch 
    # and extrapolate, or just run and fallback if it takes too long.
    # Given the constraint, we'll run in chunks to monitor time.
    
    chunk_size = 100
    bootstrap_means = []
    mae_array = np.array(mae_values)
    n_samples = len(mae_array)
    total_iterations = 0
    
    while total_iterations < iterations_to_use:
        # Check elapsed time
        elapsed = time.time() - start_time
        if elapsed > timeout_seconds:
            logger.warning(
                f"Wall-clock time ({elapsed:.1f}s) exceeded threshold ({timeout_seconds:.1f}s). "
                f"Falling back to {fallback_iterations} iterations."
            )
            fallback_triggered = True
            iterations_to_use = fallback_iterations
            # Reset bootstrap_means for the new count if we haven't started or if we need to restart
            # But since we might have partial data, we'll just stop and use what we have up to fallback_iterations?
            # Actually, the requirement is to fallback to 100. So we should stop and re-run 100 if we haven't done 100 yet?
            # Or just stop the current run and use 100.
            # Let's interpret: if we are running and time exceeds, we stop and re-run with 100.
            # But to avoid infinite loops, we'll set a flag and break.
            # However, the simplest interpretation: if total time > 5.5h, use 100 iterations.
            # So we break and then re-run with 100? Or just use the first 100 we did?
            # The spec says: "fallback to 100 iterations if wall-clock time > 5.5h"
            # This implies we should not exceed 5.5h. So if we are about to start a run that might take too long, we use 100.
            # But we don't know how long 1000 will take until we run.
            # Alternative: run in small chunks and if time exceeds, stop and use 100.
            # But if we already ran 500, and time is 5.5h, we can't go back to 100.
            # So the safe way: estimate time for 100 first? No, that's extra work.
            # Given the ambiguity, we'll implement: run up to max_iterations, but if at any point 
            # elapsed time > timeout_seconds, we stop and use the first min(100, total_iterations) as the result?
            # That doesn't meet "fallback to 100". 
            # Better: if we detect that we are running slow, we switch to 100 immediately and run 100.
            # But we've already run some. 
            # Let's do this: 
            #   - Run in chunks of 100.
            #   - After each chunk, check time.
            #   - If time > timeout, then we stop and if we haven't done 100, we run 100 (but we already did some, so we have at least 100?).
            #   - Actually, if we did 100 and time is still low, we continue.
            #   - If we did 100 and time is already > 5.5h, then we stop and use these 100.
            #   - If we did 200 and time is > 5.5h, then we should have stopped at 100? But we didn't know.
            # This is tricky. 
            # Revised plan: 
            #   We are allowed to run up to 5.5h. If we exceed, we must have used only 100 iterations.
            #   So we can't exceed 5.5h. Therefore, we should check before starting the full run if the system is slow.
            #   But we don't know.
            #   Alternative: run 100 first, measure time. If time for 100 > 5.5h/1000 * 100 = 1980s (33 min), then we know 1000 will take 5.5h.
            #   But 5.5h is 19800s. So if 100 iterations take > 1980s, then 1000 will take > 19800s.
            #   So: 
            #       Step 1: Run 100 iterations.
            #       Step 2: If time > 1980s, then fallback to 100 (we already have 100).
            #       Step 3: Else, run remaining 900.
            #   But the requirement says "fallback to 100 if wall-clock time > 5.5h", meaning if the total time for the run exceeds 5.5h, then we should have used 100.
            #   So if we run 100 and it takes 2000s, then we are already over the per-iteration budget? Not exactly.
            #   Let's stick to the literal: if during the run the total time exceeds 5.5h, then we stop and use 100.
            #   But we can't use 100 if we already ran 500. 
            #   Therefore, the only safe way is to run 100 first, and if that takes too long, we stop. Otherwise, we continue.
            #   However, the spec doesn't say "if 100 takes too long", it says "if wall-clock time > 5.5h".
            #   Given the ambiguity, we'll implement:
            #       - Run in chunks of 100.
            #       - After each chunk, check total elapsed time.
            #       - If elapsed > 5.5h, then we stop and use the first 100 iterations we did (if we did at least 100) or if we did less than 100, we run up to 100? 
            #   This is messy.
            #
            #   Simpler interpretation: The fallback is a safety net. We try to run 1000, but if the system is so slow that we hit 5.5h before finishing, then we stop and use the first 100 iterations we managed to complete.
            #   But the requirement says "fallback to 100", meaning we should only do 100.
            #   So: 
            #       If we detect that we are running slow (e.g., first 100 took > 1980s), then we only do 100.
            #       Otherwise, we do 1000.
            #   This ensures we never exceed 5.5h (because 1000 * (time_per_iter) < 1000 * (1980/100) = 19800s = 5.5h).
            #
            #   Let's do:
            #       1. Run 100 iterations.
            #       2. Measure time.
            #       3. If time > 1980s (5.5h / 1000 * 100), then we set iterations_to_use = 100 and stop.
            #       4. Else, we run the remaining 900.
            #
            #   This is a proactive fallback.
            #
            #   We'll implement this proactive approach.
            pass

    # Proactive fallback: run 100 first to estimate time
    chunk_size = 100
    bootstrap_means = []
    mae_array = np.array(mae_values)
    n_samples = len(mae_array)
    
    # Run first chunk of 100
    for _ in range(chunk_size):
        resample = np.random.choice(mae_array, size=n_samples, replace=True)
        bootstrap_means.append(np.mean(resample))
    
    elapsed_after_100 = time.time() - start_time
    
    if elapsed_after_100 > (timeout_seconds / 10):  # 5.5h / 1000 * 100 = 1980s, so threshold for 100 is 1980s
        # If 100 iterations took more than 1/10th of the total budget (which is 1980s), then 1000 would take 10x that -> 19800s = 5.5h.
        # So we fallback to 100.
        logger.warning(
            f"First 100 iterations took {elapsed_after_100:.1f}s. "
            f"Projected time for 1000 iterations: {elapsed_after_100 * 10:.1f}s. "
            f"Falling back to 100 iterations to stay within {timeout_seconds:.1f}s budget."
        )
        fallback_triggered = True
        iterations_used = 100
    else:
        # Continue with remaining 900
        remaining = max_iterations - chunk_size
        for _ in range(remaining):
            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                logger.warning(
                    f"Wall-clock time ({elapsed:.1f}s) exceeded threshold ({timeout_seconds:.1f}s) during extended run. "
                    f"Stopping early. Using {len(bootstrap_means)} iterations."
                )
                # We have at least 100, so we can use what we have? But the requirement is 100.
                # Since we already have 100 and more, and we exceeded time, we should have used 100.
                # But we can't undo. We'll use the first 100? Or all we have?
                # The requirement says "fallback to 100", meaning we should only do 100.
                # Since we exceeded time, we break and use the first 100 we did.
                bootstrap_means = bootstrap_means[:100]
                fallback_triggered = True
                break
            resample = np.random.choice(mae_array, size=n_samples, replace=True)
            bootstrap_means.append(np.mean(resample))
        iterations_used = len(bootstrap_means)

    bootstrap_means = np.array(bootstrap_means)
    mean_mae = np.mean(bootstrap_means)
    std_mae = np.std(bootstrap_means)
    ci_lower = np.percentile(bootstrap_means, 100 * (1 - CI_LEVEL) / 2)
    ci_upper = np.percentile(bootstrap_means, 100 * (1 + CI_LEVEL) / 2)
    
    return BootstrapIterationResult(
        solvent=solvent,
        timescale=timescale,
        mean_mae=float(mean_mae),
        std_mae=float(std_mae),
        ci_lower=float(ci_lower),
        ci_upper=float(ci_upper),
        iterations_used=iterations_used,
        fallback_triggered=fallback_triggered,
        timestamp=datetime.utcnow().isoformat()
    )

def save_bootstrap_stats(
    results: List[BootstrapIterationResult],
    output_path: Path
) -> None:
    """
    Save bootstrap statistics to a CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        'solvent', 'timescale', 'mean_mae', 'std_mae', 
        'ci_lower', 'ci_upper', 'iterations_used', 
        'fallback_triggered', 'timestamp'
    ]
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(asdict(result))
    
    logger.info(f"Bootstrap statistics saved to {output_path}")

def batch_bootstrap_analysis(
    solvents: List[str],
    timescales: List[str],
    data_dir: Path,
    output_dir: Path
) -> List[BootstrapIterationResult]:
    """
    Run bootstrap analysis for all solvent-timescale combinations.
    """
    results = []
    output_path = output_dir / "bootstrap_stats.csv"
    
    for solvent in solvents:
        for timescale in timescales:
            try:
                result = run_bootstrap_analysis(
                    solvent=solvent,
                    timescale=timescale,
                    data_dir=data_dir
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed bootstrap for {solvent} at {timescale}: {e}")
                # Optionally, we could skip or record a failure
                continue
    
    if results:
        save_bootstrap_stats(results, output_path)
    else:
        logger.warning("No bootstrap results to save.")
    
    return results

def main():
    """
    Entry point for bootstrap analysis.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Hard-coded configuration for now, but could be loaded from config.py
    solvents = ['water', 'ethanol', 'acetone']
    timescales = ['1ns', '5ns', '10ns']
    
    data_dir = Path("data/processed")
    output_dir = Path("data/processed")
    
    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        return 1
    
    results = batch_bootstrap_analysis(solvents, timescales, data_dir, output_dir)
    
    if results:
        logger.info(f"Successfully processed {len(results)} solvent-timescale combinations.")
    else:
        logger.warning("No results generated.")
    
    return 0

if __name__ == "__main__":
    exit(main())
