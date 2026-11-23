import json
import logging
import os
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np

from pathlib import Path

# Project root handling (relative to code/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"

logger = logging.getLogger(__name__)

@dataclass
class CostMetric:
    """Dataclass representing a single cost metric entry."""
    variant: str
    baseline_mae: float
    variant_mae: float
    relative_mae_increase: float
    baseline_time_sec: float
    variant_time_sec: float
    relative_time_increase: float
    metabolic_cost: float  # Time / MAE (lower is better, higher means more 'cost' per unit accuracy)
    metabolic_cost_ratio: float  # Variant cost / Baseline cost

def load_json_file(path: Path) -> Dict[str, Any]:
    """Load a JSON file safely."""
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def load_ablation_results() -> List[Dict[str, Any]]:
    """
    Load ablation results from data/results/ablation_*.json.
    We expect files named like: data/results/ablation_{variant}.json
    """
    results = []
    ablation_files = list(DATA_RESULTS_DIR.glob("ablation_*.json"))
    
    if not ablation_files:
        # Fallback to generic ablation results if specific files aren't found
        generic_file = DATA_RESULTS_DIR / "ablation_results.json"
        if generic_file.exists():
            ablation_files = [generic_file]
        else:
            raise FileNotFoundError("No ablation result files found in data/results/")

    for f in ablation_files:
        try:
            data = load_json_file(f)
            # Handle if the JSON is a list of results or a single result dict
            if isinstance(data, list):
                results.extend(data)
            else:
                results.append(data)
        except Exception as e:
            logger.warning(f"Failed to load {f}: {e}")

    if not results:
        raise ValueError("No valid ablation results found.")
    return results

def load_scaling_metrics() -> pd.DataFrame:
    """
    Load scaling law metrics from data/results/scaling_law.csv.
    Returns a DataFrame with columns: columns, params, mae, time_sec
    """
    scaling_file = DATA_RESULTS_DIR / "scaling_law.csv"
    if not scaling_file.exists():
        raise FileNotFoundError(f"Scaling law CSV not found: {scaling_file}")
    
    df = pd.read_csv(scaling_file)
    required_cols = ['columns', 'params', 'mae', 'time_sec']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Scaling CSV missing required columns: {missing}")
    
    return df

def load_baseline_metrics() -> Dict[str, float]:
    """
    Load baseline metrics. We look for a baseline run result or generalization report.
    Typically data/results/baseline_run.json or data/results/generalization_report.md (parsed).
    For this implementation, we assume a JSON file 'baseline_metrics.json' or 'baseline_run.json'
    exists with 'mae' and 'time_sec'.
    """
    # Try specific baseline run file first
    baseline_file = DATA_RESULTS_DIR / "baseline_run.json"
    if baseline_file.exists():
        data = load_json_file(baseline_file)
        return {
            'mae': float(data.get('mae', data.get('final_mae', 0))),
            'time_sec': float(data.get('time_sec', data.get('total_time', 0)))
        }
    
    # Fallback: try to extract from generalization report if it's a JSON
    gen_report = DATA_RESULTS_DIR / "generalization_report.json"
    if gen_report.exists():
         data = load_json_file(gen_report)
         return {
            'mae': float(data.get('mae', 0)),
            'time_sec': float(data.get('time_sec', 0))
         }

    raise FileNotFoundError("Baseline metrics file (baseline_run.json) not found.")

