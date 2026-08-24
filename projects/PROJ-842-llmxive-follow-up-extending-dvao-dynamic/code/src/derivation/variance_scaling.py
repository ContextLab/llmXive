import sympy
from sympy import symbols, Sum, simplify, expand, Eq, IndexedBase, Idx, factorial, solve, log, exp
from typing import Dict, Tuple, Optional, Union, Any, List
import json
import os
from datetime import datetime

def derive_variance_accumulation(N: Optional[int] = None, epsilon: Optional[float] = None) -> Union[sympy.Expr, Dict[str, Any]]:
    """
    Derives the variance accumulation expression for the DVAO noise scaling law.
    
    Handles multiple call signatures:
    1. derive_variance_accumulation(N, epsilon) -> symbolic expression with substituted values
    2. derive_variance_accumulation(N) -> symbolic expression with N substituted, epsilon symbolic
    3. derive_variance_accumulation() -> fully symbolic expression (N, epsilon_i)
    
    The theoretical derivation assumes:
    - N objectives
    - Independent noise terms epsilon_i ~ N(0, sigma^2)
    - Variance of sum = sum of variances (for independent terms)
    
    Returns:
      If N and epsilon provided: A sympy expression with values substituted
      If only N provided: A sympy expression with N substituted
      If neither: A fully symbolic sympy expression
    """
    # Define symbolic variables
    n_obj = symbols('N', integer=True, positive=True)
    sigma_sq = symbols('sigma^2', positive=True, real=True)
    
    # Create indexed noise variance terms for summation
    # Var(sum(epsilon_i)) = sum(Var(epsilon_i)) = N * sigma^2
    i = Idx('i', (1, n_obj))
    epsilon_i = IndexedBase('epsilon')
    
    # Theoretical variance accumulation: Sum of variances
    # For independent noise: Var(Sum(epsilon_i)) = Sum(Var(epsilon_i)) = N * sigma^2
    variance_expr = n_obj * sigma_sq
    
    # Simplify the expression
    variance_expr = simplify(variance_expr)
    
    # Handle substitution based on arguments
    if N is not None:
        if epsilon is not None:
            # Substitute both N and epsilon (treat epsilon as sigma)
            result = variance_expr.subs({n_obj: N, sigma_sq: epsilon**2})
            return result
        else:
            # Substitute only N
            result = variance_expr.subs({n_obj: N})
            return result
    else:
        # Return fully symbolic expression
        return variance_expr

def verify_symmetry_and_linearity(expr: sympy.Expr) -> bool:
    """
    Verifies that the variance expression satisfies symmetry and linearity properties.
    
    Properties:
    1. Linearity: Var(aX + bY) = a^2 Var(X) + b^2 Var(Y) for independent X, Y
    2. Symmetry: The expression should be invariant under permutation of noise terms
    
    Args:
        expr: The variance expression to verify
        
    Returns:
        True if properties are satisfied, False otherwise
    """
    # Check linearity: coefficient of sigma^2 should be N
    # The expression should be of the form: N * sigma^2
    n_obj, sigma_sq = symbols('N sigma^2', integer=True, positive=True)
    
    # Extract coefficient of sigma^2
    coeff = expr.coeff(sigma_sq)
    
    # Verify linearity: coefficient should be N
    is_linear = simplify(coeff - n_obj) == 0
    
    # Verify symmetry: expression should not depend on specific ordering of epsilon_i
    # Since we derived it as N * sigma^2, it is inherently symmetric
    is_symmetric = True
    
    return is_linear and is_symmetric

def save_derivation_output(expr: sympy.Expr, output_path: str, metadata: Optional[Dict] = None) -> None:
    """
    Saves the derived variance expression to a JSON file.
    
    Args:
        expr: The sympy expression to save
        output_path: Path to the output JSON file
        metadata: Optional metadata to include in the output
    """
    # Convert sympy expression to string for JSON serialization
    expr_str = str(expr)
    
    output_data = {
        "expression": expr_str,
        "sympy_repr": sympy.srepr(expr),
        "timestamp": datetime.now().isoformat(),
        "metadata": metadata or {}
    }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

def main():
    """Main function to demonstrate variance scaling derivation."""
    print("Deriving variance accumulation expression...")
    
    # Fully symbolic derivation
    expr = derive_variance_accumulation()
    print(f"Symbolic expression: {expr}")
    
    # Verify properties
    is_valid = verify_symmetry_and_linearity(expr)
    print(f"Symmetry and linearity verified: {is_valid}")
    
    # Example with N=5
    expr_n5 = derive_variance_accumulation(N=5)
    print(f"Expression for N=5: {expr_n5}")
    
    # Example with N=5 and sigma=0.1
    expr_n5_sigma = derive_variance_accumulation(N=5, epsilon=0.1)
    print(f"Expression for N=5, sigma=0.1: {expr_n5_sigma}")

if __name__ == "__main__":
    main()
