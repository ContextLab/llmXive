"""
Core Convergence Inference & Logging (k=1..3)
Implements iterative inference, Docker sandbox execution, and convergence detection.
"""
import os
import sys
import json
import logging
import tempfile
import shutil
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import random

# Import from sibling modules as per API surface
from .data_loader import load_config, load_filtered_splits
from .utils import set_global_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SandboxResult:
    """Result of code execution in sandbox."""
    success: bool
    output: str
    error: str
    runtime_s: float

def load_model(model_path: str, device: str = "cpu"):
    """
    Load the CodeLlama model.
    Raises FileNotFoundError if model path is invalid or missing.
    """
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        logger.info(f"Loading model from {model_path} on {device}...")
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype="auto" if device == "cuda" else None,
            device_map="auto" if device == "cuda" else None
        )
        logger.info("Model loaded successfully.")
        return model, tokenizer
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def generate_solution(prompt: str, model, tokenizer, k: int) -> str:
    """
    Generate a code solution for the given prompt.
    Uses the model to generate text based on the prompt.
    """
    inputs = tokenizer(prompt, return_tensors="pt")
    if inputs['input_ids'].device.type == 'cpu':
        inputs = {k: v for k, v in inputs.items()}
    
    # Generate
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=512,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
    
    # Decode
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Extract code block if present
    if "```python" in generated_text:
        start = generated_text.find("```python") + len("```python")
        end = generated_text.find("```", start)
        return generated_text[start:end].strip()
    elif "```" in generated_text:
        start = generated_text.find("```") + 3
        end = generated_text.find("```", start)
        return generated_text[start:end].strip()
    return generated_text.strip()

def execute_code_in_sandbox(code: str, test_code: str, timeout: int = 10) -> SandboxResult:
    """
    Execute code in a Docker sandbox and compare against test.
    Returns SandboxResult with success status and output.
    """
    start_time = time.perf_counter()
    try:
        # Create temporary directory for execution
        with tempfile.TemporaryDirectory() as tmpdir:
            solution_path = os.path.join(tmpdir, "solution.py")
            test_path = os.path.join(tmpdir, "test.py")
            
            # Write solution and test
            with open(solution_path, "w") as f:
                f.write(code)
            
            with open(test_path, "w") as f:
                f.write(test_code)
            
            # Run tests using Docker sandbox
            # Assuming Docker image 'entropy-sandbox:latest' is built (T009b)
            docker_cmd = [
                "docker", "run", "--rm",
                "-v", f"{tmpdir}:/workspace",
                "-w", "/workspace",
                "entropy-sandbox:latest",
                "python", "test.py"
            ]
            
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            runtime = time.perf_counter() - start_time
            
            if result.returncode == 0:
                return SandboxResult(
                    success=True,
                    output=result.stdout,
                    error="",
                    runtime_s=runtime
                )
            else:
                return SandboxResult(
                    success=False,
                    output=result.stdout,
                    error=result.stderr,
                    runtime_s=runtime
                )
                
    except subprocess.TimeoutExpired:
        runtime = time.perf_counter() - start_time
        return SandboxResult(
            success=False,
            output="",
            error="Execution timeout",
            runtime_s=runtime
        )
    except Exception as e:
        runtime = time.perf_counter() - start_time
        return SandboxResult(
            success=False,
            output="",
            error=str(e),
            runtime_s=runtime
        )

def detect_convergence(
    history: List[Dict[str, Any]],
    current_k: int,
    k_max: int = 3
) -> Tuple[bool, Optional[int], bool]:
    """
    Detect convergence based on the sequence of results.
    
    Args:
        history: List of results for k=1, 2, ..., current_k
        current_k: Current iteration number
        k_max: Maximum allowed iterations
        
    Returns:
        Tuple of (converged, first_correct_step, censored)
    """
    # Check if current result is correct
    is_correct_current = history[-1]['is_correct']
    
    # Determine if converged
    # Converged if: is_correct at step k AND (k==1 OR is_correct was False at k-1)
    converged = False
    first_correct_step = None
    censored = False
    
    if is_correct_current:
        # Check if this is the first correct step
        if current_k == 1:
            converged = True
            first_correct_step = 1
        else:
            # Check previous step
            prev_correct = history[-2]['is_correct']
            if not prev_correct:
                converged = True
                first_correct_step = current_k
            else:
                # Already converged earlier, but we record convergence at this step too
                # Actually, per spec: "converged" means the FIRST time it becomes correct
                # So if it was correct before, this step is not the convergence point
                # But we still need to track if it's correct now
                # The spec says: "converged (defined as: is_correct at step k AND (k==1 OR is_correct was False at k-1))"
                # So if it was correct before, this step is NOT a convergence event
                converged = False
                # Find the first correct step from history
                for i, h in enumerate(history):
                    if h['is_correct']:
                        first_correct_step = i + 1
                        break
    else:
        # Not correct at this step
        if current_k >= k_max:
            # Max iterations reached without convergence
            censored = True
        else:
            # Continue iterating
            pass
    
    return converged, first_correct_step, censored

