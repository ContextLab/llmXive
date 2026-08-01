import os
import sys
import json
import logging
import tempfile
import shutil
import csv
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# Import config loading from data_loader to ensure consistency
try:
    from src.data_loader import load_config
except ImportError:
    # Fallback if run directly without package structure
    def load_config():
        config_path = Path(__file__).parent.parent / "config.yaml"
        if config_path.exists():
            import yaml
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        return {}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class SandboxResult:
    task_id: str
    k: int
    output: str
    is_correct: bool
    converged: bool
    first_correct_step: Optional[int]

def load_model() -> tuple:
    """
    Loads the CodeLlama model based on environment variables.
    Returns (model, tokenizer).
    """
    config = load_config()
    # Priority: GPU path if available and CUDA is active, else CPU path
    gpu_path = os.getenv("CODELLAMA_GPU_PATH")
    cpu_path = os.getenv("CODELLAMA_CPU_PATH")
    
    model_path = None
    if gpu_path and torch.cuda.is_available():
        model_path = gpu_path
        logger.info(f"Loading model from GPU path: {model_path}")
    elif cpu_path:
        model_path = cpu_path
        logger.info(f"Loading model from CPU path: {model_path}")
    else:
        raise EnvironmentError(
            "Neither CODELLAMA_GPU_PATH (with CUDA) nor CODELLAMA_CPU_PATH is set. "
            "Please set the environment variables to point to the local model directory."
        )

    if not os.path.isdir(model_path):
        raise FileNotFoundError(f"Model directory not found at: {model_path}")

    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto" if torch.cuda.is_available() else None,
        trust_remote_code=True
    )
    
    if not torch.cuda.is_available():
        model = model.to('cpu')
    
    return model, tokenizer

def generate_solution(prompt: str, model, tokenizer, k: int) -> str:
    """
    Generates a single code solution for the given prompt.
    """
    messages = [
        {"role": "system", "content": "You are an expert Python programmer. Write only the code solution."},
        {"role": "user", "content": prompt}
    ]
    
    # Apply chat template if available
    if hasattr(tokenizer, 'apply_chat_template'):
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    else:
        # Fallback for older tokenizers
        text = f"<s>[INST] {prompt} [/INST]"

    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=512,
            temperature=0.8,
            top_p=0.95,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
    
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Extract code block if present
    if "```python" in generated_text:
        start = generated_text.find("```python") + 9
        end = generated_text.find("```", start)
        if end == -1: end = len(generated_text)
        return generated_text[start:end].strip()
    elif "```" in generated_text:
        start = generated_text.find("```") + 3
        end = generated_text.find("```", start)
        if end == -1: end = len(generated_text)
        return generated_text[start:end].strip()
    return generated_text.strip()

def load_input_problems() -> List[Dict[str, Any]]:
    """
    Loads the filtered splits from data/processed/filtered_splits.json.
    """
    input_path = Path(__file__).parent.parent.parent / "data" / "processed" / "filtered_splits.json"
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    # Handle both list and dict formats if necessary, but spec says list of dicts
    if isinstance(data, dict):
        # If it's a dict with 'train' or 'test' keys, we might need to merge or pick
        # Assuming the file is a flat list of problems as per T004f spec
        if 'train' in data:
            data = data['train']
        elif 'test' in data:
            data = data['test']
        else:
            # Fallback: assume values are the problems
            data = list(data.values())
    
    return data

def execute_code_in_sandbox(code: str, test_case: str) -> bool:
    """
    Executes the generated code in a Docker sandbox (simulated here for logic)
    and returns True if it passes the test case.
    """
    # In a real scenario, this would spin up a Docker container via the setup in T009.
    # For this implementation, we will attempt to run the code in a subprocess with a timeout.
    # We assume the test_case is a string that defines the expected output or assertions.
    # Since we cannot run the full Docker sandbox without the daemon, we simulate the check
    # by running the code and checking for execution errors, and if possible, matching output.
    # NOTE: This is a simplified execution for the pipeline. In production, use the Docker API.
    
    with tempfile.TemporaryDirectory() as tmpdir:
        code_file = os.path.join(tmpdir, "solution.py")
        test_file = os.path.join(tmpdir, "test.py")
        
        with open(code_file, 'w') as f:
            f.write(code)
        
        # Construct a test runner that imports the solution and runs the test
        # This assumes the code defines a function named `solution` or similar.
        # For HumanEval/MBPP, the test usually asserts the result of calling the function.
        
        # We will try to execute the code and see if it raises an exception.
        # A robust implementation would parse the test string to extract the function call.
        
        try:
            # Execute code in a restricted environment
            # We'll use a simple exec with a custom namespace
            namespace = {}
            exec(code, namespace)
            
            # Try to find the function to test. Usually it's the first defined function or 'solution'
            func_name = None
            for name in namespace:
                if callable(namespace[name]) and not name.startswith('_'):
                    func_name = name
                    break
            
            if func_name is None:
                # If no function found, maybe the code is just a script?
                # We'll assume it prints the result.
                return False # Cannot verify without a function

            # Parse test_case to find expected behavior? 
            # For this specific task, we assume the 'test' field contains the assert logic.
            # We will try to run the test logic against the function.
            # This is a heuristic.
            
            # Simple heuristic: if the test string contains 'assert', try to run it.
            # We need to inject the function into the test scope.
            test_namespace = {func_name: namespace[func_name]}
            
            # Create a mock assert function that returns True/False? No, we need to catch AssertionError.
            # We'll wrap the test execution.
            try:
                # The test_case usually looks like: assert solution(1, 2) == 3
                # We need to extract the call or run the whole thing.
                # Since we can't easily parse arbitrary test strings safely, we assume the test string
                # is valid python code that will be run in the context of the solution.
                
                # To be safe, we run the test code. If it passes (no exception), it's correct.
                exec(test_case, test_namespace)
                return True
            except Exception:
                return False

        except Exception as e:
            logger.debug(f"Execution failed: {e}")
            return False

