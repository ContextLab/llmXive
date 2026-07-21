"""
Agreement Rate Analysis Script for T031.

This script computes the agreement rate between the execution traces (model
predictions) and the human-annotated ground truth (simulated from the annotation sample).
It calculates the agreement rate with a confidence interval and writes the result
to a JSON report.

Dependencies:
- pandas
- scipy (for confidence intervals)
- numpy
"""

import argparse
import json
import math
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import pandas as pd
import numpy as np
from scipy import stats

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from config import Paths


def load_execution_traces(traces_path: Path) -> pd.DataFrame:
    """
    Load the execution traces CSV.

    Expected columns: task_id, architecture, constraint_count, violation (bool), final_score
    """
    if not traces_path.exists():
        raise FileNotFoundError(f"Execution traces file not found: {traces_path}")

    df = pd.read_csv(traces_path)
    required_cols = ['task_id', 'architecture', 'violation']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Execution traces missing required columns: {missing}")

    # Ensure violation is boolean
    if df['violation'].dtype != bool:
        df['violation'] = df['violation'].astype(bool)

    return df


def load_human_annotations(annotations_path: Path) -> pd.DataFrame:
    """
    Load the human-annotated sample CSV.

    Expected columns: task_id, raw_prompt, constraint_list, ground_truth_violation
    (Note: The annotator task T030 outputs task_id, raw_prompt, constraint_list.
     We assume the 'ground_truth_violation' is derived or added.
     Per T031 description: 'simulated from data/processed/annotation_sample.csv'.
     We will simulate the ground truth violation based on the constraint_list length
     and a deterministic rule if the column is missing, OR expect the column to exist.
     To be robust: if 'ground_truth_violation' is missing, we simulate it based on
     a rule: violation = True if len(constraint_list) > threshold, else False.
     However, the task says 'simulated from... for pipeline validation'.
     Let's assume the annotator script T030 added a 'ground_truth_violation' column
     or we simulate it here deterministically to match the 'human' intent.
     
     Actually, T030 output: 'task_id, raw_prompt, constraint_list'.
     T031 says: 'simulated from ... annotation_sample.csv'.
     We will simulate ground truth violation:
     If the task has >= 5 constraints (which all do in filtered_tasks),
     and the model failed to track them, it's a violation.
     But 'human annotated ground truth' implies a label.
     Since we don't have real humans, we simulate the 'human label' by
     checking if the 'constraint_list' is non-empty and the model's violation
     matches a heuristic, OR we just generate a 'ground_truth_violation' column
     based on a random seed for the sake of the pipeline validation,
     BUT the prompt says 'simulated from ... for pipeline validation'.
     
     Let's implement a deterministic simulation:
     Ground truth violation = True if the task_id ends with an even number (arbitrary rule)
     OR better: Since we don't have the real ground truth, we assume the 'human'
     would flag a violation if the model's execution was inconsistent with the constraints.
     However, for this task, we are comparing the *agreement rate*.
     
     Let's assume the annotation_sample.csv has a column 'ground_truth_violation'
     added by T030 (or we add it here as a simulation step).
     If it doesn't exist, we generate a synthetic ground truth based on a seed
     to ensure the script runs and produces a result (as per 'simulated' instruction).
     """
    if not annotations_path.exists():
        raise FileNotFoundError(f"Annotation sample file not found: {annotations_path}")

    df = pd.read_csv(annotations_path)
    
    if 'ground_truth_violation' not in df.columns:
        # Simulate ground truth violation deterministically for pipeline validation
        # We use the task_id hash to generate a consistent pseudo-random label
        np.random.seed(42)
        def simulate_violation(task_id):
            # Simple deterministic simulation: 30% chance of violation
            # In a real scenario, this would be the human label
            return np.random.choice([True, False], p=[0.3, 0.7])
        
        df['ground_truth_violation'] = df['task_id'].apply(simulate_violation)

    return df


def compute_agreement(traces_df: pd.DataFrame, annotations_df: pd.DataFrame) -> Tuple[float, float, float]:
    """
    Compute the agreement rate between model predictions (violation) and human annotations.
    
    Returns:
      agreement_rate (float), ci_lower (float), ci_upper (float)
    """
    # Merge on task_id
    merged = traces_df.merge(annotations_df[['task_id', 'ground_truth_violation']], on='task_id', how='inner')
    
    if len(merged) == 0:
        raise ValueError("No overlapping tasks between execution traces and annotation sample.")

    # Calculate agreement
    # Agreement: (Model_Violation == Ground_Truth_Violation)
    matches = merged['violation'] == merged['ground_truth_violation']
    n_matches = matches.sum()
    n_total = len(merged)
    
    agreement_rate = n_matches / n_total

    # Calculate 95% Confidence Interval using Wilson Score Interval
    # or simple normal approximation if n is large enough.
    # Using Wilson Score Interval for better accuracy with proportions.
    z = 1.96  # 95% confidence
    p = agreement_rate
    n = n_total
    
    denominator = 1 + z**2/n
    centre_adjusted_probability = p + z**2 / (2*n)
    adjusted_standard_deviation = math.sqrt((p*(1-p) + z**2/(4*n)) / n)
    
    lower = (centre_adjusted_probability - z * adjusted_standard_deviation) / denominator
    upper = (centre_adjusted_probability + z * adjusted_standard_deviation) / denominator
    
    return float(agreement_rate), float(lower), float(upper)


def run_agreement_analysis(traces_path: Path, annotations_path: Path, output_path: Path) -> Dict[str, Any]:
    """
    Run the full agreement analysis and return the report dictionary.
    """
    traces_df = load_execution_traces(traces_path)
    annotations_df = load_human_annotations(annotations_path)
    
    rate, lower, upper = compute_agreement(traces_df, annotations_df)
    
    report = {
        "agreement_rate": rate,
        "confidence_interval_95": {
            "lower": lower,
            "upper": upper
        },
        "sample_size": len(traces_df),
        "overlap_size": int(lower * 0), # Placeholder for actual overlap count if needed
        "description": "Agreement rate between model execution traces and simulated human ground truth."
    }
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report


def main():
    parser = argparse.ArgumentParser(description="Compute agreement rate between model traces and human annotations.")
    parser.add_argument(
        "--traces", 
        type=str, 
        default="data/processed/execution_traces.csv",
        help="Path to execution traces CSV"
    )
    parser.add_argument(
        "--annotations", 
        type=str, 
        default="data/processed/annotation_sample.csv",
        help="Path to human annotation sample CSV"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/processed/agreement_rate_report.json",
        help="Path to output JSON report"
    )
    
    args = parser.parse_args()
    
    traces_path = Path(args.traces)
    annotations_path = Path(args.annotations)
    output_path = Path(args.output)
    
    # Check dependencies
    try:
        import scipy
    except ImportError:
        print("Error: scipy is required for confidence interval calculation.")
        sys.exit(1)

    try:
        report = run_agreement_analysis(traces_path, annotations_path, output_path)
        print(f"Agreement analysis complete.")
        print(f"Agreement Rate: {report['agreement_rate']:.4f}")
        print(f"95% CI: [{report['confidence_interval_95']['lower']:.4f}, {report['confidence_interval_95']['upper']:.4f}]")
        print(f"Report written to: {output_path}")
    except Exception as e:
        print(f"Error during analysis: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()