"""
Agreement Rate Analysis (Task T034)

Computes the agreement rate between rule-based violation flags and human annotations,
excluding 'implicit_unverified' cases as per SC-005.
"""
import argparse
import json
import math
import os
import sys
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import Paths

def load_execution_traces(input_path: str) -> List[Dict[str, Any]]:
    """Load execution traces from CSV."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Execution traces file not found: {input_path}")
    
    traces = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            traces.append(row)
    return traces

def load_human_annotations(input_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Load human annotations from CSV.
    Returns a dictionary keyed by task_id.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Human annotations file not found: {input_path}")
    
    annotations = {}
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            task_id = row.get('task_id')
            if not task_id:
                continue
            # Parse boolean-like strings if necessary, otherwise keep as string
            # We expect 'is_violation' and 'is_implicit' to be filled by humans
            is_violation = row.get('is_violation', '').lower()
            is_implicit = row.get('is_implicit', '').lower()
            
            # Convert empty strings to None, 'true'/'false' to bool
            val_violation = None
            if is_violation == 'true':
                val_violation = True
            elif is_violation == 'false':
                val_violation = False
            
            val_implicit = None
            if is_implicit == 'true':
                val_implicit = True
            elif is_implicit == 'false':
                val_implicit = False

            annotations[task_id] = {
                'is_violation': val_violation,
                'is_implicit': val_implicit
            }
    return annotations

def compute_agreement(traces: List[Dict[str, Any]], annotations: Dict[str, Dict[str, Any]]) -> Tuple[int, int, int, int]:
    """
    Compute agreement metrics.
    Excludes rows where violation_status is 'implicit_unverified'.
    
    Returns: (agreed_count, total_count, true_positives, false_negatives)
    """
    agreed = 0
    total = 0
    # For precision/recall context if needed later, though task asks for agreement rate
    # We strictly compare: Rule Flag == Human Flag (where Human Flag is is_violation)
    
    for trace in traces:
        task_id = trace.get('task_id')
        violation_status = trace.get('violation_status', '')
        
        # SC-005: Exclude implicit_unverified
        if violation_status == 'implicit_unverified':
            continue
        
        if task_id not in annotations:
            # If human annotation is missing for a valid row, we cannot compute agreement
            # Skip or treat as disagreement? Spec implies we compute on available ground truth.
            # We will skip missing annotations to avoid bias, but log warning.
            continue
        
        human_data = annotations[task_id]
        is_violation = human_data.get('is_violation')
        
        # If human hasn't marked it yet (None), skip
        if is_violation is None:
            continue
        
        # Determine rule-based flag
        # The rule-based system flags a violation if violation_boolean is True
        # Note: The trace might have violation_status='false_negative' which implies a violation was missed,
        # but for "agreement on violations", we compare the final boolean outcome against the human.
        # The task says: "Compare rule-based violation flags (true/false) against human annotations"
        rule_flag = trace.get('violation_boolean', '').lower() == 'true'
        
        total += 1
        if rule_flag == is_violation:
            agreed += 1
    
    return agreed, total

def compute_confidence_interval(proportion: float, n: int, z: float = 1.96) -> Tuple[float, float]:
    """
    Compute Wilson Score Interval for proportion.
    """
    if n == 0:
        return 0.0, 0.0
    
    denominator = 1 + z**2 / n
    center = (proportion + z**2 / (2*n)) / denominator
    margin = (z * math.sqrt((proportion * (1 - proportion) + z**2 / (4*n)) / n)) / denominator
    
    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)
    
    return lower, upper

def run_agreement_analysis(input_traces: str, input_annotations: str, output_path: str) -> Dict[str, Any]:
    """
    Main logic to run agreement analysis.
    """
    # Load data
    traces = load_execution_traces(input_traces)
    annotations = load_human_annotations(input_annotations)
    
    # Compute agreement
    agreed, total = compute_agreement(traces, annotations)
    
    if total == 0:
        raise ValueError("No valid samples found for agreement calculation. "
                         "Check if 'implicit_unverified' excluded all rows or annotations are missing.")
    
    rate = agreed / total
    lower, upper = compute_confidence_interval(rate, total)
    
    result = {
        "agreement_rate": rate,
        "confidence_interval_lower": lower,
        "confidence_interval_upper": upper,
        "sample_size": total,
        "agreed_count": agreed
    }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    return result

def main():
    parser = argparse.ArgumentParser(description="Compute agreement rate between rule-based flags and human annotations.")
    parser.add_argument("--input-traces", default="data/processed/execution_traces.csv",
                        help="Path to execution_traces.csv")
    parser.add_argument("--input-annotations", default="data/processed/annotation_labels.csv",
                        help="Path to human annotated annotation_labels.csv")
    parser.add_argument("--output", default="data/processed/agreement_rate_report.json",
                        help="Path to output JSON report")
    
    args = parser.parse_args()
    
    try:
        result = run_agreement_analysis(args.input_traces, args.input_annotations, args.output)
        print(f"Agreement analysis complete. Report written to {args.output}")
        print(f"Agreement Rate: {result['agreement_rate']:.4f} ({result['sample_size']} samples)")
        print(f"95% CI: [{result['confidence_interval_lower']:.4f}, {result['confidence_interval_upper']:.4f}]")
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Analysis Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
