import os
import sys
import json
import logging
import tempfile
import shutil
import csv
import hashlib
import random
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig
import torch
import numpy as np

# Import local modules
from src.config import load_config, get_config_value, ensure_config_file
from src.utils import set_global_seed, calculate_flops
from src.models import InputProblem, ConvergenceTrajectory, ConvergenceStatus
from src.data_loader import load_filtered_splits

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SandboxResult:
    is_correct: bool
    output: str
    execution_time: float
    error_message: Optional[str] = None

def load_model(config: Dict[str, Any]) -> Tuple[Any, Any]:
    """Load the model and tokenizer."""
    model_path = get_config_value("MODEL_PATH", config)
    device = get_config_value("DEVICE", config, default="cpu")
    
    logger.info(f"Loading model from {model_path} on {device}")
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            device_map=device if device != "cpu" else None
        )
        if device == "cpu":
            model = model.to("cpu")
        
        # Ensure tokenizer has a pad token
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        logger.info("Model loaded successfully")
        return model, tokenizer
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def generate_solution(
    prompt: str, 
    model: Any, 
    tokenizer: Any, 
    k: int, 
    temperature: float = 0.7,
    top_p: float = 0.95,
    max_new_tokens: int = 512
) -> List[str]:
    """Generate k solutions for a given prompt."""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    # Set generation parameters
    generation_config = GenerationConfig(
        temperature=temperature,
        top_p=top_p,
        do_sample=True,
        max_new_tokens=max_new_tokens,
        pad_token_id=tokenizer.pad_token_id,
        eos_token_id=tokenizer.eos_token_id
    )
    
    # Generate multiple samples
    generated_ids_list = model.generate(
        **inputs,
        generation_config=generation_config,
        num_return_sequences=k,
        return_dict_in_generate=True,
        output_scores=False
    )
    
    # Decode the generated tokens
    outputs = []
    for i in range(k):
        # Extract the generated tokens for this sequence
        generated_ids = generated_ids_list.sequences[i]
        # Remove input tokens
        generated_ids = generated_ids[inputs['input_ids'].shape[1]:]
        decoded = tokenizer.decode(generated_ids, skip_special_tokens=True)
        outputs.append(decoded)
    
    return outputs

def execute_code_in_sandbox(code: str, test_cases: List[Dict[str, Any]]) -> SandboxResult:
    """Execute code in a sandbox and validate against test cases."""
    start_time = time.time()
    
    try:
        # Create a temporary directory for execution
        with tempfile.TemporaryDirectory() as tmpdir:
            code_file = os.path.join(tmpdir, "solution.py")
            with open(code_file, "w") as f:
                f.write(code)
            
            # Execute the code
            exec_globals = {}
            exec_locals = {}
            exec(compile(open(code_file).read(), code_file, 'exec'), exec_globals, exec_locals)
            
            # Validate against test cases
            is_correct = True
            for test_case in test_cases:
                try:
                    input_args = test_case.get("input", {})
                    expected_output = test_case.get("expected_output")
                    func_name = test_case.get("function_name", "solution")
                    
                    if func_name in exec_locals:
                        result = exec_locals[func_name](**input_args)
                        if result != expected_output:
                            is_correct = False
                            break
                    else:
                        is_correct = False
                        break
                except Exception:
                    is_correct = False
                    break
    
    except Exception as e:
        return SandboxResult(
            is_correct=False,
            output="",
            execution_time=0,
            error_message=str(e)
        )
    
    execution_time = time.time() - start_time
    return SandboxResult(
        is_correct=is_correct,
        output=code,
        execution_time=execution_time
    )

def load_input_problem(problem_data: Dict[str, Any]) -> InputProblem:
    """Load an input problem from data."""
    return InputProblem(
        task_id=problem_data.get("task_id"),
        prompt=problem_data.get("prompt"),
        test_cases=problem_data.get("test_cases", []),
        difficulty=problem_data.get("difficulty", "unknown")
    )

