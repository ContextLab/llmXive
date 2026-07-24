import os
import sys
import json
import logging
import tempfile
import shutil
import ast
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

from models import InputProblem, ConvergenceTrajectory, ConvergenceStatus
from scripts.execute import setup_execution_env, validate_code_syntax, execute_code
from data_loader import load_processed_dataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global model/tokenizer cache
_model = None
_tokenizer = None

def load_model(model_path: str, device: str = "cpu"):
    """
    Load the model and tokenizer.
    Caches them globally to avoid reloading during multiple calls.
    """
    global _model, _tokenizer
    if _model is None:
        logger.info(f"Loading model from {model_path} on {device}...")
        _tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        if 'CodeLlama' in model_path or 'codellama' in model_path:
            _tokenizer.pad_token = _tokenizer.eos_token
            _tokenizer.padding_side = "left"

        _model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float32 if device == "cpu" else torch.float16,
            device_map="auto" if device != "cpu" else None,
            trust_remote_code=True
        )
        if device == "cpu":
            _model = _model.to(device)
        logger.info("Model loaded successfully.")
    return _model, _tokenizer

def generate_solution(prompt: str, model, tokenizer, max_new_tokens: int = 512, temperature: float = 0.2) -> str:
    """
    Generate a single solution given a prompt.
    """
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Extract code block if present
    if "```python" in response:
        start = response.find("```python") + len("```python")
        end = response.find("```", start)
        return response[start:end].strip()
    return response.strip()

def load_input_problems(data_path: str) -> List[InputProblem]:
    """
    Load processed dataset from JSON.
    """
    with open(data_path, 'r') as f:
        data = json.load(f)
    problems = []
    for item in data:
        problems.append(InputProblem(
            task_id=item.get('task_id'),
            prompt=item.get('prompt'),
            test=item.get('test'),
            difficulty=item.get('difficulty', 'unknown')
        ))
    return problems

def execute_code_in_sandbox(code: str, test_code: str, timeout: int = 10) -> Tuple[bool, str]:
    """
    Execute code in a sandbox and compare against test cases.
    Returns (is_correct, output)
    """
    try:
        # Validate syntax first
        if not validate_code_syntax(code):
            return False, "SyntaxError"

        # Setup environment
        env = setup_execution_env()

        # Execute
        result = execute_code(code, test_code, env=env, timeout=timeout)

        if result.get('status') == 'success':
            return True, result.get('output', '')
        else:
            return False, result.get('error', 'Execution failed')
    except Exception as e:
        logger.error(f"Execution error: {e}")
        return False, str(e)

def detect_convergence(trajectory: List[Dict[str, Any]], test_code: str) -> int:
    """
    Detect the first step (k) where the solution passes all tests.
    Returns the step index (1-based) or -1 if no convergence.
    """
    for k, step in enumerate(trajectory, start=1):
        code = step.get('code', '')
        is_correct, _ = execute_code_in_sandbox(code, test_code)
        if is_correct:
            return k
    return -1

def save_non_convergence_log(non_converged_problems: List[Dict], path: str):
    """
    Log problems that did not converge within max_k steps.
    """
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(non_converged_problems, f, indent=2)
    logger.info(f"Saved non-convergence log to {path}")

def write_convergence_results(results: List[ConvergenceTrajectory], path: str):
    """
    Write convergence results to a CSV file.
    Columns: task_id, k_correct, trajectory_status
    """
    import csv
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['task_id', 'k_correct', 'trajectory_status'])
        for traj in results:
            status = 'converged' if traj.k_correct > 0 else 'non_converged'
            writer.writerow([traj.task_id, traj.k_correct, status])
    logger.info(f"Saved convergence results to {path}")

