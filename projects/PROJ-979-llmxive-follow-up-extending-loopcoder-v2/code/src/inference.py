import os
import sys
import json
import logging
import tempfile
import shutil
import time
import hashlib
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig
import torch
import random
import numpy as np

from src.config import get_config_value
from src.utils import set_global_seed
from src.models import InputProblem, ConvergenceTrajectory, ConvergenceStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SandboxResult:
    task_id: str
    k: int
    output: str
    is_correct: bool
    execution_time: float
    error_msg: Optional[str] = None

def load_model(model_path: str):
    """Load model and tokenizer."""
    logger.info(f"Loading model from {model_path}")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        if not hasattr(tokenizer, 'pad_token') or tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {device}")
        
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            device_map="auto" if device == "cuda" else None,
            trust_remote_code=True
        )
        if device == "cpu":
            model = model.to(device)
        
        return model, tokenizer, device
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def generate_solution(model, tokenizer, prompt: str, k: int, temperature: float = 0.7, top_p: float = 0.95) -> str:
    """Generate a single solution for a given prompt."""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=512,
            temperature=temperature,
            top_p=top_p,
            do_sample=True,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id
        )
    generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Extract code block if present
    if "```python" in generated:
        start = generated.find("```python") + len("```python")
        end = generated.find("```", start)
        if end != -1:
            return generated[start:end].strip()
    elif "```" in generated:
        start = generated.find("```") + 3
        end = generated.find("```", start)
        if end != -1:
            return generated[start:end].strip()
    return generated.strip()

def execute_code_in_sandbox(code: str, test_case: Dict[str, Any]) -> Tuple[bool, Optional[str], float]:
    """Execute code in a simple sandbox and check against test case."""
    start_time = time.time()
    try:
        # Create a temporary directory for execution
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write code to file
            code_file = os.path.join(tmpdir, "solution.py")
            with open(code_file, "w") as f:
                f.write(code)
            
            # Prepare execution command
            # Note: This is a simplified sandbox. In production, use Docker.
            exec_globals = {}
            exec(code, exec_globals)
            
            # Run test case
            func_name = test_case.get("func_name")
            if func_name and func_name in exec_globals:
                func = exec_globals[func_name]
                inputs = test_case.get("inputs", [])
                expected = test_case.get("expected")
                
                for inp in inputs:
                    result = func(*inp)
                    if result != expected:
                        return False, f"Output mismatch: got {result}, expected {expected}", time.time() - start_time
                return True, None, time.time() - start_time
            else:
                return False, f"Function {func_name} not found", time.time() - start_time
    except Exception as e:
        return False, str(e), time.time() - start_time

def load_input_problem(problem_path: str) -> List[InputProblem]:
    """Load input problems from JSON file."""
    with open(problem_path, "r") as f:
        data = json.load(f)
    
    problems = []
    for item in data:
        problems.append(InputProblem(
            task_id=item["task_id"],
            prompt=item["prompt"],
            test_cases=item.get("test_cases", [])
        ))
    return problems

def detect_convergence(results: List[SandboxResult]) -> Tuple[Optional[int], bool]:
    """
    Detect convergence: find the smallest k where is_correct is True.
    Returns (first_correct_step, censored).
    censored is True if no correct answer by k=3 (or max k).
    """
    first_correct = None
    for res in sorted(results, key=lambda x: x.k):
        if res.is_correct:
            first_correct = res.k
            break
    
    censored = first_correct is None
    return first_correct, censored

def save_convergence_results(results: List[ConvergenceTrajectory], output_path: str):
    """Save convergence results to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    rows = []
    for traj in results:
        rows.append({
            "task_id": traj.task_id,
            "k": traj.k,
            "output": traj.output[:500] if traj.output else "",  # Truncate for CSV safety
            "is_correct": traj.is_correct,
            "first_correct_step": traj.first_correct_step,
            "censored": traj.censored,
            "time_to_event": traj.time_to_event
        })
    
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(rows)} rows to {output_path}")

def run_iterative_inference(
    model, 
    tokenizer, 
    problems: List[InputProblem], 
    k_range: List[int], 
    device: str
) -> List[ConvergenceTrajectory]:
    """
    Run iterative inference for k in k_range.
    For each problem and each k, generate ONE solution and check correctness.
    Track convergence across k values.
    """
    all_results = []
    
    for problem in problems:
        logger.info(f"Processing task: {problem.task_id}")
        
        k_results = []
        for k in k_range:
            # Reset seed for determinism per k
            set_global_seed(get_config_value("RANDOM_SEED", 42))
            
            # Generate solution
            prompt = problem.prompt
            solution = generate_solution(model, tokenizer, prompt, k)
            
            # Check correctness against test cases
            is_correct = False
            for test_case in problem.test_cases:
                correct, error, _ = execute_code_in_sandbox(solution, test_case)
                if correct:
                    is_correct = True
                    break
            
            k_results.append(SandboxResult(
                task_id=problem.task_id,
                k=k,
                output=solution,
                is_correct=is_correct
            ))
        
        # Detect convergence
        first_correct, censored = detect_convergence(k_results)
        time_to_event = first_correct if first_correct is not None else max(k_range)
        
        # Create trajectory for each k
        for res in k_results:
            traj = ConvergenceTrajectory(
                task_id=res.task_id,
                k=res.k,
                output=res.output,
                is_correct=res.is_correct,
                first_correct_step=first_correct,
                censored=censored,
                time_to_event=time_to_event
            )
            all_results.append(traj)
    
    return all_results

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run convergence inference")
    parser.add_argument("--input", required=True, help="Path to input splits JSON")
    parser.add_argument("--output", required=True, help="Path to output CSV")
    parser.add_argument("--k_range", nargs="+", type=int, default=[1, 2, 3], help="K values to test")
    parser.add_argument("--model_path", default=None, help="Model path (overrides config)")
    args = parser.parse_args()
    
    # Load config
    model_path = args.model_path or get_config_value("MODEL_PATH")
    if not model_path:
        raise ValueError("Model path not specified in config or args")
    
    # Load model
    model, tokenizer, device = load_model(model_path)
    
    # Load problems
    problems = load_input_problem(args.input)
    
    # Run inference
    logger.info(f"Starting inference for {len(problems)} problems with k_range={args.k_range}")
    results = run_iterative_inference(model, tokenizer, problems, args.k_range, device)
    
    # Save results
    save_convergence_results(results, args.output)
    
    logger.info("Inference complete")

if __name__ == "__main__":
    main()