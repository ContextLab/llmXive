"""
Logic Generator Module for llmXive Project.
Implements generation of propositional and arithmetic logic problems with controlled entropy.
"""

import hashlib
import random
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import asdict

from models.synthetic_problem import SyntheticProblem
from config import Config, get_config
from utils.logger import get_logger

logger = get_logger(__name__)

# Constants for problem generation
LOGIC_OPERATORS = ['AND', 'OR', 'IMPLIES', 'IFF']
ARITHMETIC_OPERATORS = ['+', '-', '*', '//']
ARITHMETIC_PATTERNS = [
    "If {p1} is true and {p2} is false, what is the result of {val1} {op} {val2}?",
    "Given {val1} {op} {val2} = {res}, determine the truth of {p1} {op_logic} {p2}.",
    "Calculate {val1} {op} {val2} assuming {p1} implies {p2}."
]
LOGIC_PATTERNS = [
    "Premise: {p1}. Premise: {p2}. Operator: {op}. What is the solution?",
    "Given {p1} {op} {p2}, determine the truth value.",
    "If {p1} and {p2} hold, does {op} apply?"
]

def generate_propositional_problem(seed: Optional[int] = None) -> SyntheticProblem:
    """
    Generates a valid propositional logic problem with randomized premises and operators.
    
    Args:
        seed: Optional seed for reproducibility within this call.
        
    Returns:
        SyntheticProblem instance with randomized premises, operators, and a solution.
    """
    if seed is not None:
        random.seed(seed)
    
    config = get_config()
    # Use config seed if not provided
    effective_seed = seed if seed is not None else config.seed
    random.seed(effective_seed)

    # Generate random premises (simple boolean statements)
    premise_templates = [
        "The sky is blue",
        "Grass is green",
        "The sun is hot",
        "Water is wet",
        "Fire is warm",
        "Ice is cold",
        "Snow is white",
        "The moon is bright"
    ]
    
    # Select 2 random premises
    p1 = random.choice(premise_templates)
    p2 = random.choice([p for p in premise_templates if p != p1])
    
    # Select a random operator
    op = random.choice(LOGIC_OPERATORS)
    
    # Generate solution based on logic
    # For simplicity, we map operators to a deterministic string representation
    # In a full implementation, this would involve a SAT solver or truth table
    solution_map = {
        'AND': 'Both premises must be true.',
        'OR': 'At least one premise must be true.',
        'IMPLIES': 'If the first is true, the second must be true.',
        'IFF': 'Both premises must have the same truth value.'
    }
    solution = solution_map[op]
    
    # Assign entropy level based on randomness (placeholder logic, refined in T012)
    entropy_level = random.choice(['High', 'Low', 'Target'])

    problem = SyntheticProblem(
        id=f"prop_{random.randint(10000, 99999)}",
        premises=[p1, p2],
        operators=[op],
        solution=solution,
        entropy_level=entropy_level,
        metadata={
            "type": "propositional",
            "seed": effective_seed
        }
    )
    
    return problem

def generate_arithmetic_problem(seed: Optional[int] = None) -> SyntheticProblem:
    """
    Generates a valid arithmetic word problem with randomized operands and operators.
    
    Args:
        seed: Optional seed for reproducibility.
        
    Returns:
        SyntheticProblem instance representing an arithmetic problem.
    """
    if seed is not None:
        random.seed(seed)
    
    config = get_config()
    effective_seed = seed if seed is not None else config.seed
    random.seed(effective_seed)

    # Generate random numbers
    val1 = random.randint(1, 100)
    val2 = random.randint(1, 50)
    op = random.choice(ARITHMETIC_OPERATORS)
    
    # Calculate result to ensure validity
    if op == '//':
        # Avoid division by zero and ensure integer result
        val2 = random.randint(1, 20)
        res = val1 // val2
    elif op == '*':
        res = val1 * val2
    elif op == '+':
        res = val1 + val2
    elif op == '-':
        res = val1 - val2
        
    # Construct problem statement
    pattern = random.choice(ARITHMETIC_PATTERNS)
    problem_text = pattern.format(
        p1="The first number is valid",
        p2="The second number is valid",
        val1=val1,
        val2=val2,
        op=op,
        res=res,
        op_logic="AND"
    )
    
    solution = f"The result is {res}."
    entropy_level = random.choice(['High', 'Low', 'Target'])

    problem = SyntheticProblem(
        id=f"arith_{random.randint(10000, 99999)}",
        premises=[f"{val1} {op} {val2}"],
        operators=[op],
        solution=solution,
        entropy_level=entropy_level,
        metadata={
            "type": "arithmetic",
            "operand1": val1,
            "operand2": val2,
            "result": res,
            "seed": effective_seed
        }
    )
    
    return problem

def generate_dataset_batch(
    count: int, 
    problem_type: str = 'propositional',
    seed: Optional[int] = None
) -> List[SyntheticProblem]:
    """
    Generates a batch of logic problems.
    
    Args:
        count: Number of problems to generate.
        problem_type: 'propositional' or 'arithmetic'.
        seed: Base seed for the batch.
        
    Returns:
        List of SyntheticProblem instances.
    """
    if seed is None:
        seed = get_config().seed
        
    problems = []
    for i in range(count):
        # Increment seed slightly to ensure variety while maintaining reproducibility
        current_seed = seed + i
        
        if problem_type == 'propositional':
            prob = generate_propositional_problem(seed=current_seed)
        elif problem_type == 'arithmetic':
            prob = generate_arithmetic_problem(seed=current_seed)
        else:
            raise ValueError(f"Unknown problem type: {problem_type}")
        
        problems.append(prob)
        
    return problems

def compute_structure_hash(problem: SyntheticProblem) -> str:
    """
    Computes a deterministic hash of the problem's logical structure.
    Used for ensuring distinctness between training and test sets.
    
    Args:
        problem: The SyntheticProblem instance.
        
    Returns:
        SHA256 hash string of the canonical structure representation.
    """
    # Canonical representation: sorted premises + sorted operators
    canonical_str = f"{sorted(problem.premises)}|{sorted(problem.operators)}"
    return hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()

def main():
    """
    Entry point for testing the logic generator directly.
    """
    config = get_config()
    logger.info(f"Starting Logic Generator with seed: {config.seed}")
    
    # Generate a sample propositional problem
    prop_prob = generate_propositional_problem()
    logger.info(f"Generated Propositional Problem: {prop_prob.id}")
    logger.info(f"  Premises: {prop_prob.premises}")
    logger.info(f"  Operator: {prop_prob.operators}")
    logger.info(f"  Solution: {prop_prob.solution}")
    
    # Generate a sample arithmetic problem
    arith_prob = generate_arithmetic_problem()
    logger.info(f"Generated Arithmetic Problem: {arith_prob.id}")
    logger.info(f"  Premises: {arith_prob.premises}")
    logger.info(f"  Operator: {arith_prob.operators}")
    logger.info(f"  Solution: {arith_prob.solution}")
    
    # Test batch generation
    batch = generate_dataset_batch(5, problem_type='propositional')
    logger.info(f"Generated batch of {len(batch)} problems.")
    
    # Test structure hash
    h = compute_structure_hash(prop_prob)
    logger.info(f"Structure hash for {prop_prob.id}: {h}")

if __name__ == "__main__":
    main()