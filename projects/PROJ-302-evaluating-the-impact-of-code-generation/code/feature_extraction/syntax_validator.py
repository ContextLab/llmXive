"""
Syntax validation module for code snippets.

Validates Python code snippets for syntactic correctness using the ast module.
Supports batch validation of datasets and reports success rates.
"""
import os
import sys
import ast
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_snippet_syntax(code_snippet: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a single code snippet for syntactic correctness.
    
    Args:
        code_snippet: The code snippet to validate as a string.
        
    Returns:
        Tuple of (is_valid, error_message).
        is_valid: True if the snippet is syntactically valid, False otherwise.
        error_message: None if valid, otherwise the exception message.
    """
    if not code_snippet or not isinstance(code_snippet, str):
        return False, "Empty or invalid input"
    
    try:
        # Try to parse the code snippet
        ast.parse(code_snippet)
        return True, None
    except SyntaxError as e:
        return False, f"SyntaxError: {e.msg} at line {e.lineno}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def validate_dataset(
    input_path: str,
    output_path: str,
    code_column: str = 'code_snippet',
    success_threshold: float = 0.95
) -> Dict[str, Any]:
    """
    Validate all code snippets in a dataset and report success rate.
    
    Args:
        input_path: Path to the input Parquet file containing code snippets.
        output_path: Path to write the validation report (JSON).
        code_column: Name of the column containing code snippets.
        success_threshold: Minimum required success rate (default 0.95).
        
    Returns:
        Dictionary containing validation results including success rate.
        
    Raises:
        ValueError: If success rate is below the threshold.
        FileNotFoundError: If input file does not exist.
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading dataset from {input_path}")
    df = pd.read_parquet(input_path)
    
    if code_column not in df.columns:
        raise ValueError(f"Column '{code_column}' not found in dataset. Available columns: {df.columns.tolist()}")
    
    logger.info(f"Validating {len(df)} snippets from column '{code_column}'")
    
    results = []
    valid_count = 0
    invalid_count = 0
    error_details = []
    
    for idx, row in df.iterrows():
        snippet = row[code_column]
        is_valid, error_msg = validate_snippet_syntax(snippet)
        
        result = {
            'index': idx,
            'is_valid': is_valid,
            'error_message': error_msg
        }
        results.append(result)
        
        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1
            if len(error_details) < 10:  # Limit error details in report
                error_details.append({
                    'index': idx,
                    'error': error_msg,
                    'snippet_preview': str(snippet)[:200] + "..." if len(str(snippet)) > 200 else str(snippet)
                })
    
    total_count = valid_count + invalid_count
    success_rate = valid_count / total_count if total_count > 0 else 0.0
    
    validation_report = {
        'input_file': str(input_path),
        'total_snippets': total_count,
        'valid_snippets': valid_count,
        'invalid_snippets': invalid_count,
        'success_rate': round(success_rate, 4),
        'success_threshold': success_threshold,
        'meets_threshold': success_rate >= success_threshold,
        'error_details_sample': error_details
    }
    
    # Write validation report to output path
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    import json
    with open(output_file, 'w') as f:
        json.dump(validation_report, f, indent=2)
    
    logger.info(f"Validation complete: {success_rate:.2%} success rate ({valid_count}/{total_count})")
    
    if success_rate < success_threshold:
        raise ValueError(
            f"Validation failed: Success rate {success_rate:.2%} is below threshold {success_threshold:.2%}. "
            f"Valid: {valid_count}, Invalid: {invalid_count}, Total: {total_count}. "
            f"Report saved to {output_path}"
        )
    
    return validation_report

def main():
    """
    Main entry point for syntax validation CLI.
    
    Usage:
        python code/feature_extraction/syntax_validator.py \\
            --input data/processed/generated_snippets.parquet \\
            --output data/processed/syntax_validation_report.json \\
            --threshold 0.95
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Validate syntax of code snippets in a dataset.'
    )
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Path to input Parquet file containing code snippets'
    )
    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='Path to output validation report (JSON)'
    )
    parser.add_argument(
        '--code-column',
        type=str,
        default='code_snippet',
        help='Name of the column containing code snippets (default: code_snippet)'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.95,
        help='Minimum required success rate (default: 0.95)'
    )
    
    args = parser.parse_args()
    
    try:
        report = validate_dataset(
            input_path=args.input,
            output_path=args.output,
            code_column=args.code_column,
            success_threshold=args.threshold
        )
        
        print(f"\nValidation Summary:")
        print(f"  Total snippets: {report['total_snippets']}")
        print(f"  Valid: {report['valid_snippets']}")
        print(f"  Invalid: {report['invalid_snippets']}")
        print(f"  Success rate: {report['success_rate']:.2%}")
        print(f"  Threshold: {report['success_threshold']:.2%}")
        print(f"  Meets threshold: {report['meets_threshold']}")
        print(f"\nReport saved to: {args.output}")
        
        sys.exit(0)
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(2)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(3)

if __name__ == '__main__':
    main()
