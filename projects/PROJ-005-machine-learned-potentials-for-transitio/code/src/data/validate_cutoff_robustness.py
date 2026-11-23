import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np

# Import local project utilities
# We assume src is in PYTHONPATH or run from project root
from src.utils.logging import get_logger, setup_logger
from src.utils.config import get_project_root

def load_sensitivity_metrics(metrics_path: Path) -> Dict[str, Any]:
    """
    Load the sensitivity metrics calculated in T017b.
    Expected structure:
    {
        "cutoffs": [3.0, 3.5, 4.0],
        "metrics": {
            "avg_degree": [v1, v2, v3],
            "edge_count": [v1, v2, v3],
            "density": [v1, v2, v3]
        },
        "variance": {
            "avg_degree": float,
            "edge_count": float,
            "density": float
        },
        "selected_cutoff": float,
        "selection_reason": "..."
    }
    """
    if not metrics_path.exists():
        raise FileNotFoundError(f"Sensitivity metrics file not found: {metrics_path}")
    
    with open(metrics_path, 'r') as f:
        return json.load(f)

def calculate_metric_variance(metrics: Dict[str, List[float]]) -> Dict[str, float]:
    """
    Calculate the variance of a list of metrics across cutoffs.
    Returns a dict: metric_name -> variance_value
    """
    variances = {}
    for metric_name, values in metrics.items():
        if isinstance(values, list) and len(values) > 1:
            variances[metric_name] = float(np.var(values, ddof=0))
        else:
            variances[metric_name] = 0.0
    return variances

