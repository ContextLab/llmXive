"""
Validator module for ensuring Python syntax correctness of generated code variants.

Implements FR-002: Parse generated Python variants and ensure syntax correctness
before LLM submission to prevent downstream failures.
"""
import ast
import os
import json
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

from transform.seed_manager import log_transform_seed, compute_mapping_hash


class ValidationError(Exception):
    """Custom exception for syntax validation failures."""
    pass


def validate_python_syntax(code_string: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that a string contains syntactically correct Python code.
    
    Args:
        code_string: The Python code to validate.
        
    Returns:
        Tuple of (is_valid, error_message).
        - is_valid: True if code is syntactically correct, False otherwise.
        - error_message: None if valid, otherwise a string describing the syntax error.
    """
    if not isinstance(code_string, str):
        return False, "Input must be a string"
    
    if not code_string.strip():
        return False, "Input code string is empty"
    
    try:
        ast.parse(code_string)
        return True, None
    except SyntaxError as e:
        error_msg = f"SyntaxError: {e.msg} at line {e.lineno}, column {e.offset}"
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected error during parsing: {str(e)}"
        return False, error_msg


def validate_code_variants(variants_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate a list of code variants for syntax correctness.
    
    Args:
        variants_data: List of dictionaries containing 'code' and 'variant_id' keys.
        
    Returns:
        Dictionary containing validation results:
        - total_count: Total number of variants processed
        - valid_count: Number of syntactically correct variants
        - invalid_count: Number of variants with syntax errors
        - success_rate: Proportion of valid variants (0.0 to 1.0)
        - valid_ids: List of variant IDs that passed validation
        - invalid_details: List of dictionaries with 'variant_id' and 'error_message'
    """
    if not variants_data:
        return {
            "total_count": 0,
            "valid_count": 0,
            "invalid_count": 0,
            "success_rate": 1.0,
            "valid_ids": [],
            "invalid_details": []
        }
    
    valid_ids = []
    invalid_details = []
    
    for variant in variants_data:
        variant_id = variant.get("variant_id", "unknown")
        code = variant.get("code", "")
        
        is_valid, error_msg = validate_python_syntax(code)
        
        if is_valid:
            valid_ids.append(variant_id)
        else:
            invalid_details.append({
                "variant_id": variant_id,
                "error_message": error_msg
            })
    
    total_count = len(variants_data)
    valid_count = len(valid_ids)
    invalid_count = total_count - valid_count
    success_rate = valid_count / total_count if total_count > 0 else 1.0
    
    return {
        "total_count": total_count,
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "success_rate": success_rate,
        "valid_ids": valid_ids,
        "invalid_details": invalid_details
    }


def filter_valid_variants(variants_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter a list of code variants to return only those with valid syntax.
    
    Args:
        variants_data: List of dictionaries containing 'code' and 'variant_id' keys.
        
    Returns:
        List of dictionaries for variants that passed syntax validation.
    """
    validation_results = validate_code_variants(variants_data)
    valid_ids_set = set(validation_results["valid_ids"])
    
    return [
        variant for variant in variants_data
        if variant.get("variant_id") in valid_ids_set
    ]


def validate_file(filepath: str) -> Dict[str, Any]:
    """
    Validate all Python code variants stored in a JSON file.
    
    Args:
        filepath: Path to the JSON file containing variants data.
        
    Returns:
        Validation results dictionary (same structure as validate_code_variants).
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Variant file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both list format and dict with 'variants' key
    if isinstance(data, list):
        variants_data = data
    elif isinstance(data, dict) and "variants" in data:
        variants_data = data["variants"]
    else:
        raise ValueError("Invalid JSON structure: expected list or dict with 'variants' key")
    
    return validate_code_variants(variants_data)


def save_validation_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Save validation results to a JSON file.
    
    Args:
        results: Dictionary containing validation results.
        output_path: Path to the output JSON file.
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    results["timestamp"] = datetime.now().isoformat()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)


def main():
    """
    CLI entry point for validating code variants.
    
    Usage:
        python code/transform/validator.py --input <path_to_variants.json> [--output <path_to_results.json>]
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Validate Python syntax correctness of generated code variants."
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to JSON file containing code variants"
    )
    parser.add_argument(
        "--output", "-o",
        default="results/validation_results.json",
        help="Path to save validation results (default: results/validation_results.json)"
    )
    parser.add_argument(
        "--filter", "-f",
        action="store_true",
        help="If set, save only valid variants to a separate file"
    )
    
    args = parser.parse_args()
    
    try:
        # Log seed for reproducibility
        log_transform_seed("validator", "syntax_validation")
        
        print(f"Loading variants from: {args.input}")
        results = validate_file(args.input)
        
        print(f"Validation complete:")
        print(f"  Total variants: {results['total_count']}")
        print(f"  Valid: {results['valid_count']}")
        print(f"  Invalid: {results['invalid_count']}")
        print(f"  Success rate: {results['success_rate']:.2%}")
        
        if results['invalid_count'] > 0:
            print("\nInvalid variants:")
            for detail in results['invalid_details'][:5]:  # Show first 5
                print(f"  - {detail['variant_id']}: {detail['error_message']}")
            if results['invalid_count'] > 5:
                print(f"  ... and {results['invalid_count'] - 5} more")
        
        # Save results
        save_validation_results(results, args.output)
        print(f"\nResults saved to: {args.output}")
        
        # Optionally save filtered valid variants
        if args.filter:
            filtered_output = args.output.replace('.json', '_filtered.json')
            valid_variants = filter_valid_variants(
                json.load(open(args.input, 'r')) if isinstance(json.load(open(args.input, 'r')), list) 
                else json.load(open(args.input, 'r'))['variants']
            )
            
            with open(filtered_output, 'w', encoding='utf-8') as f:
                json.dump(valid_variants, f, indent=2)
            print(f"Valid variants saved to: {filtered_output}")
        
        # Return exit code based on success rate
        if results['success_rate'] < 1.0:
            print(f"\nWarning: {100 - results['success_rate'] * 100:.1f}% of variants have syntax errors.")
            return 1
        
        return 0
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file: {e}", file=sys.stderr)
        return 3
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    import sys
    sys.exit(main())
