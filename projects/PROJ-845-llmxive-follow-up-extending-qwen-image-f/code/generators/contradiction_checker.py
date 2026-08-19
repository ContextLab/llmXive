"""
Contradiction Checker Module for T014 and T016.
Implements solvability checks (SAT-lite) for generated problems.
"""
import hashlib
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict

# Add project root to path
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models.synthetic_problem import SyntheticProblem
from utils.logger import get_logger

logger = get_logger(__name__)

def is_problem_solvable(problem: SyntheticProblem) -> bool:
    """
    Perform a lightweight solvability check.
    For propositional logic, we check for immediate contradictions 
    like "A" and "NOT A" in premises that make the solution impossible 
    or trivially false in a specific context.
    
    Since we are generating synthetic data, we assume most generated 
    problems are solvable by design, but we filter out obvious 
    structural contradictions (e.g., premises imply NOT solution).
    
    Returns True if the problem is considered solvable.
    """
    # Simple heuristic: check if solution is directly negated by a single premise
    # e.g., Premises: ["NOT A"], Solution: "A" -> Unsolvable (contradiction)
    premises_set = set(problem.premises)
    solution = problem.solution
    
    # Check for direct negation
    neg_solution = f"NOT {solution}"
    if neg_solution in premises_set:
        return False
    
    # Check for double negation that simplifies to contradiction (advanced check)
    # For this MVP, we stick to the direct check to avoid complex SAT solving overhead.
    # In a real scenario, we'd use a library like python-sat or z3.
    
    # Ensure at least one premise exists
    if not problem.premises:
        return False

    return True

def filter_contradictions(problems: List[SyntheticProblem]) -> List[SyntheticProblem]:
    """
    Filter a list of problems, keeping only those that are solvable.
    """
    solvable = []
    for p in problems:
        if is_problem_solvable(p):
            solvable.append(p)
        else:
            logger.debug(f"Filtered out unsolvable problem: {p.id}")
    return solvable

def verify_solution_consistency(problem: SyntheticProblem) -> bool:
    """
    Verify that the solution is consistent with the premises 
    (simplified check).
    """
    return is_problem_solvable(problem)
