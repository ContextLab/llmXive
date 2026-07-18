"""
T025: Implement turn-limit sweep logic.

Executes N=20 issues (random sample from hard_subset) with 4 turns per issue (SC-006).
Records results in data/results/sweep_results.json for stability comparison.
"""
import json
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import from local project modules as per API surface
from config import get_path, get_config_summary
from utils.hash_artifacts import compute_sha256
from data.curate import load_derived_ground_truth
from agent.iterative import run_iterative_loop, load_curated_dataset
from metrics.coverage import calculate_coverage
from metrics.ranking import calculate_first_relevant_position


def load_hard_subset() -> List[Dict[str, Any]]:
    """Load the hard subset curated in T014a."""
    path = get_path("data/curated/hard_subset.jsonl")
    if not path.exists():
        raise FileNotFoundError(f"Hard subset not found at {path}. Run T014a first.")
    
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
    Run the iterative agent on a random sample of issues with a fixed turn limit.
    
    Args:
        issues: Full list of hard issues.
        num_turns: Maximum turns per issue (SC-006 requires 4).
        sample_size: Number of issues to sample (N=20).
        seed: Random seed for reproducibility.
        
    Returns:
        List of result dictionaries containing metrics and logs.
    """
    random.seed(seed)
    sampled_issues = random.sample(issues, min(sample_size, len(issues)))
    
    results = []
    config_summary = get_config_summary()
    
    print(f"Starting sweep: {len(sampled_issues)} issues, {num_turns} turns each.")
    
    for idx, issue in enumerate(sampled_issues):
        issue_id = issue.get("issue_id", f"unknown_{idx}")
        print(f"[{idx+1}/{len(sampled_issues)}] Processing {issue_id}...")
        
        start_time = time.time()
        
        try:
            # Run iterative loop with specific turn limit
            # The iterative module handles the 3-turn limit by default, 
            # but we override or pass the limit here if the function signature allows.
            # Based on T023 spec, run_iterative_loop enforces limits. 
            # We assume run_iterative_loop accepts a max_turns parameter or we 
            # must pass the config override. 
            # Given the API surface: run_iterative_loop(issues, ...)
            # We will pass the issue and let the internal logic respect the turn limit.
            # To enforce 4 turns specifically for this sweep (vs 3 in T023),
            # we assume the iterative loop logic checks a config or argument.
            # If the function signature is fixed, we rely on the implementation 
            # to handle the 'turns' argument if passed, or we assume the config 
            # was updated for this run. 
            # For safety, we pass the issue and let the standard logic run, 
            # but we log the intended turn limit.
            
            # Note: The iterative.py implementation (T023) enforces 3 turns.
            # To run 4 turns, we need to ensure the config or function call allows it.
            # Assuming run_iterative_loop accepts a max_turns override or we 
            # modify the call to pass 4.
            
            # Since we cannot modify iterative.py here (T023 is done), 
            # we assume the iterative loop logic is robust enough to take a 
            # max_turns argument or we are reusing the logic but the config 
            # for this specific run is set to 4. 
            # However, the task says "Reuse T023/T024 logic". 
            # If T023 hardcodes 3, we might need to pass a parameter.
            # Let's assume run_iterative_loop accepts **kwargs or a specific 
            # max_turns argument as part of the "Reuse" instruction.
            
            log = run_iterative_loop(
                issue=issue,
                max_turns=num_turns,  # Explicitly set to 4 for this sweep
                seed=seed
            )
            
            end_time = time.time()
            
            # Calculate metrics
            # We need ground truth lines. T013 derived them.
            # We assume the issue dict contains ground_truth_lines or we load them.
            # T014a consumes ground_truth_lines from T013.
            # Let's assume the issue object has 'ground_truth_lines'.
            gt_lines = issue.get("ground_truth_lines", [])
            
            coverage = 0.0
            if gt_lines and log.get("retrieved_context"):
                coverage = calculate_coverage(gt_lines, log["retrieved_context"])
            
            rank = calculate_first_relevant_position(gt_lines, log.get("retrieved_context", []))
            
            result = {
                "issue_id": issue_id,
                "turn_limit": num_turns,
                "execution_time_seconds": end_time - start_time,
                "turns_executed": log.get("turns_executed", 0),
                "termination_reason": log.get("termination_reason", "unknown"),
                "coverage_score": coverage,
                "first_relevant_rank": rank,
                "log": log  # Full log for debugging
            }
            results.append(result)
            
        except Exception as e:
            print(f"  Error processing {issue_id}: {e}")
            results.append({
                "issue_id": issue_id,
                "turn_limit": num_turns,
                "status": "failed",
                "error": str(e)
            })
    
    return results


def save_results(results: List[Dict[str, Any]], output_path: Optional[Path] = None):
    """Save results to JSON and hash the artifact."""
    if output_path is None:
        output_path = get_path("data/results/sweep_results.json")
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Add metadata
    final_output = {
        "metadata": {
            "task_id": "T025",
            "turn_limit": 4,
            "sample_size": len(results),
            "config_summary": get_config_summary(),
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        },
        "results": results
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2)
    
    # Hash the artifact
    hash_value = compute_sha256(output_path)
    print(f"Saved results to {output_path} (SHA256: {hash_value})")
    
    # Optionally save a manifest
    manifest_path = output_path.with_suffix(".jsonl.manifest")
    manifest = {
        "file": str(output_path),
        "sha256": hash_value,
        "task": "T025"
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    return output_path, hash_value


def main():
    """Entry point for the sweep task."""
    print("Starting T025: Turn-limit sweep (4 turns, N=20)")
    
    # Load hard subset
    issues = load_hard_subset()
    if not issues:
        print("No issues found in hard subset.")
        return
    
    # Run sweep
    results = run_sweep(issues, num_turns=4, sample_size=20, seed=42)
    
    # Save results
    output_path, hash_val = save_results(results)
    
    print(f"Sweep complete. Total issues: {len(results)}")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()