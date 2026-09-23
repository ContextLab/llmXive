import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def load_results(input_path: str) -> Dict[str, Any]:
    """Load correlation results from a JSON file."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {input_path}")
    
    logger.info(f"Loading results from {input_path}")
    with open(path, 'r') as f:
        return json.load(f)

def flag_significance(results: Dict[str, Any], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Add a statistical significance flag to the results based on p-value.
    
    Args:
        results: Dictionary containing correlation results (must include 'p_value').
        alpha: Significance threshold (default 0.05).
    
    Returns:
        Updated dictionary with 'is_significant' and 'significance_level' keys.
    """
    if 'p_value' not in results:
        raise ValueError("Results must contain 'p_value' to determine significance.")
    
    p_value = results['p_value']
    
    if not isinstance(p_value, (int, float)):
        raise TypeError(f"p_value must be numeric, got {type(p_value)}")
    
    is_significant = p_value < alpha
    
    # Determine significance level description
    if p_value < 0.001:
        significance_level = "p < 0.001 (Highly Significant)"
    elif p_value < 0.01:
        significance_level = "p < 0.01 (Very Significant)"
    elif p_value < 0.05:
        significance_level = "p < 0.05 (Significant)"
    else:
        significance_level = "p >= 0.05 (Not Significant)"
    
    results['is_significant'] = is_significant
    results['significance_level'] = significance_level
    results['alpha_threshold'] = alpha
    
    logger.info(f"Significance check: p={p_value:.6f}, alpha={alpha}, significant={is_significant}")
    
    return results

def save_results(results: Dict[str, Any], output_path: str) -> None:
    """Save the updated results to a JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving results to {output_path}")
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)

def main():
    """Main entry point for the significance flagging script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Flag statistical significance in correlation results."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the input JSON file containing correlation results."
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to the output JSON file with significance flags."
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance threshold (default: 0.05)."
    )
    
    args = parser.parse_args()
    
    try:
        # Load results
        results = load_results(args.input)
        
        # Flag significance
        flagged_results = flag_significance(results, alpha=args.alpha)
        
        # Save results
        save_results(flagged_results, args.output)
        
        logger.info("Significance flagging completed successfully.")
        
        # Print summary to stdout
        print(f"Input: {args.input}")
        print(f"Output: {args.output}")
        print(f"P-value: {flagged_results.get('p_value')}")
        print(f"Is Significant (p < {args.alpha}): {flagged_results.get('is_significant')}")
        print(f"Significance Level: {flagged_results.get('significance_level')}")
        
    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
