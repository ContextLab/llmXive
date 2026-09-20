"""
Analyze failure cases to distinguish between Geometric Ambiguity and Semantic Gap.
"""
import os
import sys
import json
import csv
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure code directory is in path for imports
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "code"))

from config import Config

def classify_failure(scene_id: str, symbolic_pred: Any, vlm_pred: Any, ground_truth: Any) -> Dict[str, Any]:
    """Classify a failure case."""
    if symbolic_pred == ground_truth:
        return {"classification": "Correct", "reason": "Symbolic solver matched ground truth"}
    if vlm_pred == ground_truth:
        # VLM correct, Symbolic wrong
        if symbolic_pred is None or symbolic_pred == "No Solution":
            return {"classification": "Geometric Ambiguity", "reason": "Solver could not find a solution"}
        else:
            return {"classification": "Semantic Gap", "reason": "Solver found a solution but it was incorrect"}
    return {"classification": "Both Wrong", "reason": "Both models failed"}

def analyze_failures(results_path: str, output_path: str):
    """Analyze failures from benchmark results."""
    config = Config()
    logger = config.logger
    
    if not os.path.exists(results_path):
        logger.error(f"Benchmark results not found: {results_path}")
        sys.exit(1)
    
    failures = []
    semantic_gap_count = 0
    symbolic_failures_count = 0
    
    with open(results_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            scene_id = row['scene_id']
            symbolic_pred = row['symbolic_pred']
            vlm_pred = row['vlm_pred']
            ground_truth = row['ground_truth']
            
            classification = classify_failure(scene_id, symbolic_pred, vlm_pred, ground_truth)
            
            if classification['classification'] in ['Geometric Ambiguity', 'Semantic Gap']:
                symbolic_failures_count += 1
                if classification['classification'] == 'Semantic Gap':
                    semantic_gap_count += 1
            
            failures.append({
                "scene_id": scene_id,
                "classification": classification['classification'],
                "reason": classification['reason']
            })
    
    semantic_gap_proportion = semantic_gap_count / symbolic_failures_count if symbolic_failures_count > 0 else 0.0
    
    output_data = {
        "failures": failures,
        "summary": {
            "total_symbolic_failures": symbolic_failures_count,
            "semantic_gap_count": semantic_gap_count,
            "semantic_gap_proportion": semantic_gap_proportion
        }
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Failure analysis complete. Output: {output_path}")
    logger.info(f"Semantic Gap Proportion: {semantic_gap_proportion:.2f}")

def main():
    parser = argparse.ArgumentParser(description="Analyze failure cases")
    parser.add_argument("--results", type=str, required=True, help="Path to benchmark_results.csv")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON")
    args = parser.parse_args()
    
    analyze_failures(args.results, args.output)

if __name__ == "__main__":
    main()