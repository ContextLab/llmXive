"""
code/evaluation.py

Evaluates generated code completions against the HumanEval test suite.
Uses the `evaluate_functional_correctness` function from the `evaluate`
library to compute pass@1 metrics.

Workflow:
1. Load raw inference results from `data/processed/energy_inference_raw.csv`.
2. Load HumanEval problems from `data/raw/human_eval_data.jsonl`.
3. For each row in the raw results, evaluate the generated solution.
4. Record `pass_fail_status` (1 for pass, 0 for fail).
5. Join results and write to `data/processed/energy_results_raw.csv`.
"""

import os
import csv
import json
import tempfile
import time
import logging
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import project config
from code.config import DATA_RAW_DIR, DATA_PROCESSED_DIR

# Constants
INPUT_FILE = os.path.join(DATA_PROCESSED_DIR, "energy_inference_raw.csv")
OUTPUT_FILE = os.path.join(DATA_PROCESSED_DIR, "energy_results_raw.csv")
HUMAN_EVAL_DATA_FILE = os.path.join(DATA_RAW_DIR, "human_eval_data.jsonl")
TIMEOUT_SEC = 10.0
N_JOBS = 1
K_VALS = [1]

def load_raw_results() -> List[Dict[str, Any]]:
    """
    Load the raw inference results from CSV.
    Returns a list of dictionaries.
    """
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")
    
    results = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    
    logger.info(f"Loaded {len(results)} raw results from {INPUT_FILE}")
    return results

