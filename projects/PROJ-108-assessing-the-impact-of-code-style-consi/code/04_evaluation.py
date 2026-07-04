"""
Evaluation script for T021: Compute BLEU-4 for summaries and Precision/Recall/F1 for bug localization.

Reads inference results from data/processed/inference_results.jsonl and ground truth
(embedded in the inference results or provided separately) to compute:
- BLEU-4 score for natural language summaries
- Precision, Recall, and F1-score for bug localization predictions

Handles null/missing metrics gracefully.
"""
import argparse
import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set

# Import helper metrics from the existing utils module
# Note: We need to extend utils/metrics.py to include the full BLEU implementation
# since the existing one was reported as truncated.
sys.path.insert(0, str(Path(__file__).parent / "utils"))
from metrics import bleu_score, f1_score

def load_inference_results(input_path: Path) -> List[Dict[str, Any]]:
    """Load inference results from JSONL file."""
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    
    results = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                results.append(data)
            except json.JSONDecodeError as e:
                print(f"Warning: Skipping malformed JSON on line {line_num}: {e}", file=sys.stderr)
    
    return results

def compute_bleu_for_summary(summary: str, reference: str) -> float:
    """
    Compute BLEU-4 score between generated summary and reference.
    Returns 0.0 if either string is empty or null.
    """
    if not summary or not reference:
        return 0.0
    
    # bleu_score expects lists of tokens (words)
    try:
        gen_tokens = summary.split()
        ref_tokens = reference.split()
        
        if not gen_tokens or not ref_tokens:
            return 0.0
        
        score = bleu_score([ref_tokens], gen_tokens, n=4)
        return score if score is not None else 0.0
    except Exception as e:
        print(f"Warning: BLEU computation failed: {e}", file=sys.stderr)
        return 0.0

def compute_bug_localization_metrics(
    predicted_lines: List[int], 
    ground_truth_lines: List[int]
) -> Tuple[float, float, float]:
    """
    Compute Precision, Recall, and F1-score for bug localization.
    
    Args:
        predicted_lines: List of line numbers predicted to contain bugs
        ground_truth_lines: List of actual bug line numbers
    
    Returns:
        Tuple of (precision, recall, f1). Returns (0.0, 0.0, 0.0) if inputs are empty/null.
    """
    if not predicted_lines or not ground_truth_lines:
        return 0.0, 0.0, 0.0
    
    pred_set = set(predicted_lines)
    truth_set = set(ground_truth_lines)
    
    if not pred_set or not truth_set:
        return 0.0, 0.0, 0.0
    
    # Calculate metrics
    precision, recall, f1 = f1_score(truth_set, pred_set)
    
    # f1_score returns (precision, recall, f1) or (0,0,0) on error
    return precision, recall, f1

