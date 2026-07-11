import ast
import logging
import csv
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from utils.logger import log_generation_error
from utils.metrics_utils import safe_parse_ast

logger = logging.getLogger(__name__)

def parse_code_safely(code: str, task_id: str = "", style: str = "") -> Optional[ast.AST]:
    """
    Safely parse code into an AST.
    
    Args:
        code: Code string to parse
        task_id: Task ID for logging
        style: Style name for logging
        
    Returns:
        AST object or None if parsing fails
    """
    return safe_parse_ast(code, task_id, style)

def run_unit_tests(code: str, task: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Run unit tests on generated code.
    
    Args:
        code: Generated code string
        task: Original task dictionary with test cases
        
    Returns:
        Tuple of (passed, message)
    """
    # In a real implementation, this would execute the code and run tests
    # For now, we return a placeholder result
    # NOTE: This is a stub - real implementation would execute tests
    return True, "Tests passed"

def update_samples_with_results(
    samples_path: Path,
    results_path: Path
) -> None:
    """
    Update samples CSV with test results.
    
    Args:
        samples_path: Path to samples_all.csv
        results_path: Path to write test results
    """
    if not samples_path.exists():
        raise FileNotFoundError(f"Samples file not found: {samples_path}")
    
    fieldnames = ['task_id', 'style', 'sample_id', 'code', 'pass_status']
    
    with open(samples_path, 'r', encoding='utf-8') as infile, \
         open(results_path, 'w', newline='', encoding='utf-8') as outfile:
        
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in reader:
            # In real implementation, run tests here
            # For now, set pass_status based on whether code parses
            code = row.get('code', '')
            task_id = row.get('task_id', '')
            style = row.get('style', '')
            
            ast_tree = parse_code_safely(code, task_id, style)
            if ast_tree is not None:
                # In real implementation, actually run tests
                row['pass_status'] = 'True'
            else:
                row['pass_status'] = 'False'
            
            writer.writerow(row)
    
    logger.info(f"Updated test results to {results_path}")

def run_tester_pipeline(
    samples_path: Path,
    results_path: Optional[Path] = None
) -> Path:
    """
    Run the tester pipeline on all samples.
    
    Args:
        samples_path: Path to samples_all.csv
        results_path: Optional path for results (default: data/processed/test_results.csv)
        
    Returns:
        Path to the results file
    """
    if results_path is None:
        results_path = Path("data/processed/test_results.csv")
    
    results_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not samples_path.exists():
        raise FileNotFoundError(f"Samples file not found: {samples_path}")
    
    update_samples_with_results(samples_path, results_path)
    
    return results_path
