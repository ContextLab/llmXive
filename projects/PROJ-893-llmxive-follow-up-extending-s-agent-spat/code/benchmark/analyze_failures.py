import os
import sys
import json
import csv
import argparse
from pathlib import Path
from config import config

def classify_failure(scene_id: str, symbolic_pred: Any, vlm_pred: Any, ground_truth: Any) -> Dict[str, Any]:
    """
    Classify failure type.
    Returns classification and reason.
    """
    if symbolic_pred == ground_truth:
        return {"classification": "Success", "reason": "Correct prediction"}
    
    if vlm_pred == ground_truth:
        # Symbolic failed but VLM succeeded
        # Check if it's a geometric ambiguity or semantic gap
        # Simplified logic: if constraints are sparse, likely geometric ambiguity
        return {"classification": "Semantic Gap", "reason": "VLM succeeded, symbolic failed"}
    else:
        # Both failed
        return {"classification": "Geometric Ambiguity", "reason": "Both models failed"}

def analyze_failures(results_path: Path) -> Path:
    """
    Analyze failures from benchmark results.
    Returns path to failure classification JSON.
    """
    if not results_path.exists():
        raise FileNotFoundError(f"Benchmark results not found: {results_path}")
    
    failures = []
    total_failures = 0
    semantic_gap_count = 0
    
    with open(results_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            scene_id = row['scene_id']
            symbolic_pred = row['symbolic_pred']
            vlm_pred = row['vlm_pred']
            ground_truth = row['ground_truth']
            
            if row['exact_match'] == 'False':
                total_failures += 1
                classification = classify_failure(scene_id, symbolic_pred, vlm_pred, ground_truth)
                classification['scene_id'] = scene_id
                failures.append(classification)
                
                if classification['classification'] == "Semantic Gap":
                    semantic_gap_count += 1
    
    # Calculate proportion
    proportion = semantic_gap_count / total_failures if total_failures > 0 else 0.0
    
    output = {
        "total_failures": total_failures,
        "semantic_gap_count": semantic_gap_count,
        "geometric_ambiguity_count": total_failures - semantic_gap_count,
        "proportion_semantic_gap": proportion,
        "failures": failures
    }
    
    output_path = config.DATA_DERIVED / "failure_classification.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"Failure analysis complete. Output written to {output_path}")
    return output_path

def main():
    """Main entry point for failure analysis."""
    parser = argparse.ArgumentParser(description="Analyze solver failures")
    parser.add_argument("--results", type=str, required=True, help="Benchmark results CSV")
    parser.add_argument("--output", type=str, help="Output JSON path (optional)")
    args = parser.parse_args()
    
    results_path = Path(args.results)
    analyze_failures(results_path)

if __name__ == "__main__":
    main()