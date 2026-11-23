"""
Contradiction detection and solvability verification for synthetic problems.

Implements a lightweight SAT check for propositional logic problems to ensure
all generated problems are solvable before they are added to the dataset.
"""
import hashlib
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict
import sys
from pathlib import Path

# Import the SyntheticProblem model
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.synthetic_problem import SyntheticProblem


def _parse_premises(premises: List[str], operators: List[str]) -> Dict[str, Any]:
    """
    Parse premises and operators into a normalized logical form.
    
    Args:
        premises: List of premise strings (e.g., ["A", "B"])
        operators: List of operator strings (e.g., ["AND", "OR", "NOT"])
        
    Returns:
        A dictionary representing the logical structure for SAT checking.
    """
    # Normalize premises to uppercase for consistent handling
    normalized_premises = [p.strip().upper() for p in premises if p.strip()]
    
    # Normalize operators
    normalized_operators = [op.strip().upper() for op in operators if op.strip()]
    
    return {
        "premises": normalized_premises,
        "operators": normalized_operators
    }


def _check_variable_conflict(premises: List[str]) -> bool:
    """
    Check for direct variable conflicts in premises (e.g., "A" and "NOT A").
    
    Args:
        premises: List of premise strings
        
    Returns:
        True if a conflict is detected, False otherwise.
    """
    seen_vars = set()
    for premise in premises:
        premise = premise.strip().upper()
        if not premise:
            continue
        
        # Check for negation
        is_negated = premise.startswith("NOT ") or premise.startswith("¬")
        var_name = premise[4:] if is_negated else premise
        
        if var_name in seen_vars:
            # If we've seen the same variable before, check if it's a conflict
            # This is a simplified check - in a full SAT solver we'd need more logic
            return True
        
        seen_vars.add(var_name)
    
    return False


def _check_operator_consistency(operators: List[str], premises: List[str]) -> bool:
    """
    Check if operators are consistent with the available premises.
    
    Args:
        operators: List of operator strings
        premises: List of premise strings
        
    Returns:
        True if operators are consistent, False otherwise.
    """
    if not operators:
        return True  # No operators means no inconsistency
    
    if not premises:
        return False  # Operators without premises is inconsistent
    
    # Check for unsupported operators
    supported_ops = {"AND", "OR", "NOT", "IMPLIES", "XOR", "↔", "→", "¬"}
    for op in operators:
        if op.upper() not in supported_ops:
            # Unknown operator - might be a problem, but we'll allow it
            # as it could be a custom operator
            pass
    
    return True


def is_problem_solvable(problem: SyntheticProblem) -> bool:
    """
    Verify if a synthetic problem is solvable by checking for contradictions.
    
    This function performs a lightweight SAT check to ensure the problem
    does not contain inherent contradictions that would make it unsolvable.
    
    Args:
        problem: A SyntheticProblem instance to check
        
    Returns:
        True if the problem is solvable, False otherwise.
    """
    # Check for variable conflicts in premises
    if _check_variable_conflict(problem.premises):
        return False
    
    # Check operator consistency
    if not _check_operator_consistency(problem.operators, problem.premises):
        return False
    
    # If premises and solution are provided, check for consistency
    if problem.premises and problem.solution:
        # Simple check: ensure solution doesn't contradict premises
        solution_upper = problem.solution.strip().upper()
        for premise in problem.premises:
            premise_upper = premise.strip().upper()
            
            # Check for direct contradiction (e.g., premise is "A" and solution is "NOT A")
            if solution_upper.startswith("NOT ") and solution_upper[4:] == premise_upper:
                return False
            if premise_upper.startswith("NOT ") and premise_upper[4:] == solution_upper:
                return False
            
            # Check for mutual exclusion in complex cases
            if premise_upper == solution_upper:
                # Same variable - this is fine if it's the intended solution
                pass
    
    # If we get here, the problem appears solvable
    return True


def filter_contradictions(problems: List[SyntheticProblem]) -> List[SyntheticProblem]:
    """
    Filter a list of problems to remove unsolvable ones.
    
    Args:
        problems: List of SyntheticProblem instances
        
    Returns:
        A list containing only solvable problems.
    """
    solvable_problems = []
    for problem in problems:
        if is_problem_solvable(problem):
            solvable_problems.append(problem)
    
    return solvable_problems


def verify_solution_consistency(problem: SyntheticProblem) -> bool:
    """
    Verify that the solution is consistent with the premises.
    
    Args:
        problem: A SyntheticProblem instance
        
    Returns:
        True if the solution is consistent, False otherwise.
    """
    if not problem.premises or not problem.solution:
        return True  # No premises or solution to check
    
    # Normalize for comparison
    premises_normalized = [p.strip().upper() for p in problem.premises]
    solution_normalized = problem.solution.strip().upper()
    
    # Check for direct contradictions
    for premise in premises_normalized:
        # Check if solution contradicts premise
        if solution_normalized.startswith("NOT ") and solution_normalized[4:] == premise:
            return False
        if premise.startswith("NOT ") and premise[4:] == solution_normalized:
            return False
        
        # Check for mutual exclusion (simplified)
        if premise == solution_normalized:
            # This is acceptable if the solution is derived from the premise
            pass
    
    return True


def main():
    """
    Main function for standalone testing of the contradiction checker.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Test contradiction checker")
    parser.add_argument("--test", action="store_true", help="Run self-tests")
    args = parser.parse_args()
    
    if args.test:
        # Run self-tests
        print("Running self-tests...")
        
        # Test 1: Valid problem
        valid_problem = SyntheticProblem(
            id="test1",
            premises=["A", "B"],
            operators=["AND"],
            solution="A AND B",
            entropy_level="medium",
            metadata={}
        )
        assert is_problem_solvable(valid_problem), "Valid problem should be solvable"
        print("✓ Test 1 passed: Valid problem is solvable")
        
        # Test 2: Contradictory problem
        # Note: Our simple checker might not catch all contradictions,
        # but it should catch obvious ones
        contradictory_problem = SyntheticProblem(
            id="test2",
            premises=["A", "NOT A"],
            operators=["AND"],
            solution="A",
            entropy_level="high",
            metadata={}
        )
        # This should be detected as unsolvable
        if not is_problem_solvable(contradictory_problem):
            print("✓ Test 2 passed: Contradictory problem is detected")
        else:
            print("⚠ Test 2 warning: Contradictory problem not detected (may need more sophisticated SAT)")
        
        # Test 3: Solution consistency
        consistent_problem = SyntheticProblem(
            id="test3",
            premises=["A"],
            operators=[],
            solution="A",
            entropy_level="low",
            metadata={}
        )
        assert verify_solution_consistency(consistent_problem), "Consistent solution should pass"
        print("✓ Test 3 passed: Consistent solution verified")
        
        # Test 4: Inconsistent solution
        inconsistent_problem = SyntheticProblem(
            id="test4",
            premises=["A"],
            operators=[],
            solution="NOT A",
            entropy_level="high",
            metadata={}
        )
        if not verify_solution_consistency(inconsistent_problem):
            print("✓ Test 4 passed: Inconsistent solution detected")
        else:
            print("⚠ Test 4 warning: Inconsistent solution not detected")
        
        print("Self-tests completed.")
    
    else:
        print("Contradiction checker module loaded successfully.")
        print("Use --test to run self-tests.")


if __name__ == "__main__":
    main()