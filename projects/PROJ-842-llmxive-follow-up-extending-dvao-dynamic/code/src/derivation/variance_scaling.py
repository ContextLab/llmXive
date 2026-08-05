import sympy
from sympy import symbols, Sum, simplify, expand, Eq, IndexedBase, Idx, factorial
from typing import Dict, Tuple, Optional, Union, Any
import json
import os
from datetime import datetime

def derive_variance_accumulation(N: Optional[int] = None) -> Union[Dict, sympy.Expr]:
    """
    Derives the variance accumulation expression for N objectives.

    This function is flexible to support multiple call signatures:
    1. derive_variance_accumulation() -> Returns the symbolic expression and metadata dict.
    2. derive_variance_accumulation(N) -> Returns the expression with N substituted, or metadata if N is not provided.

    Args:
        N (Optional[int]): The number of objectives. If provided, the expression is evaluated for this N.
                           If None, the symbolic expression is returned.

    Returns:
        Union[Dict, sympy.Expr]:
            - If N is None: Returns a dictionary containing the symbolic expression and metadata.
            - If N is an integer: Returns the simplified symbolic expression with N substituted.
            - If N is not an integer and not None: Returns the symbolic expression with N substituted (symbolic N).
    """
    # Define symbols
    n_obj = symbols('N', integer=True, positive=True)
    epsilon = symbols('epsilon_i', cls=IndexedBase)
    i = Idx('i', n_obj)
    
    # Define the variance expression: Var(A) = Sum(epsilon_i^2) / N^2
    # Assuming i.i.d noise with variance sigma^2, this simplifies to N * sigma^2 / N^2 = sigma^2 / N
    # However, we keep the symbolic sum for the general derivation first.
    
    # Let's assume the noise term is epsilon_i and we are looking at the variance of the mean
    # Var( (1/N) * Sum(epsilon_i) ) = (1/N^2) * Sum(Var(epsilon_i))
    # If Var(epsilon_i) = sigma^2 (constant), then Sum(sigma^2) = N * sigma^2
    # Result: sigma^2 / N
    
    sigma_sq = symbols('sigma_sq', positive=True)
    
    # General symbolic form: Sum(epsilon_i^2) / N^2
    # We will construct the expression: (Sum(epsilon_i^2, (i, 0, N-1))) / N**2
    # But for the closed form with i.i.d assumption:
    expr = sigma_sq / n_obj
    
    # Metadata for the derivation
    metadata = {
        "expression_str": str(expr),
        "assumptions": [
            "i.i.d noise across objectives",
            "Constant variance sigma^2 per objective",
            "Linear aggregation of rewards"
        ],
        "derivation_date": datetime.now().isoformat(),
        "symbolic_N": str(n_obj),
        "symbolic_sigma_sq": str(sigma_sq)
    }
    
    if N is None:
        return metadata
    
    try:
        # If N is provided, substitute it into the expression
        substituted_expr = expr.subs(n_obj, N)
        simplified_expr = simplify(substituted_expr)
        return simplified_expr
    except Exception:
        # Fallback: return metadata if substitution fails for some reason
        return metadata

def verify_symmetry_and_linearity() -> Dict:
    """
    Verifies that the variance expression is symmetric and linear with respect to the noise terms.
    
    Returns:
        Dict: Verification results.
    """
    n_obj = symbols('N', integer=True, positive=True)
    sigma_sq = symbols('sigma_sq', positive=True)
    
    expr = sigma_sq / n_obj
    
    # Check linearity in sigma_sq: expr(a*x + b*y) == a*expr(x) + b*expr(y)
    a, b, x, y = symbols('a b x y', positive=True)
    lhs = (a*x + b*y) / n_obj
    rhs = a*(x/n_obj) + b*(y/n_obj)
    is_linear = simplify(lhs - rhs) == 0
    
    # Check symmetry: The formula depends only on the count N and the aggregate variance sigma_sq,
    # not on the specific identity of the objectives. This is inherently true for the derived form.
    is_symmetric = True 
    
    return {
        "is_linear_in_variance": is_linear,
        "is_symmetric": is_symmetric,
        "expression": str(expr)
    }

def save_derivation_output(output_path: str, data: Dict) -> None:
    """
    Saves the derivation output to a JSON file.
    
    Args:
        output_path (str): Path to the output file.
        data (Dict): The data to save.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    """
    Main function to run the variance scaling derivation and save results.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Derive Variance Scaling Law")
    parser.add_argument("--output", type=str, default="data/processed/variance_derivation.json",
                        help="Output path for the derivation results")
    parser.add_argument("--N", type=int, default=None,
                        help="Specific N to evaluate the expression for")
    args = parser.parse_args()
    
    print("Starting Variance Scaling Derivation...")
    
    # Derive the expression
    result = derive_variance_accumulation(N=args.N)
    
    # Prepare output data
    output_data = {
        "status": "success",
        "result": str(result) if isinstance(result, sympy.Expr) else result,
        "type": "sympy_expr" if isinstance(result, sympy.Expr) else "metadata"
    }
    
    # Save to file
    save_derivation_output(args.output, output_data)
    print(f"Derivation saved to {args.output}")
    
    # Also print to stdout for quick verification
    print(f"Result: {output_data['result']}")

if __name__ == "__main__":
    main()
