import os
import json
import subprocess
import logging
import re
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

from dataset_loader import validate_and_save_catalog

logger = logging.getLogger(__name__)

def load_catalog() -> list:
    """Load the task catalog from the processed directory."""
    catalog_path = Path('data/benchmarks/processed/catalog.json')
    if not catalog_path.exists():
        logger.error(f"Catalog not found at {catalog_path}")
        return []
    
    with open(catalog_path, 'r') as f:
        return json.load(f)

def is_humaneval_task(task_entry: Dict[str, Any]) -> bool:
    """
    Check if a task is from HumanEval dataset.
    
    Args:
        task_entry: Task dictionary
    
    Returns:
        True if task is from HumanEval
    """
    task_id = task_entry.get('task_id', '')
    dataset_source = task_entry.get('dataset_source', '')
    return task_id.startswith('HumanEval/') or dataset_source == 'humaneval'

def parse_coverage_output(coverage_output: str) -> Dict[str, Any]:
    """
    Parse pytest --cov output to extract line and branch coverage.
    
    Args:
        coverage_output: Raw output from coverage tool
    
    Returns:
        Dictionary with coverage metrics
    """
    result = {
        'line_coverage': None,
        'branch_coverage': None,
        'raw_output': coverage_output
    }

    # Regex patterns to extract coverage percentages
    line_pattern = r'lines.*?(\d+)%'
    branch_pattern = r'branches.*?(\d+)%'

    line_match = re.search(line_pattern, coverage_output, re.IGNORECASE)
    branch_match = re.search(branch_pattern, coverage_output, re.IGNORECASE)

    if line_match:
        result['line_coverage'] = int(line_match.group(1))
    
    if branch_match:
        result['branch_coverage'] = int(branch_match.group(1))

    return result

def run_coverage_on_task(
    task_entry: Dict[str, Any],
    logger: Optional[logging.Logger] = None
) -> Tuple[bool, Optional[Dict], Optional[str]]:
    """
    Run pytest coverage on a generated code file.
    
    Args:
        task_entry: Task dictionary with task_id and generated code path
        logger: Optional logger instance
    
    Returns:
        Tuple of (success, coverage_data, error_message)
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    task_id = task_entry.get('task_id', 'unknown')
    generated_path = f"data/generated/{task_id}.py"
    
    if not os.path.exists(generated_path):
        error_msg = f"Generated code not found at {generated_path}"
        logger.error(error_msg)
        return (False, None, error_msg)

    # Check if HumanEval (branch coverage N/A)
    if is_humaneval_task(task_entry):
        logger.info(f"Task {task_id} is HumanEval. Branch coverage will be marked as N/A.")

    # Prepare test file path
    # We assume the test suite was already transformed by test_transformer.py
    # and is located at data/benchmarks/processed/tests/{task_id}_tests.py
    test_path = Path(f"data/benchmarks/processed/tests/{task_id}_tests.py")
    
    if not test_path.exists():
        # Try to find the test file with different naming conventions
        possible_paths = [
            f"data/benchmarks/processed/tests/{task_id.replace('/', '_')}_tests.py",
            f"data/benchmarks/processed/tests/{task_id}_test.py"
        ]
        found = False
        for p in possible_paths:
            if Path(p).exists():
                test_path = Path(p)
                found = True
                break
        
        if not found:
            error_msg = f"Test suite not found for task {task_id}"
            logger.warning(error_msg)
            # Continue without running coverage, but report failure
            return (False, None, error_msg)

    # Run pytest with coverage
    cmd = [
        'pytest',
        str(test_path),
        f'--cov={generated_path}',
        '--cov-report=term-missing',
        '--tb=short',
        '-v'
    ]

    try:
        logger.info(f"Running coverage for {task_id}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120 # 2 minute timeout
        )
        
        output = result.stdout + result.stderr
        
        if result.returncode != 0 and "no tests ran" not in output.lower():
            # Check if it's just a coverage report success but test failure
            if "coverage" in output.lower():
                logger.warning(f"Tests failed for {task_id}, but coverage data may exist.")
            else:
                error_msg = f"Coverage execution failed for {task_id}: {result.stderr}"
                return (False, None, error_msg)

        # Parse output
        coverage_data = parse_coverage_output(output)
        
        # Special handling for HumanEval branch coverage
        if is_humaneval_task(task_entry):
            coverage_data['branch_coverage'] = "N/A"
            logger.info(f"Set branch_coverage to N/A for HumanEval task {task_id}")

        return (True, coverage_data, None)

    except subprocess.TimeoutExpired:
        error_msg = f"Coverage execution timed out for {task_id}"
        logger.error(error_msg)
        return (False, None, error_msg)
    except Exception as e:
        error_msg = f"Unexpected error running coverage for {task_id}: {str(e)}"
        logger.error(error_msg)
        return (False, None, error_msg)

def main():
    """Main entry point for standalone coverage testing."""
    logging.basicConfig(level=logging.INFO)
    catalog = load_catalog()
    
    if not catalog:
        logger.error("No tasks in catalog")
        return

    logger.info(f"Testing coverage on {len(catalog)} tasks")
    
    for task in catalog[:5]: # Test first 5 tasks
        success, data, error = run_coverage_on_task(task, logger)
        if success:
            logger.info(f"Coverage result for {task['task_id']}: {data}")
        else:
            logger.error(f"Failed for {task['task_id']}: {error}")

if __name__ == '__main__':
    main()