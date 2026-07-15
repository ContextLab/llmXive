"""
Agreement Rate Calculation Script for T031.

Reads execution traces and human annotations, computes agreement rate
with confidence interval, and writes the result to JSON.
"""
import argparse
import json
import math
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
from scipy import stats

# Import project configuration for paths
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import Paths


def load_execution_traces(path: Path) -> pd.DataFrame:
    """Load execution traces CSV."""
    if not path.exists():
        raise FileNotFoundError(f"Execution traces file not found: {path}")
    df = pd.read_csv(path)
    required_cols = ['task_id', 'violation_detected', 'final_score']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Execution traces missing required columns: {missing}")
    return df


def load_human_annotations(path: Path) -> pd.DataFrame:
    """Load human annotations CSV."""
    if not path.exists():
        raise FileNotFoundError(f"Human annotations file not found: {path}")
    df = pd.read_csv(path)
    required_cols = ['task_id', 'human_violation_detected']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Human annotations missing required columns: {missing}")
    return df


def compute_agreement(traces: pd.DataFrame, annotations: pd.DataFrame) -> Tuple[float, float, float, int]:
    """
    Compute agreement rate between model detection and human ground truth.

    Returns:
        (agreement_rate, lower_ci, upper_ci, n_samples)
    """
    # Merge on task_id
    merged = pd.merge(
        traces[['task_id', 'violation_detected']],
        annotations[['task_id', 'human_violation_detected']],
        on='task_id',
        how='inner'
    )

    if len(merged) == 0:
        raise ValueError("No overlapping tasks between execution traces and human annotations.")

    # Normalize boolean types (ensure they are comparable)
    # Assume columns are boolean or 0/1
    model_det = merged['violation_detected'].astype(bool)
    human_det = merged['human_violation_detected'].astype(bool)

    # Agreement: True if both agree (both True or both False)
    agreements = (model_det == human_det).sum()
    n = len(merged)
    rate = agreements / n

    # Wilson Score Interval for proportion
    # z = 1.96 for 95% CI
    z = 1.96
    denominator = 1 + z**2 / n
    center = (agreements + z**2 / 2) / n
    term = z * math.sqrt(center * (1 - center) / n + z**2 / (4 * n**2))

    lower = max(0.0, (center - term) / denominator)
    upper = min(1.0, (center + term) / denominator)

    return rate, lower, upper, n


def run_agreement_analysis(
    traces_path: Optional[Path] = None,
    annotations_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Main logic to run the agreement analysis.
    """
    paths = Paths()
    
    if traces_path is None:
        traces_path = paths.processed_dir / "execution_traces.csv"
    if annotations_path is None:
        annotations_path = paths.processed_dir / "human_annotations.csv"
    if output_path is None:
        output_path = paths.processed_dir / "agreement_rate_report.json"

    print(f"Loading execution traces from: {traces_path}")
    traces_df = load_execution_traces(traces_path)

    print(f"Loading human annotations from: {annotations_path}")
    annotations_df = load_human_annotations(annotations_path)

    print("Computing agreement rate and confidence interval...")
    rate, lower, upper, n = compute_agreement(traces_df, annotations_df)

    result = {
        "agreement_rate": rate,
        "confidence_interval": {
            "level": 0.95,
            "lower_bound": lower,
            "upper_bound": upper,
            "method": "Wilson Score Interval"
        },
        "sample_size": n,
        "traces_file": str(traces_path),
        "annotations_file": str(annotations_path)
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Writing report to: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

    print(f"Analysis complete. Agreement Rate: {rate:.4f} (95% CI: [{lower:.4f}, {upper:.4f}])")
    return result


def main():
    parser = argparse.ArgumentParser(description="Calculate agreement rate between model and human annotations.")
    parser.add_argument("--traces", type=str, help="Path to execution_traces.csv")
    parser.add_argument("--annotations", type=str, help="Path to human_annotations.csv")
    parser.add_argument("--output", type=str, help="Path for output JSON report")
    
    args = parser.parse_args()

    traces_path = Path(args.traces) if args.traces else None
    annotations_path = Path(args.annotations) if args.annotations else None
    output_path = Path(args.output) if args.output else None

    try:
        run_agreement_analysis(traces_path, annotations_path, output_path)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error during analysis: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()