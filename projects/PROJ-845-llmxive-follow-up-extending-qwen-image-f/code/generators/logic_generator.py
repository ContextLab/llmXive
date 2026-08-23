"""
Logic Generator Module for llmXive.

Implements functions to generate propositional logic problems and arithmetic problems
with controlled entropy characteristics for the synthetic dataset.
"""
import hashlib
import random
from typing import List, Dict, Any, Tuple, Optional

from models.synthetic_problem import SyntheticProblem
from config import Config, get_config
from utils.logger import get_logger

logger = get_logger(__name__)

# Logical Connectives
CONNECTIVES = ['AND', 'OR', 'IMPLIES', 'IFF']
NEGATION = 'NOT'

# Arithmetic Operators
ARITHMETIC_OPS = ['+', '-', '*', '//']
COMPARATORS = ['==', '!=', '<', '>', '<=', '>=']

# Atomic proposition templates
ATOMIC_TEMPLATES = [
    "p_{}", "q_{}", "r_{}", "s_{}", "t_{}",
    "x_{}", "y_{}", "z_{}", "a_{}", "b_{}"
]

# Arithmetic variable templates
NUM_VAR_TEMPLATES = ["x_{}", "y_{}", "z_{}", "a_{}", "b_{}"]


def _get_config() -> Config:
    """Retrieve the global configuration."""
    return get_config()


def _compute_structure_hash(premises: List[str], operators: List[str]) -> str:
    """
    Compute a deterministic SHA256 hash of the logical structure.
    Used to ensure distinctness of problems.
    """
    # Canonicalize: sort premises and operators to ensure structural hash
    # is independent of generation order for the same structure,
    # but we want unique hashes for unique generation instances.
    # We hash the raw generated lists to preserve generation uniqueness.
    content = f"{premises}|{operators}"
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def _generate_atomic_proposition(index: int) -> str:
    """Generate a unique atomic proposition string."""
    template = random.choice(ATOMIC_TEMPLATES)
    return template.format(index)


def _generate_numeric_variable(index: int) -> str:
    """Generate a unique numeric variable string."""
    template = random.choice(NUM_VAR_TEMPLATES)
    return template.format(index)


def _generate_random_number() -> int:
    """Generate a random integer for arithmetic problems."""
    return random.randint(1, 100)


def generate_propositional_problem(
    entropy_level: str = "random",
    num_premises: Optional[int] = None
) -> SyntheticProblem:
    """
    Generates a single propositional logic problem.

    Args:
        entropy_level: 'high', 'low', or 'random'.
            - 'high': Randomized premises/operators, complex structure.
            - 'low': Structured, repetitive patterns (e.g., chains).
            - 'random': Selects 'high' or 'low' randomly.
        num_premises: Number of premises to generate. If None, uses config or random.

    Returns:
        A SyntheticProblem instance.
    """
    cfg = _get_config()
    random.seed(cfg.seed)  # Ensure local reproducibility within the call if needed

    # Determine effective entropy level
    if entropy_level == "random":
        entropy_level = random.choice(["high", "low"])

    if num_premises is None:
        num_premises = random.randint(2, 6)

    premises = []
    operators = []
    solution = ""

    if entropy_level == "low":
        # Low Entropy: Repetitive patterns (e.g., A, A->B, B->C...)
        # Chain of implications
        vars_list = [_generate_atomic_proposition(i) for i in range(num_premises + 1)]
        for i in range(num_premises):
            premises.append(f"{vars_list[i]}")
            if i < num_premises - 1:
                premises.append(f"{vars_list[i]} IMPLIES {vars_list[i+1]}")
                operators.append("IMPLIES")
            else:
                # Last premise is just the fact, or we stop
                pass
        
        # Simplify for low entropy: Just a chain of facts and implications
        # Example: p, p->q, q->r ...
        vars_list = [_generate_atomic_proposition(i) for i in range(num_premises + 1)]
        premises = [vars_list[0]] # Start with a fact
        operators = []
        for i in range(num_premises):
            if i < len(vars_list) - 1:
                premises.append(f"{vars_list[i]} IMPLIES {vars_list[i+1]}")
                operators.append("IMPLIES")
        
        # Solution is the last variable
        solution = vars_list[-1]

    else:
        # High Entropy: Randomized structure, mixed operators
        vars_list = [_generate_atomic_proposition(i) for i in range(num_premises * 2)]
        used_vars = []
        
        for i in range(num_premises):
            v1 = random.choice(vars_list)
            v2 = random.choice(vars_list)
            while v2 == v1:
                v2 = random.choice(vars_list)
            
            op = random.choice(CONNECTIVES)
            premise_str = f"({v1} {op} {v2})"
            premises.append(premise_str)
            operators.append(op)
        
        # Solution is a random variable from the set
        solution = random.choice(vars_list)

    structure_hash = _compute_structure_hash(premises, operators)

    problem = SyntheticProblem(
        id=f"prop_{structure_hash[:8]}_{random.randint(1000, 9999)}",
        premises=premises,
        operators=operators,
        solution=solution,
        entropy_level=entropy_level,
        metadata={
            "type": "propositional",
            "structure_hash": structure_hash,
            "num_premises": len(premises),
            "num_operators": len(operators),
            "seed": cfg.seed
        }
    )

    return problem


