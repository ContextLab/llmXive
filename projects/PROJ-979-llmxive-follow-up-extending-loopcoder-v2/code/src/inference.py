import os
import sys
import json
import logging
import tempfile
import shutil
import subprocess
import time
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import yaml

from src.config import load_config
from src.models import InputProblem, ConvergenceTrajectory
from src.utils import set_global_seed

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SandboxResult:
    def __init__(self, success: bool, output: str, error: str = ""):
        self.success = success
        self.output = output
        self.error = error

def load_model(model_path: str, device: str = "cpu") -> Tuple[Any, Any]:
    """Load model and tokenizer."""
    logger.info(f"Loading model from {model_path} on {device}")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        model = AutoModelForCausalLM.from_pretrained(
            model_path, 
            torch_dtype=torch.float32 if device == "cpu" else torch.float16,
            device_map=device,
            trust_remote_code=True
        )
        model.eval()
        return model, tokenizer
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def generate_solution(prompt: str, model: Any, tokenizer: Any, k: int, temperature: float = 0.7, top_p: float = 0.95) -> List[str]:
    """Generate k solutions for a given prompt."""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    generated_ids = model.generate(
        **inputs,
        max_new_tokens=512,
        do_sample=True,
        temperature=temperature,
        top_p=top_p,
        pad_token_id=tokenizer.pad_token_id,
        num_return_sequences=k
    )
    
    solutions = []
    for i in range(k):
        output_ids = generated_ids[i][inputs['input_ids'].shape[1]:]
        solution = tokenizer.decode(output_ids, skip_special_tokens=True)
        solutions.append(solution)
    return solutions

