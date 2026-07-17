"""
Sweep turn-limit logic for User Story 2.

Executes a sample of N=20 issues from the hard subset with 4 turns
(as per SC-006) to compare stability against the standard 3-turn limit.
"""
import json
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import from existing project API
from config import get_config_summary
from agent.iterative import run_iterative_loop, load_curated_dataset
from metrics.coverage import calculate_coverage
from metrics.ranking import calculate_first_relevant_position
from utils.hash_artifacts import compute_sha256


def load_hard_subset() -> List[Dict[str, Any]]:
    """
    Load the hard subset from data/curated/hard_subset.jsonl.
    Falls back to a strict error if the file is missing (no synthetic data).
    """
    config = get_config_summary()
    path = Path(config["data_curated"]) / "hard_subset.jsonl"
    
    if not path.exists():
        raise FileNotFoundError(
            f"Required dataset not found: {path}. "
            "Ensure T014a (curate.py) has been executed successfully."
        )
    
    issues = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                issues.append(json.loads(line))
    
    return issues


def run_sweep(
    issues: List[Dict[str, Any]],
    num_turns: int = 4,
    sample_size: int = 20,
    seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Run the iterative agent loop on a random sample of issues with a fixed turn limit.
    
    Args:
        issues: Full list of hard issues.
        num_turns: The turn limit to enforce (SC-006 specifies 4).
        sample_size: Number of issues to sample (N=20).
        seed: Random seed for reproducibility.
        
    Returns:
        List of result dictionaries containing metrics and logs.
    """
    random.seed(seed)
    
    # Sample N=20 issues
    if len(issues) < sample_size:
        print(f"Warning: Only {len(issues)} issues available, sampling all.")
        sample_issues = issues
    else:
        sample_issues = random.sample(issues, sample_size)
    
    results = []
    
    for idx, issue in enumerate(sample_issues):
        issue_id = issue.get("issue_id", f"unknown_{idx}")
        print(f"[Sweep] Processing {idx+1}/{len(sample_issues)}: {issue_id} (Turns: {num_turns})")
        
        start_time = time.time()
        
        try:
            # Run iterative loop with the specific turn limit
            # Note: run_iterative_loop expects the issue dict and turn limit
            log = run_iterative_loop(issue, max_turns=num_turns)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Calculate metrics
            # We assume the log contains 'retrieved_context' and 'ground_truth_lines'
            # or we need to fetch ground_truth_lines from the issue if not in log
            gt_lines = issue.get("ground_truth_lines", [])
            retrieved = log.get("retrieved_context", [])
            
            coverage = calculate_coverage(gt_lines, retrieved)
            ranking_pos = calculate_first_relevant_position(gt_lines, retrieved)
            
            result = {
                "issue_id": issue_id,
                "turn_limit": num_turns,
                "actual_turns_used": log.get("turns_used", 0),
                "duration_seconds": duration,
                "coverage_score": coverage,
                "first_relevant_rank": ranking_pos,
                "log_summary": {
                    "query_count": len(log.get("query_history", [])),
                    "error_signals": len(log.get("static_analysis_signals", [])),
                    "final_status": log.get("termination_reason", "unknown")
                }
            }
            results.append(result)
            
        except Exception as e:
            print(f"Error processing {issue_id}: {e}")
            results.append({
                "issue_id": issue_id,
                "turn_limit": num_turns,
                "actual_turns_used": 0,
                "duration_seconds": 0,
                "coverage_score": 0.0,
                "first_relevant_rank": -1,
                "error": str(e),
                "log_summary": {}
            })
    
    return results


def save_results(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save the sweep results to JSON.
    """
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    
    # Compute hash for integrity
    hash_val = compute_sha256(output_path)
    print(f"Saved results to {output_path} (SHA256: {hash_val})")


def main() -> None:
    """
    Entry point for the turn-limit sweep.
    """
    config = get_config_summary()
    output_path = Path(config["data_results"]) / "sweep_results.json"
    
    print("Starting Turn-Limit Sweep (4 turns, N=20)...")
    
    # Load data
    issues = load_hard_subset()
    print(f"Loaded {len(issues)} hard instances.")
    
    # Run sweep
    # SC-006: 4 turns
    results = run_sweep(
        issues=issues,
        num_turns=4,
        sample_size=20,
        seed=42
    )
    
    # Save results
    save_results(results, output_path)
    
    print("Sweep completed.")


if __name__ == "__main__":
    main()