"""
Syntax error detection and handling for invalid code submissions.

This module implements T034: syntax error detection and handling for
invalid submissions. It parses submitted code using Python's ast module,
catches SyntaxError exceptions, logs details, and returns appropriate
error responses.
"""
import os
import sys
import ast
import logging
import json
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from logs.experiment import setup_experiment_logger

logger = setup_experiment_logger("quality")


def validate_syntax(
    code: str,
    submission_id: Optional[str] = None
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validate the syntax of submitted code.
    
    Args:
        code: The code to validate.
        submission_id: Optional submission ID for logging.
        
    Returns:
        Tuple of (is_valid, error_message, error_details)
        - is_valid: True if code is syntactically valid, False otherwise
        - error_message: Human-readable error message if invalid
        - error_details: Dictionary with error details (line, column, type) if invalid
    """
    try:
        ast.parse(code)
        return True, None, None
        
    except SyntaxError as e:
        error_details = {
            'type': 'SyntaxError',
            'message': str(e),
            'line': e.lineno,
            'offset': e.offset,
            'text': e.text,
            'submission_id': submission_id
        }
        
        error_msg = f"Syntax error at line {e.lineno}, column {e.offset}: {e.msg}"
        
        logger.error(f"Syntax error detected for submission {submission_id}: {error_msg}")
        
        return False, error_msg, error_details
        
    except Exception as e:
        error_details = {
            'type': type(e).__name__,
            'message': str(e),
            'submission_id': submission_id
        }
        
        error_msg = f"Unexpected error during syntax validation: {str(e)}"
        
        logger.error(f"Unexpected error for submission {submission_id}: {error_msg}")
        
        return False, error_msg, error_details


def create_error_response(
    submission_id: str,
    error_message: str,
    error_details: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create a standardized error response for invalid submissions.
    
    Args:
        submission_id: The submission ID.
        error_message: Human-readable error message.
        error_details: Detailed error information.
        
    Returns:
        Dictionary with error response data (400 response format).
    """
    return {
        'status': 'error',
        'code': 400,
        'message': error_message,
        'submission_id': submission_id,
        'error_details': error_details,
        'timestamp': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
    }


def main():
    """
    Main entry point for syntax validation demonstration.
    
    Tests syntax validation with valid and invalid code samples.
    """
    logger.info("Starting syntax validation demonstration")
    
    # Test cases
    test_cases = [
        {
            'id': 'valid_code',
            'code': 'def hello():\n    return "world"',
            'expected_valid': True
        },
        {
            'id': 'invalid_syntax',
            'code': 'def hello(:\n    return "world"',
            'expected_valid': False
        },
        {
            'id': 'missing_indent',
            'code': 'def hello():\nreturn "world"',
            'expected_valid': False
        },
        {
            'id': 'unclosed_paren',
            'code': 'def hello(\n    return "world"',
            'expected_valid': False
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        submission_id = test_case['id']
        code = test_case['code']
        expected = test_case['expected_valid']
        
        is_valid, error_msg, error_details = validate_syntax(code, submission_id)
        
        result = {
            'submission_id': submission_id,
            'is_valid': is_valid,
            'expected_valid': expected,
            'match': is_valid == expected,
            'error_message': error_msg,
            'error_details': error_details
        }
        
        results.append(result)
        
        logger.info(f"Test {submission_id}: {'PASS' if result['match'] else 'FAIL'}")
    
    # Write results to output file
    output_path = PROJECT_ROOT / "data" / "quality" / "syntax_validation_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results written to {output_path}")
    
    # Return exit code based on test results
    all_passed = all(r['match'] for r in results)
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())