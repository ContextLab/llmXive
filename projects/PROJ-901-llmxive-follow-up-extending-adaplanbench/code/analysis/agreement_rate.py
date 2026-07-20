import argparse
import json
import math
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd

# Ensure the parent directory is in the path for imports if running as script
# In the actual project structure, this is handled by the runner or PYTHONPATH
# We assume standard project layout: code/analysis/
# If run as `python code/analysis/agreement_rate.py`, we need to add code/ to path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import Paths


def load_execution_traces(traces_path: Path) -> pd.DataFrame:
    """
    Loads the execution traces CSV.
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
    Loads the human annotations CSV.
    Expected columns: task_id, human_violation (bool), notes (optional)
    """
    if not annotations_path.exists():
        raise FileNotFoundError(f"Human annotations file not found: {annotations_path}")
    
    df = pd.read_csv(annotations_path)
    required_cols = ['task_id', 'human_violation']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Human annotations missing required columns: {missing}")
    
    # Ensure human_violation is boolean
    if df['human_violation'].dtype != bool:
        df['human_violation'] = df['human_violation'].astype(bool)
        
    return df


def compute_agreement(traces_df: pd.DataFrame, annotations_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes agreement rate between execution traces (model prediction) and human annotations.
    
    Returns a dictionary with:
      - total_tasks: int
      - agreed_count: int
      - agreement_rate: float (0-1)
      - ci_lower: float (95% Wilson score interval lower bound)
      - ci_upper: float (95% Wilson score interval upper bound)
    """
    # Merge on task_id
    merged = pd.merge(traces_df, annotations_df, on='task_id', how='inner')
    
    if len(merged) == 0:
        raise ValueError("No overlapping tasks found between execution traces and human annotations.")
    
    # Compare violation predictions
    # We assume 'violation' in traces is the model's prediction
    # and 'human_violation' is the ground truth
    merged['match'] = merged['violation'] == merged['human_violation']
    
    total = len(merged)
    agreed = merged['match'].sum()
    rate = agreed / total if total > 0 else 0.0
    
    # Calculate 95% Confidence Interval using Wilson Score Interval
    # p = rate, n = total, z = 1.96 for 95%
    z = 1.96
    if total > 0:
        denominator = 1 + z**2 / total
        center = (rate + z**2 / (2 * total)) / denominator
        spread = z * math.sqrt((rate * (1 - rate) + z**2 / (4 * total)) / total)
        ci_lower = max(0.0, center - spread / denominator)
        ci_upper = min(1.0, center + spread / denominator)
    else:
        ci_lower = 0.0
        ci_upper = 0.0
        
    return {
        "total_tasks": int(total),
        "agreed_count": int(agreed),
        "agreement_rate": float(rate),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "confidence_level": 0.95
    }


def run_agreement_analysis(
    traces_path: Path, 
    annotations_path: Path, 
    output_path: Path
) -> Dict[str, Any]:
    """
    Runs the full agreement analysis pipeline and saves the report.
    """
    print(f"Loading execution traces from {traces_path}...")
    traces_df = load_execution_traces(traces_path)
    
    print(f"Loading human annotations from {annotations_path}...")
    annotations_df = load_human_annotations(annotations_path)
    
    print(f"Computing agreement...")
    results = compute_agreement(traces_df, annotations_df)
    
    print(f"Writing report to {output_path}...")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    print(f"Agreement analysis complete. Rate: {results['agreement_rate']:.4f} "
          f"([{results['ci_lower']:.4f}, {results['ci_upper']:.4f}])")
          
    return results


def main():
    parser = argparse.ArgumentParser(description="Compute agreement rate between model execution and human annotations.")
    parser.add_argument(
        "--traces", 
        type=str, 
        default=str(Paths.PROCESSED_DATA_DIR / "execution_traces.csv"),
        help="Path to execution_traces.csv"
    )
    parser.add_argument(
        "--annotations", 
        type=str, 
        default=str(Paths.PROCESSED_DATA_DIR / "human_annotations.csv"),
        help="Path to human_annotations.csv"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=str(Paths.PROCESSED_DATA_DIR / "agreement_rate_report.json"),
        help="Path to output JSON report"
    )
    
    args = parser.parse_args()
    
    traces_path = Path(args.traces)
    annotations_path = Path(args.annotations)
    output_path = Path(args.output)
    
    if not traces_path.exists():
        print(f"ERROR: Execution traces file not found at {traces_path}")
        sys.exit(1)
        
    if not annotations_path.exists():
        print(f"ERROR: Human annotations file not found at {annotations_path}")
        sys.exit(1)
        
    try:
        run_agreement_analysis(traces_path, annotations_path, output_path)
    except Exception as e:
        print(f"ERROR: Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
