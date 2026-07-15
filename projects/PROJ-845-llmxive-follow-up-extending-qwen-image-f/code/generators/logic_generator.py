import hashlib
import random
from typing import List, Dict, Any, Tuple, Optional
from models.synthetic_problem import SyntheticProblem
from config import Config
from utils.logger import get_logger

logger = get_logger(__name__)

# Simple propositional logic templates
TEMPLATES_PROP = [
    ("If A then B", "A", "B", ["imp", "var"]),
    ("A and B", "A", "B", ["and", "var"]),
    ("A or B", "A", "B", ["or", "var"]),
    ("Not A", "A", "Not A", ["not", "var"]),
    ("A implies B, A, therefore B", "A", "B", ["imp", "var", "mp"]),
]

def generate_propositional_problem(entropy_level: str, seed: int) -> SyntheticProblem:
    """
    Generate a single propositional logic problem.
    """
    random.seed(seed)
    template = random.choice(TEMPLATES_PROP)
    
    premises = [template[0]]
    solution = template[2] if len(template) > 2 else "Unknown"
    operators = template[3]
    
    # Adjust entropy by complexity (simulated)
    if entropy_level == "high":
        premises.append("C is true")
        operators.append("var")
    elif entropy_level == "low":
        premises = [template[0]]
        operators = [template[3][0]]
    
    problem_id = hashlib.md5(f"{seed}{template[0]}".encode()).hexdigest()[:8]
    
    return SyntheticProblem(
        id=problem_id,
        premises=premises,
        operators=operators,
        solution=solution,
        entropy_level=entropy_level,
        metadata={"seed": seed, "template": template[0]}
    )

def generate_arithmetic_problem(entropy_level: str, seed: int) -> SyntheticProblem:
    """
    Generate a simple arithmetic problem.
    """
    random.seed(seed)
    a = random.randint(1, 10)
    b = random.randint(1, 10)
    op = random.choice(["+", "-", "*"])
    
    if op == "+":
        res = a + b
    elif op == "-":
        res = a - b
    else:
        res = a * b
    
    premises = [f"{a} {op} {b} = ?"]
    solution = str(res)
    operators = [op]
    
    problem_id = hashlib.md5(f"{seed}{a}{op}{b}".encode()).hexdigest()[:8]
    
    return SyntheticProblem(
        id=problem_id,
        premises=premises,
        operators=operators,
        solution=solution,
        entropy_level=entropy_level,
        metadata={"seed": seed, "a": a, "b": b, "op": op}
    )

def generate_dataset_batch(
    count: int,
    entropy_level: str,
    seed: int
) -> List[SyntheticProblem]:
    """
    Generate a batch of problems with a specific entropy level.
    """
    problems = []
    for i in range(count):
        # Alternate between logic and arithmetic
        if i % 2 == 0:
            p = generate_propositional_problem(entropy_level, seed + i)
        else:
            p = generate_arithmetic_problem(entropy_level, seed + i)
        problems.append(p)
    
    logger.info(f"Generated {len(problems)} problems with entropy level: {entropy_level}")
    return problems