def execute_code_in_sandbox(code: str, test_code: str, docker_image: str = "entropy-sandbox:latest") -> SandboxResult:
    """Execute code in a Docker sandbox and return the result."""
    with tempfile.TemporaryDirectory() as tmpdir:
        code_file = os.path.join(tmpdir, "solution.py")
        test_file = os.path.join(tmpdir, "test.py")
        
        with open(code_file, "w") as f:
            f.write(code)
        with open(test_file, "w") as f:
            f.write(test_code)
        
        # Create a simple test runner script
        runner_script = os.path.join(tmpdir, "run_test.py")
        with open(runner_script, "w") as f:
            f.write(f"""
import sys
import os
import importlib.util

# Add current directory to path
sys.path.insert(0, '.')

# Load solution
spec = importlib.util.spec_from_file_location("solution", "{code_file}")
solution_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(solution_module)

# Load test
try:
    with open("{test_file}", "r") as f:
  test_code = f.read()
    exec(test_code, solution_module.__dict__)
    print("PASS")
    sys.exit(0)
except Exception as e:
    print(f"FAIL: {{e}}")
    sys.exit(1)
""")
        
        try:
            result = subprocess.run(
                ["docker", "run", "--rm", "-v", f"{tmpdir}:/workspace", "-w", "/workspace", docker_image, "python", "run_test.py"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return SandboxResult(success=True, output="PASS")
            else:
                return SandboxResult(success=False, output=result.stdout, error=result.stderr)
        except subprocess.TimeoutExpired:
            return SandboxResult(success=False, output="", error="Execution timeout")
        except Exception as e:
            return SandboxResult(success=False, output="", error=str(e))

def detect_convergence(results: List[Dict[str, Any]], k_current: int) -> Tuple[bool, Optional[int]]:
    """Detect if convergence has occurred at the current step."""
    for i, res in enumerate(results):
        if res.get("is_correct", False):
            return True, i + 1  # Return 1-based index
    return False, None

def save_convergence_results(results: List[Dict[str, Any]], output_path: str):
    """Save convergence results to CSV."""
    if not results:
        logger.warning("No results to save")
        return
    
    fieldnames = ["task_id", "k", "output", "is_correct", "converged", "first_correct_step", "censored", "time_to_event"]
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    logger.info(f"Saved {len(results)} results to {output_path}")

def load_input_problem(file_path: str) -> List[Dict[str, Any]]:
    """Load input problems from JSON file."""
    with open(file_path, "r") as f:
        data = json.load(f)
    
    # Combine train and test splits if both exist
    problems = []
    if "train" in data:
        problems.extend(data["train"])
    if "test" in data:
        problems.extend(data["test"])
    
    return problems

def run_iterative_inference(
    problems: List[Dict[str, Any]],
    model: Any,
    tokenizer: Any,
    k_range: List[int],
    config: Dict[str, Any],
    output_path: str
) -> List[Dict[str, Any]]:
    """Run iterative inference for k=1..max(k_range) and track convergence."""
    all_results = []
    docker_image = "entropy-sandbox:latest"
    
    # Sampling parameters from config
    temperature = config.get("model_temperature", 0.7)
    top_p = config.get("model_top_p", 0.95)
    
    for problem in problems:
        task_id = problem["task_id"]
        prompt = problem["prompt"]
        test_code = problem["test"]
        
        logger.info(f"Processing {task_id}")
        
        # Stateful tracking for this problem
        state = {
            "converged": False,
            "first_correct_step": None,
            "censored": False
        }
        
        # Track all outputs for this task_id
        task_results = []
        
        for k in k_range:
            start_time = time.perf_counter()
            
            # Generate k fresh samples for this k value
            samples = generate_solution(prompt, model, tokenizer, k, temperature, top_p)
            
            for sample_idx, sample in enumerate(samples):
                # Execute in sandbox
                sandbox_result = execute_code_in_sandbox(sample, test_code, docker_image)
                
                is_correct = sandbox_result.success
                elapsed = time.perf_counter() - start_time
                
                # Determine convergence status
                converged = False
                first_correct_step = None
                censored = False
                
                if state["converged"]:
                    # Already converged at an earlier step
                    converged = False
                    first_correct_step = state["first_correct_step"]
                else:
                    if is_correct:
                        # First correct step found
                        converged = True
                        first_correct_step = k
                        state["converged"] = True
                        state["first_correct_step"] = k
                    elif k == max(k_range):
                        # Reached max k without convergence
                        censored = True
                        state["censored"] = True
                
                result_entry = {
                    "task_id": task_id,
                    "k": k,
                    "output": sample[:200] + "..." if len(sample) > 200 else sample,  # Truncate for CSV
                    "is_correct": is_correct,
                    "converged": converged,
                    "first_correct_step": first_correct_step,
                    "censored": censored,
                    "time_to_event": int(elapsed * 1000)  # ms
                }
                
                task_results.append(result_entry)
                all_results.append(result_entry)
                
                # If we found a correct solution, we could break early for this k,
                # but the spec says run k=1,2,3 sequentially with fresh samples each time.
                # We continue to generate all samples for the current k.
            
            # If converged at this k, we still continue to next k to fill the table,
            # but subsequent entries will be marked as not converged (already found).
        
        logger.info(f"Completed {task_id}")
    
    return all_results

def main():
    """Main entry point for convergence inference."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run convergence inference pipeline")
    parser.add_argument("--input", type=str, required=True, help="Path to input splits JSON")
    parser.add_argument("--output", type=str, required=True, help="Path to output CSV")
    parser.add_argument("--k_range", type=str, default="[1,2,3]", help="Comma-separated or JSON list of k values")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Path to config file")
    args = parser.parse_args()
    
    # Parse k_range
    if args.k_range.startswith("[") and args.k_range.endswith("]"):
        k_range = json.loads(args.k_range)
    else:
        k_range = [int(x.strip()) for x in args.k_range.split(",")]
    k_range = sorted(k_range)
    
    # Load config
    config = load_config(args.config)
    
    # Set global seed
    set_global_seed(config.get("seed", 42))
    
    # Determine model path
    model_path = os.environ.get("CODELLAMA_CPU_PATH") or os.environ.get("CODELLAMA_GPU_PATH")
    if not model_path:
        raise ValueError("Model path not set via CODELLAMA_CPU_PATH or CODELLAMA_GPU_PATH environment variable")
    
    # Determine device
    device = "cuda" if os.environ.get("CODELLAMA_GPU_PATH") and torch.cuda.is_available() else "cpu"
    
    # Load model
    model, tokenizer = load_model(model_path, device)
    
    # Load input problems
    problems = load_input_problem(args.input)
    logger.info(f"Loaded {len(problems)} problems")
    
    # Run inference
    results = run_iterative_inference(problems, model, tokenizer, k_range, config, args.output)
    
    # Save results
    save_convergence_results(results, args.output)
    
    logger.info("Convergence inference completed successfully")

if __name__ == "__main__":
    main()