"""
Inference module for running convergence analysis on code generation tasks.
Implements iterative inference (k=1..K) with stateful tracking and Docker sandbox execution.
"""
import os
import sys
import json
import logging
import tempfile
import shutil
import argparse
import ast
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import pandas as pd
import torch
import random
import numpy as np

# Import from project modules
from src.data_loader import load_config, load_filtered_splits
from src.utils import set_global_seed
from scripts.execute import execute_code

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class SandboxResult:
    """Result of executing code in the sandbox."""
    success: bool
    output: str
    error: Optional[str] = None
    execution_time: Optional[float] = None


def load_model(model_path: str, device: str = "cpu"):
    """
    Load the CodeLlama model from the specified path.
    
    Args:
        model_path: Path to the model (from env var or config)
        device: Device to load model to ('cpu' or 'cuda')
        
    Returns:
        Loaded model and tokenizer
    """
    from transformers import AutoModelForCausalLM, AutoTokenizer
    
    logger.info(f"Loading model from {model_path} on {device}")
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float32 if device == "cpu" else torch.float16,
            device_map="auto" if device == "cuda" else None
        )
        
        if device == "cpu":
            model = model.to("cpu")
        
        logger.info("Model loaded successfully")
        return model, tokenizer
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise


def generate_solution(prompt: str, model, tokenizer, k: int, max_new_tokens: int = 512) -> str:
    """
    Generate a code solution for the given prompt.
    
    Args:
        prompt: The problem prompt
        model: Loaded model
        tokenizer: Loaded tokenizer
        k: Number of samples to generate (for this implementation, generates one sample per call)
        max_new_tokens: Maximum tokens to generate
        
    Returns:
        Generated code solution
    """
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    # Generate with some randomness for diversity
    outputs = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        temperature=0.7,
        top_p=0.95,
        do_sample=True,
        num_return_sequences=1
    )
    
    generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Extract code block if present
    if "```python" in generated:
        start = generated.find("```python") + len("```python")
        end = generated.find("```", start)
        if end == -1:
            end = len(generated)
        code = generated[start:end].strip()
    else:
        code = generated.strip()
        
    return code


def execute_code_in_sandbox(code: str, test_case: str, timeout: int = 30) -> SandboxResult:
    """
    Execute generated code against test cases in a sandbox.
    
    Args:
        code: Generated code to execute
        test_case: Test case string to run
        timeout: Execution timeout in seconds
        
    Returns:
        SandboxResult with execution status
    """
    try:
        # Create temporary directory for execution
        with tempfile.TemporaryDirectory() as tmpdir:
            code_file = os.path.join(tmpdir, "solution.py")
            
            # Write code to file
            with open(code_file, "w") as f:
                f.write(code)
            
            # Prepare test execution
            test_code = f"""
import sys
import os
sys.path.insert(0, '{tmpdir}')
{code}
{test_case}
"""
            test_file = os.path.join(tmpdir, "test_runner.py")
            with open(test_file, "w") as f:
                f.write(test_code)
            
            # Execute using the project's execute_code function
            result = execute_code(
                code_path=test_file,
                timeout=timeout,
                use_docker=False  # Disable docker for CPU validation
            )
            
            return SandboxResult(
                success=result.get("success", False),
                output=result.get("output", ""),
                error=result.get("error", None),
                execution_time=result.get("execution_time", None)
            )
    except Exception as e:
        logger.error(f"Sandbox execution failed: {e}")
        return SandboxResult(
            success=False,
            output="",
            error=str(e)
        )


def detect_convergence(results: List[Dict], k_current: int) -> Tuple[bool, Optional[int]]:
    """
    Detect if the model has converged to a correct solution.
    
    Args:
        results: List of previous results for this task_id
        k_current: Current k value
        
    Returns:
        Tuple of (converged, first_correct_step)
    """
    for i, result in enumerate(results):
        if result.get("is_correct", False):
            return True, i + 1  # 1-indexed step
    return False, None


def save_convergence_results(results: List[Dict], output_path: str):
    """
    Save convergence results to CSV.
    
    Args:
        results: List of convergence result dictionaries
        output_path: Path to save CSV file
    """
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(results)} results to {output_path}")


def load_input_problems(input_path: str) -> List[Dict]:
    """
    Load input problems from JSON file.
    
    Args:
        input_path: Path to JSON file
        
    Returns:
        List of input problem dictionaries
    """
    with open(input_path, "r") as f:
        data = json.load(f)
    
    # Return test set for convergence analysis
    return data.get("test", data.get("train", []))


def run_iterative_inference(
    problems: List[Dict],
    model,
    tokenizer,
    k_range: List[int],
    output_path: str
) -> List[Dict]:
    """
    Run iterative inference for k=1..K on all problems.
    
    Args:
        problems: List of input problems
        model: Loaded model
        tokenizer: Loaded tokenizer
        k_range: List of k values to test
        output_path: Path to save results
        
    Returns:
        List of all convergence results
    """
    all_results = []
    
    for problem in problems:
        task_id = problem.get("task_id", "unknown")
        prompt = problem.get("prompt", "")
        test_case = problem.get("test", "")
        
        logger.info(f"Processing task {task_id}")
        
        # State tracking for this problem
        problem_results = []
        first_correct_step = None
        converged = False
        
        for k in k_range:
            # Generate solution
            solution = generate_solution(prompt, model, tokenizer, k)
            
            # Execute in sandbox
            sandbox_result = execute_code_in_sandbox(solution, test_case)
            
            is_correct = sandbox_result.success
            
            # Update convergence state
            if is_correct and first_correct_step is None:
                first_correct_step = k
                converged = True
            
            # Determine censored status
            censored = False
            if k == k_range[-1] and first_correct_step is None:
                censored = True
            
            result = {
                "task_id": task_id,
                "k": k,
                "output": solution[:500] if len(solution) > 500 else solution,  # Truncate for storage
                "is_correct": is_correct,
                "converged": (k == first_correct_step) if first_correct_step else False,
                "first_correct_step": first_correct_step,
                "censored": censored
            }
            
            problem_results.append(result)
            all_results.append(result)
            
            logger.info(f"  k={k}: correct={is_correct}, converged={result['converged']}")
    
    # Save results
    save_convergence_results(all_results, output_path)
    
    return all_results


def main():
    """Main entry point for convergence inference."""
    parser = argparse.ArgumentParser(description="Run convergence inference analysis")
    parser.add_argument("--input", required=True, help="Path to input splits JSON")
    parser.add_argument("--output", required=True, help="Path to output CSV file")
    parser.add_argument("--k_range", type=str, default="[1,2,3]", help="K values to test (e.g., [1,2,3])")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    # Set global seed
    set_global_seed(args.seed)
    
    # Parse k_range
    k_range = json.loads(args.k_range)
    
    # Load configuration
    config = load_config()
    model_path = os.environ.get("CODELLAMA_CPU_PATH", config.get("CODELLAMA_CPU_PATH"))
    
    if not model_path or model_path == "NOT_SET":
        logger.error("Model path not set. Please set CODELLAMA_CPU_PATH environment variable.")
        sys.exit(1)
    
    # Load model
    model, tokenizer = load_model(model_path, device="cpu")
    
    # Load input problems
    problems = load_input_problems(args.input)
    logger.info(f"Loaded {len(problems)} problems")
    
    # Run inference
    results = run_iterative_inference(
        problems=problems,
        model=model,
        tokenizer=tokenizer,
        k_range=k_range,
        output_path=args.output
    )
    
    logger.info(f"Convergence inference complete. Results saved to {args.output}")


if __name__ == "__main__":
    main()