def save_non_convergence_log(task_id: str, k: int, reason: str, output_path: str):
    """Log non-convergence events."""
    log_entry = {
        "task_id": task_id,
        "k": k,
        "reason": reason
    }
    
    # Load existing log if exists
    log_file = Path(output_path)
    if log_file.exists():
        with open(log_file, "r") as f:
            log_data = json.load(f)
    else:
        log_data = []
    
    log_data.append(log_entry)
    
    with open(log_file, "w") as f:
        json.dump(log_data, f, indent=2)

def save_convergence_results(results: List[Dict[str, Any]], output_path: str):
    """Save convergence results to CSV."""
    import csv
    
    if not results:
        logger.warning("No results to save.")
        return
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Write to CSV
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Saved {len(results)} results to {output_path}")

def run_iterative_inference(
    input_problems: List[Dict[str, Any]],
    model,
    tokenizer,
    k_range: List[int],
    output_path: str,
    sample_size: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Run iterative inference for k=1, 2, 3 on input problems.
    
    Args:
        input_problems: List of input problems (task_id, prompt, test, difficulty)
        model: Loaded model
        tokenizer: Loaded tokenizer
        k_range: List of k values to test (e.g., [1, 2, 3])
        output_path: Path to save results
        sample_size: Optional sample size for testing
        
    Returns:
        List of convergence results
    """
    results = []
    non_convergence_log = []
    
    # Filter sample if needed
    if sample_size and sample_size < len(input_problems):
        input_problems = random.sample(input_problems, sample_size)
    
    logger.info(f"Processing {len(input_problems)} input problems with k_range={k_range}")
    
    for problem in input_problems:
        task_id = problem['task_id']
        prompt = problem['prompt']
        test_code = problem['test']
        
        history = []
        
        for k in k_range:
            logger.info(f"Processing {task_id} at k={k}")
            
            # Generate solution
            try:
                solution = generate_solution(prompt, model, tokenizer, k)
            except Exception as e:
                logger.error(f"Generation failed for {task_id} at k={k}: {e}")
                solution = ""
            
            # Execute in sandbox
            sandbox_result = execute_code_in_sandbox(solution, test_code)
            
            # Determine correctness
            is_correct = sandbox_result.success
            
            # Build result record
            record = {
                "task_id": task_id,
                "k": k,
                "output": solution,
                "is_correct": is_correct,
                "converged": False,
                "first_correct_step": None,
                "censored": False
            }
            
            # Detect convergence
            history.append(record)
            converged, first_correct_step, censored = detect_convergence(
                history, k, k_max=max(k_range)
            )
            
            # Update record
            record["converged"] = converged
            record["first_correct_step"] = first_correct_step
            record["censored"] = censored
            
            results.append(record)
            
            # Log non-convergence if at max k and not converged
            if k == max(k_range) and not converged:
                non_convergence_log.append({
                    "task_id": task_id,
                    "k": k,
                    "reason": "max_iterations_reached"
                })
    
    # Save results
    save_convergence_results(results, output_path)
    
    # Save non-convergence log
    if non_convergence_log:
        log_path = str(Path(output_path).parent / "non_convergence_log.json")
        with open(log_path, "w") as f:
            json.dump(non_convergence_log, f, indent=2)
        logger.info(f"Saved non-convergence log to {log_path}")
    
    return results

def load_input_problems(input_path: str) -> List[Dict[str, Any]]:
    """Load input problems from JSON file."""
    with open(input_path, "r") as f:
        data = json.load(f)
    return data.get("test", [])  # We use test split for inference

def main():
    """Main entry point for convergence inference."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run convergence inference")
    parser.add_argument("--output", type=str, required=True,
                      help="Output path for convergence results CSV")
    parser.add_argument("--sample-size", type=int, default=None,
                      help="Sample size for testing")
    parser.add_argument("--config", type=str, default="code/config.yaml",
                      help="Path to config file")
    args = parser.parse_args()
    
    # Load config
    config = load_config(args.config)
    
    # Set global seed
    seed = config.get("seed", 42)
    set_global_seed(seed)
    
    # Determine model path
    model_path = os.getenv("CODELLAMA_CPU_PATH") or os.getenv("CODELLAMA_GPU_PATH")
    if not model_path:
        raise ValueError("Neither CODELLAMA_CPU_PATH nor CODELLAMA_GPU_PATH is set")
    
    # Determine device
    device = "cuda" if os.getenv("CODELLAMA_GPU_PATH") else "cpu"
    
    # Load model
    model, tokenizer = load_model(model_path, device)
    
    # Load input problems
    input_path = "data/processed/filtered_splits.json"
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    input_problems = load_input_problems(input_path)
    
    # Define k range (k=1, 2, 3 for core analysis)
    k_range = [1, 2, 3]
    
    # Run inference
    results = run_iterative_inference(
        input_problems,
        model,
        tokenizer,
        k_range,
        args.output,
        args.sample_size
    )
    
    logger.info(f"Convergence inference completed. Results saved to {args.output}")

if __name__ == "__main__":
    main()
