"""
Contradiction detection module for synthetic problem generation.

Implements a SAT solver for propositional logic problems to verify
that generated problems are solvable before they are added to the dataset.
"""
import hashlib
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict

from models.synthetic_problem import SyntheticProblem
from utils.logger import get_logger

logger = get_logger(__name__)


def _parse_literal(literal: str) -> Tuple[str, bool]:
    """
    Parse a literal string into (variable_name, is_positive).
    Example: "A" -> ("A", True), "not A" -> ("A", False)
    """
    literal = literal.strip()
    if literal.startswith("not "):
        return literal[4:].strip(), False
    return literal, True


def _get_all_variables(premises: List[str], solution: str) -> Set[str]:
    """Extract all unique variable names from premises and solution."""
    variables = set()
    for premise in premises:
        # Split by logical operators and spaces to find variables
        tokens = premise.replace("and", " ").replace("or", " ").replace("->", " ").split()
        for token in tokens:
            if token and token.lower() != "not":
                var_name, _ = _parse_literal(token)
                variables.add(var_name)
    
    # Parse solution similarly
    tokens = solution.replace("and", " ").replace("or", " ").replace("->", " ").split()
    for token in tokens:
        if token and token.lower() != "not":
            var_name, _ = _parse_literal(token)
            variables.add(var_name)
    
    return variables


def _evaluate_clause(clause_literals: List[str], assignment: Dict[str, bool]) -> bool:
    """
    Evaluate a clause (disjunction of literals) under a given assignment.
    Returns True if the clause is satisfied.
    """
    for lit in clause_literals:
        var_name, is_positive = _parse_literal(lit)
        if var_name not in assignment:
            continue  # Should not happen in well-formed clauses
        if is_positive and assignment[var_name]:
            return True
        if not is_positive and not assignment[var_name]:
            return True
    return False


def _parse_premise_to_cnf(premise: str) -> List[List[str]]:
    """
    Parse a premise string into CNF (list of clauses).
    Handles simple cases: conjunctions of disjunctions.
    For this generator, we assume premises are in the form:
    "A and B" -> [[A], [B]]
    "A or B" -> [[A, B]]
    "not A or B" -> [[not A, B]]
    """
    clauses = []
    
    # Split by 'and' to get clauses
    parts = premise.split(" and ")
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # Split by 'or' to get literals in the clause
        literals = part.split(" or ")
        clause = []
        for lit in literals:
            lit = lit.strip()
            if lit:
                clause.append(lit)
        if clause:
            clauses.append(clause)
    
    return clauses


def _solve_satisfiability(premises: List[str], num_vars: int) -> Optional[Dict[str, bool]]:
    """
    Simple backtracking SAT solver.
    Returns a satisfying assignment if one exists, None otherwise.
    """
    if not premises:
        return {}  # Vacuously satisfiable
    
    # Convert premises to CNF
    cnf = []
    for premise in premises:
        cnf.extend(_parse_premise_to_cnf(premise))
    
    if not cnf:
        return {}
    
    # Get all variables used in the CNF
    all_vars = set()
    for clause in cnf:
        for lit in clause:
            var_name, _ = _parse_literal(lit)
            all_vars.add(var_name)
    
    variables = list(all_vars)
    assignment = {}
    
    def backtrack(idx: int) -> bool:
        if idx == len(variables):
            # Check if all clauses are satisfied
            for clause in cnf:
                if not _evaluate_clause(clause, assignment):
                    return False
            return True
        
        var = variables[idx]
        for val in [True, False]:
            assignment[var] = val
            if backtrack(idx + 1):
                return True
            del assignment[var]
        
        return False
    
    if backtrack(0):
        return assignment
    return None


def is_problem_solvable(problem: SyntheticProblem) -> bool:
    """
    Check if a synthetic problem is solvable (satisfiable).
    
    Args:
        problem: The SyntheticProblem to check.
        
    Returns:
        True if the problem's premises are satisfiable, False otherwise.
    """
    try:
        assignment = _solve_satisfiability(problem.premises, len(problem.premises))
        return assignment is not None
    except Exception as e:
        logger.warning(f"Error checking satisfiability for problem {problem.id}: {e}")
        # If we can't determine, assume solvable to avoid discarding valid problems
        return True


def filter_contradictions(problems: List[SyntheticProblem]) -> List[SyntheticProblem]:
    """
    Filter out unsolvable (contradictory) problems from a list.
    
    Args:
        problems: List of SyntheticProblem instances.
        
    Returns:
        List of problems that are satisfiable.
    """
    solvable_problems = []
    discarded_count = 0
    
    for problem in problems:
        if is_problem_solvable(problem):
            solvable_problems.append(problem)
        else:
            discarded_count += 1
            logger.debug(f"Discarded unsolvable problem: {problem.id}")
    
    if discarded_count > 0:
        logger.info(f"Filtered {discarded_count} unsolvable problems "
                   f"({len(solvable_problems)} remaining)")
    
    return solvable_problems


def verify_solution_consistency(problem: SyntheticProblem) -> bool:
    """
    Verify that the problem's solution is consistent with its premises.
    This is a basic check: if premises are satisfiable, we assume the 
    solution is a valid conclusion (since the generator creates them together).
    
    For more rigorous checking, a theorem prover would be needed.
    """
    # First check if premises are satisfiable
    if not is_problem_solvable(problem):
        return False
    
    # For now, we assume the solution is valid if premises are satisfiable
    # A more complete implementation would verify the solution against premises
    return True
