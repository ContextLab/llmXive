"""
Turn-limit sweep logic for User Story 2.

Executes N=20 issues from the hard subset with a 4-turn limit (SC-006)
to compare stability against the standard 3-turn limit.

Output: data/results/sweep_results.json
"""
import json
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import from existing API surface
from config import get_config_summary
from agent.iterative import run_iterative_agent
from agent.base import load_curated_dataset

# Constants
SWEEP_SAMPLE_SIZE = 20
SWEEP_TURN_LIMIT = 4  # SC-006 requirement
RANDOM_SEED = 42  # Reproducibility

def load_hard_subset() -> List[Dict[str, Any]]:
    """Load the curated hard subset from data/curated/hard_subset.jsonl"""
    config = get_config_summary()
    hard_subset_path = config["paths"]["data_curated"] / "hard_subset.jsonl"
    
    if not hard_subset_path.exists():
        raise FileNotFoundError(
            f"Hard subset not found at {hard_subset_path}. "
            "Run T014 (curate.py) first."
        )
    
    issues = []
    with open(hard_subset_path, "r", encoding="utf-8") as f:
        for line in f:
            issues.append(json.loads(line.strip()))
    
    return issues

def run_sweep(
    issues: List[Dict[str, Any]],
    turn_limit: int,
    sample_size: int,
    seed: int
) -> Dict[str, Any]:
    """
    Run the turn-limit sweep on a random sample of issues.
    
    Args:
        issues: Full list of hard issues
        turn_limit: Number of turns to enforce (4 for this sweep)
        sample_size: Number of issues to sample (N=20)
        seed: Random seed for reproducibility
    
    Returns:
        Dictionary containing sweep results and metadata
    """
    # Seed random for reproducibility
    random.seed(seed)
    
    # Select random sample
    sampled_issues = random.sample(issues, min(sample_size, len(issues)))
    
    results = {
        "metadata": {
            "task_id": "T025",
            "turn_limit": turn_limit,
            "sample_size": len(sampled_issues),
            "total_pool_size": len(issues),
            "random_seed": seed,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "config_summary": get_config_summary()
        },
        "runs": []
    }
    
    print(f"Starting sweep with {len(sampled_issues)} issues (turn limit: {turn_limit})")
    
    for idx, issue in enumerate(sampled_issues):
        issue_id = issue.get("issue_id", f"unknown_{idx}")
        print(f"[{idx+1}/{len(sampled_issues)}] Processing {issue_id}...")
        
        start_time = time.time()
        
        try:
            # Run iterative agent with custom turn limit
            # Note: run_iterative_agent accepts turn_limit parameter based on T023 implementation
            result = run_iterative_agent(
                issue=issue,
                turn_limit=turn_limit,
                verbose=False
            )
            
            elapsed = time.time() - start_time
            
            run_record = {
                "issue_id": issue_id,
                "turn_limit_used": turn_limit,
                "actual_turns": result.get("turns_taken", 0),
                "termination_reason": result.get("termination_reason", "unknown"),
                "query_count": result.get("query_count", 0),
                "coverage_score": result.get("coverage_score", 0.0),
                "first_relevant_rank": result.get("first_relevant_rank", None),
                "execution_time_sec": elapsed,
                "success": result.get("success", False),
                "error_message": result.get("error_message", None)
            }
            
            results["runs"].append(run_record)
            print(f"  -> Completed: {run_record['termination_reason']} "
                   f"(turns: {run_record['actual_turns']}, "
                   f"coverage: {run_record['coverage_score']:.2%})")
            
        except Exception as e:
            elapsed = time.time() - start_time
            error_record = {
                "issue_id": issue_id,
                "turn_limit_used": turn_limit,
                "actual_turns": 0,
                "termination_reason": "error",
                "query_count": 0,
                "coverage_score": 0.0,
                "first_relevant_rank": None,
                "execution_time_sec": elapsed,
                "success": False,
                "error_message": str(e)
            }
            results["runs"].append(error_record)
            print(f"  -> FAILED: {str(e)}")
    
    # Compute aggregate statistics
    successful_runs = [r for r in results["runs"] if r["success"]]
    if successful_runs:
        results["summary"] = {
            "total_runs": len(results["runs"]),
            "successful_runs": len(successful_runs),
            "success_rate": len(successful_runs) / len(results["runs"]),
            "avg_turns": sum(r["actual_turns"] for r in successful_runs) / len(successful_runs),
            "avg_coverage": sum(r["coverage_score"] for r in successful_runs) / len(successful_runs),
            "avg_execution_time": sum(r["execution_time_sec"] for r in successful_runs) / len(successful_runs)
        }
    else:
        results["summary"] = {
            "total_runs": len(results["runs"]),
            "successful_runs": 0,
            "success_rate": 0.0,
            "avg_turns": 0.0,
            "avg_coverage": 0.0,
            "avg_execution_time": 0.0
        }
    
    return results

def save_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save sweep results to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"Sweep results saved to {output_path}")

def main() -> int:
    """Main entry point for the turn-limit sweep."""
    print("=" * 60)
    print("T025: Turn-Limit Sweep (4 turns, N=20)")
    print("=" * 60)
    
    try:
        # Load hard subset
        hard_issues = load_hard_subset()
        print(f"Loaded {len(hard_issues)} hard issues from curated subset")
        
        # Run sweep
        sweep_results = run_sweep(
            issues=hard_issues,
            turn_limit=SWEEP_TURN_LIMIT,
            sample_size=SWEEP_SAMPLE_SIZE,
            seed=RANDOM_SEED
        )
        
        # Save results
        config = get_config_summary()
        output_path = config["paths"]["data_results"] / "sweep_results.json"
        save_results(sweep_results, output_path)
        
        # Print summary
        print("\n" + "=" * 60)
        print("SWEEP SUMMARY")
        print("=" * 60)
        summary = sweep_results["summary"]
        print(f"Total Runs: {summary['total_runs']}")
        print(f"Success Rate: {summary['success_rate']:.2%}")
        print(f"Avg Turns: {summary['avg_turns']:.2f}")
        print(f"Avg Coverage: {summary['avg_coverage']:.2%}")
        print(f"Avg Time: {summary['avg_execution_time']:.2f}s")
        
        return 0
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        print("Please ensure T014 (curate.py) has been run to generate hard_subset.jsonl", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())