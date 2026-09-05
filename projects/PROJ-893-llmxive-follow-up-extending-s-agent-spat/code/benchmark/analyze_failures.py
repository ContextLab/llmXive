"""
Failure Analysis Module for US3.
Classifies solver failures into 'Geometric Ambiguity' or 'Semantic Gap'
and calculates the proportion of failures attributable to semantic disambiguation.
"""
import os
import sys
import json
import csv
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Import from project config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import Config

# Import from existing benchmark modules
from benchmark.metrics import load_jsonl, load_csv

def classify_failure(
    scene_id: str,
    solver_prediction: Any,
    vlm_prediction: Any,
    ground_truth: Any,
    constraints: Dict[str, Any]
) -> str:
    """
    Classifies a specific failure case.
    
    Logic:
    1. If VLM matches Ground Truth but Solver does not -> 'Semantic Gap' (Solver lacked the reasoning capability VLM had).
    2. If VLM does NOT match Ground Truth AND Solver does NOT match Ground Truth -> 'Geometric Ambiguity' (Both failed, likely due to ill-posed constraints or inherent ambiguity in the scene).
    3. If Solver matches Ground Truth -> Not a failure (should not be passed here).
    
    Returns:
        str: 'Geometric Ambiguity' or 'Semantic Gap'
    """
    # Normalize predictions for comparison (handle string/int/float variations)
    def normalize(val):
        if val is None:
            return None
        if isinstance(val, str):
            val = val.strip().lower()
            if val == 'none' or val == 'nan':
                return None
            # Try to parse as number if possible for strict comparison
            try:
                return float(val)
            except ValueError:
                return val
        return val

    norm_solver = normalize(solver_prediction)
    norm_vlm = normalize(vlm_prediction)
    norm_gt = normalize(ground_truth)

    # If both match GT, it's not a failure (sanity check)
    if norm_solver == norm_gt:
        return "No Failure"

    # If VLM is correct but Solver is wrong -> Semantic Gap
    if norm_vlm == norm_gt:
        return "Semantic Gap"

    # If VLM is also wrong -> Geometric Ambiguity (Both models struggled with the ambiguity)
    # Note: This assumes VLM is a reasonable proxy for "correct" in ambiguous cases,
    # or that if both fail, the problem is inherently ambiguous.
    return "Geometric Ambiguity"

def analyze_failures(
    predictions_path: Path,
    vlm_baseline_path: Path,
    ground_truth_path: Path,
    constraints_path: Path,
    output_report_path: Path
) -> Dict[str, Any]:
    """
    Main analysis function. Loads data, identifies mismatches, classifies them,
    and calculates the proportion of semantic gap failures.
    
    Returns:
        Dict containing summary statistics and the list of classified failures.
    """
    # Load data
    predictions = load_jsonl(predictions_path)
    vlm_baseline = load_csv(vlm_baseline_path)
    ground_truth = load_csv(ground_truth_path)
    
    # Load constraints for context (optional but useful for detailed logging)
    constraints_map = {}
    if constraints_path.exists():
        with open(constraints_path, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        constraints_map[data['scene_id']] = data
                    except json.JSONDecodeError:
                        continue

    # Index VLM and Ground Truth by scene_id
    vlm_map = {row['scene_id']: row['prediction'] for row in vlm_baseline}
    gt_map = {row['scene_id']: row['ground_truth'] for row in ground_truth}

    classified_failures = []
    failure_counts = {
        "Semantic Gap": 0,
        "Geometric Ambiguity": 0,
        "Total Failures": 0
    }

    for pred_row in predictions:
        scene_id = pred_row['scene_id']
        solver_pred = pred_row['prediction']
        
        # Get ground truth
        if scene_id not in gt_map:
            continue # Skip if GT missing (should be handled by T019)
        
        gt_val = gt_map[scene_id]
        vlm_val = vlm_map.get(scene_id, None)

        # Check if this is a failure (Solver != GT)
        def normalize(val):
            if val is None:
                return None
            if isinstance(val, str):
                val = val.strip().lower()
                if val == 'none' or val == 'nan':
                    return None
            try:
                return float(val)
            except ValueError:
                return val

        if normalize(solver_pred) == normalize(gt_val):
            continue # Not a failure

        # It is a failure. Classify it.
        constraints = constraints_map.get(scene_id, {})
        category = classify_failure(scene_id, solver_pred, vlm_val, gt_val, constraints)
        
        if category in ["Semantic Gap", "Geometric Ambiguity"]:
            failure_counts["Total Failures"] += 1
            failure_counts[category] += 1
            
            classified_failures.append({
                "scene_id": scene_id,
                "solver_prediction": solver_pred,
                "vlm_prediction": vlm_val,
                "ground_truth": gt_val,
                "category": category
            })

    # Calculate Proportion
    proportion_semantic = 0.0
    if failure_counts["Total Failures"] > 0:
        proportion_semantic = failure_counts["Semantic Gap"] / failure_counts["Total Failures"]

    result = {
        "summary": {
            "total_failures": failure_counts["Total Failures"],
            "semantic_gap_count": failure_counts["Semantic Gap"],
            "geometric_ambiguity_count": failure_counts["Geometric Ambiguity"],
            "proportion_semantic_gap": proportion_semantic
        },
        "failures": classified_failures
    }

    # Write detailed report (JSON for machine reading, we will generate MD in T022)
    # But T021 requires calculating the proportion. We save the analysis data.
    output_report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_report_path, 'w') as f:
        json.dump(result, f, indent=2)

    return result

