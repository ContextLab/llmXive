"""
comparison_report.py

Implements the generation of a paired comparison report between AST-based
and Neural baseline adapters (US2 Scenario 2).

This module:
1. Loads exact-match scores from `data/results/ast_scores.csv` and `data/results/neural_scores.csv`.
2. Aligns them by `task_id`.
3. Computes the performance delta (AST - Neural).
4. Generates a summary report (mean delta, count, pass/fail rates) and a detailed CSV.
5. Outputs artifacts to `data/results/comparison_report.csv` and `data/results/comparison_summary.json`.
"""

import csv
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from existing project modules
from evaluation.baseline_loader import get_baseline_adapter_path
from utils.logging import get_logger

logger = get_logger(__name__)


def load_scores_from_csv(file_path: Path) -> Dict[str, float]:
    """
    Loads scores from a CSV file into a dictionary keyed by task_id.
    Expects columns: task_id, score (or exact_match).
    """
    scores = {}
    if not file_path.exists():
        raise FileNotFoundError(f"Score file not found: {file_path}")

    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Handle potential variations in column names
            task_id = row.get('task_id') or row.get('id')
            score_val = row.get('score') or row.get('exact_match') or row.get('accuracy')
            
            if task_id and score_val is not None:
                try:
                    scores[task_id] = float(score_val)
                except ValueError:
                    logger.warning(f"Skipping non-numeric score for {task_id}: {score_val}")
    
    return scores


def align_and_compute_delta(ast_scores: Dict[str, float], neural_scores: Dict[str, float]) -> List[Dict[str, Any]]:
    """
    Aligns scores by task_id and computes the performance delta (AST - Neural).
    Returns a list of dictionaries containing task_id, ast_score, neural_score, delta.
    """
    common_tasks = set(ast_scores.keys()) & set(neural_scores.keys())
    
    if not common_tasks:
        raise ValueError("No common tasks found between AST and Neural score files.")
    
    results = []
    for task_id in sorted(common_tasks):
        ast_val = ast_scores[task_id]
        neural_val = neural_scores[task_id]
        delta = ast_val - neural_val
        
        results.append({
            "task_id": task_id,
            "ast_score": ast_val,
            "neural_score": neural_val,
            "delta": delta,
            "improved": delta > 0
        })
    
    return results


def generate_summary_report(detailed_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Computes aggregate statistics for the comparison report.
    """
    if not detailed_results:
        return {}

    deltas = [r["delta"] for r in detailed_results]
    ast_scores = [r["ast_score"] for r in detailed_results]
    neural_scores = [r["neural_score"] for r in detailed_results]

    mean_delta = sum(deltas) / len(deltas)
    mean_ast = sum(ast_scores) / len(ast_scores)
    mean_neural = sum(neural_scores) / len(neural_scores)

    improved_count = sum(1 for r in detailed_results if r["improved"])
    total_count = len(detailed_results)

    return {
        "total_tasks": total_count,
        "mean_ast_score": mean_ast,
        "mean_neural_score": mean_neural,
        "mean_delta": mean_delta,
        "improved_tasks": improved_count,
        "improvement_rate": improved_count / total_count if total_count > 0 else 0.0,
        "tasks_with_negative_delta": sum(1 for d in deltas if d < 0),
        "tasks_with_positive_delta": sum(1 for d in deltas if d > 0),
        "tasks_with_zero_delta": sum(1 for d in deltas if d == 0)
    }


def save_comparison_csv(detailed_results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Saves the detailed comparison results to a CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ["task_id", "ast_score", "neural_score", "delta", "improved"]
    
    with open(output_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(detailed_results)
    
    logger.info(f"Comparison CSV saved to: {output_path}")


def save_summary_json(summary: Dict[str, Any], output_path: Path) -> None:
    """
    Saves the summary statistics to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, mode='w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Comparison summary saved to: {output_path}")


def run_comparison_report(
    ast_scores_path: Optional[Path] = None,
    neural_scores_path: Optional[Path] = None,
    output_dir: Optional[Path] = None
) -> Tuple[Dict[str, Any], Path]:
    """
    Main entry point to generate the paired comparison report.
    
    Args:
        ast_scores_path: Path to ast_scores.csv. Defaults to data/results/ast_scores.csv.
        neural_scores_path: Path to neural_scores.csv. Defaults to data/results/neural_scores.csv.
        output_dir: Directory for output files. Defaults to data/results/.
        
    Returns:
        Tuple of (summary_dict, path_to_detailed_csv)
    """
    # Default paths
    results_dir = Path("data/results")
    ast_scores_path = ast_scores_path or results_dir / "ast_scores.csv"
    neural_scores_path = neural_scores_path or results_dir / "neural_scores.csv"
    output_dir = output_dir or results_dir

    logger.info(f"Loading AST scores from: {ast_scores_path}")
    ast_scores = load_scores_from_csv(ast_scores_path)
    
    logger.info(f"Loading Neural scores from: {neural_scores_path}")
    neural_scores = load_scores_from_csv(neural_scores_path)

    logger.info(f"Aligning scores and computing deltas...")
    detailed_results = align_and_compute_delta(ast_scores, neural_scores)

    logger.info(f"Generating summary statistics...")
    summary = generate_summary_report(detailed_results)

    # Save outputs
    csv_output_path = output_dir / "comparison_report.csv"
    json_output_path = output_dir / "comparison_summary.json"

    save_comparison_csv(detailed_results, csv_output_path)
    save_summary_json(summary, json_output_path)

    return summary, csv_output_path


def main() -> None:
    """
    CLI entry point for generating the comparison report.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate AST vs Neural comparison report.")
    parser.add_argument("--ast-input", type=str, default=None, help="Path to AST scores CSV")
    parser.add_argument("--neural-input", type=str, default=None, help="Path to Neural scores CSV")
    parser.add_argument("--output-dir", type=str, default="data/results", help="Output directory")
    
    args = parser.parse_args()
    
    ast_path = Path(args.ast_input) if args.ast_input else None
    neural_path = Path(args.neural_input) if args.neural_input else None
    out_dir = Path(args.output_dir)
    
    try:
        summary, csv_path = run_comparison_report(ast_path, neural_path, out_dir)
        print(f"\n--- Comparison Report Summary ---")
        print(f"Total Tasks: {summary['total_tasks']}")
        print(f"Mean AST Score: {summary['mean_ast_score']:.4f}")
        print(f"Mean Neural Score: {summary['mean_neural_score']:.4f}")
        print(f"Mean Delta (AST - Neural): {summary['mean_delta']:.4f}")
        print(f"Tasks Improved by AST: {summary['improved_tasks']} ({summary['improvement_rate']*100:.1f}%)")
        print(f"---------------------------------")
        print(f"Detailed report saved to: {csv_path}")
        print(f"Summary saved to: {out_dir / 'comparison_summary.json'}")
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Data alignment error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during report generation: {e}")
        raise


if __name__ == "__main__":
    main()