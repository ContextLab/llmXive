"""
Oracle-Symbolic Comparison Analysis (Secondary/Diagnostic)

Implements the comparison between the Symbolic-Guava agent and the Oracle-Symbolic agent.
This is a secondary/diagnostic analysis as per the project plan methodology.

The Oracle-Symbolic agent uses ground-truth action sequences to simulate a perfect policy,
allowing us to isolate reasoning limitations from perception limitations.
"""
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from utils.config import get_path, get_hyperparameter
from data.models import TaskOutcome
from utils.exceptions import LlmXiveError


def load_oracle_outcomes() -> List[Dict[str, Any]]:
    """
    Load the Oracle-Symbolic evaluation outcomes.
    
    Returns:
        List of outcome dictionaries from the Oracle evaluation run.
        
    Raises:
        LlmXiveError: If the oracle outcomes file is not found.
    """
    oracle_path = get_path("oracle_outcomes")
    if not oracle_path.exists():
        raise LlmXiveError(
            f"Oracle outcomes file not found at {oracle_path}. "
            "Run inference_oracle.py first to generate this file."
        )
    
    with open(oracle_path, "r") as f:
        return json.load(f)


def load_symbolic_outcomes() -> List[Dict[str, Any]]:
    """
    Load the Symbolic-Guava evaluation outcomes.
    
    Returns:
        List of outcome dictionaries from the Symbolic evaluation run.
        
    Raises:
        LlmXiveError: If the symbolic outcomes file is not found.
    """
    symbolic_path = get_path("evaluation_outcomes")
    if not symbolic_path.exists():
        raise LlmXiveError(
            f"Symbolic outcomes file not found at {symbolic_path}. "
            "Run inference_symbolic.py first to generate this file."
        )
    
    with open(symbolic_path, "r") as f:
        return json.load(f)


def calculate_success_rate(outcomes: List[Dict[str, Any]]) -> float:
    """
    Calculate the success rate from a list of outcomes.
    
    Args:
        outcomes: List of outcome dictionaries with 'success' boolean field.
        
    Returns:
        Success rate as a float between 0 and 1.
    """
    if not outcomes:
        return 0.0
    
    successful = sum(1 for o in outcomes if o.get("success", False))
    return successful / len(outcomes)


def calculate_step_efficiency(outcomes: List[Dict[str, Any]]) -> float:
    """
    Calculate the average step efficiency (actual_steps / optimal_steps).
    
    Args:
        outcomes: List of outcome dictionaries with 'steps' and 'optimal_steps' fields.
        
    Returns:
        Average step efficiency as a float.
    """
    if not outcomes:
        return 0.0
    
    total_ratio = 0.0
    valid_count = 0
    
    for o in outcomes:
        steps = o.get("steps", 0)
        optimal = o.get("optimal_steps", 1)
        
        if optimal > 0:
            total_ratio += steps / optimal
            valid_count += 1
    
    return total_ratio / valid_count if valid_count > 0 else 0.0


def compare_agents(
    symbolic_outcomes: List[Dict[str, Any]],
    oracle_outcomes: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Compare Symbolic-Guava and Oracle-Symbolic agents.
    
    Args:
        symbolic_outcomes: Outcomes from the Symbolic-Guava agent.
        oracle_outcomes: Outcomes from the Oracle-Symbolic agent.
        
    Returns:
        Dictionary with comparison metrics.
    """
    symbolic_success = calculate_success_rate(symbolic_outcomes)
    oracle_success = calculate_success_rate(oracle_outcomes)
    
    symbolic_efficiency = calculate_step_efficiency(symbolic_outcomes)
    oracle_efficiency = calculate_step_efficiency(oracle_outcomes)
    
    # Calculate the gap
    success_gap = oracle_success - symbolic_success
    efficiency_gap = oracle_efficiency - symbolic_efficiency
    
    # Identify failure categories unique to Symbolic (not present in Oracle)
    symbolic_failures = [o for o in symbolic_outcomes if not o.get("success", False)]
    oracle_failures = [o for o in oracle_outcomes if not o.get("success", False)]
    
    # Count failures by category
    symbolic_failure_categories = {}
    for f in symbolic_failures:
        category = f.get("failure_category", "unknown")
        symbolic_failure_categories[category] = symbolic_failure_categories.get(category, 0) + 1
    
    oracle_failure_categories = {}
    for f in oracle_failures:
        category = f.get("failure_category", "unknown")
        oracle_failure_categories[category] = oracle_failure_categories.get(category, 0) + 1
    
    # Find categories where Symbolic fails but Oracle succeeds
    reasoning_failures = 0
    for outcome in symbolic_failures:
        task_id = outcome.get("task_id")
        oracle_match = next((o for o in oracle_outcomes if o.get("task_id") == task_id), None)
        
        if oracle_match and oracle_match.get("success", False):
            reasoning_failures += 1
    
    return {
        "symbolic_success_rate": symbolic_success,
        "oracle_success_rate": oracle_success,
        "success_gap": success_gap,
        "symbolic_step_efficiency": symbolic_efficiency,
        "oracle_step_efficiency": oracle_efficiency,
        "efficiency_gap": efficiency_gap,
        "reasoning_induced_failures": reasoning_failures,
        "total_symbolic_failures": len(symbolic_failures),
        "total_oracle_failures": len(oracle_failures),
        "symbolic_failure_breakdown": symbolic_failure_categories,
        "oracle_failure_breakdown": oracle_failure_categories,
        "comparison_timestamp": time.time()
    }


def write_comparison_results(results: Dict[str, Any]) -> Path:
    """
    Write the comparison results to the artifacts directory.
    
    Args:
        results: Dictionary with comparison metrics.
        
    Returns:
        Path to the written results file.
    """
    output_path = get_path("oracle_comparison_results")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    return output_path


def main() -> int:
    """
    Main entry point for the Oracle-Symbolic comparison analysis.
    
    Returns:
        Exit code (0 for success, 1 for error).
    """
    try:
        print("Loading Oracle-Symbolic outcomes...")
        oracle_outcomes = load_oracle_outcomes()
        print(f"  Loaded {len(oracle_outcomes)} Oracle outcomes")
        
        print("Loading Symbolic-Guava outcomes...")
        symbolic_outcomes = load_symbolic_outcomes()
        print(f"  Loaded {len(symbolic_outcomes)} Symbolic outcomes")
        
        print("Comparing agents...")
        results = compare_agents(symbolic_outcomes, oracle_outcomes)
        
        print("Writing comparison results...")
        output_path = write_comparison_results(results)
        print(f"  Results written to {output_path}")
        
        # Print summary
        print("\n" + "="*60)
        print("ORACLE-SYMBOLIC COMPARISON SUMMARY")
        print("="*60)
        print(f"Symbolic Success Rate: {results['symbolic_success_rate']:.2%}")
        print(f"Oracle Success Rate:   {results['oracle_success_rate']:.2%}")
        print(f"Success Gap:           {results['success_gap']:.2%}")
        print(f"Symbolic Efficiency:   {results['symbolic_step_efficiency']:.2f}")
        print(f"Oracle Efficiency:     {results['oracle_step_efficiency']:.2f}")
        print(f"Efficiency Gap:        {results['efficiency_gap']:.2f}")
        print(f"Reasoning Failures:    {results['reasoning_induced_failures']}/{results['total_symbolic_failures']}")
        print("="*60)
        
        return 0
        
    except Exception as e:
        print(f"Error during Oracle-Symbolic comparison: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())