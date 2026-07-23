"""
Agreement Rate Analysis Script.

Compares rule-based violation flags from execution traces against human-annotated
ground truth to compute agreement rates and confidence intervals.

Dependencies:
  - T027: data/processed/execution_traces.csv
  - T033: data/processed/annotation_sample.csv

Output:
  - data/processed/agreement_rate_report.json
"""

import argparse
import json
import math
import os
import sys
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Ensure project root is in path for imports if run as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import get_paths

def load_execution_traces(input_path: str) -> List[Dict[str, Any]]:
    """
    Load execution traces from CSV.
    Returns a list of dictionaries.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Execution traces file not found: {input_path}")

    traces = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse boolean and float fields
            row['violation_boolean'] = row['violation_boolean'].lower() == 'true'
            row['final_score'] = float(row['final_score'])
            row['constraint_count'] = int(row['constraint_count'])
            traces.append(row)
    return traces

def load_human_annotations(input_path: str) -> List[Dict[str, Any]]:
    """
    Load human-annotated ground truth from CSV.
    Expected columns: task_id, raw_prompt, constraint_list (or similar).
    We need to infer the 'ground truth violation' status.
    For this specific task, we assume the annotation sample contains a column
    or logic to determine if a violation occurred that the rule-based system should have caught.

    Since T033 produces `data/processed/annotation_sample.csv` with columns:
    `task_id`, `raw_prompt`, `constraint_list`, we must interpret the human annotation.
    In the absence of a specific 'human_violation_flag' column in T033's schema,
    we assume the 'constraint_list' implies that if the list is non-empty and the
    plan (from execution_traces) violated it, that's a ground truth violation.
    
    However, T034 description says: "Compare rule-based violation flags against human annotations."
    This implies the human annotation file *must* contain the ground truth label.
    If T033 only produced the sample for *future* annotation, this script would fail.
    Given the task requirement to *compute* agreement now, we assume `annotation_sample.csv`
    has been populated with a `human_violation_flag` or similar column by the time this runs,
    or we derive it if the schema allows.
    
    Re-reading T033: "Output `data/processed/annotation_sample.csv`. Output Schema: Columns must be `task_id`, `raw_prompt`, `constraint_list`."
    This suggests T033 is just sampling. The "human-annotated ground truth" implies a step where humans *actually* annotated it.
    If the file only has `constraint_list`, we cannot compute agreement against a "human annotation" unless we assume
    the presence of a `human_violation_flag` column that T033 might have been extended to include, or the task implies
    a mock annotation step for the sake of the pipeline.
    
    CRITICAL FIX: The task description says "reads ... human-annotated ground truth".
    If the file from T033 lacks the annotation, we cannot compute agreement.
    We will assume the file *does* contain a `human_violation_flag` column (added by a human or a simulated human step)
    as per the requirement of T034. If not, we raise an error.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Human annotation file not found: {input_path}")

    annotations = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        if not fieldnames:
            raise ValueError("Annotation file is empty or has no headers.")
        
        # Check for expected ground truth column
        if 'human_violation_flag' not in fieldnames:
            # Fallback: if the task implies we must simulate or if the column is named differently
            # But per strict requirements, we must read real data.
            # We will assume the column exists. If not, we fail loudly.
            raise ValueError(f"Annotation file missing required column 'human_violation_flag'. Found: {fieldnames}")

        for row in reader:
            row['human_violation_flag'] = row['human_violation_flag'].lower() == 'true'
            annotations.append(row)
    return annotations

def compute_agreement(traces: List[Dict], annotations: List[Dict]) -> Tuple[int, int, int]:
    """
    Compute agreement between rule-based flags and human annotations.
    Returns (total_compared, agreements, disagreements).
    """
    # Create a map of task_id -> human annotation
    human_map = {ann['task_id']: ann for ann in annotations}
    
    total = 0
    agreements = 0
    disagreements = 0

    for trace in traces:
        task_id = trace['task_id']
        if task_id not in human_map:
            continue  # Skip if no human annotation for this task

        human_flag = human_map[task_id]['human_violation_flag']
        model_flag = trace['violation_boolean']

        total += 1
        if human_flag == model_flag:
            agreements += 1
        else:
            disagreements += 1

    return total, agreements, disagreements

def compute_confidence_interval(agreements: int, total: int, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Compute the confidence interval for the agreement rate using the Wilson score interval.
    """
    if total == 0:
        return 0.0, 0.0

    p = agreements / total
    z = 1.96  # For 95% confidence, z is approximately 1.96
    if confidence == 0.90:
        z = 1.645
    elif confidence == 0.99:
        z = 2.576

    denominator = 1 + (z ** 2) / total
    center = (p + (z ** 2) / (2 * total)) / denominator
    margin = (z / denominator) * math.sqrt((p * (1 - p) / total) + ((z ** 2) / (4 * total ** 2)))

    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)

    return lower, upper

def run_agreement_analysis(traces_path: str, annotations_path: str, output_path: str) -> Dict[str, Any]:
    """
    Main analysis function.
    """
    print(f"Loading execution traces from {traces_path}...")
    traces = load_execution_traces(traces_path)
    print(f"Loaded {len(traces)} traces.")

    print(f"Loading human annotations from {annotations_path}...")
    annotations = load_human_annotations(annotations_path)
    print(f"Loaded {len(annotations)} annotations.")

    print("Computing agreement...")
    total, agreements, disagreements = compute_agreement(traces, annotations)

    if total == 0:
        raise ValueError("No overlapping tasks found between traces and annotations.")

    agreement_rate = agreements / total
    lower_ci, upper_ci = compute_confidence_interval(agreements, total)

    report = {
        "agreement_rate": round(agreement_rate, 4),
        "confidence_interval_lower": round(lower_ci, 4),
        "confidence_interval_upper": round(upper_ci, 4),
        "sample_size": total,
        "agreements": agreements,
        "disagreements": disagreements
    }

    print(f"Writing report to {output_path}...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f"Agreement Rate: {agreement_rate:.2%} (95% CI: [{lower_ci:.2%}, {upper_ci:.2%}])")
    return report

def main():
    parser = argparse.ArgumentParser(description="Compute agreement rate between model and human annotations.")
    parser.add_argument("--traces", type=str, required=True, help="Path to execution_traces.csv")
    parser.add_argument("--annotations", type=str, required=True, help="Path to annotation_sample.csv")
    parser.add_argument("--output", type=str, default="data/processed/agreement_rate_report.json", help="Output JSON path")
    
    args = parser.parse_args()

    try:
        run_agreement_analysis(args.traces, args.annotations, args.output)
        print("Agreement analysis completed successfully.")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()