"""
Evaluation module for assessing generated code completions against HumanEval test suites.

This module implements the evaluation logic for User Story 1, specifically:
- Loading raw inference results from data/processed/energy_inference_raw.csv
- Loading HumanEval problems from data/raw/human_eval_data.jsonl
- Evaluating generated solutions using the evaluate_functional_correctness library
- Joining results to produce data/processed/energy_results_raw.csv
"""
import os
import csv
import json
import tempfile
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import config to ensure paths are consistent
from code.config import DATA_RAW_DIR, DATA_PROCESSED_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for evaluation
EVALUATION_TIMEOUT = 10.0  # seconds per test case
K_VALUES = [1]  # Pass@k values to compute
N_JOBS = 1  # Number of parallel jobs (CPU constraint)

def load_raw_results(input_path: str) -> List[Dict[str, Any]]:
    """
    Load raw inference results from CSV.
    
    Args:
        input_path: Path to energy_inference_raw.csv
        
    Returns:
        List of dictionaries containing inference results
    """
    results = []
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            try:
                row['tokens_generated'] = int(row['tokens_generated']) if row['tokens_generated'] else 0
                row['energy_kwh'] = float(row['energy_kwh']) if row['energy_kwh'] else None
                row['runtime_seconds'] = float(row['runtime_seconds']) if row['runtime_seconds'] else None
            except (ValueError, TypeError) as e:
                logger.warning(f"Error parsing row: {row}, error: {e}")
                # Set defaults for malformed rows
                if 'tokens_generated' not in row or not row['tokens_generated']:
                    row['tokens_generated'] = 0
                if 'energy_kwh' not in row or not row['energy_kwh']:
                    row['energy_kwh'] = None
                if 'runtime_seconds' not in row or not row['runtime_seconds']:
                    row['runtime_seconds'] = None
            results.append(row)
    
    logger.info(f"Loaded {len(results)} rows from {input_path}")
    return results