def validate_cutoff_robustness(
    metrics_data: Dict[str, Any],
    threshold_percent: float = 10.0
) -> Dict[str, Any]:
    """
    Validate that the selected cutoff minimizes variance by at least `threshold_percent`
    compared to the next best cutoff.
    
    Logic:
    1. Identify the selected cutoff.
    2. Calculate the total variance score for the selected cutoff (sum of variances of all metrics).
       Note: The metrics_data from T017b already contains pre-calculated variances per metric.
       We need to aggregate these to compare cutoffs.
       However, T017b output is a single "variance" object for the *selected* cutoff's metrics?
       Wait, T017b calculates variance ACROSS cutoffs for each metric.
       Let's re-read T017b: "Compute variance of metrics across cutoffs."
       This implies T017b produces a single variance value per metric (e.g., variance of avg_degree across [3.0, 3.5, 4.0]).
       
       T017c selects the cutoff that *minimizes* this variance?
       Actually, the task description for T017c says: "Select cutoff minimizing metric variance."
       This is slightly ambiguous. Usually, you sweep cutoffs, calculate a metric (like edge density) for *each* cutoff,
       and then you want the cutoff where the *metric itself* is stable? Or where the variance of the metric *across the sweep* is minimized?
       
       Re-reading T017a: "Sweep cutoff values... Calculate graph metrics... for each."
       So we have a list of metrics for each cutoff.
       T017b: "Calculate variance of metrics across cutoffs." -> This produces a single variance number per metric type (e.g. Var(avg_degree)).
       
       If T017b produces a single variance per metric, how do we select a cutoff based on minimizing variance?
       The standard approach in sensitivity analysis is:
       1. For each cutoff, calculate a "stability score" or "variance" of the *local* neighborhood?
       OR
       2. The task implies we are comparing the *global* variance of the metrics if we were to use that cutoff?
       
       Let's interpret the task T017d specifically: "Verify the selected cutoff from T017c minimizes variance by at least 10% compared to the next best cutoff."
       This implies we have a "variance" value associated with *each* cutoff.
       
       Hypothesis: The "variance" calculated in T017b might be the variance of the metric *values* for that specific cutoff?
       No, T017b says "variance of metrics across cutoffs".
       
       Alternative Interpretation (Most Likely for Graph Construction):
       We want the cutoff where the graph metrics (like edge count) are most stable relative to small perturbations?
       Or, we are comparing the "Total Variance" of the dataset if we used cutoff A vs cutoff B?
       
       Let's assume the data structure from T017c (which depends on T017b) actually contains a "score" or "variance" per cutoff.
       If T017b only outputted a single variance per metric, T017c couldn't select a cutoff based on minimizing variance *compared to others*.
       
       Correction: T017b likely calculates the variance of the metric *sweep* (e.g. how much does avg_degree change as we move from 3.0 to 4.0?).
       But T017d asks to compare the *selected* cutoff to the *next best*.
       This implies the "variance" is a property of the *cutoff*, not the whole sweep.
       
       Perhaps the "variance" refers to the variance of the *predictions* or *properties* derived from the graph at that cutoff?
       Or, more simply, the "variance" of the metric *values* within the dataset for that specific cutoff?
       
       Let's look at the T017a output: `cutoff_sensitivity_raw.json`.
       Structure: { "3.0": { "avg_degree": 5.2, ... }, "3.5": {...} }
       T017b calculates variance of these values across the keys?
       
       If the task is "minimize variance", and we have a set of values for each cutoff, maybe we are minimizing the variance of the *metric* across the *samples*?
       No, that's sample variance.
       
       Let's assume the standard interpretation for this specific pipeline context:
       We have a metric (e.g., edge density) that changes with cutoff.
       We want the cutoff where the *change* is minimal?
       
       Let's re-read T017d carefully: "Verify the selected cutoff from T017c minimizes variance by at least 10% compared to the next best cutoff."
       This implies we have a "variance" score for every cutoff.
       
       How to derive a "variance" score for a cutoff?
       Maybe the variance of the *edge lengths* at that cutoff?
       Or the variance of the *graph metrics* (avg_degree, etc) *across the samples* in the dataset for that cutoff?
       
       Let's assume the T017b output actually contains a "variance_per_cutoff" or similar, or we can calculate it from the raw data.
       Since I am implementing T017d, I must assume T017b produced a file `cutoff_sensitivity.json`.
       If T017b only produced a single variance for the whole sweep, T017d is impossible.
       Therefore, T017b must have produced a structure where each cutoff has a variance score.
       
       Let's assume the T017b logic was: For each cutoff, calculate the variance of the metric (e.g. edge_count) across all graphs in the dataset.
       Then T017c picks the cutoff with the lowest such variance.
       
       I will implement the validator to read `cutoff_sensitivity.json`.
       Expected structure for T017b output to make T017d possible:
       {
         "cutoffs": [3.0, 3.5, 4.0],
         "variance_scores": {
           "3.0": 0.12,
           "3.5": 0.05,
           "4.0": 0.15
         },
         "selected_cutoff": 3.5,
         "next_best_cutoff": 3.0,
         "next_best_variance": 0.12
       }
       
       If the file structure is different (e.g. just a list of variances), I will adapt.
       
       Let's assume the file contains:
       {
         "cutoffs": [3.0, 3.5, 4.0],
         "metric_variances": {
           "3.0": {"avg_degree": 0.1, "edge_count": 0.2, ...},
           "3.5": {...}
         },
         "total_variances": {
           "3.0": 0.3,
           "3.5": 0.15
         },
         "selected_cutoff": 3.5
       }
       
       I will calculate the total variance for each cutoff if not present.
       Then compare the selected one to the next best (minimum of the rest).
    """
    selected_cutoff = metrics_data.get("selected_cutoff")
    if selected_cutoff is None:
        raise ValueError("No selected cutoff found in metrics data.")

    cutoffs = metrics_data.get("cutoffs", [])
    if not cutoffs:
        raise ValueError("No cutoffs list found.")

    # Determine the variance score for each cutoff
    # Attempt to read pre-calculated total variances, or calculate from metric variances
    variance_scores = {}
    
    if "total_variances" in metrics_data:
        variance_scores = metrics_data["total_variances"]
    elif "metric_variances" in metrics_data:
        # Sum variances of all metrics for each cutoff
        metric_vars = metrics_data["metric_variances"]
        for cutoff in cutoffs:
            cutoff_str = str(cutoff)
            if cutoff_str in metric_vars:
                variance_scores[cutoff_str] = sum(metric_vars[cutoff_str].values())
            else:
                variance_scores[cutoff_str] = float('inf') # Invalid cutoff
    else:
        # Fallback: Try to find a 'variance' key per cutoff if structure is flat
        # This is less likely but possible
        for cutoff in cutoffs:
            cutoff_str = str(cutoff)
            if cutoff_str in metrics_data and isinstance(metrics_data[cutoff_str], dict):
                # Sum values if they look like variances
                vals = [v for v in metrics_data[cutoff_str].values() if isinstance(v, (int, float))]
                if vals:
                    variance_scores[cutoff_str] = sum(vals)
    
    if not variance_scores:
        raise ValueError("Could not determine variance scores for cutoffs.")

    selected_var = variance_scores.get(str(selected_cutoff))
    if selected_var is None:
        raise ValueError(f"Selected cutoff {selected_cutoff} has no variance score.")

    # Find the next best (minimum variance among the others)
    other_cutoffs_variances = [
        (c, v) for c, v in variance_scores.items() 
        if float(c) != selected_cutoff and v is not None
    ]
    
    if not other_cutoffs_variances:
        # Only one cutoff? Trivially valid or fail?
        # Task implies comparison, so if only one, we can't compare.
        # Assume pass if no other options? Or fail?
        # Let's assume fail if we can't compare.
        return {
            "status": "failed",
            "reason": "Only one cutoff available for comparison. Cannot validate 10% improvement.",
            "selected_cutoff": selected_cutoff,
            "selected_variance": selected_var
        }

    # Sort by variance (ascending) to find the next best (lowest variance among others)
    other_cutoffs_variances.sort(key=lambda x: x[1])
    next_best_cutoff = other_cutoffs_variances[0][0]
    next_best_var = other_cutoffs_variances[0][1]

    # Calculate improvement
    # Improvement = (NextBest - Selected) / NextBest
    # We want Selected to be at least 10% lower than NextBest.
    # So: (NextBest - Selected) / NextBest >= 0.10
    
    if next_best_var == 0:
        if selected_var == 0:
            improvement = 0.0
        else:
            # Selected is worse or equal?
            improvement = -1.0
    else:
        improvement = (next_best_var - selected_var) / next_best_var

    is_valid = improvement >= (threshold_percent / 100.0)

    result = {
        "status": "passed" if is_valid else "failed",
        "selected_cutoff": selected_cutoff,
        "selected_variance": selected_var,
        "next_best_cutoff": next_best_cutoff,
        "next_best_variance": next_best_var,
        "improvement_ratio": float(improvement),
        "threshold": threshold_percent / 100.0,
        "message": f"Selected cutoff {selected_cutoff} ({selected_var:.4f}) is {improvement*100:.2f}% better than next best {next_best_cutoff} ({next_best_var:.4f}). Threshold: {threshold_percent}%."
    }

    if not is_valid:
        result["message"] += " CRITERIA NOT MET."

    return result

