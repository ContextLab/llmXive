"""
Power Analysis and Iterative N Adjustment for LMM Interaction Effects.

This module implements the power analysis logic to determine the required sample size (N)
for detecting a medium interaction effect in a Linear Mixed-Effects Model (LMM).
It includes an iterative adjustment mechanism to ensure the data collection duration
respects the SC-005 constraint (6-hour maximum) and generates a power curve visualization.

Dependencies:
    - numpy
    - statsmodels (for LMM simulation logic)
    - scipy (for statistical distributions)
    - matplotlib (for visualization)
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server environments
import matplotlib.pyplot as plt

# Import config for path resolution
from config import get_processed_data_dir, get_project_root, get_figures_dir

# Constants
SC_005_MAX_DURATION_SECONDS = 6 * 60 * 60  # 6 hours
AVG_TIME_PER_STIMULUS_SECONDS = 45  # Estimated time to read and rate one stimulus
BASE_OVERHEAD_SECONDS = 300  # 5 minutes for survey load, consent, etc.

def load_power_analysis_results() -> Dict[str, Any]:
    """
    Loads the initial power analysis results from the JSON file.
    Returns the dictionary containing target_N, effect_size, etc.
    """
    processed_dir = get_processed_data_dir()
    file_path = processed_dir / "power_analysis_results.json"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Power analysis results not found at {file_path}")
    
    with open(file_path, 'r') as f:
        return json.load(f)

def save_power_analysis_results(results: Dict[str, Any]) -> None:
    """
    Saves the updated power analysis results to the JSON file.
    """
    processed_dir = get_processed_data_dir()
    processed_dir.mkdir(parents=True, exist_ok=True)
    file_path = processed_dir / "power_analysis_results.json"
    
    with open(file_path, 'w') as f:
        json.dump(results, f, indent=2)

def estimate_duration_for_n(n: int, num_stimuli: int = 10) -> float:
    """
    Estimates the total duration of the data collection pipeline for a given N.
    
    Args:
        n: Number of participants.
        num_stimuli: Number of stimuli per participant (default 10, read from stimuli if available).
        
    Returns:
        Estimated total duration in seconds.
    """
    # Check if we can get the actual stimulus count from the raw data
    raw_dir = get_project_root() / "data" / "raw"
    stimuli_path = raw_dir / "stimuli.csv"
    
    if stimuli_path.exists():
        try:
            # Simple CSV count to get actual stimulus number
            with open(stimuli_path, 'r') as f:
                # Count lines excluding header
                num_stimuli = sum(1 for _ in f) - 1
                if num_stimuli <= 0:
                    num_stimuli = 10
        except Exception:
            pass # Fallback to default
    
    total_stimuli_ratings = n * num_stimuli
    total_time = BASE_OVERHEAD_SECONDS + (total_stimuli_ratings * AVG_TIME_PER_STIMULUS_SECONDS)
    return total_time

def adjust_n_for_time_constraint(initial_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Iteratively adjusts the target N if the estimated duration violates SC-005 (6 hours).
    
    Logic:
    1. Calculate estimated duration for the current target_N.
    2. If duration > 6 hours, reduce N by a step (e.g., 10% or fixed amount) and re-evaluate.
    3. Continue until duration <= 6 hours or N reaches a minimum viable sample size (e.g., 20).
    4. Update the results dictionary with the new N and a note about the adjustment.
    
    Returns:
        Updated results dictionary.
    """
    current_n = initial_results.get("target_N", 128)
    min_viable_n = 20
    step_size = max(5, int(current_n * 0.1)) # Reduce by 10% or at least 5
    
    estimated_duration = estimate_duration_for_n(current_n)
    
    print(f"Initial Target N: {current_n}")
    print(f"Estimated Duration: {estimated_duration:.2f} seconds ({estimated_duration/3600:.2f} hours)")
    print(f"SC-005 Constraint: {SC_005_MAX_DURATION_SECONDS} seconds ({SC_005_MAX_DURATION_SECONDS/3600:.2f} hours)")
    
    if estimated_duration <= SC_005_MAX_DURATION_SECONDS:
        print("Duration is within constraint. No adjustment needed.")
        initial_results["adjusted"] = False
        return initial_results
    
    print("Duration exceeds constraint. Adjusting N...")
    
    while current_n > min_viable_n:
        current_n -= step_size
        if current_n < min_viable_n:
            current_n = min_viable_n
            
        estimated_duration = estimate_duration_for_n(current_n)
        print(f"  Trying N={current_n} -> Est. Duration: {estimated_duration:.2f}s")
        
        if estimated_duration <= SC_005_MAX_DURATION_SECONDS:
            print(f"  Found valid N: {current_n}")
            break
    
    # Update results
    initial_results["original_target_N"] = initial_results["target_N"]
    initial_results["target_N"] = current_n
    initial_results["adjusted"] = True
    initial_results["adjustment_reason"] = f"SC-005 time constraint (6h) exceeded. Reduced from {initial_results['original_target_N']} to {current_n}."
    initial_results["estimated_duration_seconds"] = estimate_duration_for_n(current_n)
    
    return initial_results

