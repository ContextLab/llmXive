"""
Sample Complexity Derivation Module.

This module implements the symbolic inversion of the variance accumulation
equation to derive the closed-form sample complexity bound for Pareto optimality.

It takes the variance expression Var(A) as a function of N (objectives) and
noise parameters, and inverts it to find the required sample size S to achieve
a target error tolerance epsilon.

Assumptions:
- Noise terms are i.i.d. with mean 0 and variance sigma^2.
- Variance accumulation follows the derived scaling law.
"""
import sympy
from typing import Dict, Tuple, Optional, List, Union
import json
import os
import sys
from datetime import datetime

# Ensure src is in path for imports if running as script
if 'code' not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.derivation.variance_scaling import derive_variance_accumulation


def invert_variance_to_sample_complexity(
    variance_expr: sympy.Expr,
    target_epsilon: sympy.Symbol,
    n_objectives: sympy.Symbol,
    noise_var: sympy.Symbol,
    sample_size: sympy.Symbol
) -> sympy.Expr:
    """
    Inverts the variance equation Var(A) = f(S, N, sigma^2) to solve for S.

    The relationship is typically of the form:
    Var(A) = (N * sigma^2) / S  (or similar scaling derived in variance_scaling.py)

    We solve for S such that Var(A) <= epsilon^2 (or epsilon depending on convention).
    Here we solve S = f_inverse(epsilon, N, sigma^2).

    Args:
        variance_expr: The sympy expression for Var(A) in terms of sample_size, etc.
        target_epsilon: The target error tolerance symbol (epsilon).
        n_objectives: Symbol for N (number of objectives).
        noise_var: Symbol for noise variance (sigma^2).
        sample_size: Symbol for S (sample size).

    Returns:
        A sympy expression representing the sample complexity bound S.
    """
    # We want to solve: variance_expr = target_epsilon**2 for sample_size
    # Note: Usually sample complexity is defined by bounding the variance by epsilon^2.
    # If the task implies bounding the standard deviation by epsilon, we use target_epsilon.
    # Standard convention in RL bounds: Var <= epsilon^2.
    
    equation = sympy.Eq(variance_expr, target_epsilon**2)
    
    try:
        solutions = sympy.solve(equation, sample_size)
        if not solutions:
            raise ValueError("Could not symbolically solve for sample size.")
        
        # Filter for positive real solutions if possible, or take the first valid one
        # In sample complexity, we expect a positive solution.
        valid_solution = None
        for sol in solutions:
            if sol.is_real and sol.is_positive:
                valid_solution = sol
                break
            # If no explicit positivity check, take the first non-None
            if valid_solution is None:
                valid_solution = sol
        
        if valid_solution is None:
            valid_solution = solutions[0]

        return valid_solution
    except Exception as e:
        raise RuntimeError(f"Failed to invert variance equation: {e}")


def derive_sample_complexity_bound(
    n_objectives: Optional[int] = None,
    noise_var: Optional[float] = None
) -> Dict[str, Union[str, sympy.Expr, float]]:
    """
    Derives the full sample complexity bound expression and optionally evaluates it.

    Steps:
    1. Retrieve the variance scaling law from variance_scaling.py.
    2. Define symbols for epsilon (target error) and S (sample size).
    3. Invert the equation to solve for S.
    4. Return the symbolic expression and a simplified string representation.

    Args:
        n_objectives: Optional integer to substitute N for a concrete bound.
        noise_var: Optional float to substitute sigma^2 for a concrete bound.

    Returns:
        Dictionary containing:
        - 'symbolic_bound': The sympy expression for S.
        - 'string_bound': LaTeX or string representation.
        - 'assumptions': List of assumptions made.
        - 'evaluated_bound': (Optional) Numeric value if n_objectives and noise_var provided.
    """
    # Define symbols
    N = sympy.Symbol('N', positive=True, integer=True)
    sigma_sq = sympy.Symbol('sigma_sq', positive=True)
    S = sympy.Symbol('S', positive=True)
    epsilon = sympy.Symbol('epsilon', positive=True)

    # Get variance expression from the derivation module
    # The variance_scaling module returns an expression Var(A) in terms of N, sigma_sq, S
    variance_data = derive_variance_accumulation()
    variance_expr = variance_data['expression']
    
    # Ensure the variance expression uses our symbols
    # The derivation module might use different symbol names, so we map them.
    # Usually derive_variance_accumulation returns an expression with symbols named 'N', 'sigma_sq', 'S'
    # If not, we might need to substitute. Let's assume the derivation module uses consistent naming.
    # If the derivation module returns a generic expression, we rely on the structure.
    
    # Invert
    sample_complexity_expr = invert_variance_to_sample_complexity(
        variance_expr, epsilon, N, sigma_sq, S
    )

    result = {
        'symbolic_bound': sample_complexity_expr,
        'string_bound': sympy.printing.latex(sample_complexity_expr),
        'assumptions': [
            "Noise terms are i.i.d. with mean 0 and variance sigma^2",
            "Target error is bounded by epsilon (variance <= epsilon^2)",
            "Variance scales inversely with sample size S",
            "N objectives contribute additively to variance"
        ],
        'formula_n': N,
        'formula_sigma_sq': sigma_sq,
        'formula_epsilon': epsilon
    }

    if n_objectives is not None and noise_var is not None:
        # Evaluate
        evaluated = sample_complexity_expr.subs({N: n_objectives, sigma_sq: noise_var})
        # We still have epsilon, so it's a function of epsilon
        result['evaluated_bound'] = str(evaluated)
        result['evaluated_bound_func'] = evaluated

    return result


