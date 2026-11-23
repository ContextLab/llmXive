import os
import sys
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from utils.logging import initialize_logging, info, error, debug
from loops.base_zppo import run_static_zppo_simulation
from loops.cap_zppo import run_cap_zppo_simulation
from config import get_config
from utils.seeds import ensure_seed_set, get_rng

def select_tasks_deterministically(num_tasks: int, seed: int) -> List[str]:
    """Selects a deterministic subset of tasks."""
    # Placeholder for task selection logic
    return [f"task_{i:03d}" for i in range(num_tasks)]

def run_baseline_simulation(seed: int, num_cycles: int = 50, pool_size: int = 10) -> Dict[str, Any]:
    """
    Executes a single baseline (Static ZPPO) simulation cycle.
    
    This function is the internal engine for the baseline simulation.
    It does NOT handle CLI argument parsing or batch orchestration.
    It strictly returns the convergence curve data structure.
    
    Args:
        seed: Random seed for reproducibility.
        num_cycles: Number of buffer cycles to simulate.
        pool_size: Initial candidate pool size.
        
    Returns:
        A dictionary containing the convergence curve data structure:
        {
            "seed": int,
            "mode": "baseline",
            "cycles": List[Dict],  # Per-cycle metrics
            "summary": Dict        # Aggregated metrics (accuracy, aucc, etc.)
        }
    """
    ensure_seed_set(seed)
    debug(f"Starting baseline simulation with seed {seed}.")
    
    try:
        # Run the static ZPPO simulation loop
        # This calls the implementation from T016 via base_zppo.py
        raw_data = run_static_zppo_simulation(seed, num_cycles, pool_size)
        
        if not raw_data:
            error("Baseline simulation returned empty data.")
            return {
                "seed": seed,
                "mode": "baseline",
                "cycles": [],
                "summary": {
                    "accuracy": 0.0,
                    "aucc": 0.0,
                    "final_accuracy": 0.0,
                    "avg_prompt_length": 0.0
                }
            }
        
        # Calculate metrics from the raw data
        # We assume raw_data is a list of dicts with 'correct', 'prompt_length', etc.
        correct_count = sum(1 for r in raw_data if r.get('correct', False))
        total_count = len(raw_data)
        final_accuracy = correct_count / total_count if total_count > 0 else 0.0
        
        # Calculate AUCC (Area Under the Convergence Curve)
        # Assuming 'accuracy' or 'correct' is tracked per cycle in raw_data
        # If raw_data contains per-cycle accuracy, we integrate that.
        # For this implementation, we assume raw_data is a list of cycle results.
        # We calculate AUCC using trapezoidal rule on accuracy vs cycle index.
        accuracies = []
        for r in raw_data:
            acc = 1.0 if r.get('correct', False) else 0.0
            accuracies.append(acc)
        
        aucc = 0.0
        if len(accuracies) > 1:
            # Trapezoidal rule
            for i in range(len(accuracies) - 1):
                avg_acc = (accuracies[i] + accuracies[i+1]) / 2.0
                aucc += avg_acc
        
        avg_prompt_length = sum(r.get('prompt_length', 0) for r in raw_data) / total_count if total_count > 0 else 0.0
        
        summary = {
            "accuracy": final_accuracy,
            "aucc": aucc,
            "final_accuracy": final_accuracy,
            "avg_prompt_length": avg_prompt_length
        }
        
        return {
            "seed": seed,
            "mode": "baseline",
            "cycles": raw_data,
            "summary": summary
        }
        
    except Exception as e:
        error(f"Error during baseline simulation: {e}")
        raise

def run_cap_simulation(seed: int, num_cycles: int = 50, pool_size: int = 10) -> Dict[str, Any]:
    """
    Executes a single CAP (Confidence-Adaptive Pruning) simulation cycle.
    
    This function is the internal engine for the CAP simulation.
    It does NOT handle CLI argument parsing or batch orchestration.
    It strictly returns the convergence curve data structure.
    
    Args:
        seed: Random seed for reproducibility.
        num_cycles: Number of buffer cycles to simulate.
        pool_size: Initial candidate pool size.
        
    Returns:
        A dictionary containing the convergence curve data structure:
        {
            "seed": int,
            "mode": "cap",
            "cycles": List[Dict],
            "summary": Dict
        }
    """
    ensure_seed_set(seed)
    debug(f"Starting CAP simulation with seed {seed}.")
    
    try:
        raw_data = run_cap_zppo_simulation(seed, num_cycles, pool_size)
        
        if not raw_data:
            error("CAP simulation returned empty data.")
            return {
                "seed": seed,
                "mode": "cap",
                "cycles": [],
                "summary": {
                    "accuracy": 0.0,
                    "aucc": 0.0,
                    "final_accuracy": 0.0,
                    "avg_prompt_length": 0.0
                }
            }
        
        correct_count = sum(1 for r in raw_data if r.get('correct', False))
        total_count = len(raw_data)
        final_accuracy = correct_count / total_count if total_count > 0 else 0.0
        
        accuracies = []
        for r in raw_data:
            acc = 1.0 if r.get('correct', False) else 0.0
            accuracies.append(acc)
        
        aucc = 0.0
        if len(accuracies) > 1:
            for i in range(len(accuracies) - 1):
                avg_acc = (accuracies[i] + accuracies[i+1]) / 2.0
                aucc += avg_acc
        
        avg_prompt_length = sum(r.get('prompt_length', 0) for r in raw_data) / total_count if total_count > 0 else 0.0
        
        summary = {
            "accuracy": final_accuracy,
            "aucc": aucc,
            "final_accuracy": final_accuracy,
            "avg_prompt_length": avg_prompt_length
        }
        
        return {
            "seed": seed,
            "mode": "cap",
            "cycles": raw_data,
            "summary": summary
        }
        
    except Exception as e:
        error(f"Error during CAP simulation: {e}")
        raise

def run_single_run(mode: str, seed: int, num_cycles: int = 50, pool_size: int = 10) -> Dict[str, Any]:
    """Runs a single simulation run (wrapper for T031)."""
    info(f"Running {mode} simulation with seed {seed}.")
    if mode == "baseline":
        data = run_baseline_simulation(seed, num_cycles, pool_size)
    elif mode == "cap":
        data = run_cap_simulation(seed, num_cycles, pool_size)
    else:
        raise ValueError(f"Unknown mode: {mode}")
    return data

def main():
    initialize_logging()
    config = get_config()
    
    # Example: Run a single baseline
    result = run_single_run("baseline", config.seed)
    info(f"Result: {result['summary']['accuracy']}")

if __name__ == "__main__":
    main()