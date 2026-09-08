import os
import sys
import json
import csv
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import config

def classify_failure(scene_data: Dict[str, Any]) -> str:
    """
    Classify a failure case as 'Geometric Ambiguity' or 'Semantic Gap'.
    
    Logic:
    - If the solver status is 'No Solution' or 'Ambiguous', it's likely Geometric Ambiguity.
    - If the solver found a solution but it differs from ground truth (and VLM also differed or was ambiguous),
      it might be a Semantic Gap if the constraints were insufficient to capture the full scene semantics.
    - For this implementation, we use a heuristic:
      * If symbolic_pred != ground_truth AND vlm_pred != ground_truth: Semantic Gap (both models failed on semantics)
      * If symbolic_pred != ground_truth AND solver_status in ['No Solution', 'Ambiguous']: Geometric Ambiguity
      * Otherwise: Semantic Gap (solver made a wrong geometric deduction based on valid constraints)
    """
    status = scene_data.get('status', '')
    symbolic_pred = scene_data.get('symbolic_pred')
    ground_truth = scene_data.get('ground_truth')
    vlm_pred = scene_data.get('vlm_pred')

    if symbolic_pred == ground_truth:
        return "Success"

    # Failure case
    if status in ['No Solution', 'Ambiguous']:
        return "Geometric Ambiguity"
    
    # If both models failed, it suggests the constraints (which are derived from VLM)
    # might not capture the necessary semantic nuance, or the task is inherently ambiguous.
    # However, per the task definition:
    # - Geometric Ambiguity: Constraints are insufficient to deduce a unique solution.
    # - Semantic Gap: Constraints are valid but the deduction logic or the mapping to semantics is flawed.
    
    # Heuristic: If VLM got it right but Symbolic didn't -> Semantic Gap in Symbolic logic.
    # If VLM also got it wrong -> likely Semantic Gap in the input data (constraints derived from VLM).
    # We classify as Semantic Gap if the solver ran successfully (found a solution) but it was wrong.
    if status == 'Success':
        return "Semantic Gap"
    
    return "Geometric Ambiguity"

def analyze_failures(results_path: Path, output_path: Path):
    """
    Analyze failures from benchmark results and classify them.
    Output: data/derived/failure_classification.json
    """
    if not results_path.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}")

    with open(results_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    classifications = []
    counts = {"Geometric Ambiguity": 0, "Semantic Gap": 0, "Success": 0}

    for row in rows:
        category = classify_failure(row)
        counts[category] += 1
        classifications.append({
            "scene_id": row['scene_id'],
            "classification": category,
            "symbolic_pred": row['symbolic_pred'],
            "vlm_pred": row['vlm_pred'],
            "ground_truth": row['ground_truth'],
            "status": row['status']
        })

    total_failures = counts["Geometric Ambiguity"] + counts["Semantic Gap"]
    semantic_gap_proportion = counts["Semantic Gap"] / total_failures if total_failures > 0 else 0.0

    output_data = {
        "summary": {
            "total_scenes": len(rows),
            "success_count": counts["Success"],
            "failure_count": total_failures,
            "geometric_ambiguity_count": counts["Geometric Ambiguity"],
            "semantic_gap_count": counts["Semantic Gap"],
            "semantic_gap_proportion": semantic_gap_proportion
        },
        "failures": [c for c in classifications if c['classification'] != 'Success']
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"Failure analysis saved to {output_path}")
    print(f"Semantic Gap Proportion: {semantic_gap_proportion:.2%}")

def main():
    parser = argparse.ArgumentParser(description="Analyze and classify failures")
    parser.add_argument("--results", type=str, required=True, help="Path to benchmark_results.csv")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON")
    args = parser.parse_args()

    analyze_failures(Path(args.results), Path(args.output))

if __name__ == "__main__":
    main()