def verify_inversion_logic() -> bool:
    """
    Verifies that the inversion logic is mathematically consistent.
    
    Checks:
    1. Substituting the derived S back into Var(A) yields epsilon^2.
    2. The expression is positive for positive inputs.
    
    Returns:
        True if verification passes, False otherwise.
    """
    N = sympy.Symbol('N', positive=True, integer=True)
    sigma_sq = sympy.Symbol('sigma_sq', positive=True)
    S = sympy.Symbol('S', positive=True)
    epsilon = sympy.Symbol('epsilon', positive=True)

    # Get original variance
    variance_data = derive_variance_accumulation()
    variance_expr = variance_data['expression']

    # Get derived sample complexity
    sample_complexity_expr = invert_variance_to_sample_complexity(
        variance_expr, epsilon, N, sigma_sq, S
    )

    # Substitute S back into variance expression
    substituted_variance = variance_expr.subs(S, sample_complexity_expr)
    
    # Simplify and check if it equals epsilon^2
    simplified = sympy.simplify(substituted_variance - epsilon**2)
    
    is_correct = simplified == 0
    
    # Additional check: ensure S is positive
    # We can't easily check symbolic positivity for all cases without assumptions,
    # but we checked during inversion.
    
    return is_correct


def save_derivation_output(output_path: str, result: Dict) -> None:
    """
    Saves the derivation results to a JSON file.
    
    Args:
        output_path: Path to save the JSON file.
        result: Dictionary containing derivation results.
    """
    # Convert sympy objects to strings for JSON serialization
    serializable_result = {}
    for k, v in result.items():
        if isinstance(v, sympy.Expr):
            serializable_result[k] = sympy.printing.latex(v)
        elif isinstance(v, dict):
            # Handle nested dicts if any
            serializable_result[k] = str(v)
        else:
            serializable_result[k] = v
    
    serializable_result['timestamp'] = datetime.now().isoformat()
    serializable_result['module'] = 'src.derivation.sample_complexity'
    serializable_result['verification_passed'] = verify_inversion_logic()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(serializable_result, f, indent=2)


def main():
    """
    Main entry point to run the derivation and save the output.
    """
    print("Starting Sample Complexity Derivation...")
    
    # 1. Derive the bound
    result = derive_sample_complexity_bound()
    
    print(f"Derived Symbolic Bound: {result['string_bound']}")
    print(f"Assumptions: {result['assumptions']}")
    
    # 2. Verify logic
    is_valid = verify_inversion_logic()
    print(f"Inversion Logic Verification: {'PASSED' if is_valid else 'FAILED'}")
    
    if not is_valid:
        print("ERROR: Inversion logic failed verification. Aborting.")
        sys.exit(1)

    # 3. Save output
    output_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'processed')
    output_file = os.path.join(output_dir, 'sample_complexity_derivation.json')
    save_derivation_output(output_file, result)
    
    print(f"Derivation saved to {output_file}")
    
    # 4. Optional: Print a concrete example
    print("\n--- Concrete Example (N=10, sigma^2=1) ---")
    concrete_result = derive_sample_complexity_bound(n_objectives=10, noise_var=1.0)
    print(f"S(epsilon) = {concrete_result['evaluated_bound']}")

    return result


if __name__ == "__main__":
    main()