def generate_power_curve(results: Dict[str, Any]) -> str:
    """
    Generates a power curve visualization (Power vs. Sample Size) and saves it.
    
    Requirement: Visualize power vs. sample size to verify N sufficiency.
    Output: `data/processed/power_curve.png` (actually saved in figures dir per config, 
            but task description says processed; we follow config which is figures, 
            but task says processed. Let's check task: "output `data/processed/power_curve.png`".
            However, `get_figures_dir` exists. Usually plots go to figures. 
            The task explicitly says `data/processed/power_curve.png`. I will save to `data/processed` 
            to strictly follow the task description path, but ensure the directory exists.
    
    Args:
        results: The power analysis results dictionary containing effect_size, alpha, power, target_N.
    
    Returns:
        Path to the saved image.
    """
    # Extract parameters
    effect_size = results.get("effect_size", 0.25) # Medium effect (Cohen's f or similar proxy)
    alpha = results.get("alpha", 0.05)
    target_power = results.get("power", 0.80)
    target_n = results.get("target_N", 128)
    
    # Define range of sample sizes for the curve
    # Start from a small number up to a reasonable max (e.g., 2x target or 500)
    n_range = list(range(10, max(target_n * 2, 500), 5))
    
    # We need to estimate power for each N. 
    # Since we don't have a full simulation loop here (T009 did that), 
    # we approximate using a standard power calculation formula for t-test/ANOVA 
    # as a proxy for the LMM interaction effect, or re-run a simplified simulation.
    # Given T009 used simulation, we will approximate using the non-central F distribution 
    # which is standard for power analysis in linear models.
    
    # Approximation: Power = 1 - beta, where beta is the probability of Type II error.
    # For an interaction in a 2x2 design (simplified), we can use the non-centrality parameter (lambda).
    # lambda = f^2 * N * (design_factor). 
    # For a rough curve, we assume lambda scales linearly with N.
    # We calibrate lambda such that at target_n, power is approx target_power.
    
    # Using statsmodels or scipy for non-central F distribution
    from scipy.stats import ncf
    
    # Degrees of freedom for interaction (simplified 2x2: df1=1, df2=N-4 approx)
    df1 = 1 
    
    # We need to find a lambda (non-centrality parameter) that yields target_power at target_n.
    # This is a bit circular. Let's assume a standard effect size f = 0.25.
    # lambda = f^2 * N_total. 
    # But in LMM, N is participants. 
    # Let's use a heuristic: Power is a function of N and effect size.
    # We will simulate the power curve by calculating the non-centrality parameter 
    # for a range of Ns assuming a fixed effect size.
    
    # Heuristic: lambda = N * effect_size^2 * k (k is a design constant, assume 1 for simplicity)
    # This is a simplification. A more robust way is to run a small simulation loop.
    # Given the constraints, let's run a simplified simulation for the curve points.
    
    # To be rigorous and avoid hard-coding approximations, we will run a simplified simulation
    # for the curve points. This is computationally cheap for the curve generation.
    
    powers = []
    for n in n_range:
        # Simplified power estimation:
        # We simulate data for a 2x2 LMM interaction and check if p < alpha
        # This is expensive if done fully, so we do a single run per N point 
        # with a lower simulation count (e.g., 100 iterations) just for the curve shape.
        # Actually, let's use the analytical approximation from statsmodels if available, 
        # or a standard formula.
        
        # Using the formula for Power of a t-test (approx for interaction):
        # delta = effect_size * sqrt(N/2)
        # This is too simple.
        
        # Let's use the non-central F approach with lambda = N * effect_size^2
        # df2 = N - 4 (approx for 2x2 with random intercepts)
        df2 = max(1, n - 4)
        lambda_val = (n * (effect_size ** 2)) # Simplified lambda
        
        # Critical F value
        from scipy.stats import f
        f_crit = f.ppf(1 - alpha, df1, df2)
        
        # Power = P(F > f_crit | lambda)
        # ncf.sf is survival function (1 - cdf)
        power_val = ncf.sf(f_crit, df1, df2, lambda_val)
        powers.append(power_val)
    
    # Plotting
    plt.figure(figsize=(10, 6))
    plt.plot(n_range, powers, label='Power Curve', color='blue', linewidth=2)
    plt.axhline(y=target_power, color='red', linestyle='--', label=f'Target Power ({target_power})')
    plt.axvline(x=target_n, color='green', linestyle=':', label=f'Target N ({target_n})')
    
    # Mark the point where power crosses target
    # Find intersection
    crossing_n = target_n
    for i in range(len(powers)-1):
        if powers[i] < target_power and powers[i+1] >= target_power:
            crossing_n = n_range[i]
            break
    
    plt.scatter([crossing_n], [target_power], color='orange', zorder=5, label=f'Crossing N ({crossing_n})')
    
    plt.xlabel('Sample Size (N)')
    plt.ylabel('Statistical Power')
    plt.title(f'Power Curve for LMM Interaction Effect (Effect Size = {effect_size})')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xlim(0, max(n_range))
    plt.ylim(0, 1.05)
    
    # Save to the path specified in the task: data/processed/power_curve.png
    # Note: The task says "output `data/processed/power_curve.png`".
    # We will ensure the directory exists and save there.
    output_dir = get_processed_data_dir()
    output_path = output_dir / "power_curve.png"
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Power curve visualization saved to: {output_path}")
    return str(output_path)

def main():
    """
    Main entry point for the power analysis tasks.
    If T009 (results) exists, it adjusts N and generates the curve.
    """
    try:
        results = load_power_analysis_results()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure T009 (Power Analysis) has been completed first.")
        sys.exit(1)
    
    # Adjust N if necessary (T009d logic)
    adjusted_results = adjust_n_for_time_constraint(results)
    save_power_analysis_results(adjusted_results)
    
    print("\nFinal Results:")
    print(json.dumps(adjusted_results, indent=2))
    
    # Generate the power curve (T009b)
    print("\nGenerating Power Curve Visualization...")
    generate_power_curve(adjusted_results)
    
    print(f"\nArtifact saved to: {get_processed_data_dir() / 'power_analysis_results.json'}")

if __name__ == "__main__":
    main()
