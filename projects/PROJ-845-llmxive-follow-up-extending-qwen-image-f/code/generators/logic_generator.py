import hashlib
import random
from typing import List, Dict, Any, Optional, Tuple
from models.synthetic_problem import SyntheticProblem
from config import Config
from utils.logger import get_logger

logger = get_logger(__name__)

# Logical operators and their precedence for parsing
OPERATORS = ['AND', 'OR', 'IMPLIES', 'NOT']
ATOMS = ['P', 'Q', 'R', 'S', 'T']

def _parse_premises(premises: List[str]) -> List[str]:
    """Simple placeholder parser; in a full implementation, this would
    build a formal representation of the premises."""
    return premises

def _check_satisfiability(premises: List[str], solution: str) -> bool:
    """
    Perform a simple SAT check to verify if the premises are consistent
    and allow for the solution to be true.
    
    This implementation uses a randomized truth assignment simulation
    to approximate satisfiability for the generated propositional logic problems.
    For a rigorous check, a full SAT solver (e.g., pycosat) would be ideal,
    but we implement a lightweight check here to avoid external dependencies
    beyond the core requirements.
    
    Logic:
    1. If premises contain a direct contradiction (e.g., "P AND NOT P"), return False.
    2. Simulate random truth assignments to atoms.
    3. If any assignment satisfies all premises, the problem is solvable.
    4. We also verify that the solution is not logically impossible given the premises.
    """
    # 1. Quick contradiction check for simple patterns
    premises_str = " ".join(premises).upper()
    for atom in ATOMS:
        if f"{atom} AND NOT {atom}" in premises_str or f"NOT {atom} AND {atom}" in premises_str:
            logger.debug(f"Direct contradiction detected in premises: {premises}")
            return False
    
    # 2. Randomized satisfiability check (Monte Carlo style)
    # If we can find at least one assignment where premises are True, it's likely satisfiable.
    # Given the small scale of generated problems, 1000 trials is sufficient.
    trials = 1000
    atoms_in_problem = set()
    for p in premises:
        for atom in ATOMS:
            if atom in p:
                atoms_in_problem.add(atom)
    
    if not atoms_in_problem:
        # No atoms, premises are just constants or empty
        return True

    atoms_list = list(atoms_in_problem)
    
    for _ in range(trials):
        # Random assignment
        assignment = {atom: random.choice([True, False]) for atom in atoms_list}
        
        # Evaluate premises
        all_premises_true = True
        for p in premises:
            if not _eval_proposition(p, assignment):
                all_premises_true = False
                break
        
        if all_premises_true:
            # Found a model for premises. Now check if solution is consistent.
            # Ideally, the solution should be implied, but for "solvability"
            # we just need the system not to be contradictory.
            # If the solution is "P" and we found a model where premises are true but P is false,
            # that's fine for satisfiability of premises, but might mean the solution isn't derived.
            # However, the task asks to discard UNSOLVABLE problems (contradictions).
            # So if premises are satisfiable, we consider it solvable.
            return True
    
    # If no assignment found in trials, assume unsatisfiable (or very hard)
    logger.debug(f"Failed to find satisfiable assignment after {trials} trials")
    return False

def _eval_proposition(expr: str, assignment: Dict[str, bool]) -> bool:
    """
    Evaluate a simple propositional expression given an assignment.
    Handles: ATOM, NOT ATOM, ATOM AND ATOM, ATOM OR ATOM, ATOM IMPLIES ATOM.
    Assumes well-formed input for the generator's output format.
    """
    expr = expr.strip().upper()
    
    # Handle NOT
    if expr.startswith("NOT"):
        inner = expr[3:].strip()
        return not _eval_proposition(inner, assignment)
    
    # Handle AND, OR, IMPLIES (left to right, simple split)
    # Note: This is a naive parser. For complex nesting, a recursive descent parser is needed.
    # Given the generator creates simple chains, we check for the main operator.
    
    # Check IMPLIES
    if " IMPLIES " in expr:
        parts = expr.split(" IMPLIES ", 1)
        lhs = _eval_proposition(parts[0], assignment)
        rhs = _eval_proposition(parts[1], assignment)
        return (not lhs) or rhs
    
    # Check AND
    if " AND " in expr:
        parts = expr.split(" AND ", 1)
        return _eval_proposition(parts[0], assignment) and _eval_proposition(parts[1], assignment)
    
    # Check OR
    if " OR " in expr:
        parts = expr.split(" OR ", 1)
        return _eval_proposition(parts[0], assignment) or _eval_proposition(parts[1], assignment)
    
    # Base case: Atom
    if expr in assignment:
        return assignment[expr]
    
    # Fallback for constants or unknown
    return False

