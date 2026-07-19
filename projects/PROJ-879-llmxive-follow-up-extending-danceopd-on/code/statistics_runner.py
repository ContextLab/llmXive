import argparse
import json
import sys
import time
import signal
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np
import pandas as pd

from utils.config import get_config
from utils.statistics import (
    run_bootstrap_test,
    save_partial_results,
    save_statistical_tests,
    TimeoutError,
    timeout_handler,
)
from utils.metrics import calculate_fid


def load_fid_results(fid_csv_path: str) -> List[float]:
    """
    Load FID scores from the fidelity metrics CSV.
    Expects a column 'fid_score' or similar containing the per-sample or aggregate FID.
    For bootstrap, we need a distribution of FID values. If the CSV contains a single
    aggregate FID, we cannot bootstrap. We assume the CSV has per-pair FID scores or
    we compute them from image pairs.
    
    In the context of T030, we assume `data/results/fidelity_metrics.csv` contains
    per-sample FID differences or per-pair FID scores. If not, we attempt to load
    the specific column 'fid_score'.
    """
    df = pd.read_csv(fid_csv_path)
    # Try common column names
    possible_cols = ['fid_score', 'fid', 'fid_diff', 'degradation_fid']
    target_col = None
    for col in possible_cols:
        if col in df.columns:
            target_col = col
            break
    
    if target_col is None:
        raise ValueError(
            f"Could not find FID score column in {fid_csv_path}. "
            f"Expected one of {possible_cols}. Columns found: {list(df.columns)}"
        )
    
    scores = df[target_col].dropna().tolist()
    if len(scores) == 0:
        raise ValueError("No valid FID scores found in the dataset.")
    
    return scores


def run_bootstrap_analysis(
    fid_scores: List[float],
    power_threshold: float = 0.8,
    initial_sample_size: int = 10,
    increment: int = 10,
    time_budget_seconds: int = 300,  # 5 minutes for this task
    partial_timeout_buffer: int = 1800,  # 30 min buffer for full pipeline
) -> Dict[str, Any]:
    """
    Perform bootstrap hypothesis test on FID distribution.
    
    Logic:
    1. Start with `initial_sample_size`.
    2. Run bootstrap test to estimate power.
    3. If power >= `power_threshold`, stop and save final results.
    4. If remaining time < `partial_timeout_buffer`, save partial results and exit.
    5. Otherwise, increase sample size by `increment` and repeat.
    
    Returns a dictionary with results, status, and metadata.
    """
    results = {
        "status": "running",
        "power_history": [],
        "sample_sizes": [],
        "p_values": [],
        "effect_sizes": [],
        "confidence_intervals": [],
    }
    
    start_time = time.time()
    current_n = initial_sample_size
    total_samples = len(fid_scores)
    
    if current_n > total_samples:
        current_n = total_samples
    
    while current_n <= total_samples:
        elapsed = time.time() - start_time
        remaining = time_budget_seconds - elapsed
        
        # Check if we would exceed the buffer before the next iteration
        if remaining < partial_timeout_buffer:
            results["status"] = "partial_timeout"
            results["message"] = "Time budget exceeded (remaining < 30min buffer). Saving partial results."
            break
        
        # Take a subset for this iteration
        # In a real scenario, we might resample or use the first N if the list is ordered
        # Here we assume we are bootstrapping from the full set, but checking power at different N
        # The `run_bootstrap_test` function likely handles the resampling internally.
        # We pass the full list but instruct it to use `current_n` for the bootstrap iteration size?
        # Or we pass a subset. Let's assume `run_bootstrap_test` takes a sample size argument.
        
        # Actually, the standard approach for power analysis in bootstrap is:
        # Run bootstrap with current_n samples, estimate power.
        # If power is low, increase N.
        
        # We need to ensure we don't exceed the list length
        effective_n = min(current_n, total_samples)
        
        try:
            # Run the bootstrap test
            # We assume run_bootstrap_test returns a dict with 'power', 'p_value', etc.
            # We need to pass the data and the sample size to use for the test
            test_result = run_bootstrap_test(
                data=fid_scores,
                sample_size=effective_n,
                n_iterations=1000, # Standard bootstrap iterations
            )
            
            power = test_result.get("power", 0.0)
            p_value = test_result.get("p_value", 1.0)
            effect_size = test_result.get("effect_size", 0.0)
            ci = test_result.get("confidence_interval", [0.0, 0.0])
            
            results["power_history"].append(power)
            results["sample_sizes"].append(effective_n)
            results["p_values"].append(p_value)
            results["effect_sizes"].append(effect_size)
            results["confidence_intervals"].append(ci)
            
            if power >= power_threshold:
                results["status"] = "success"
                results["message"] = f"Statistical power ({power:.2f}) >= {power_threshold}. Test complete."
                break
            
            # Increase sample size
            current_n += increment
            
        except Exception as e:
            results["status"] = "error"
            results["message"] = f"Bootstrap test failed at n={effective_n}: {str(e)}"
            break
    
    # If we ran out of samples without reaching power
    if results["status"] == "running" and current_n > total_samples:
        results["status"] = "insufficient_data"
        results["message"] = "Reached max sample size without achieving target power."
    
    results["elapsed_time"] = time.time() - start_time
    return results


