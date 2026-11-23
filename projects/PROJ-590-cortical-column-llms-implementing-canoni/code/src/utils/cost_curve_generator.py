"""
Cost Curve Generator for Cortical Column LLMs.

This module computes the "Cost of Biological Plausibility" curve by comparing
ablated variants (recurrence, inhibition) against the full model and baseline.
It calculates relative MAE increase, training time increase, and a "Metabolic Cost"
metric defined as Training Time (sec) / MAE.

Output: data/results/cost_curve_data.csv
"""
import json
import os
import logging
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd
from pathlib import Path

# Project root relative to code/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"
DATA_LOGS_DIR = PROJECT_ROOT / "data" / "logs"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_json_file(filepath: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    if not filepath.exists():
        raise FileNotFoundError(f"Required input file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)


def load_baseline_metrics() -> Dict[str, float]:
    """
    Load baseline metrics from the training log or results file.
    Expected source: data/logs/training_log.json or data/results/baseline_run.json
    """
    # Try the most likely location based on T012b_impl and T011a_run
    baseline_log_path = DATA_LOGS_DIR / "training_log.json"
    baseline_run_path = DATA_RESULTS_DIR / "baseline_run.json"

    if baseline_log_path.exists():
        data = load_json_file(baseline_log_path)
        # Handle if data is a list of steps or a single dict
        if isinstance(data, list):
            # Take the last step (final metrics)
            final_step = data[-1]
        else:
            final_step = data
        
        # Extract MAE and Time. Keys might vary slightly, normalize them.
        mae = final_step.get("mae") or final_step.get("mae_value") or final_step.get("test_mae")
        time_sec = final_step.get("time_sec") or final_step.get("total_time") or final_step.get("training_time")
        
        if mae is None or time_sec is None:
            # Fallback: try to find them in a 'metrics' sub-dict
            if "metrics" in final_step:
                mae = final_step["metrics"].get("mae")
                time_sec = final_step["metrics"].get("time_sec")

        if mae is None or time_sec is None:
            raise ValueError(f"Could not find 'mae' and 'time_sec' in {baseline_log_path}. Found keys: {final_step.keys()}")
        
        return {"mae": float(mae), "time_sec": float(time_sec)}

    elif baseline_run_path.exists():
        data = load_json_file(baseline_run_path)
        mae = data.get("mae") or data.get("test_mae")
        time_sec = data.get("time_sec") or data.get("total_time")
        if mae is None or time_sec is None:
            raise ValueError(f"Could not find 'mae' and 'time_sec' in {baseline_run_path}")
        return {"mae": float(mae), "time_sec": float(time_sec)}
    else:
        raise FileNotFoundError(f"Neither {baseline_log_path} nor {baseline_run_path} found. Run baseline training first.")


def load_microcircuit_metrics() -> Dict[str, float]:
    """
    Load full microcircuit model metrics.
    Expected source: data/results/microcircuit_run.json
    """
    microcircuit_path = DATA_RESULTS_DIR / "microcircuit_run.json"
    if not microcircuit_path.exists():
        raise FileNotFoundError(f"Microcircuit run results not found: {microcircuit_path}. Run T048/T071c_exec first.")
    
    data = load_json_file(microcircuit_path)
    mae = data.get("mae") or data.get("test_mae")
    time_sec = data.get("time_sec") or data.get("total_time")
    
    if mae is None or time_sec is None:
        raise ValueError(f"Could not find 'mae' and 'time_sec' in {microcircuit_path}")
    
    return {"mae": float(mae), "time_sec": float(time_sec)}


def load_ablation_results(variant_name: str) -> Dict[str, float]:
    """
    Load ablation result for a specific variant.
    Expected source: data/results/ablation_{variant_name}.json
    """
    ablation_path = DATA_RESULTS_DIR / f"ablation_{variant_name}.json"
    if not ablation_path.exists():
        raise FileNotFoundError(f"Ablation result not found for variant '{variant_name}': {ablation_path}. Run T025b first.")
    
    data = load_json_file(ablation_path)
    # Handle if data is a list of runs or a single result
    if isinstance(data, list):
        # Take the first or last result depending on convention
        result = data[-1] if data else {}
    else:
        result = data
    
    mae = result.get("mae") or result.get("test_mae")
    time_sec = result.get("time_sec") or result.get("total_time")
    
    if mae is None or time_sec is None:
        raise ValueError(f"Could not find 'mae' and 'time_sec' in {ablation_path}")
    
    return {"mae": float(mae), "time_sec": float(time_sec)}


def calculate_relative_increase(base_value: float, variant_value: float) -> float:
    """
    Calculate the relative increase: (variant - base) / base.
    Returns 0.0 if base is 0 to avoid division by zero (though MAE should not be 0).
    """
    if base_value == 0:
        return 0.0
    return (variant_value - base_value) / base_value


def calculate_metabolic_cost(time_sec: float, mae: float) -> float:
    """
    Calculate 'Metabolic Cost' as Training Time (sec) / MAE.
    This quantifies the trade-off: higher cost means more time per unit of error reduction.
    """
    if mae == 0:
        return float('inf')
    return time_sec / mae


def generate_cost_curve_data() -> pd.DataFrame:
    """
    Compute the cost curve data by comparing ablated variants against baseline and full model.
    
    Variants to analyze:
    - baseline
    - microcircuit_full
    - ablation_recurrence
    - ablation_inhibition
    
    Columns:
    - variant: str
    - mae: float
    - time_sec: float
    - relative_mae_increase: float (vs baseline)
    - relative_time_increase: float (vs baseline)
    - metabolic_cost: float (time_sec / mae)
    - metabolic_cost_vs_baseline: float (ratio of metabolic costs)
    
    Output: data/results/cost_curve_data.csv
    """
    logger.info("Starting cost curve data generation...")
    
    # Ensure output directory exists
    DATA_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load baseline (reference point)
        baseline = load_baseline_metrics()
        logger.info(f"Loaded baseline: MAE={baseline['mae']:.4f}, Time={baseline['time_sec']:.2f}s")
        
        # Load full microcircuit
        microcircuit = load_microcircuit_metrics()
        logger.info(f"Loaded microcircuit: MAE={microcircuit['mae']:.4f}, Time={microcircuit['time_sec']:.2f}s")
        
        # Define variants to analyze
        variants = [
            ("baseline", baseline),
            ("microcircuit_full", microcircuit),
            ("ablation_recurrence", load_ablation_results("recurrence")),
            ("ablation_inhibition", load_ablation_results("inhibition")),
        ]
        
        results = []
        baseline_mae = baseline["mae"]
        baseline_time = baseline["time_sec"]
        baseline_metabolic_cost = calculate_metabolic_cost(baseline_time, baseline_mae)
        
        for name, metrics in variants:
            mae = metrics["mae"]
            time_sec = metrics["time_sec"]
            
            rel_mae_inc = calculate_relative_increase(baseline_mae, mae)
            rel_time_inc = calculate_relative_increase(baseline_time, time_sec)
            metabolic_cost = calculate_metabolic_cost(time_sec, mae)
            metabolic_cost_ratio = metabolic_cost / baseline_metabolic_cost if baseline_metabolic_cost != 0 else 0.0
            
            results.append({
                "variant": name,
                "mae": mae,
                "time_sec": time_sec,
                "relative_mae_increase": rel_mae_inc,
                "relative_time_increase": rel_time_inc,
                "metabolic_cost": metabolic_cost,
                "metabolic_cost_vs_baseline": metabolic_cost_ratio
            })
            
        df = pd.DataFrame(results)
        output_path = DATA_RESULTS_DIR / "cost_curve_data.csv"
        df.to_csv(output_path, index=False)
        
        logger.info(f"Successfully wrote cost curve data to {output_path}")
        return df
        
    except FileNotFoundError as e:
        logger.error(f"Missing required input data: {e}")
        logger.error("Ensure T011a_run (baseline), T048 (microcircuit), and T025b (ablation) have completed successfully.")
        raise
    except Exception as e:
        logger.error(f"Error generating cost curve data: {e}")
        raise


def main():
    """Entry point for the cost curve generator script."""
    try:
        df = generate_cost_curve_data()
        print("\nCost Curve Data Summary:")
        print(df.to_string(index=False))
        print(f"\nSaved to: {DATA_RESULTS_DIR / 'cost_curve_data.csv'}")
    except Exception as e:
        print(f"FAILED: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import sys
    main()