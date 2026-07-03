import os
import sys
import json
import logging
from typing import List, Dict, Any, Tuple

from generate.validate_distinctness import validate_distinctness, validate_explanation_pair

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_explanation_pairs(
    explanations_dir: str
) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """
    Find pairs of symbolic and neuro-symbolic explanations in the given directory.

    Args:
        explanations_dir: Path to the directory containing explanation files

    Returns:
        List of tuples (symbolic_explanation, neuro_symbolic_explanation)
    """
    pairs = []

    if not os.path.exists(explanations_dir):
        logger.error(f"Explanations directory not found: {explanations_dir}")
        return pairs

    # Walk through the directory to find explanation files
    for root, _, files in os.walk(explanations_dir):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        explanation = json.load(f)

                    # Determine if this is a symbolic or neuro-symbolic explanation
                    if 'symbolic_trace' in explanation and 'neural_narrative' in explanation:
                        # This is a neuro-symbolic explanation
                        # We need to find the corresponding pure symbolic explanation
                        # For now, we'll treat the neuro-symbolic as both (in a real scenario,
                        # we'd match by problem_id)
                        pairs.append((explanation, explanation))
                    elif 'symbolic_trace' in explanation:
                        # This is a symbolic explanation
                        # Look for the corresponding neuro-symbolic explanation
                        problem_id = explanation.get('problem_id', '')
                        if problem_id:
                            # Try to find matching neuro-symbolic explanation
                            # This is a simplified approach
                            pass
                except (json.JSONDecodeError, IOError) as e:
                    logger.warning(f"Failed to read {file_path}: {e}")

    return pairs

def run_batch_validation(
    explanations_dir: str,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run distinctness validation on all explanation pairs in a directory.

    Args:
        explanations_dir: Path to the directory containing explanation files
        output_path: Optional path to write validation results

    Returns:
        Validation summary dictionary
    """
    pairs = find_explanation_pairs(explanations_dir)

    if not pairs:
        logger.warning("No explanation pairs found for validation")
        return {
            'total_pairs': 0,
            'valid_pairs': 0,
            'invalid_pairs': 0,
            'details': []
        }

    results = []
    valid_count = 0
    invalid_count = 0

    for i, (symbolic_exp, neuro_symbolic_exp) in enumerate(pairs):
        is_valid, details = validate_explanation_pair(symbolic_exp, neuro_symbolic_exp)

        result = {
            'pair_id': i,
            'problem_id': neuro_symbolic_exp.get('problem_id', 'unknown'),
            'is_valid': is_valid,
            'details': details
        }
        results.append(result)

        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1

    summary = {
        'total_pairs': len(pairs),
        'valid_pairs': valid_count,
        'invalid_pairs': invalid_count,
        'validation_rate': valid_count / len(pairs) if pairs else 0.0,
        'details': results
    }

    # Write results to output file if specified
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Validation results written to {output_path}")

    return summary

def main():
    """
    Main entry point for running distinctness validation.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Validate distinctness between symbolic and neural explanations'
    )
    parser.add_argument(
        '--explanations-dir',
        type=str,
        default='data/explanations',
        help='Directory containing explanation JSON files'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/validation/distinctness_report.json',
        help='Output path for validation results'
    )

    args = parser.parse_args()

    logger.info(f"Running distinctness validation on {args.explanations_dir}")

    summary = run_batch_validation(args.explanations_dir, args.output)

    print(json.dumps(summary, indent=2))

    # Exit with error code if validation failed for any pair
    if summary['invalid_pairs'] > 0:
        logger.warning(f"{summary['invalid_pairs']} pairs failed validation")
        sys.exit(1)
    else:
        logger.info("All explanation pairs passed distinctness validation")

if __name__ == "__main__":
    main()