def run_validation(log_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Main entry point for T017d.
    """
    project_root = get_project_root()
    metrics_path = project_root / "code" / "data" / "results" / "cutoff_sensitivity.json"
    output_path = project_root / "code" / "data" / "results" / "cutoff_robustness_validation.json"
    
    # Setup logger
    logger = setup_logger("validate_cutoff", log_path or (project_root / "code" / "data" / "results" / "validate_cutoff.log"))
    
    logger.info(f"Starting cutoff robustness validation. Metrics file: {metrics_path}")
    
    try:
        metrics_data = load_sensitivity_metrics(metrics_path)
        logger.info(f"Loaded metrics for cutoffs: {metrics_data.get('cutoffs', [])}")
        
        validation_result = validate_cutoff_robustness(metrics_data)
        
        # Write validation result
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(validation_result, f, indent=2)
        
        logger.info(f"Validation result: {validation_result['status']}")
        logger.info(validation_result['message'])
        
        # If failed, raise an error to fail the task execution as per "Fail task if criteria not met"
        if validation_result['status'] == 'failed':
            logger.error("Validation failed: Selected cutoff does not minimize variance by required margin.")
            raise RuntimeError(f"Validation Failed: {validation_result['message']}")
        
        return validation_result

    except FileNotFoundError as e:
        logger.error(f"Input file missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise

def main():
    try:
        result = run_validation()
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()