def compute_cost_metrics() -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Compute the cost curve metrics by comparing ablation variants against the baseline.
    
    Returns:
        Tuple of (list of CostMetric dicts, summary stats dict)
    """
    logger.info("Computing cost metrics...")
    
    # 1. Load Baseline
    try:
        baseline = load_baseline_metrics()
    except FileNotFoundError as e:
        logger.error(f"Cannot compute cost metrics: {e}")
        # In a real run, we might return empty or fail. Here we raise to fail loudly.
        raise e

    baseline_mae = baseline['mae']
    baseline_time = baseline['time_sec']

    if baseline_mae == 0:
        baseline_mae = 1e-9 # Avoid division by zero

    # 2. Load Ablation Results
    ablation_results = load_ablation_results()

    # 3. Load Scaling Metrics (for context, though cost curve is primarily ablation vs baseline)
    # We might use the scaling data to normalize or add a 'size' dimension later, 
    # but the core task is ablation cost.
    try:
        scaling_df = load_scaling_metrics()
        # We can compute an average scaling metric if needed, but for now we just verify it exists.
        logger.info(f"Loaded scaling data with {len(scaling_df)} entries.")
    except FileNotFoundError:
        logger.warning("Scaling law CSV not found. Proceeding with ablation-only cost analysis.")
        scaling_df = None

    cost_metrics = []

    for result in ablation_results:
        variant_name = result.get('variant', 'unknown')
        variant_mae = float(result.get('mae', result.get('final_mae', 0)))
        variant_time = float(result.get('time_sec', result.get('total_time', 0)))

        if variant_mae == 0:
            variant_mae = 1e-9

        # Calculate relative increases
        rel_mae_inc = (variant_mae - baseline_mae) / baseline_mae
        rel_time_inc = (variant_time - baseline_time) / baseline_time if baseline_time > 0 else 0.0

        # Metabolic Cost = Time / MAE
        # Higher cost means more time spent per unit of error (or rather, per unit of performance? 
        # The spec says "Metabolic Cost = Training Time (sec) / MAE". 
        # If MAE is error, lower MAE is better. So Time/MAE: High Time + Low MAE = High Cost? 
        # Or High Time + High MAE = Low Cost?
        # Let's stick strictly to the formula: Cost = Time / MAE.
        # If we improve accuracy (lower MAE) but take much longer, Cost goes up.
        # If we are faster but much worse (higher MAE), Cost goes down.
        # This metric quantifies the "price" of accuracy in time.
        
        metabolic_cost = variant_time / variant_mae
        baseline_metabolic_cost = baseline_time / baseline_mae

        if baseline_metabolic_cost == 0:
            baseline_metabolic_cost = 1e-9

        metabolic_cost_ratio = metabolic_cost / baseline_metabolic_cost

        metric = CostMetric(
            variant=variant_name,
            baseline_mae=baseline_mae,
            variant_mae=variant_mae,
            relative_mae_increase=rel_mae_inc,
            baseline_time_sec=baseline_time,
            variant_time_sec=variant_time,
            relative_time_increase=rel_time_inc,
            metabolic_cost=metabolic_cost,
            metabolic_cost_ratio=metabolic_cost_ratio
        )
        cost_metrics.append(asdict(metric))

    # Sort by metabolic cost ratio descending (most expensive first)
    cost_metrics.sort(key=lambda x: x['metabolic_cost_ratio'], reverse=True)

    summary = {
        "baseline_mae": baseline_mae,
        "baseline_time_sec": baseline_time,
        "num_variants": len(cost_metrics),
        "scaling_law_available": scaling_df is not None,
        "metrics": cost_metrics
    }

    return cost_metrics, summary

def main():
    """Entry point for the cost analyzer script."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    output_path = DATA_RESULTS_DIR / "cost_metrics.json"
    
    try:
        metrics, summary = compute_cost_metrics()
        
        # Write the full summary including the list of metrics
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Cost metrics written to {output_path}")
        
        # Also write a CSV for easier plotting if needed (optional but helpful)
        csv_path = DATA_RESULTS_DIR / "cost_curve_data.csv"
        df_metrics = pd.DataFrame(metrics)
        df_metrics.to_csv(csv_path, index=False)
        logger.info(f"Cost curve data CSV written to {csv_path}")
        
    except Exception as e:
        logger.error(f"Failed to compute cost metrics: {e}")
        raise

if __name__ == "__main__":
    main()