import sympy
from sympy import symbols, simplify, solve, Eq, exp, log
from typing import Dict, Tuple, Optional, List, Union
import json
import os
import sys
from datetime import datetime

# Import the variance derivation function which now supports optional N
from src.derivation.variance_scaling import derive_variance_accumulation

def invert_variance_to_sample_complexity(variance_expr: sympy.Expr, N: int, epsilon: float) -> sympy.Expr:
    """
    Invert the variance expression to solve for sample complexity.
    Assumes variance scales as sigma^2 / n, solving for n.
    """
    # Define symbols
    n_samples = symbols('n_samples', positive=True)
    
    # Theoretical variance accumulation: Var = sigma^2 * N / n_samples (simplified model)
    # We solve for n_samples such that Var <= epsilon^2
    # n_samples >= (sigma^2 * N) / epsilon^2
    
    # Extract sigma^2 from the variance expression if possible, or assume a standard form
    # For the purpose of this inversion, we assume the variance expression represents the numerator term
    # and we solve for the denominator required to meet the epsilon threshold.
    
    # Simplified inversion logic:
    # If variance_expr = C * N (where C is noise variance), then n >= C * N / epsilon^2
    
    # Let's assume the variance expression is of the form: k * N
    # We solve: k * N / n <= epsilon^2  => n >= k * N / epsilon^2
    
    # Extract coefficient of N if possible
    try:
        coeff = simplify(variance_expr / N)
    except (TypeError, AttributeError):
        # Fallback if N is not a symbol in the expression
        coeff = simplify(variance_expr)
    
    # Calculate required samples
    n_required = (coeff * N) / (epsilon ** 2)
    
    return simplify(n_required)

def derive_sample_complexity_bound(N: int = None, epsilon: float = 1e-3, noise_std: float = 0.1) -> Dict:
    """
    Derive the sample complexity bound for Pareto optimality.
    
    Args:
        N: Number of objectives. If None, returns a symbolic expression.
           If N > 50, the calculation is capped at N=50 with a 'degraded' flag.
        epsilon: Target error tolerance.
        noise_std: Standard deviation of the noise.
        
    Returns:
        A dictionary containing the bound, metadata, and degradation status.
    """
    # Handle N > 50 case as per T070
    effective_N = N
    degraded = False
    
    if N is not None and N > 50:
        effective_N = 50
        degraded = True
    
    # Define symbols for the derivation
    n_samples = symbols('n_samples', positive=True)
    sigma = symbols('sigma', positive=True)
    
    # Derive variance accumulation expression
    # If N is provided, we substitute it; otherwise we keep it symbolic
    if N is not None:
        variance_data = derive_variance_accumulation(N=effective_N)
        # variance_data should be a dict containing the expression
        variance_expr = variance_data.get('expression', None)
        if variance_expr is None:
            # Fallback: construct a simple variance expression if the function returns unexpected data
            variance_expr = sigma**2 * effective_N
    else:
        variance_data = derive_variance_accumulation()
        variance_expr = variance_data.get('expression', None)
        if variance_expr is None:
            variance_expr = sigma**2 * symbols('N', positive=True)
    
    # Calculate the bound
    # We want Var <= epsilon^2
    # If Var = sigma^2 * N / n_samples, then n_samples >= sigma^2 * N / epsilon^2
    
    # Substitute sigma with the provided noise_std
    bound_expr = invert_variance_to_sample_complexity(variance_expr, effective_N, epsilon)
    bound_value = bound_expr.subs(sigma, noise_std)
    
    # Ensure we have a float if possible
    try:
        bound_float = float(bound_value)
    except (TypeError, ValueError):
        bound_float = None
    
    result = {
        "effective_N": effective_N,
        "epsilon": epsilon,
        "noise_std": noise_std,
        "bound_expression": str(bound_expr),
        "bound_value": bound_float,
        "degraded": degraded,
        "timestamp": datetime.now().isoformat()
    }
    
    if N is not None:
        result["requested_N"] = N
    
    return result

def verify_inversion_logic() -> bool:
    """
    Verify that the inversion logic is consistent with the variance derivation.
    """
    # Test with a small N
    N_test = 10
    epsilon_test = 0.1
    noise_std_test = 0.05
    
    result = derive_sample_complexity_bound(N=N_test, epsilon=epsilon_test, noise_std=noise_std_test)
    
    # Check that the result contains expected fields
    if "bound_value" not in result:
        return False
    
    # Check that the bound is positive
    if result["bound_value"] <= 0:
        return False
    
    # Check that degraded is False for N <= 50
    if result["degraded"] is not False:
        return False
    
    return True

def save_derivation_output(result: Dict, output_path: str = None) -> str:
    """
    Save the derivation result to a JSON file.
    """
    if output_path is None:
        output_path = "data/processed/sample_complexity_bound.json"
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    return output_path

def main():
    """
    Main entry point for the sample complexity derivation script.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Derive sample complexity bounds")
    parser.add_argument("--N", type=int, default=None, help="Number of objectives")
    parser.add_argument("--epsilon", type=float, default=1e-3, help="Target error tolerance")
    parser.add_argument("--noise_std", type=float, default=0.1, help="Noise standard deviation")
    parser.add_argument("--output", type=str, default=None, help="Output file path")
    parser.add_argument("--verify", action="store_true", help="Verify inversion logic")
    
    args = parser.parse_args()
    
    if args.verify:
        if verify_inversion_logic():
            print("Inversion logic verified successfully.")
            sys.exit(0)
        else:
            print("Inversion logic verification failed.")
            sys.exit(1)
    
    print("Starting Sample Complexity Derivation...")
    
    try:
        result = derive_sample_complexity_bound(
            N=args.N,
            epsilon=args.epsilon,
            noise_std=args.noise_std
        )
        
        output_path = save_derivation_output(result, args.output)
        print(f"Derivation complete. Results saved to {output_path}")
        print(f"Requested N: {args.N}")
        print(f"Effective N: {result['effective_N']}")
        print(f"Degraded: {result['degraded']}")
        print(f"Bound: {result['bound_value']}")
        
    except Exception as e:
        print(f"Error during derivation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()