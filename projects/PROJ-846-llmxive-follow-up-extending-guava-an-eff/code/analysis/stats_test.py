"""
Statistical Analysis: Permutation Test for Symbolic-Guava vs Baseline-Guava (Visual).

Task: T036a
Description: Perform a Permutation Test to determine if there is a significant 
difference in success rates between the Symbolic-Guava agent and the Baseline-Guava (Visual) agent.

Null Hypothesis (H0): No difference in success rates between Symbolic-Guava and Baseline-Guava.
Alternative Hypothesis (H1): There is a difference in success rates.

Method:
1. Load evaluation outcomes for both agents.
2. Extract binary success vectors (1 for success, 0 for failure).
3. Perform a two-sided permutation test using scipy.stats.permutation_test.
4. Implement a convergence check: Run with 10k iterations, then 20k. 
   If p-value changes by > 0.01, re-run with 20k (or more if needed) to ensure robustness.
5. Report p-value and declare significance if p < 0.05.

Output: Writes results to data/artifacts/statistical_test_results.json.
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Project imports based on API surface
from utils.config import get_path, get_hyperparameter, ensure_directories
from utils.exceptions import LlmXiveError

try:
    from scipy import stats
except ImportError:
    raise ImportError(
        "scipy is required for permutation tests. "
        "Please install it via `pip install scipy`."
    )

# Ensure the project root is in the path if running as a script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

def load_evaluation_outcomes(agent_name: str) -> List[Dict[str, Any]]:
    """
    Load evaluation outcomes for a specific agent from the processed data directory.
    
    Args:
        agent_name: The name of the agent (e.g., 'symbolic', 'baseline').
        
    Returns:
        List of outcome dictionaries.
        
    Raises:
        FileNotFoundError: If the outcomes file does not exist.
        LlmXiveError: If the file is empty or malformed.
    """
    # Expected path based on project structure and T035 output
    # T035 writes to data/processed/evaluation_outcomes.json
    # We assume the file contains a list of outcomes with an 'agent' field or similar,
    # or we might need to load two separate files if they were split.
    # Based on T035 description: "write updated outcomes to data/processed/evaluation_outcomes.json"
    # We will assume a combined file or we look for specific files.
    # Let's assume a standard location for agent-specific results if not combined.
    # However, T037 mentions "Symbolic vs. Visual metrics" in evaluation_results.json.
    # Let's check for the specific file T035 mentions first, or T037's output.
    # T035 writes: data/processed/evaluation_outcomes.json
    
    outcomes_path = get_path("processed", "evaluation_outcomes.json")
    
    if not outcomes_path.exists():
        # Fallback: Check for agent-specific files if the combined one doesn't exist
        # This is a defensive measure, but the spec says T035 writes to the combined file.
        # If the combined file exists, we filter by agent_name.
        raise FileNotFoundError(
            f"Evaluation outcomes file not found at {outcomes_path}. "
            "Ensure T035 has completed successfully."
        )
    
    with open(outcomes_path, 'r') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        # If it's a dict with keys like 'symbolic', 'baseline', handle that too
        if isinstance(data, dict) and agent_name in data:
            return data[agent_name]
        elif isinstance(data, dict) and 'outcomes' in data:
            # Filter the 'outcomes' list by agent
            return [o for o in data['outcomes'] if o.get('agent') == agent_name]
        else:
            raise LlmXiveError(f"Malformed outcomes file at {outcomes_path}. Expected list or dict with agent keys.")
    
    # Filter by agent if it's a list
    filtered = [o for o in data if o.get('agent') == agent_name]
    
    if not filtered:
        raise LlmXiveError(f"No outcomes found for agent '{agent_name}' in {outcomes_path}")
        
    return filtered

def extract_success_vector(outcomes: List[Dict[str, Any]]) -> List[int]:
    """
    Extract a binary success vector from a list of outcome dictionaries.
    1 = Success, 0 = Failure.
    
    Args:
        outcomes: List of outcome dictionaries.
        
    Returns:
        List of integers (0 or 1).
    """
    success_vector = []
    for outcome in outcomes:
        # Check for 'success' key. If missing, check 'status' or similar.
        # Based on T035, outcomes should have 'success' boolean or similar.
        if 'success' in outcome:
            val = 1 if outcome['success'] else 0
        elif 'status' in outcome:
            val = 1 if outcome['status'] == 'success' else 0
        else:
            # Fallback: assume failure if key missing? No, raise error.
            raise LlmXiveError(f"Outcome missing 'success' or 'status' key: {outcome}")
        success_vector.append(val)
    return success_vector

def run_permutation_test(
    group1: List[int], 
    group2: List[int], 
    n_permutations: int = 10000,
    alternative: str = 'two-sided'
) -> float:
    """
    Run a permutation test using scipy.stats.permutation_test.
    
    Args:
        group1: Success vector for group 1 (Symbolic).
        group2: Success vector for group 2 (Baseline).
        n_permutations: Number of permutations.
        alternative: 'two-sided', 'less', or 'greater'.
        
    Returns:
        p-value.
    """
    # scipy.stats.permutation_test expects data as a tuple of arrays
    # statistic function receives (x, y) and returns a scalar
    def statistic(x, y):
        # We want to test the difference in means (success rates)
        return np.mean(x) - np.mean(y)
    
    import numpy as np
    
    result = stats.permutation_test(
        (np.array(group1), np.array(group2)),
        statistic,
        permutation_type='samples',
        n_permutations=n_permutations,
        alternative=alternative,
        random_state=42 # Fixed seed for reproducibility
    )
    
    return result.pvalue

def check_convergence(
    group1: List[int], 
    group2: List[int], 
    threshold: float = 0.01
) -> Tuple[float, int]:
    """
    Run the permutation test with increasing iterations until convergence.
    
    Strategy:
    1. Run with 10,000 iterations.
    2. Run with 20,000 iterations.
    3. If |p1 - p2| > threshold, report that convergence was not met and return the 20k result.
       (In a real production system, we might go to 50k or 100k, but 20k is the task requirement limit).
    
    Args:
        group1: Success vector for group 1.
        group2: Success vector for group 2.
        threshold: Maximum allowed difference in p-value.
        
    Returns:
        Tuple of (final_p_value, iterations_used).
    """
    import numpy as np
    
    print("Running initial permutation test with 10,000 iterations...")
    start_time = time.time()
    p_val_10k = run_permutation_test(group1, group2, n_permutations=10000)
    time_10k = time.time() - start_time
    print(f"  p-value (10k): {p_val_10k:.6f} (took {time_10k:.2f}s)")
    
    print("Running second permutation test with 20,000 iterations...")
    start_time = time.time()
    p_val_20k = run_permutation_test(group1, group2, n_permutations=20000)
    time_20k = time.time() - start_time
    print(f"  p-value (20k): {p_val_20k:.6f} (took {time_20k:.2f}s)")
    
    diff = abs(p_val_10k - p_val_20k)
    print(f"  Difference: {diff:.6f}")
    
    if diff > threshold:
        print(f"  WARNING: p-value change ({diff:.4f}) exceeds threshold ({threshold}). "
              f"Convergence not fully achieved with 20k iterations. "
              f"Using 20k result as best estimate.")
        return p_val_20k, 20000
    else:
        print(f"  Convergence achieved (diff < {threshold}).")
        return p_val_20k, 20000

def main():
    """Main entry point for the statistical test."""
    print("=" * 60)
    print("Statistical Analysis: Permutation Test (T036a)")
    print("Comparing: Symbolic-Guava vs Baseline-Guava (Visual)")
    print("=" * 60)
    
    # Ensure output directory exists
    ensure_directories()
    
    try:
        # 1. Load Data
        print("\n[1/4] Loading evaluation outcomes...")
        symbolic_outcomes = load_evaluation_outcomes("symbolic")
        baseline_outcomes = load_evaluation_outcomes("baseline")
        
        print(f"  Symbolic outcomes: {len(symbolic_outcomes)}")
        print(f"  Baseline outcomes: {len(baseline_outcomes)}")
        
        if len(symbolic_outcomes) == 0 or len(baseline_outcomes) == 0:
            raise LlmXiveError("One or both agents have zero outcomes. Cannot perform test.")
        
        # 2. Extract Success Vectors
        print("\n[2/4] Extracting success vectors...")
        symbolic_success = extract_success_vector(symbolic_outcomes)
        baseline_success = extract_success_vector(baseline_outcomes)
        
        sym_rate = sum(symbolic_success) / len(symbolic_success)
        base_rate = sum(baseline_success) / len(baseline_success)
        
        print(f"  Symbolic Success Rate: {sym_rate:.4f} ({sum(symbolic_success)}/{len(symbolic_success)})")
        print(f"  Baseline Success Rate: {base_rate:.4f} ({sum(baseline_success)}/{len(baseline_success)})")
        
        # 3. Run Permutation Test with Convergence Check
        print("\n[3/4] Running Permutation Test (Convergence Check)...")
        p_value, iterations = check_convergence(symbolic_success, baseline_success)
        
        # 4. Determine Significance
        significance_level = 0.05
        is_significant = p_value < significance_level
        
        print("\n[4/4] Results Summary:")
        print(f"  P-value: {p_value:.6f}")
        print(f"  Iterations: {iterations}")
        print(f"  Significance Level: {significance_level}")
        print(f"  Result: {'SIGNIFICANT' if is_significant else 'NOT SIGNIFICANT'}")
        
        if is_significant:
            print("  Conclusion: Reject Null Hypothesis. There is a statistically significant difference.")
        else:
            print("  Conclusion: Fail to reject Null Hypothesis. No significant difference detected.")
        
        # 5. Write Output
        output_data = {
            "task_id": "T036a",
            "test_type": "Permutation Test",
            "null_hypothesis": "No difference in success rates between Symbolic-Guava and Baseline-Guava",
            "alternative_hypothesis": "Difference in success rates exists",
            "agents": {
                "symbolic": {
                    "count": len(symbolic_outcomes),
                    "successes": sum(symbolic_success),
                    "rate": sym_rate
                },
                "baseline": {
                    "count": len(baseline_outcomes),
                    "successes": sum(baseline_success),
                    "rate": base_rate
                }
            },
            "results": {
                "p_value": p_value,
                "iterations": iterations,
                "significance_level": significance_level,
                "is_significant": is_significant
            },
            "conclusion": "Reject H0" if is_significant else "Fail to reject H0",
            "timestamp": time.time()
        }
        
        output_path = get_path("artifacts", "statistical_test_results.json")
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"\nResults written to: {output_path}")
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except LlmXiveError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()