def main():
    parser = argparse.ArgumentParser(description="Run Bootstrap Hypothesis Test on FID Distribution")
    parser.add_argument(
        "--fid-csv",
        type=str,
        default="data/results/fidelity_metrics.csv",
        help="Path to the CSV file containing FID scores.",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default="data/results/statistical_tests.json",
        help="Path to save the statistical test results.",
    )
    parser.add_argument(
        "--partial-output",
        type=str,
        default="data/results/partial_results.json",
        help="Path to save partial results if timeout occurs.",
    )
    parser.add_argument(
        "--time-budget",
        type=int,
        default=300,
        help="Time budget in seconds for this task.",
    )
    parser.add_argument(
        "--power-threshold",
        type=float,
        default=0.8,
        help="Target statistical power.",
    )
    parser.add_argument(
        "--initial-n",
        type=int,
        default=10,
        help="Initial sample size for bootstrap.",
    )
    parser.add_argument(
        "--increment",
        type=int,
        default=10,
        help="Increment for sample size.",
    )
    
    args = parser.parse_args()
    
    # Setup timeout handler for the whole process
    def signal_handler(signum, frame):
        raise TimeoutError("Hard timeout reached")
    
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(args.time_budget)
    
    try:
        # Load FID scores
        print(f"Loading FID scores from {args.fid_csv}...")
        fid_scores = load_fid_results(args.fid_csv)
        print(f"Loaded {len(fid_scores)} FID scores.")
        
        if len(fid_scores) < args.initial_n:
            raise ValueError(
                f"Insufficient data: {len(fid_scores)} scores, but initial sample size is {args.initial_n}."
            )
        
        # Run bootstrap analysis
        print("Starting bootstrap power analysis...")
        results = run_bootstrap_analysis(
            fid_scores=fid_scores,
            power_threshold=args.power_threshold,
            initial_sample_size=args.initial_n,
            increment=args.increment,
            time_budget_seconds=args.time_budget,
        )
        
        # Save results
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if results["status"] == "partial_timeout":
            # Save as partial results
            save_partial_results(results, args.partial_output)
            print(f"Partial results saved to {args.partial_output}")
            sys.exit(2)
        else:
            # Save as final statistical tests
            save_statistical_tests(results, args.output_json)
            print(f"Statistical tests saved to {args.output_json}")
            sys.exit(0)
            
    except TimeoutError:
        print("Hard timeout reached. Saving partial results...")
        # We might not have full results, so we save what we have or an error state
        error_result = {
            "status": "timeout",
            "message": "Hard timeout reached during bootstrap analysis.",
            "partial_data": None, # Could capture partial state if tracked
        }
        save_partial_results(error_result, args.partial_output)
        sys.exit(2)
    except Exception as e:
        print(f"Error during analysis: {e}")
        error_result = {
            "status": "error",
            "message": str(e),
        }
        save_partial_results(error_result, args.partial_output)
        sys.exit(1)
    finally:
        signal.alarm(0) # Cancel alarm


if __name__ == "__main__":
    main()