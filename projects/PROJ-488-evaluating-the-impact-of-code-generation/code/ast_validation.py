import ast
import json
import sys
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional

from logging_config import setup_logger, get_logger
from data_model import CodeSnippet

# Error codes defined in tasks.md
ERROR_INVALID_PARSE_THRESHOLD = 102

def parse_snippet(snippet_id: str, code: str, language: str) -> Tuple[bool, Optional[str]]:
    """
    Attempt to parse a code snippet using Python's ast module.
    
    Args:
        snippet_id: Unique identifier for the snippet.
        code: The source code string.
        language: Language identifier (e.g., 'python').
        
    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    if language != "python":
        return False, f"Unsupported language for AST parsing: {language}"
    
    try:
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, f"SyntaxError: {e.msg} at line {e.lineno}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def validate_datasets(snippets_data: List[Dict], threshold: float = 0.95) -> Tuple[bool, List[str], float]:
    """
    Validate a list of snippets by parsing them with AST.
    
    Args:
        snippets_data: List of dicts with keys 'id', 'code', 'language'.
        threshold: Minimum required success rate (default 0.95).
        
    Returns:
        Tuple of (passed: bool, failed_ids: List[str], success_rate: float)
    """
    failed_ids = []
    total = len(snippets_data)
    
    if total == 0:
        logging.warning("No snippets provided for validation.")
        return False, [], 0.0
    
    success_count = 0
    
    for item in snippets_data:
        snippet_id = item.get('id', 'unknown')
        code = item.get('code', '')
        language = item.get('language', 'python')
        
        success, error = parse_snippet(snippet_id, code, language)
        
        if success:
            success_count += 1
        else:
            failed_ids.append(snippet_id)
            # Log at debug level to avoid spamming logs, but we track it
            logging.debug(f"AST validation failed for {snippet_id}: {error}")
    
    success_rate = success_count / total
    passed = success_rate >= threshold
    
    return passed, failed_ids, success_rate

def run_ast_validation(
    input_path: str,
    output_path: str,
    threshold: float = 0.95,
    logger_name: Optional[str] = None
) -> bool:
    """
    Main entry point to run AST validation on a processed dataset file.
    
    Args:
        input_path: Path to JSON file containing list of snippets.
        output_path: Path to write validation report (JSON).
        threshold: Minimum success rate required.
        logger_name: Optional logger name.
        
    Returns:
        True if validation passed, False otherwise (and exits with error code).
    """
    logger = setup_logger(logger_name or "ast_validation", level=logging.INFO)
    
    input_file = Path(input_path)
    if not input_file.exists():
        logger.error(f"Input file not found: {input_path}")
        return False
    
    # Load snippets
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            snippets_data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON input: {e}")
        return False
    
    logger.info(f"Loaded {len(snippets_data)} snippets from {input_path}")
    
    # Run validation
    passed, failed_ids, success_rate = validate_datasets(snippets_data, threshold)
    
    # Prepare report
    report = {
        "input_file": str(input_path),
        "total_snippets": len(snippets_data),
        "successful_parses": len(snippets_data) - len(failed_ids),
        "failed_parses": len(failed_ids),
        "success_rate": success_rate,
        "threshold": threshold,
        "passed": passed,
        "failed_ids": failed_ids,
        "timestamp": str(Path(input_file).stat().st_mtime)
    }
    
    # Write report
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"AST validation complete. Success rate: {success_rate:.2%} (threshold: {threshold:.2%})")
    logger.info(f"Report written to: {output_path}")
    
    if not passed:
        logger.error(f"Validation FAILED: Success rate {success_rate:.2%} is below threshold {threshold:.2%}")
        logger.error(f"Error code: {ERROR_INVALID_PARSE_THRESHOLD}")
        return False
    
    return True

def main():
    """CLI entry point for AST validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate code snippets via AST parsing.")
    parser.add_argument(
        "--input", 
        type=str, 
        required=True, 
        help="Path to input JSON file containing snippets."
    )
    parser.add_argument(
        "--output", 
        type=str, 
        required=False, 
        default="data/processed/ast_validation_report.json",
        help="Path to output JSON report."
    )
    parser.add_argument(
        "--threshold", 
        type=float, 
        default=0.95,
        help="Minimum required success rate (default: 0.95)."
    )
    
    args = parser.parse_args()
    
    success = run_ast_validation(
        input_path=args.input,
        output_path=args.output,
        threshold=args.threshold
    )
    
    sys.exit(0 if success else ERROR_INVALID_PARSE_THRESHOLD)

if __name__ == "__main__":
    main()