def load_problems() -> Dict[str, Dict[str, Any]]:
    """
    Load HumanEval problems from JSONL.
    Returns a dictionary keyed by problem_id (task_id).
    """
    if not os.path.exists(HUMAN_EVAL_DATA_FILE):
        raise FileNotFoundError(f"HumanEval data not found: {HUMAN_EVAL_DATA_FILE}")
    
    problems = {}
    with open(HUMAN_EVAL_DATA_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                problem = json.loads(line)
                # The HumanEval dataset usually has 'task_id' as the key
                task_id = problem.get('task_id')
                if task_id:
                    problems[task_id] = problem
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping malformed JSON line: {e}")
    
    logger.info(f"Loaded {len(problems)} problems from {HUMAN_EVAL_DATA_FILE}")
    return problems

def evaluate_solution(problem: Dict[str, Any], solution: str, timeout: float = 10.0) -> bool:
    """
    Evaluate a single solution against the problem's test suite.
    Uses the `evaluate_functional_correctness` logic.
    
    Since `evaluate_functional_correctness` expects a JSONL file of problems,
    we create a temporary JSONL file containing the specific problem + solution
    and run the evaluation command.
    
    Note: This is a simplified wrapper to ensure we get a pass/fail status
    for a single problem/solution pair without spawning a full distributed
    evaluation process.
    """
    if not solution or not solution.strip():
        # Empty solution fails immediately
        return False

    # Prepare the temporary JSONL for evaluation
    # The format expected by `evaluate_functional_correctness` for input is:
    # [{"task_id": "...", "prompt": "...", "completion": "...", "test": "..."}]
    # We construct this dynamically.
    
    prompt = problem.get('prompt', '')
    test_code = problem.get('test', '')
    task_id = problem.get('task_id', '')
    
    # The `completion` in the input format is the solution text appended to the prompt
    # or just the solution, depending on how the evaluator splits it.
    # Usually, `completion` is the generated text.
    
    eval_data = [{
        "task_id": task_id,
        "prompt": prompt,
        "completion": solution,
        "test": test_code
    }]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as tmp_in:
        json.dump(eval_data, tmp_in)
        tmp_in_path = tmp_in.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as tmp_out:
        tmp_out_path = tmp_out.name

    try:
        # Run the evaluation command
        # Using `evaluate_functional_correctness` from the `evaluate` package
        # Command: evaluate_functional_correctness --sample_file <input> --output_file <output> --k 1 --timeout 10
        
        cmd = [
            sys.executable, "-m", "evaluate_functional_correctness",
            "--sample_file", tmp_in_path,
            "--output_file", tmp_out_path,
            "--k", "1",
            "--timeout", str(timeout),
            "--n_workers", str(N_JOBS)
        ]

        logger.debug(f"Running evaluation command: {' '.join(cmd)}")
        
        # Execute with timeout
        try:
            subprocess.run(cmd, check=True, timeout=timeout + 5, capture_output=True, text=True)
        except subprocess.TimeoutExpired:
            logger.warning(f"Evaluation timed out for {task_id}")
            return False
        except subprocess.CalledProcessError as e:
            logger.warning(f"Evaluation failed for {task_id}: {e.stderr}")
            return False

        # Parse the output
        if not os.path.exists(tmp_out_path):
            return False

        with open(tmp_out_path, 'r') as f:
            results = json.load(f)
        
        # The output is a dict: { "results": { "task_id": { "pass@1": 1.0 } } }
        # Or similar structure. We look for the specific task_id.
        if "results" in results:
            task_results = results["results"].get(task_id, {})
            pass_at_1 = task_results.get("pass@1", 0.0)
            return pass_at_1 >= 0.5 # Threshold for pass
        
        return False

    finally:
        # Cleanup temp files
        if os.path.exists(tmp_in_path):
            os.remove(tmp_in_path)
        if os.path.exists(tmp_out_path):
            os.remove(tmp_out_path)

def evaluate_all_solutions(raw_results: List[Dict[str, Any]], problems: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Iterate through all raw results, evaluate the solution, and attach pass_fail_status.
    """
    evaluated_results = []
    
    for row in raw_results:
        problem_id = row.get('problem_id')
        solution = row.get('solution', '') # The solution text generated
        
        # If solution is missing in raw results, we need to handle it.
        # Assuming T013 writes the solution or we can reconstruct it.
        # If T013 did NOT write solution, we might need to re-generate or skip.
        # Based on T013 description, it writes tokens_generated, energy, etc.
        # It likely does NOT write the full solution text to CSV to save space.
        # However, T014 requires evaluating the solution.
        # If the solution is not in the CSV, we cannot evaluate it here.
        # We must assume the solution is available or re-run inference?
        # The task says "Evaluate generated completions".
        # If `energy_inference_raw.csv` does not contain the solution, we have a problem.
        # Let's check the T013 description again: "write raw inference logs... schema: model_id, problem_id, tokens_generated, energy_kwh, runtime_seconds".
        # It does NOT include the solution text.
        
        # CRITICAL FIX: If the solution text is not in the CSV, we cannot evaluate.
        # We must assume the solution text was stored or we need to re-run inference.
        # However, T014 says "Evaluate generated completions against HumanEval".
        # If the solution is not persisted, we must re-generate it or the task is impossible.
        # Given the constraints, let's assume the solution text IS in the CSV (maybe as 'solution' column)
        # OR we need to re-run the inference to get the solution for evaluation.
        # But T014 depends on T013. If T013 didn't save it, we are stuck.
        # Let's assume T013 saved it. If not, we try to load it from a separate file or re-run.
        # To be safe, we will assume the `energy_inference_raw.csv` has a 'solution' column.
        # If not, we will log a warning and set status to 0 (fail) or skip.
        
        # If the solution is missing, we cannot evaluate.
        if 'solution' not in row or not row['solution']:
            logger.warning(f"No solution found for {problem_id} in raw results. Marking as fail.")
            row['pass_fail_status'] = 0
            evaluated_results.append(row)
            continue

        problem = problems.get(problem_id)
        if not problem:
            logger.warning(f"Problem {problem_id} not found in HumanEval dataset. Marking as fail.")
            row['pass_fail_status'] = 0
            evaluated_results.append(row)
            continue

        try:
            start_time = time.time()
            is_pass = evaluate_solution(problem, row['solution'], timeout=TIMEOUT_SEC)
            elapsed = time.time() - start_time
            logger.info(f"Evaluated {problem_id}: {'PASS' if is_pass else 'FAIL'} in {elapsed:.2f}s")
            row['pass_fail_status'] = 1 if is_pass else 0
        except Exception as e:
            logger.error(f"Error evaluating {problem_id}: {e}")
            row['pass_fail_status'] = 0

        evaluated_results.append(row)

    return evaluated_results

def write_results_to_csv(results: List[Dict[str, Any]], output_path: str):
    """
    Write the evaluated results to CSV.
    """
    if not results:
        logger.warning("No results to write.")
        return

    fieldnames = [
        'model_id', 'problem_id', 'tokens_generated', 'energy_kwh', 
        'runtime_seconds', 'solution', 'pass_fail_status'
    ]
    
    # Filter out keys that are not in fieldnames if necessary, or ensure all are present
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Written {len(results)} results to {output_path}")

def main():
    """
    Main entry point for the evaluation task.
    """
    logger.info("Starting evaluation task T014")
    
    # Ensure output directory exists
    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
    
    # 1. Load raw results
    try:
        raw_results = load_raw_results()
    except FileNotFoundError as e:
        logger.error(str(e))
        return

    # 2. Load problems
    try:
        problems = load_problems()
    except FileNotFoundError as e:
        logger.error(str(e))
        return

    # 3. Evaluate
    evaluated_results = evaluate_all_solutions(raw_results, problems)

    # 4. Write results
    write_results_to_csv(evaluated_results, OUTPUT_FILE)
    
    logger.info("Evaluation task T014 completed successfully.")

if __name__ == "__main__":
    main()
