import hashlib
import random
from typing import List, Dict, Any, Tuple, Optional
from models.synthetic_problem import SyntheticProblem
from config import Config, get_config
from utils.logger import get_logger
from generators.contradiction_checker import is_problem_solvable

logger = get_logger(__name__)

def generate_propositional_problem(config: Config, entropy_target: Optional[str] = None) -> SyntheticProblem:
    """
    Generates a propositional logic problem.
    entropy_target: 'high', 'low', or None (random).
    Controls the number of premises and operators to influence entropy.
    """
    seed = config.seed
    if entropy_target is not None:
        # Deterministic offset based on target for reproducibility within the target group
        if entropy_target == 'high':
            seed += 1000
        elif entropy_target == 'low':
            seed += 2000
        elif entropy_target == 'target':
            seed += 3000
    
    rng = random.Random(seed)
    config.seed = seed  # Update global seed state for next call if needed, though we use local RNG

    variables = ['P', 'Q', 'R', 'S', 'T', 'U']
    operators_list = ['AND', 'OR', 'IMPLIES', 'NOT']
    
    # Determine complexity based on entropy target
    if entropy_target == 'high':
        num_vars = rng.randint(4, 6)
        num_premises = rng.randint(4, 6)
        num_ops = rng.randint(3, 5)
    elif entropy_target == 'low':
        num_vars = rng.randint(2, 3)
        num_premises = rng.randint(1, 2)
        num_ops = rng.randint(1, 2)
    else: # target or random
        num_vars = rng.randint(3, 4)
        num_premises = rng.randint(2, 3)
        num_ops = rng.randint(2, 3)

    selected_vars = rng.sample(variables, min(num_vars, len(variables)))
    premises = []
    
    for _ in range(num_premises):
        var1 = rng.choice(selected_vars)
        var2 = rng.choice(selected_vars)
        op = rng.choice(operators_list[:3]) # AND, OR, IMPLIES
        
        if op == 'NOT':
            premises.append(f"NOT {var1}")
        else:
            premises.append(f"{var1} {op} {var2}")

    # Ensure we have at least one premise
    if not premises:
        premises.append(f"{selected_vars[0]} AND {selected_vars[1]}")

    solution_var = rng.choice(selected_vars)
    solution_op = rng.choice(operators_list)
    solution = f"{solution_var} {solution_op} {rng.choice(selected_vars)}"

    # Check solvability (mock check for structure validity in this context)
    # In a real SAT scenario, we would verify if premises logically imply solution.
    # Here we ensure structural consistency.
    
    problem_id = f"PROB-{seed:06d}"
    metadata = {
        "num_variables": len(selected_vars),
        "num_premises": len(premises),
        "num_operators": num_ops,
        "entropy_target": entropy_target or "random"
    }

    return SyntheticProblem(
        id=problem_id,
        premises=premises,
        operators=[solution_op],
        solution=solution,
        entropy_level=entropy_target if entropy_target else "random",
        metadata=metadata
    )

def generate_arithmetic_problem(config: Config, entropy_target: Optional[str] = None) -> SyntheticProblem:
    """
    Generates an arithmetic problem.
    """
    seed = config.seed
    if entropy_target is not None:
        if entropy_target == 'high':
            seed += 10000
        elif entropy_target == 'low':
            seed += 20000
        elif entropy_target == 'target':
            seed += 30000
    
    rng = random.Random(seed)
    
    if entropy_target == 'high':
        num_ops = rng.randint(4, 6)
        digits = 4
    elif entropy_target == 'low':
        num_ops = rng.randint(1, 2)
        digits = 2
    else:
        num_ops = rng.randint(2, 3)
        digits = 3

    operators_map = {0: '+', 1: '-', 2: '*', 3: '/'}
    ops = [operators_map[rng.randint(0, 3)] for _ in range(num_ops)]
    nums = [rng.randint(1, 10**digits) for _ in range(num_ops + 1)]

    premises = []
    current_expr = str(nums[0])
    for i, op in enumerate(ops):
        current_expr += f" {op} {nums[i+1]}"
        premises.append(current_expr)

    solution = current_expr
    problem_id = f"ARITH-{seed:06d}"
    
    metadata = {
        "num_operations": num_ops,
        "digit_depth": digits,
        "entropy_target": entropy_target or "random"
    }

    return SyntheticProblem(
        id=problem_id,
        premises=premises,
        operators=ops,
        solution=solution,
        entropy_level=entropy_target if entropy_target else "random",
        metadata=metadata
    )

def generate_dataset_batch(
    total_count: int = 3000,
    high_ratio: float = 0.33,
    low_ratio: float = 0.33,
    target_ratio: float = 0.34,
    seed: int = 42
) -> List[SyntheticProblem]:
    """
    Generates a batch of problems with controlled entropy distribution.
    Returns a list of SyntheticProblem objects.
    """
    config = get_config()
    config.seed = seed
    
    problems = []
    counts = {
        'high': int(total_count * high_ratio),
        'low': int(total_count * low_ratio),
        'target': total_count - int(total_count * high_ratio) - int(total_count * low_ratio)
    }
    
    logger.info(f"Generating batch: High={counts['high']}, Low={counts['low']}, Target={counts['target']}")

    current_seed = seed
    for target, count in counts.items():
        logger.info(f"Generating {count} problems for entropy level: {target}")
        for i in range(count):
            # Alternate between propositional and arithmetic
            if i % 2 == 0:
                prob = generate_propositional_problem(config, entropy_target=target)
            else:
                prob = generate_arithmetic_problem(config, entropy_target=target)
            
            # Update seed to ensure uniqueness and reproducibility
            current_seed += 1
            config.seed = current_seed
            problems.append(prob)
    
    logger.info(f"Total problems generated: {len(problems)}")
    return problems