def main():
    """
    Entry point for T021.
    Reads from data/derived and data/results, writes to data/results.
    """
    config = Config()
    
    # Define paths based on project structure
    predictions_path = config.DATA_DERIVED / "predictions.jsonl"
    vlm_baseline_path = config.DATA_RESULTS / "vlm_baseline.csv" # Assuming T006b put it here or T019
    ground_truth_path = config.DATA_RAW / "ground_truth.csv" # Adjust based on T006b/T019 output location
    constraints_path = config.DATA_DERIVED / "constraints.jsonl"
    output_report_path = config.DATA_RESULTS / "failure_analysis_data.json"

    # Fallbacks for standard locations if config paths differ slightly in implementation
    if not predictions_path.exists():
        predictions_path = Path("data/derived/predictions.jsonl")
    if not vlm_baseline_path.exists():
        # Try common locations
        vlm_baseline_path = Path("data/derived/vlm_baseline.csv")
        if not vlm_baseline_path.exists():
            vlm_baseline_path = Path("data/results/vlm_baseline.csv")
    if not ground_truth_path.exists():
        ground_truth_path = Path("data/raw/ground_truth.csv")
        if not ground_truth_path.exists():
            ground_truth_path = Path("data/derived/ground_truth.csv")
    if not constraints_path.exists():
        constraints_path = Path("data/derived/constraints.jsonl")

    print(f"Loading data from: {predictions_path}, {vlm_baseline_path}, {ground_truth_path}")
    
    if not predictions_path.exists() or not vlm_baseline_path.exists() or not ground_truth_path.exists():
        print("ERROR: Required input files for failure analysis are missing.")
        print("Ensure T012 (predictions), T006b (vlm_baseline), and T019 (ground_truth) have run.")
        sys.exit(1)

    try:
        results = analyze_failures(
            predictions_path,
            vlm_baseline_path,
            ground_truth_path,
            constraints_path,
            output_report_path
        )
        
        print("\n--- Failure Analysis Summary ---")
        print(f"Total Failures: {results['summary']['total_failures']}")
        print(f"Semantic Gap Failures: {results['summary']['semantic_gap_count']}")
        print(f"Geometric Ambiguity Failures: {results['summary']['geometric_ambiguity_count']}")
        print(f"Proportion of Failures due to Semantic Gap: {results['summary']['proportion_semantic_gap']:.4f}")
        print(f"Full analysis saved to: {output_report_path}")
        
    except Exception as e:
        print(f"ERROR during failure analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()