def evaluate_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evaluate all inference results and compute aggregate metrics.
    
    Args:
        results: List of inference result dictionaries containing:
            - summary: generated summary
            - summary_reference: ground truth summary (if available)
            - bug_lines: predicted bug line numbers
            - bug_lines_ground_truth: actual bug line numbers (if available)
    
    Returns:
        Dictionary with aggregate metrics and per-file scores.
    """
    bleu_scores = []
    precision_scores = []
    recall_scores = []
    f1_scores = []
    
    file_results = []
    
    for i, result in enumerate(results):
        file_metrics = {"file_index": i, "bleu": None, "precision": None, "recall": None, "f1": None}
        
        # Evaluate summary (BLEU)
        summary = result.get("summary")
        reference = result.get("summary_reference")
        
        if summary is not None and reference is not None:
            bleu = compute_bleu_for_summary(summary, reference)
            file_metrics["bleu"] = bleu
            bleu_scores.append(bleu)
        else:
            file_metrics["bleu"] = None
        
        # Evaluate bug localization (Precision/Recall/F1)
        predicted_lines = result.get("bug_lines")
        ground_truth_lines = result.get("bug_lines_ground_truth")
        
        if predicted_lines is not None and ground_truth_lines is not None:
            # Ensure they are lists of integers
            if isinstance(predicted_lines, str):
                predicted_lines = [int(x) for x in predicted_lines.split(",") if x.strip().isdigit()]
            if isinstance(ground_truth_lines, str):
                ground_truth_lines = [int(x) for x in ground_truth_lines.split(",") if x.strip().isdigit()]
            
            precision, recall, f1 = compute_bug_localization_metrics(predicted_lines, ground_truth_lines)
            file_metrics["precision"] = precision
            file_metrics["recall"] = recall
            file_metrics["f1"] = f1
            precision_scores.append(precision)
            recall_scores.append(recall)
            f1_scores.append(f1)
        else:
            file_metrics["precision"] = None
            file_metrics["recall"] = None
            file_metrics["f1"] = None
        
        file_results.append(file_metrics)
    
    # Compute aggregates
    aggregate = {
        "total_samples": len(results),
        "bleu_metrics": {
            "count": len(bleu_scores),
            "mean": sum(bleu_scores) / len(bleu_scores) if bleu_scores else 0.0,
            "min": min(bleu_scores) if bleu_scores else 0.0,
            "max": max(bleu_scores) if bleu_scores else 0.0,
        },
        "bug_localization_metrics": {
            "precision": {
                "count": len(precision_scores),
                "mean": sum(precision_scores) / len(precision_scores) if precision_scores else 0.0,
                "min": min(precision_scores) if precision_scores else 0.0,
                "max": max(precision_scores) if precision_scores else 0.0,
            },
            "recall": {
                "count": len(recall_scores),
                "mean": sum(recall_scores) / len(recall_scores) if recall_scores else 0.0,
                "min": min(recall_scores) if recall_scores else 0.0,
                "max": max(recall_scores) if recall_scores else 0.0,
            },
            "f1": {
                "count": len(f1_scores),
                "mean": sum(f1_scores) / len(f1_scores) if f1_scores else 0.0,
                "min": min(f1_scores) if f1_scores else 0.0,
                "max": max(f1_scores) if f1_scores else 0.0,
            }
        },
        "per_file_metrics": file_results
    }
    
    return aggregate

def save_evaluation_report(aggregate: Dict[str, Any], output_path: Path) -> None:
    """Save evaluation report to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(aggregate, f, indent=2, default=str)
    
    print(f"Evaluation report saved to: {output_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Evaluate LLM inference results for summaries and bug localization."
    )
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/processed/inference_results.jsonl",
        help="Path to input JSONL file with inference results"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/processed/evaluation_results.json",
        help="Path to output JSON evaluation report"
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    print(f"Loading inference results from: {input_path}")
    results = load_inference_results(input_path)
    print(f"Loaded {len(results)} results")
    
    if not results:
        print("Warning: No valid results to evaluate. Creating empty report.", file=sys.stderr)
        aggregate = {
            "total_samples": 0,
            "bleu_metrics": {"count": 0, "mean": 0.0, "min": 0.0, "max": 0.0},
            "bug_localization_metrics": {
                "precision": {"count": 0, "mean": 0.0, "min": 0.0, "max": 0.0},
                "recall": {"count": 0, "mean": 0.0, "min": 0.0, "max": 0.0},
                "f1": {"count": 0, "mean": 0.0, "min": 0.0, "max": 0.0}
            },
            "per_file_metrics": []
        }
    else:
        print("Computing evaluation metrics...")
        aggregate = evaluate_results(results)
    
    save_evaluation_report(aggregate, output_path)
    
    # Print summary
    print("\n=== Evaluation Summary ===")
    print(f"Total samples: {aggregate['total_samples']}")
    print(f"BLEU-4 (n={aggregate['bleu_metrics']['count']}): mean={aggregate['bleu_metrics']['mean']:.4f}")
    print(f"F1 (n={aggregate['bug_localization_metrics']['f1']['count']}): mean={aggregate['bug_localization_metrics']['f1']['mean']:.4f}")

if __name__ == "__main__":
    main()
