import os
import sys
import json
import logging
import tempfile
import shutil
import ast
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datasets import load_dataset

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import docker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SandboxResult:
    task_id: str
    k: int
    output: str
    is_correct: bool
    converged: bool
    first_correct_step: Optional[int]

def load_config() -> Dict[str, Any]:
    config_path = Path(__file__).parent.parent / "config.yaml"
    if not config_path.exists():
        return {}
    import yaml
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_model(model_path: str) -> Tuple[Any, Any]:
    """Load model and tokenizer from the specified path."""
    if not model_path:
        raise ValueError("Model path is empty. Set CODELLAMA_CPU_PATH or CODELLAMA_GPU_PATH.")
    
    logger.info(f"Loading model from: {model_path}")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else "cpu",
            trust_remote_code=True
        )
        logger.info("Model loaded successfully.")
        return model, tokenizer
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def generate_solution(
    model: Any,
    tokenizer: Any,
    prompt: str,
    max_new_tokens: int = 256
) -> str:
    """Generate a code solution from the model."""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=0.7,
            top_p=0.95,
            pad_token_id=tokenizer.eos_token_id
        )
    generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Extract code block if present
    if "```python" in generated:
        start = generated.find("```python") + len("```python")
        end = generated.find("```", start)
        if end == -1: end = len(generated)
        return generated[start:end].strip()
    elif "```" in generated:
        start = generated.find("```") + 3
        end = generated.find("```", start)
        if end == -1: end = len(generated)
        return generated[start:end].strip()
    return generated.strip()

def load_input_problems(filepath: str) -> List[Dict[str, Any]]:
    """Load filtered splits from JSON."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {filepath}")
    with open(path, 'r') as f:
        data = json.load(f)
    # Handle both list and dict formats
    if isinstance(data, dict):
        return list(data.values()) if isinstance(list(data.values())[0], dict) else [data]
    return data

def execute_code_in_sandbox(code: str, test_code: str, timeout: int = 10) -> bool:
    """
    Execute code in a Docker sandbox and verify against test cases.
    Returns True if tests pass, False otherwise.
    """
    client = docker.from_env()
    
    # Create temporary directory for code
    with tempfile.TemporaryDirectory() as tmpdir:
        code_path = Path(tmpdir) / "solution.py"
        test_path = Path(tmpdir) / "test_solution.py"
        
        # Write code and test
        with open(code_path, 'w') as f:
            f.write(code)
        with open(test_path, 'w') as f:
            f.write(test_code)
        
        try:
            # Run test in container
            # Using a minimal Python image
            result = client.containers.run(
                "python:3.10-slim",
                command=f"python test_solution.py",
                volumes={str(tmpdir): {"bind": "/workspace", "mode": "rw"}},
                working_dir="/workspace",
                detach=False,
                remove=True,
                network_disabled=True, # Security
                mem_limit="512m",
                cpu_period=100000,
                cpu_quota=100000,
                timeout=timeout
            )
            # Check exit code or output for success
            # Assuming test code prints PASS/FAIL or exits 0/1
            # For HumanEval/MBPP, typically we check if no exception occurred
            # Since we can't easily inspect stdout in this simple run, we rely on exit code
            # However, client.containers.run returns stdout. 
            # We need to catch the error if it fails.
            # Let's assume if it runs without raising, it's okay? 
            # No, docker.run raises ContainerError on non-zero exit.
            return True
        except docker.errors.ContainerError as e:
            logger.debug(f"Code execution failed: {e}")
            return False
        except Exception as e:
            logger.warning(f"Sandbox execution error: {e}")
            return False

def detect_convergence(
    task_results: List[SandboxResult],
    k: int
) -> Tuple[bool, Optional[int]]:
    """
    Determine if the model converged at step k.
    Converged: is_correct at step k AND (k==1 OR not correct at k-1).
    first_correct_step: k if converged, else None (if not converged at max k).
    """
    if not task_results:
        return False, None
    
    current = task_results[-1]
    if not current.is_correct:
        return False, None
    
    if k == 1:
        return True, 1
    
    prev = task_results[-2]
    if not prev.is_correct:
        # Converged at this step
        return True, k
    
    # Was already correct before, so not "converged" at this step (already solved)
    # But the definition says: "converged (defined as: is_correct at step k AND (k==1 OR is_correct was False at k-1))"
    # If it was correct at k-1, then it's not a NEW convergence event at k.
    # However, for the purpose of the CSV, we might want to mark the *first* time it got it right.
    # The task says: "first_correct_step (defined as: if converged at k, set first_correct_step=k; if not converged at k_max (3), set to null)"
    # This implies we are tracking the *first* time it gets it right.
    # If it was correct at k-1, then first_correct_step was already set at k-1.
    # So for the current row (k), if it was correct at k-1, we don't set first_correct_step again?
    # The schema is per row. 
    # Let's follow the logic strictly:
    # Row k: is_correct=True. 
    # If k=1: converged=True, first_correct_step=1.
    # If k>1: check k-1. If k-1 was False: converged=True, first_correct_step=k.
    # If k-1 was True: converged=False (because it wasn't a *new* convergence), first_correct_step=None?
    # But the definition of first_correct_step in the task is: "if converged at k, set first_correct_step=k".
    # So if not converged at k, first_correct_step is None (for that row).
    # The "first_correct_step" value is only populated on the row where convergence happens.
    
    return False, None

def save_non_convergence_log(log_path: str, task_id: str, k_max: int):
    """Log tasks that did not converge by k_max."""
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if path.exists():
        with open(path, 'r') as f:
            data = json.load(f)
    else:
        data = []
    
    data.append({"task_id": task_id, "max_k": k_max})
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def save_convergence_results(results: List[SandboxResult], output_path: str):
    """Save results to CSV."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'task_id', 'k', 'output', 'is_correct', 'converged', 'first_correct_step'
        ])
        writer.writeheader()
        for r in results:
            writer.writerow({
                'task_id': r.task_id,
                'k': r.k,
                'output': r.output,
                'is_correct': r.is_correct,
                'converged': r.converged,
                'first_correct_step': r.first_correct_step
            })