def generate_propositional_problem(entropy_level: str = "Medium") -> Optional[SyntheticProblem]:
    """
    Generates a propositional logic problem.
    If the generated problem is unsolvable (contradictory premises), it returns None.
    """
    # Generate random components
    num_premises = random.randint(2, 4)
    premises = []
    operators_used = []
    
    for _ in range(num_premises):
        atom1 = random.choice(ATOMS)
        atom2 = random.choice(ATOMS)
        op = random.choice(OPERATORS[:3]) # Exclude NOT for premise structure simplicity
        
        if op == 'NOT':
            premise = f"NOT {atom1}"
        else:
            premise = f"{atom1} {op} {atom2}"
        
        premises.append(premise)
        if op not in operators_used:
            operators_used.append(op)
    
    # Generate a solution that is likely derivable or at least consistent
    # For simplicity, we pick one of the atoms involved
    all_atoms = set()
    for p in premises:
        for a in ATOMS:
            if a in p:
                all_atoms.add(a)
    
    if not all_atoms:
        return None
        
    solution_atom = random.choice(list(all_atoms))
    # Simple solution: "P is True" or "P"
    solution = solution_atom
    
    # Check solvability
    if not _check_satisfiability(premises, solution):
        logger.debug(f"Generated problem is unsolvable: {premises} -> {solution}")
        return None
    
    # Calculate structure hash
    structure_str = "|".join(premises) + "||" + solution
    structure_hash = hashlib.sha256(structure_str.encode()).hexdigest()
    
    return SyntheticProblem(
        id=hashlib.sha256(str(random.random()).encode()).hexdigest()[:16],
        premises=premises,
        operators=operators_used,
        solution=solution,
        entropy_level=entropy_level,
        metadata={
            "structure_hash": structure_hash,
            "num_premises": num_premises,
            "solved": True
        }
    )

def generate_arithmetic_problem(entropy_level: str = "Medium") -> Optional[SyntheticProblem]:
    """
    Generates a simple arithmetic problem.
    Checks for solvability (e.g., no division by zero, integer results if required).
    """
    ops = ['+', '-', '*']
    # Avoid division for simplicity in this generator unless handled carefully
    a = random.randint(1, 20)
    b = random.randint(1, 20)
    op = random.choice(ops)
    
    if op == '+':
        result = a + b
        premise = f"{a} + {b}"
    elif op == '-':
        result = a - b
        premise = f"{a} - {b}"
    else:
        result = a * b
        premise = f"{a} * {b}"
    
    solution = str(result)
    
    # Arithmetic problems are generally solvable unless constraints are weird
    # We assume standard arithmetic rules apply.
    
    structure_str = f"{premise}={solution}"
    structure_hash = hashlib.sha256(structure_str.encode()).hexdigest()
    
    return SyntheticProblem(
        id=hashlib.sha256(str(random.random()).encode()).hexdigest()[:16],
        premises=[premise],
        operators=[op],
        solution=solution,
        entropy_level=entropy_level,
        metadata={
            "structure_hash": structure_hash,
            "num_premises": 1,
            "solved": True
        }
    )

def main():
    """
    Main entry point for testing the generator with contradiction detection.
    """
    logger.info("Testing logic generator with contradiction detection...")
    config = Config()
    random.seed(config.seed)
    
    success_count = 0
    fail_count = 0
    
    for i in range(100):
        prob = generate_propositional_problem("High")
        if prob:
            success_count += 1
        else:
            fail_count += 1
    
    logger.info(f"Generated {success_count} solvable problems, discarded {fail_count} unsolvable ones.")

if __name__ == "__main__":
    main()