def generate_arithmetic_problem(
    entropy_level: str = "random",
    num_ops: Optional[int] = None
) -> SyntheticProblem:
    """
    Generates a single arithmetic problem.

    Args:
        entropy_level: 'high', 'low', or 'random'.
        num_ops: Number of operations.

    Returns:
        A SyntheticProblem instance.
    """
    cfg = _get_config()
    random.seed(cfg.seed)

    if entropy_level == "random":
        entropy_level = random.choice(["high", "low"])

    if num_ops is None:
        num_ops = random.randint(2, 5)

    premises = []
    operators = []
    solution = ""

    if entropy_level == "low":
        # Low Entropy: Simple linear sequence, same operator
        op = random.choice(ARITHMETIC_OPS)
        vars_list = [_generate_numeric_variable(i) for i in range(num_ops + 1)]
        
        # Assign random values to variables
        values = [random.randint(1, 10) for _ in vars_list]
        
        # Premises: Define variables
        for i, (v, val) in enumerate(zip(vars_list, values)):
            premises.append(f"{v} = {val}")
            operators.append("=") # Metadata operator

        # Chain of operations
        current_expr = vars_list[0]
        for i in range(num_ops):
            if i < len(vars_list) - 1:
                next_var = vars_list[i+1]
                premises.append(f"{current_expr} {op} {next_var}")
                operators.append(op)
                current_expr = f"({current_expr} {op} {next_var})"
        
        solution = f"result_{random.randint(100, 999)}"

    else:
        # High Entropy: Mixed operators, random structure
        vars_list = [_generate_numeric_variable(i) for i in range(num_ops * 2)]
        values = [random.randint(1, 20) for _ in vars_list]
        
        # Premises: Variable definitions
        for i, (v, val) in enumerate(zip(vars_list, values)):
            premises.append(f"{v} = {val}")
        
        # Random expression construction
        expr_parts = []
        for i in range(num_ops):
            v1 = random.choice(vars_list)
            v2 = random.choice(vars_list)
            op = random.choice(ARITHMETIC_OPS + COMPARATORS)
            premises.append(f"{v1} {op} {v2}")
            operators.append(op)
            expr_parts.append(f"({v1} {op} {v2})")
        
        solution = f"res_{random.randint(100, 999)}"

    structure_hash = _compute_structure_hash(premises, operators)

    problem = SyntheticProblem(
        id=f"arith_{structure_hash[:8]}_{random.randint(1000, 9999)}",
        premises=premises,
        operators=operators,
        solution=solution,
        entropy_level=entropy_level,
        metadata={
            "type": "arithmetic",
            "structure_hash": structure_hash,
            "num_ops": num_ops,
            "seed": cfg.seed
        }
    )

    return problem


def generate_dataset_batch(
    subset_type: str,
    count: int,
    entropy_level: Optional[str] = None
) -> List[SyntheticProblem]:
    """
    Generates a batch of problems for a specific subset.

    Args:
        subset_type: 'high_entropy', 'low_entropy', 'target_specific', or 'test'.
        count: Number of problems to generate.
        entropy_level: Explicit entropy level to force (overrides subset_type logic if provided).

    Returns:
        List of SyntheticProblem instances.
    """
    cfg = _get_config()
    problems = []
    
    # Determine entropy target based on subset type if not explicitly forced
    target_entropy = entropy_level
    if target_entropy is None:
        if subset_type == "high_entropy":
            target_entropy = "high"
        elif subset_type == "low_entropy":
            target_entropy = "low"
        elif subset_type == "target_specific":
            # Target specific: could be a mix or specific narrow style
            # For now, default to 'low' as a specific style
            target_entropy = "low" 
        elif subset_type == "test":
            target_entropy = "random" # Mix for generalization
        else:
            target_entropy = "random"

    logger.info(f"Generating {count} problems for subset '{subset_type}' (target entropy: {target_entropy})")

    for i in range(count):
        # Seed the random state for this iteration to ensure reproducibility
        # based on the global config seed + iteration index
        iteration_seed = cfg.seed + i
        random.seed(iteration_seed)
        
        # Decide problem type (50/50 split)
        if random.random() < 0.5:
            prob = generate_propositional_problem(entropy_level=target_entropy)
        else:
            prob = generate_arithmetic_problem(entropy_level=target_entropy)
        
        problems.append(prob)

    logger.info(f"Successfully generated {len(problems)} problems.")
    return problems