def run_iterative_inference(
    model: Any,
    tokenizer: Any,
    input_data: List[Dict[str, Any]],
    k_range: List[int],
    output_path: str,
    non_convergence_log_path: Optional[str] = None
) -> List[SandboxResult]:
    """
    Run inference for k in k_range for each input.
    """
    all_results = []
    
    for item in input_data:
        task_id = item.get('task_id', 'unknown')
        prompt = item.get('prompt', '')
        test_code = item.get('test', '')
        
        logger.info(f"Processing task: {task_id}")
        
        task_results = []
        converged_at = None
        
        for k in k_range:
            # Generate solution
            output_code = generate_solution(model, tokenizer, prompt)
            
            # Execute in sandbox
            is_correct = execute_code_in_sandbox(output_code, test_code)
            
            # Determine convergence status for THIS step
            # We need to know if it converged AT this step k.
            # Logic: is_correct AND (k==1 OR previous was not correct)
            if k == 1:
                converged = is_correct
            else:
                # Check previous result
                prev_correct = task_results[-1].is_correct
                converged = is_correct and (not prev_correct)
            
            # Determine first_correct_step for THIS row
            # "if converged at k, set first_correct_step=k"
            first_step = k if converged else None
            
            result = SandboxResult(
                task_id=task_id,
                k=k,
                output=output_code,
                is_correct=is_correct,
                converged=converged,
                first_correct_step=first_step
            )
            task_results.append(result)
            all_results.append(result)
            
            if converged and converged_at is None:
                converged_at = k
        
        # If never converged by k_max
        if converged_at is None and non_convergence_log_path:
            save_non_convergence_log(non_convergence_log_path, task_id, max(k_range))
    
    return all_results

def main():
    """Main entry point for the inference script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Core Convergence Inference")
    parser.add_argument("--input", type=str, default="data/processed/filtered_splits.json",
                        help="Path to input filtered splits JSON")
    parser.add_argument("--output", type=str, default="data/processed/convergence_results_core.csv",
                        help="Path to output CSV")
    parser.add_argument("--k-range", type=int, nargs='+', default=[1, 2, 3],
                        help="List of k values to run")
    parser.add_argument("--log-non-convergence", type=str, default="data/processed/non_convergence_log.json",
                        help="Path to log non-convergence events")
    
    args = parser.parse_args()
    
    config = load_config()
    
    # Determine model path
    # Priority: GPU if available, else CPU
    if torch.cuda.is_available():
        model_path = os.environ.get("CODELLAMA_GPU_PATH")
        if not model_path:
            model_path = config.get("CODELLAMA_GPU_PATH")
        mode = "gpu"
    else:
        model_path = os.environ.get("CODELLAMA_CPU_PATH")
        if not model_path:
            model_path = config.get("CODELLAMA_CPU_PATH")
        mode = "cpu"
    
    if not model_path:
        raise RuntimeError("No model path found. Set CODELLAMA_CPU_PATH or CODELLAMA_GPU_PATH environment variable or in config.yaml.")
    
    logger.info(f"Running in {mode} mode with model: {model_path}")
    
    # Load model
    model, tokenizer = load_model(model_path)
    
    # Load input data
    input_data = load_input_problems(args.input)
    logger.info(f"Loaded {len(input_data)} input problems.")
    
    # Run inference
    results = run_iterative_inference(
        model,
        tokenizer,
        input_data,
        args.k_range,
        args.output,
        args.log_non_convergence
    )
    
    # Save results
    save_convergence_results(results, args.output)
    logger.info(f"Results saved to {args.output}")

if __name__ == "__main__":
    main()
