import os
import sys
import json
import logging
import math
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# Import logging infrastructure
from logging_config import setup_logger, get_logger

# Import state tracker for artifact tracking
from state_tracker import load_state_file, save_state_file, update_state_with_artifact

# Import data model for schema validation
from data_model import MetricResult

# Configure logger
logger = setup_logger("cliffs_delta", level=logging.INFO)

def load_metric_values(metrics_dir: Path, metric_type: str, group_human: str = "human", group_llm: str = "llm") -> Tuple[List[float], List[float]]:
    """
    Load metric values for a specific metric type from CSV files.
    
    Args:
        metrics_dir: Directory containing metric CSV files.
        metric_type: The specific metric column name (e.g., 'cyclomatic_complexity').
        group_human: Label for human-written snippets.
        group_llm: Label for LLM-generated snippets.
        
    Returns:
        Tuple of (human_values, llm_values) lists of floats.
        
    Raises:
        FileNotFoundError: If the metric CSV file is not found.
        ValueError: If the metric type is not found in the CSV.
    """
    # Determine the file name based on metric type naming convention
    # Assuming files are named like: data/metrics/cyclomatic_complexity.csv
    file_path = metrics_dir / f"{metric_type}.csv"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Metric file not found: {file_path}")
    
    import pandas as pd
    df = pd.read_csv(file_path)
    
    if metric_type not in df.columns:
        raise ValueError(f"Column '{metric_type}' not found in {file_path}. Available: {list(df.columns)}")
    
    if 'group' not in df.columns:
        raise ValueError(f"Column 'group' not found in {file_path}. Required for separation.")
    
    human_values = df[df['group'] == group_human][metric_type].dropna().tolist()
    llm_values = df[df['group'] == group_llm][metric_type].dropna().tolist()
    
    logger.info(f"Loaded {len(human_values)} human and {len(llm_values)} LLM values for {metric_type}")
    
    return human_values, llm_values

def compute_cliffs_delta(x: List[float], y: List[float]) -> float:
    """
    Compute Cliff's Delta effect size between two distributions.
    
    Cliff's Delta measures the probability that a random value from one group
    is greater than a random value from the other group, minus the reverse probability.
    
    Formula: delta = (number of pairs where x > y - number of pairs where x < y) / (n_x * n_y)
    
    Args:
        x: List of values from group 1 (e.g., human).
        y: List of values from group 2 (e.g., LLM).
        
    Returns:
        Cliff's Delta value in range [-1, 1].
    """
    if not x or not y:
        return 0.0
    
    n_x = len(x)
    n_y = len(y)
    total_pairs = n_x * n_y
    
    if total_pairs == 0:
        return 0.0
    
    # Use vectorized operations for efficiency if possible, or simple loops
    # For robustness with standard library, we use loops but optimize with sorting if needed.
    # Given typical sizes (n < 10000), O(N*M) is acceptable.
    
    greater_count = 0
    smaller_count = 0
    
    # Optimization: sort y to use binary search or simple iteration if N is large
    # But for clarity and correctness, we'll do direct comparison.
    # If performance is critical, we can use numpy.
    
    import numpy as np
    x_arr = np.array(x)
    y_arr = np.array(y)
    
    # Vectorized comparison
    # x > y: broadcast x against y
    # This creates a matrix of comparisons.
    # x_arr[:, None] > y_arr[None, :]
    
    greater_matrix = x_arr[:, None] > y_arr[None, :]
    smaller_matrix = x_arr[:, None] < y_arr[None, :]
    
    greater_count = np.sum(greater_matrix)
    smaller_count = np.sum(smaller_matrix)
    
    delta = (greater_count - smaller_count) / total_pairs
    return float(delta)