def detect_convergence(results: List[SandboxResult], k_max: int = 3) -> Dict[str, Any]:
    """Detect convergence based on results."""
    first_correct_step = None
    is_censored = True
    
    for k, result in enumerate(results, 1):
        if result.is_correct:
            first_correct_step = k
            is_censored = False
            break
    
    if first_correct_step is None:
        first_correct_step = k_max
    
    return {
        "first_correct_step": first_correct_step,
        "censored": is_censored,
        "time_to_event": first_correct_step
    }

def save_convergence_results(results: List[Dict[str, Any]], output_path: str):
    """Save convergence results to a CSV file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', newline='') as csvfile:
        fieldnames = ['task_id', 'k', 'output', 'is_correct', 'first_correct_step', 'censored', 'time_to_event']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for result in results:
            writer.writerow(result)
    
    logger.info(f"Saved convergence results to {output_path}")

def run_iterative_inference(
    model: Any,
    tokenizer: Any,
    problem: InputProblem,
    k_range: List[int],
    config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Run iterative inference for a single problem across k values."""
    results = []
    temperature = get_config_value("MODEL_TEMP", config, default=0.7)
    top_p = get_config_value("MODEL_TOP_P", config, default=0.95)
    
    # Prepare the prompt
    prompt = f"Complete the following function:\n\n{problem.prompt}"
    
    # Track convergence
    all_solutions = {}
    for k in k_range:
        # Set seed for determinism
        set_global_seed(get_config_value("RANDOM_SEED", config, default=42))
        
        # Generate solutions
        solutions = generate_solution(
            prompt, 
            model, 
            tokenizer, 
            k=1,  # Generate one solution per k for convergence
            temperature=temperature,
            top_p=top_p
        )
        
        if solutions:
            all_solutions[k] = solutions[0]
    
    # Determine convergence
    convergence = detect_convergence(
        [SandboxResult(
            is_correct=execute_code_in_sandbox(all_solutions[k], problem.test_cases).is_correct if k in all_solutions else False,
            output=all_solutions.get(k, ""),
            execution_time=0
        ) for k in sorted(k_range)],
        k_max=max(k_range)
    )
    
    first_correct_step = convergence["first_correct_step"]
    censored = convergence["censored"]
    time_to_event = convergence["time_to_event"]
    
    for k in k_range:
        is_correct = False
        if k in all_solutions:
            result = execute_code_in_sandbox(all_solutions[k], problem.test_cases)
            is_correct = result.is_correct
        
        results.append({
            "task_id": problem.task_id,
            "k": k,
            "output": all_solutions.get(k, ""),
            "is_correct": is_correct,
            "first_correct_step": first_correct_step,
            "censored": censored,
            "time_to_event": time_to_event
        })
    
    return results

def main():
    """Main entry point for convergence inference."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run convergence inference")
    parser.add_argument("--input", type=str, required=True, help="Input data file (JSON)")
    parser.add_argument("--output", type=str, required=True, help="Output CSV file")
    parser.add_argument("--k_range", type=int, nargs="+", default=[1, 2, 3], help="K values to test")
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    # Load model
    model, tokenizer = load_model(config)
    
    # Load input data
    logger.info(f"Loading input data from {args.input}")
    data = load_filtered_splits(args.input)
    
    all_results = []
    
    # Process each problem
    for problem_data in data:
        problem = load_input_problem(problem_data)
        logger.info(f"Processing problem: {problem.task_id}")
        
        try:
            results = run_iterative_inference(
                model, 
                tokenizer, 
                problem, 
                args.k_range, 
                config
            )
            all_results.extend(results)
        except Exception as e:
            logger.error(f"Failed to process problem {problem.task_id}: {e}")
            # Log exclusion
            continue
    
    # Save results
    save_convergence_results(all_results, args.output)
    
    logger.info("Convergence inference completed successfully")

if __name__ == "__main__":
    main()