def save_convergence_results(results: List[ConvergenceTrajectory], path: str):
    """
    Save full trajectory details to JSON.
    """
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    data = [
        {
            'task_id': r.task_id,
            'k_correct': r.k_correct,
            'trajectory_status': 'converged' if r.k_correct > 0 else 'non_converged',
            'steps': [
                {
                    'k': s.k,
                    'code': s.code,
                    'correct': s.correct,
                    'output': s.output
                }
                for s in r.steps
            ]
        }
        for r in results
    ]
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved full convergence results to {path}")

def run_refinement_loop(problem: InputProblem, model, tokenizer, max_k: int = 3) -> ConvergenceTrajectory:
    """
    Run iterative refinement loop for a single problem.
    For k=1: input is prompt.
    For k>1: input is prompt + "\n" + prev_output.
    """
    steps = []
    current_prompt = problem.prompt
    k_correct = -1

    for k in range(1, max_k + 1):
        code = generate_solution(current_prompt, model, tokenizer)
        is_correct, output = execute_code_in_sandbox(code, problem.test)
        steps.append({
            'k': k,
            'code': code,
            'correct': is_correct,
            'output': output
        })

        if is_correct and k_correct == -1:
            k_correct = k
            break

        # Prepare prompt for next iteration
        if k < max_k:
            current_prompt = f"{problem.prompt}\nPrevious attempt:\n{code}\nPlease refine the solution:"

    return ConvergenceTrajectory(
        task_id=problem.task_id,
        k_correct=k_correct,
        steps=steps
    )

def run_sensitivity_inference_pass(
    dataset_path: str,
    output_path: str,
    model_path: str,
    max_k: int = 4,
    device: str = "cpu"
):
    """
    Re-run model for k=4 on the same dataset to generate trajectory data for sensitivity analysis (SC-004).
    This function implements the T013e task.

    Args:
        dataset_path: Path to the filtered dataset JSON (from T004e)
        output_path: Path to save the convergence results CSV
        model_path: Path to the model checkpoint
        max_k: Number of refinement steps (fixed at 4 for sensitivity analysis)
        device: Device to run model on ('cpu' or 'cuda')
    """
    logger.info(f"Starting sensitivity inference pass with max_k={max_k}")

    # Load model
    model, tokenizer = load_model(model_path, device)

    # Load problems
    problems = load_input_problems(dataset_path)
    logger.info(f"Loaded {len(problems)} problems from {dataset_path}")

    results = []
    non_converged = []

    for i, problem in enumerate(problems):
        logger.info(f"Processing problem {i+1}/{len(problems)}: {problem.task_id}")
        trajectory = run_refinement_loop(problem, model, tokenizer, max_k=max_k)
        results.append(trajectory)

        if trajectory.k_correct == -1:
            non_converged.append({
                'task_id': problem.task_id,
                'max_k': max_k,
                'reason': 'No solution passed tests within {max_k} iterations'
            })

    # Write results
    write_convergence_results(results, output_path)

    # Log non-convergence
    non_conv_log_path = str(Path(output_path).parent / "sensitivity_non_convergence_log.json")
    save_non_convergence_log(non_converged, non_conv_log_path)

    logger.info(f"Sensitivity inference pass completed. Results saved to {output_path}")
    return results

def main():
    """
    Entry point for running the sensitivity inference pass.
    Expects environment variables or command line args for configuration.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Run sensitivity inference pass (k=4)")
    parser.add_argument("--dataset", type=str, required=True, help="Path to filtered dataset JSON")
    parser.add_argument("--output", type=str, required=True, help="Path to save convergence results CSV")
    parser.add_argument("--model", type=str, default="codellama/CodeLlama-1.3b-Instruct", help="Model path")
    parser.add_argument("--device", type=str, default="cpu", choices=["cpu", "cuda"], help="Device")
    parser.add_argument("--max_k", type=int, default=4, help="Number of refinement steps")

    args = parser.parse_args()

    run_sensitivity_inference_pass(
        dataset_path=args.dataset,
        output_path=args.output,
        model_path=args.model,
        max_k=args.max_k,
        device=args.device
    )

if __name__ == "__main__":
    main()