def load_problems(input_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Load HumanEval problems from JSONL file.
    
    Args:
        input_path: Path to human_eval_data.jsonl
        
    Returns:
        Dictionary mapping problem_id to problem data
    """
    problems = {}
    if not os.path.exists(input_path):
        logger.error(f"Problems file not found: {input_path}")
        raise FileNotFoundError(f"Problems file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                problem = json.loads(line)
                # Use the task_id as the key
                problem_id = problem.get('task_id')
                if problem_id:
                    problems[problem_id] = problem
            except json.JSONDecodeError as e:
                logger.warning(f"Error parsing JSON line: {e}")
    
    logger.info(f"Loaded {len(problems)} problems from {input_path}")
    return problems

def evaluate_solution(problem: Dict[str, Any], completion: str, timeout: float = 10.0) -> bool:
    """
    Evaluate a single solution against the problem's test suite.
    
    This function creates a temporary file with the solution and runs the tests.
    It returns True if the solution passes all tests, False otherwise.
    
    Args:
        problem: Problem dictionary containing prompt, test, etc.
        completion: Generated code completion
        timeout: Maximum time allowed for evaluation (seconds)
        
    Returns:
        True if solution passes, False otherwise
    """
    if not completion or completion.strip() == "":
        # Empty completion fails
        return False
    
    prompt = problem.get('prompt', '')
    test_code = problem.get('test', '')
    
    # Construct the full code to evaluate
    full_code = prompt + completion + "\n" + test_code
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp_file:
        tmp_file.write(full_code)
        tmp_path = tmp_file.name
    
    try:
        # Run the test file with a timeout
        start_time = time.time()
        result = subprocess.run(
            ['python', tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        elapsed = time.time() - start_time
        
        # Check if execution was successful (exit code 0)
        # Note: In HumanEval, tests typically assert and raise exceptions on failure
        # A successful run means no exceptions were raised
        if result.returncode == 0:
            logger.debug(f"Solution passed for problem {problem.get('task_id')} in {elapsed:.2f}s")
            return True
        else:
            logger.debug(f"Solution failed for problem {problem.get('task_id')} (exit code {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        logger.debug(f"Solution timed out for problem {problem.get('task_id')} after {timeout}s")
        return False
    except Exception as e:
        logger.debug(f"Error evaluating solution for problem {problem.get('task_id')}: {e}")
        return False
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def evaluate_all_solutions(inference_results: List[Dict[str, Any]], problems: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Evaluate all generated solutions against their respective problem test suites.
    
    Args:
        inference_results: List of inference result dictionaries
        problems: Dictionary of problem data indexed by problem_id
        
    Returns:
        List of result dictionaries with pass_fail_status added
    """
    evaluated_results = []
    
    for result in inference_results:
        problem_id = result.get('problem_id')
        model_id = result.get('model_id')
        tokens_generated = result.get('tokens_generated', 0)
        
        # Get the problem data
        problem = problems.get(problem_id)
        if not problem:
            logger.warning(f"Problem {problem_id} not found, marking as failed")
            result['pass_fail_status'] = 0
            evaluated_results.append(result)
            continue
        
        # Extract the completion
        # The completion is typically stored in a field like 'completion' or we need to reconstruct it
        # Since our inference script might not have stored the completion, we need to handle this
        # For now, we assume the completion is not stored and we need to re-run inference or handle missing
        # However, the task description implies we evaluate "generated completions"
        # Let's check if there's a completion field or if we need to handle missing completions
        
        completion = result.get('completion', '')
        
        # If no completion was generated (0 tokens), it's a failure
        if tokens_generated == 0 or not completion:
            logger.debug(f"No completion for problem {problem_id} by {model_id}, marking as failed")
            result['pass_fail_status'] = 0
            evaluated_results.append(result)
            continue
        
        # Evaluate the solution
        is_passed = evaluate_solution(problem, completion, timeout=EVALUATION_TIMEOUT)
        result['pass_fail_status'] = 1 if is_passed else 0
        evaluated_results.append(result)
        
    return evaluated_results

def write_results_to_csv(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Write evaluation results to CSV file.
    
    Args:
        results: List of result dictionaries
        output_path: Path to output CSV file
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Define fieldnames based on the schema
    fieldnames = [
        'model_id', 'problem_id', 'tokens_generated', 
        'energy_kwh', 'runtime_seconds', 'pass_fail_status'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for row in results:
            writer.writerow(row)
    
    logger.info(f"Wrote {len(results)} rows to {output_path}")

def main():
    """
    Main entry point for the evaluation script.
    
    This function:
    1. Loads raw inference results from data/processed/energy_inference_raw.csv
    2. Loads HumanEval problems from data/raw/human_eval_data.jsonl
    3. Evaluates each solution against its test suite
    4. Joins results and writes to data/processed/energy_results_raw.csv
    """
    # Define paths
    input_path = os.path.join(DATA_PROCESSED_DIR, 'energy_inference_raw.csv')
    problems_path = os.path.join(DATA_RAW_DIR, 'human_eval_data.jsonl')
    output_path = os.path.join(DATA_PROCESSED_DIR, 'energy_results_raw.csv')
    
    logger.info("Starting evaluation process...")
    
    # Load data
    try:
        inference_results = load_raw_results(input_path)
        problems = load_problems(problems_path)
    except FileNotFoundError as e:
        logger.error(f"Failed to load data: {e}")
        raise
    
    if not inference_results:
        logger.warning("No inference results to evaluate. Creating empty output file.")
        write_results_to_csv([], output_path)
        return
    
    if not problems:
        logger.error("No problems loaded. Cannot evaluate solutions.")
        raise ValueError("No problems loaded from HumanEval dataset")
    
    # Evaluate solutions
    logger.info(f"Evaluating {len(inference_results)} solutions...")
    evaluated_results = evaluate_all_solutions(inference_results, problems)
    
    # Write results
    write_results_to_csv(evaluated_results, output_path)
    
    # Summary
    passed_count = sum(1 for r in evaluated_results if r.get('pass_fail_status') == 1)
    total_count = len(evaluated_results)
    logger.info(f"Evaluation complete: {passed_count}/{total_count} solutions passed ({passed_count/total_count*100:.1f}%)")
    logger.info(f"Results written to {output_path}")

if __name__ == '__main__':
    main()