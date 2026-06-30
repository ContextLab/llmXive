import os
import json
import subprocess
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import re

# Add parent directory to path to allow imports from code/ if run as script
# but primarily designed to be imported as a module within the project
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_seed
from utils import safe_get

logger = logging.getLogger(__name__)

def parse_pytest_cov_output(output: str) -> Dict[str, Any]:
    """
    Parse pytest --cov output to extract line and branch coverage.
    
    Args:
        output: The stdout/stderr from pytest --cov command
        
    Returns:
        Dictionary with 'line_coverage' and 'branch_coverage' keys.
        Values are percentages (float) or None if not found.
    """
    result = {
        "line_coverage": None,
        "branch_coverage": None
    }
    
    # Common patterns for pytest-cov output
    # Example: "TOTAL 100 90 9 90%" -> 90% line coverage
    # Example: "TOTAL 100 90 9 90% 45% (branches)" -> 90% line, 45% branch
    
    lines = output.split('\n')
    for line in lines:
        # Look for the TOTAL line which usually contains coverage stats
        if 'TOTAL' in line or 'total' in line:
            # Extract percentages
            percentages = re.findall(r'(\d+\.?\d*)%', line)
            if len(percentages) >= 1:
                result["line_coverage"] = float(percentages[0])
            if len(percentages) >= 2:
                # Second percentage is usually branch coverage
                result["branch_coverage"] = float(percentages[1])
            break
    
    # If we couldn't find in TOTAL line, try to parse specific lines
    if result["line_coverage"] is None:
        for line in lines:
            # Pattern: "Name Stmts Miss Cover"
            if 'Stmts' in line and 'Miss' in line and 'Cover' in line:
                continue
            if 'TOTAL' in line or line.strip().endswith('%'):
                parts = line.split()
                for part in parts:
                    if '%' in part:
                        try:
                            pct = float(part.replace('%', ''))
                            if result["line_coverage"] is None:
                                result["line_coverage"] = pct
                            elif result["branch_coverage"] is None:
                                result["branch_coverage"] = pct
                                break
                        except ValueError:
                            continue
                        break
    
    return result

def run_coverage(task_id: str, generated_code_path: Path, test_suite_path: Path) -> Dict[str, Any]:
    """
    Execute pytest --cov on the generated code and parse results.
    
    Args:
        task_id: Unique identifier for the task
        generated_code_path: Path to the generated Python file
        test_suite_path: Path to the test suite file
        
    Returns:
        Dictionary containing coverage results and metadata
    """
    result = {
        "task_id": task_id,
        "status": "failed",
        "error_message": None,
        "line_coverage": None,
        "branch_coverage": None,
        "timestamp": None
    }
    
    if not generated_code_path.exists():
        result["error_message"] = f"Generated code file not found: {generated_code_path}"
        logger.error(result["error_message"])
        return result
    
    if not test_suite_path.exists():
        result["error_message"] = f"Test suite file not found: {test_suite_path}"
        logger.warning(result["error_message"])
        # Continue without tests if test suite is missing, as per T007 handling
        result["status"] = "no_tests"
        result["line_coverage"] = 0.0
        result["branch_coverage"] = 0.0
        return result
    
    # Prepare command
    # We run pytest on the test file, targeting the generated code for coverage
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_suite_path),
        f"--cov={generated_code_path.stem}",
        "--cov-report=term-missing",
        "--cov-fail-under=0",  # Don't fail on low coverage
        "-v"
    ]
    
    # Change to the directory containing the generated code to ensure imports work
    working_dir = generated_code_path.parent
    
    try:
        logger.info(f"Running coverage for {task_id} in {working_dir}")
        process = subprocess.run(
            cmd,
            cwd=str(working_dir),
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout per task
        )
        
        output = process.stdout + "\n" + process.stderr
        
        if process.returncode != 0 and "no tests ran" not in output.lower():
            # Check if it's just a coverage threshold issue (which we set to 0)
            if "failed" not in output.lower() or "coverage" not in output.lower():
                logger.warning(f"Pytest returned non-zero for {task_id}: {process.returncode}")
        
        # Parse the output
        coverage_data = parse_pytest_cov_output(output)
        
        result["line_coverage"] = coverage_data["line_coverage"]
        result["branch_coverage"] = coverage_data["branch_coverage"]
        
        if result["line_coverage"] is not None:
            result["status"] = "completed"
        else:
            result["status"] = "partial"
            result["error_message"] = "Could not extract line coverage from output"
            
    except subprocess.TimeoutExpired:
        result["error_message"] = "Coverage execution timed out"
        logger.error(result["error_message"])
    except Exception as e:
        result["error_message"] = f"Exception during coverage run: {str(e)}"
        logger.error(result["error_message"])
        
    return result