def get_effect_size_magnitude(delta: float) -> str:
    """
    Classify the magnitude of Cliff's Delta based on standard thresholds.
    
    Thresholds (commonly used):
    |delta| < 0.147: negligible
    0.147 <= |delta| < 0.33: small
    0.33 <= |delta| < 0.474: medium
    |delta| >= 0.474: large
    
    Args:
        delta: The computed Cliff's Delta value.
        
    Returns:
        String label: 'negligible', 'small', 'medium', or 'large'.
    """
    abs_delta = abs(delta)
    if abs_delta < 0.147:
        return "negligible"
    elif abs_delta < 0.33:
        return "small"
    elif abs_delta < 0.474:
        return "medium"
    else:
        return "large"

def compute_cliffs_delta_for_all_metrics(metrics_dir: Path) -> Dict[str, Dict[str, Any]]:
    """
    Compute Cliff's Delta for all available metrics.
    
    Args:
        metrics_dir: Path to the directory containing metric CSVs.
        
    Returns:
        Dictionary mapping metric names to results (delta, magnitude, counts).
    """
    results = {}
    
    # Known metrics based on T020/T021
    metric_types = [
        "cyclomatic_complexity", 
        "maintainability_index", 
        "potential_issues", 
        "style_issues"
    ]
    
    for metric in metric_types:
        try:
            human_vals, llm_vals = load_metric_values(metrics_dir, metric)
            delta = compute_cliffs_delta(human_vals, llm_vals)
            magnitude = get_effect_size_magnitude(delta)
            
            results[metric] = {
                "cliffs_delta": delta,
                "magnitude": magnitude,
                "n_human": len(human_vals),
                "n_llm": len(llm_vals),
                "interpretation": f"Delta={delta:.4f} ({magnitude})"
            }
            logger.info(f"Computed Cliff's Delta for {metric}: {delta:.4f} ({magnitude})")
        except FileNotFoundError as e:
            logger.warning(f"Skipping {metric}: {e}")
        except ValueError as e:
            logger.warning(f"Skipping {metric} due to data error: {e}")
        except Exception as e:
            logger.error(f"Error computing {metric}: {e}")
            
    return results

def write_results_to_file(results: Dict[str, Dict[str, Any]], output_path: Path) -> None:
    """
    Write the computed Cliff's Delta results to a JSON file.
    
    Args:
        results: Dictionary of results.
        output_path: Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Wrote Cliff's Delta results to {output_path}")

def update_state_with_cliffs_delta(results: Dict[str, Dict[str, Any]], state_path: Path) -> None:
    """
    Update the project state file with the Cliff's Delta results.
    
    Args:
        results: Dictionary of results.
        state_path: Path to the state YAML file.
    """
    try:
        state = load_state_file(state_path)
        
        if "cliffs_delta_analysis" not in state:
            state["cliffs_delta_analysis"] = {}
        
        state["cliffs_delta_analysis"]["results"] = results
        state["cliffs_delta_analysis"]["status"] = "completed"
        
        save_state_file(state, state_path)
        logger.info("Updated state file with Cliff's Delta results")
    except Exception as e:
        logger.error(f"Failed to update state file: {e}")

def main():
    """Main entry point for Cliff's Delta analysis."""
    # Define paths
    project_root = Path(__file__).parent.parent
    metrics_dir = project_root / "data" / "metrics"
    output_dir = project_root / "results" / "statistics"
    output_file = output_dir / "cliffs_delta_results.json"
    state_file = project_root / "state" / "projects" / "PROJ-488-evaluating-the-impact-of-code-generation.yaml"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting Cliff's Delta Analysis")
    
    # Compute
    results = compute_cliffs_delta_for_all_metrics(metrics_dir)
    
    if not results:
        logger.warning("No results computed. Check if metric files exist.")
        return 1
    
    # Write results
    write_results_to_file(results, output_file)
    
    # Update state
    if state_file.exists():
        update_state_with_cliffs_delta(results, state_file)
    else:
        logger.warning(f"State file not found at {state_file}. Skipping state update.")
    
    # Print summary
    print("\n=== Cliff's Delta Summary ===")
    for metric, data in results.items():
        print(f"{metric}: Delta = {data['cliffs_delta']:.4f} ({data['magnitude']})")
    
    logger.info("Cliff's Delta Analysis completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
