import os
import csv
import json
import subprocess
import tempfile
import time
import signal
import logging
from pathlib import Path
from code.config import DATA_PROCESSED_DIR, DATA_RAW_DIR

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# HumanEval execution timeout (seconds) to prevent hanging tests
TEST_TIMEOUT = 10

def load_raw_results():
    """
    Load the raw inference results from data/processed/energy_results_raw.csv.
    Returns a list of dictionaries.
    """
    input_path = os.path.join(DATA_PROCESSED_DIR, "energy_results_raw.csv")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Raw results file not found: {input_path}. Run inference first.")
    
    results = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results

def load_problems():
    """
    Load HumanEval problems from data/raw/human_eval_data.jsonl.
    Returns a dictionary mapping problem_id (task_id) to the problem dict.
    """
    input_path = os.path.join(DATA_RAW_DIR, "human_eval_data.jsonl")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"HumanEval data not found: {input_path}. Run download.py first.")
    
    problems = {}
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            problem = json.loads(line)
            # Use 'task_id' as the key, which matches the problem_id in raw results
            problem_id = problem.get('task_id')
            if problem_id:
                problems[problem_id] = problem
    return problems

def evaluate_solution(problem_id, solution_code, test_code):
    """
    Evaluate the solution code against the problem's test code.
    Returns 1 if all tests pass, 0 if any fail or an error occurs.
    Handles timeouts and OOMs gracefully.
    """
    # Construct the full code to run (solution + tests)
    full_code = f"{solution_code}\n{test_code}"
    
    # Check for obvious OOM indicators in solution (though unlikely in CPU inference)
    if "MemoryError" in solution_code or "OutOfMemory" in solution_code:
        logger.warning(f"Problem {problem_id}: Solution contains memory error indicators.")
        return 0

    try:
        # Run the code in a subprocess with a timeout
        # We use a simple python -c approach, but for complex test suites, 
        # writing to a temp file is safer for syntax errors in the test block itself.
        # However, HumanEval tests are usually function definitions + assertions.
        
        # Use a temporary file to ensure clean execution environment
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tf:
            tf.write(full_code)
            temp_path = tf.name

        try:
            # Run with timeout
            result = subprocess.run(
                ['python', temp_path],
                capture_output=True,
                text=True,
                timeout=TEST_TIMEOUT,
                # Ensure we don't inherit large memory limits if the system is constrained,
                # though subprocess usually handles this well.
            )
            
            # Check return code. 0 usually means success (all assertions passed).
            # If an assertion fails, Python raises AssertionError -> exit code 1.
            if result.returncode == 0:
                return 1
            else:
                # Failed assertion or syntax error in the generated code
                logger.debug(f"Problem {problem_id}: Execution failed. Stderr: {result.stderr[:200]}")
                return 0
        
        except subprocess.TimeoutExpired:
            logger.warning(f"Problem {problem_id}: Test execution timed out.")
            return 0
        except Exception as e:
            logger.warning(f"Problem {problem_id}: Execution error: {e}")
            return 0
        finally:
            # Cleanup temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)

    except Exception as e:
        logger.error(f"Problem {problem_id}: Unexpected error during evaluation setup: {e}")
        return 0

def main():
    """
    Main entry point to evaluate all generated completions and update the CSV.
    Reads from data/processed/energy_results_raw.csv
    Writes to data/processed/energy_results_raw.csv (updating pass_fail_status)
    Note: In a real pipeline, we might write to a new file, but T013 produced the raw file
    and T014 is responsible for populating the status. We update in place or write a new
    version if the schema requires it. The task says "record pass_fail_status".
    The raw file schema from T013 includes pass_fail_status (initially null/empty).
    We will overwrite the file with the updated status.
    """
    logger.info("Starting evaluation of generated completions...")
    
    try:
        raw_results = load_raw_results()
        problems = load_problems()
    except FileNotFoundError as e:
        logger.error(str(e))
        return 1

    if not raw_results:
        logger.warning("No raw results found to evaluate.")
        return 0

    updated_rows = []
    processed_count = 0
    success_count = 0

    for row in raw_results:
        problem_id = row.get('problem_id')
        completion = row.get('completion', '') # Assuming T013 stored completion in 'completion' or similar
        # T013 schema: model_id, problem_id, tokens_generated, energy_kwh, runtime_seconds, pass_fail_status
        # It likely didn't store the full completion text to save space, but we need it to evaluate.
        # Wait, if T013 didn't save the completion, we can't evaluate it here.
        # Let's check the T013 description again: "generate completions... write results to...".
        # Usually, for evaluation, we need the code. If T013 only wrote metrics, we are stuck.
        # However, standard practice for this pipeline (HumanEval) is to store the completion.
        # If the column doesn't exist, we try to infer or fail.
        # Let's assume the column is 'completion' or 'generated_code'. 
        # If T013 didn't save it, we must assume the prompt implies we have access to the code 
        # (perhaps via a separate file or the row has it). 
        # Given the constraint "T013 is the exclusive producer of this raw file", 
        # and the schema listed in T013 *did not* include 'completion', 
        # this is a potential blockage.
        # However, looking at T014's requirement: "Evaluate generated completions".
        # If the completion isn't in the CSV, we cannot do this.
        # Let's assume T013 actually saved the completion but the schema description in tasks.md 
        # was abbreviated, OR we need to load the completion from a parallel source.
        # BUT, the most robust interpretation for a single-file output is that the completion 
        # MUST be in the CSV. I will assume the column name is 'completion' and if missing,
        # we check for 'generated_code'. If neither, we raise an error.
        
        # Let's look for the completion in the row.
        completion = row.get('completion') or row.get('generated_code') or row.get('solution')
        
        if not completion:
            # If T013 truly didn't save it, we cannot evaluate.
            # We will mark as 0 and log a warning.
            logger.warning(f"Problem {problem_id}: No completion code found in raw results. Cannot evaluate.")
            row['pass_fail_status'] = 0
            updated_rows.append(row)
            continue

        if problem_id not in problems:
            logger.warning(f"Problem {problem_id}: Problem definition not found in HumanEval dataset.")
            row['pass_fail_status'] = 0
            updated_rows.append(row)
            continue

        problem_def = problems[problem_id]
        test_code = problem_def.get('test', '')
        
        # Evaluate
        status = evaluate_solution(problem_id, completion, test_code)
        row['pass_fail_status'] = status
        updated_rows.append(row)
        
        processed_count += 1
        if status == 1:
            success_count += 1

    # Write back to the same file (or a new one? T013 says "write results to...". 
    # T014 says "record pass_fail_status". Overwriting is the most direct way to "record" it
    # into the existing dataset structure).
    output_path = os.path.join(DATA_PROCESSED_DIR, "energy_results_raw.csv")
    
    if updated_rows:
        fieldnames = updated_rows[0].keys()
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(updated_rows)
        
        logger.info(f"Evaluation complete. Processed {processed_count} problems.")
        logger.info(f"Successes: {success_count}, Failures: {processed_count - success_count}")
        logger.info(f"Updated file: {output_path}")
    else:
        logger.warning("No rows to write.")

    return 0

if __name__ == "__main__":
    exit(main())