def is_humaneval_task(task_id: str, catalog_data: Optional[Dict] = None) -> bool:
    """
    Determine if a task is from the HumanEval dataset.
    
    Args:
        task_id: The task identifier (e.g., 'HumanEval/0', 'mbpp_1')
        catalog_data: Optional pre-loaded catalog entry for the task
        
    Returns:
        True if the task is from HumanEval, False otherwise
    """
    if task_id.startswith("HumanEval/"):
        return True
    
    if catalog_data:
        if catalog_data.get("dataset_source") == "humaneval":
            return True
        if "humaneval" in task_id.lower():
            return True
            
    return False

def run_coverage_with_catalog_check(task_id: str, generated_code_path: Path, 
                                   test_suite_path: Path, catalog_path: Path) -> Dict[str, Any]:
    """
    Run coverage and validate branch coverage for HumanEval tasks.
    
    Args:
        task_id: Unique identifier for the task
        generated_code_path: Path to the generated Python file
        test_suite_path: Path to the test suite file
        catalog_path: Path to the task catalog (catalog.json)
        
    Returns:
        Dictionary containing coverage results with HumanEval validation
    """
    # Load catalog if it exists
    catalog_data = None
    if catalog_path.exists():
        try:
            with open(catalog_path, 'r') as f:
                catalog = json.load(f)
                # Find the specific task in the catalog
                for entry in catalog:
                    if entry.get("task_id") == task_id:
                        catalog_data = entry
                        break
        except Exception as e:
            logger.warning(f"Could not load catalog: {e}")
    
    # Run coverage
    result = run_coverage(task_id, generated_code_path, test_suite_path)
    
    # Validate and log branch coverage for HumanEval
    if is_humaneval_task(task_id, catalog_data):
        if result["branch_coverage"] is not None:
            logger.warning(f"HumanEval task {task_id} unexpectedly has branch coverage: {result['branch_coverage']}%. Setting to N/A.")
            result["branch_coverage"] = "N/A"
        else:
            logger.info(f"HumanEval task {task_id} correctly has no branch coverage data. Setting to N/A.")
            result["branch_coverage"] = "N/A"
    
    return result

def save_coverage_report(result: Dict[str, Any], output_dir: Path, task_id: str) -> Path:
    """
    Save coverage results to a JSON file.
    
    Args:
        result: Coverage result dictionary
        output_dir: Directory to save the report
        task_id: Task identifier for the filename
        
    Returns:
        Path to the saved report file
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{task_id}.json"
    
    # Ensure timestamp is present
    if "timestamp" not in result or result["timestamp"] is None:
        from datetime import datetime
        result["timestamp"] = datetime.utcnow().isoformat()
        
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
        
    logger.info(f"Saved coverage report to {output_path}")
    return output_path

def main():
    """
    Main entry point for running coverage on generated code.
    This function is designed to be called by main.py or other orchestrators.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run coverage on generated code")
    parser.add_argument("--task-id", required=True, help="Task ID to process")
    parser.add_argument("--generated-path", required=True, help="Path to generated code file")
    parser.add_argument("--test-path", required=True, help="Path to test suite file")
    parser.add_argument("--catalog-path", default="data/benchmarks/processed/catalog.json", 
                      help="Path to task catalog")
    parser.add_argument("--output-dir", default="data/coverage_reports", 
                      help="Directory to save coverage reports")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    generated_path = Path(args.generated_path)
    test_path = Path(args.test_path)
    catalog_path = Path(args.catalog_path)
    output_dir = Path(args.output_dir)
    
    # Run coverage with HumanEval validation
    result = run_coverage_with_catalog_check(
        args.task_id, 
        generated_path, 
        test_path, 
        catalog_path
    )
    
    # Save report
    save_coverage_report(result, output_dir, args.task_id)
    
    # Return success/fail code
    if result["status"] == "completed":
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