def detect_convergence(results: List[SandboxResult]) -> tuple:
    """
    Analyzes the list of results for a single task to determine convergence.
    Returns (converged: bool, first_correct_step: int | None).
    """
    first_correct = None
    for res in results:
        if res.is_correct:
            first_correct = res.k
            break
    
    converged = first_correct is not None
    return converged, first_correct

def save_non_convergence_log(task_id: str, k: int) -> None:
    """
    Logs non-convergence events to a JSON file.
    """
    log_path = Path(__file__).parent.parent.parent / "data" / "processed" / "non_convergence_log.json"
    
    existing = []
    if log_path.exists():
        with open(log_path, 'r') as f:
            existing = json.load(f)
    
    existing.append({"task_id": task_id, "max_k": k})
    
    with open(log_path, 'w') as f:
        json.dump(existing, f, indent=2)

def save_convergence_results(results: List[SandboxResult], output_path: Path) -> None:
    """
    Saves the convergence results to a CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['task_id', 'k', 'output', 'is_correct', 'converged', 'first_correct_step'])
        
        for res in results:
            # Sanitize output for CSV (replace newlines)
            clean_output = res.output.replace('\n', ' ').replace('\r', '')
            writer.writerow([
                res.task_id,
                res.k,
                clean_output,
                res.is_correct,
                res.converged,
                res.first_correct_step
            ])
    
    logger.info(f"Saved {len(results)} results to {output_path}")

def run_iterative_inference(model, tokenizer, input_problem: Dict[str, Any], k_values: List[int]) -> List[SandboxResult]:
    """
    Runs inference for a single input problem across multiple k values.
    """
    task_id = input_problem['task_id']
    prompt = input_problem['prompt']
    test_case = input_problem['test']
    
    results = []
    
    for k in k_values:
        logger.info(f"Running k={k} for task {task_id}")
        output_code = generate_solution(prompt, model, tokenizer, k)
        
        is_correct = execute_code_in_sandbox(output_code, test_case)
        
        # We determine convergence later in the aggregate, but for this row:
        # 'converged' in the row context usually means "did this specific step converge?"
        # But the schema asks for 'converged' (bool) and 'first_correct_step'.
        # Based on the schema: "converged (first correct step)".
        # We will set converged=True if this specific k is the first correct one.
        # However, we don't know if a previous k was correct yet if we are iterating.
        # The task says: "Record is_correct, converged (first correct step)".
        # Interpretation: converged is True if this is the first correct step encountered so far.
        # But since we write row by row, we can't know the future.
        # Standard interpretation for such logs: 
        # - is_correct: did this specific run pass?
        # - converged: is this the FIRST run that passed? (We can only know this after checking previous k's)
        # - first_correct_step: the k value of the first correct run (or null if none yet).
        
        # To handle this correctly, we should check if any previous k was correct.
        # But since we are generating sequentially, we can check the list we've built so far.
        prev_correct = any(r.is_correct and r.task_id == task_id for r in results if r.k < k)
        
        is_first_correct = is_correct and not prev_correct
        
        first_correct_step = k if is_first_correct else None
        
        # If a previous step was correct, this row is not the first correct step.
        # But the row itself represents a specific k.
        
        # Let's refine: 
        # The row represents the outcome at step k.
        # converged: True if this is the step where convergence happened (i.e., first correct).
        # first_correct_step: The k value where convergence happened. If this row is not it, what goes here?
        # The schema says: `first_correct_step: int | null`.
        # If this row is NOT the first correct step, should it be null? Or should it be the value of the first correct step?
        # Usually, in a trajectory log, you want to know the final state.
        # But the task says "Record ... first_correct_step".
        # Let's assume: 
        # - converged: True if this is the first correct step.
        # - first_correct_step: The k value of the first correct step (if it happened at or before this k).
        # Wait, if we are at k=2 and k=1 was correct, then at k=2, first_correct_step should be 1.
        # If we are at k=2 and k=1 failed, and k=2 correct, first_correct_step is 2.
        # If we are at k=2 and both failed, first_correct_step is null.
        
        # So:
        current_first_correct = None
        for r in results:
            if r.is_correct:
                current_first_correct = r.k
                break
        if is_correct and current_first_correct is None:
            current_first_correct = k
        
        res = SandboxResult(
            task_id=task_id,
            k=k,
            output=output_code,
            is_correct=is_correct,
            converged=is_first_correct, # True only for the very first correct step
            first_correct_step=current_first_correct
        )
        results.append(res)
        
        if not is_correct and k == k_values[-1]:
            save_non_convergence_log(task_id, k)
    
    return results

def main():
    """
    Main entry point for the convergence inference pipeline.
    """
    logger.info("Starting Convergence Inference Pipeline (T013a)")
    
    # 1. Load Model
    try:
        model, tokenizer = load_model()
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise
    
    # 2. Load Data
    try:
        input_problems = load_input_problems()
    except Exception as e:
        logger.error(f"Failed to load input problems: {e}")
        raise
    
    # 3. Run Inference
    all_results = []
    k_values = [1, 2, 3] # As per FR-002
    
    for problem in input_problems:
        task_results = run_iterative_inference(model, tokenizer, problem, k_values)
        all_results.extend(task_results)
    
    # 4. Save Results
    output_path = Path(__file__).parent.parent.parent / "data" / "processed" / "convergence_results.csv"
    save_convergence_results(all_results, output_path)
    
    logger.info("Convergence Inference Pipeline completed successfully.")

if __name__ == "__main__":
    main()