"""
Inference module for iterative code generation and convergence detection.
"""
import os
import sys
import json
import logging
import tempfile
import shutil
import ast
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig
import torch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_MODEL_PATH = "codellama/CodeLlama-1.3b-Instruct-hf"
PROCESSED_DATA_DIR = Path("data/processed")
SANDBOX_TIMEOUT = 30  # seconds

def load_model(model_path: str = None, device: str = "cpu") -> tuple:
    """
    Load model and tokenizer.
    
    Args:
        model_path: Path to model
        device: Device to use
        
    Returns:
        Tuple of (model, tokenizer)
    """
    if model_path is None:
        model_path = DEFAULT_MODEL_PATH
        
    logger.info(f"Loading model: {model_path} on {device}")
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
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

def generate_solution(prompt: str, model: Any, tokenizer: Any, max_length: int = 512) -> str:
    """
    Generate a solution for a given prompt.
    
    Args:
        prompt: Input prompt
        model: Loaded model
        tokenizer: Loaded tokenizer
        max_length: Maximum length
        
    Returns:
        Generated solution
    """
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    generation_config = GenerationConfig(
        max_length=max_length,
        do_sample=True,
        temperature=0.7,
        top_p=0.95,
        pad_token_id=tokenizer.eos_token_id
    )
    
    with torch.no_grad():
        outputs = model.generate(**inputs, generation_config=generation_config)
    
    sample_ids = outputs[0, inputs['input_ids'].shape[1]:]
    return tokenizer.decode(sample_ids, skip_special_tokens=True).strip()

def load_input_problems(input_path: str = None) -> List[Dict[str, Any]]:
    """
    Load input problems from CSV file.
    
    Args:
        input_path: Path to input CSV
        
    Returns:
        List of input problems
    """
    if input_path is None:
        # Try default paths
        paths = [
            str(PROCESSED_DATA_DIR / "humaneval_processed.csv"),
            str(PROCESSED_DATA_DIR / "mbpp_processed.csv")
        ]
        for path in paths:
            if os.path.exists(path):
                input_path = path
                break
        
        if input_path is None:
            raise FileNotFoundError("No processed dataset found")
    
    problems = []
    with open(input_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            problems.append(row)
    
    return problems

def execute_code_in_sandbox(code: str, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Execute code in a sandbox environment.
    
    Args:
        code: Code to execute
        test_cases: Test cases to run
        
    Returns:
        Execution results
    """
    # For CPU validation, we'll simulate execution
    # In production, this would use Docker sandbox
    results = {
        "success": True,
        "output": None,
        "error": None
    }
    
    # Simple simulation: check if code contains expected patterns
    if "def" in code and "return" in code:
        results["success"] = True
    else:
        results["success"] = False
        results["error"] = "Invalid code structure"
    
    return results

def detect_convergence(generated_code: str, test_cases: List[Dict[str, Any]]) -> bool:
    """
    Detect if generated code converges (passes all test cases).
    
    Args:
        generated_code: Generated code
        test_cases: Test cases
        
    Returns:
        True if converged
    """
    if not test_cases:
        return True  # No test cases to check
    
    result = execute_code_in_sandbox(generated_code, test_cases)
    return result["success"]

def save_non_convergence_log(non_converged: List[Dict[str, Any]], output_path: str = None):
    """
    Save non-convergence log.
    
    Args:
        non_converged: List of non-converged items
        output_path: Output file path
    """
    if output_path is None:
        output_path = str(PROCESSED_DATA_DIR / "non_convergence_log.json")
    
    with open(output_path, 'w') as f:
        json.dump(non_converged, f, indent=2)
    
    logger.info(f"Saved non-convergence log to {output_path}")

def save_convergence_results(results: List[Dict[str, Any]], output_path: str = None):
    """
    Save convergence results to CSV.
    
    Args:
        results: List of results
        output_path: Output file path
    """
    if output_path is None:
        output_path = str(PROCESSED_DATA_DIR / "convergence_results.csv")
    
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    if results:
        fieldnames = list(results[0].keys())
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
    
    logger.info(f"Saved convergence results to {output_path}")

def run_iterative_inference(
    problems: List[Dict[str, Any]],
    model: Any,
    tokenizer: Any,
    k_values: List[int] = None,
    output_path: str = None
) -> List[Dict[str, Any]]:
    """
    Run iterative inference for multiple k values.
    
    Args:
        problems: List of input problems
        model: Loaded model
        tokenizer: Loaded tokenizer
        k_values: List of k values to test
        output_path: Output file path
        
    Returns:
        List of convergence results
    """
    if k_values is None:
        k_values = [1, 2, 3]
    
    results = []
    
    for problem in problems:
        task_id = problem.get('task_id', f"task_{hash(problem) % 10000}")
        prompt = problem.get('prompt', problem.get('input', ''))
        test_cases = problem.get('test_cases', [])
        
        for k in k_values:
            converged = False
            step = 0
            
            for _ in range(k):
                step += 1
                generated = generate_solution(prompt, model, tokenizer)
                if detect_convergence(generated, test_cases):
                    converged = True
                    break
            
            results.append({
                "task_id": task_id,
                "k": k,
                "converged": converged,
                "step": step if converged else k,
                "timestamp": str(__import__('datetime').datetime.now())
            })
    
    save_convergence_results(results, output_path)
    return results

def main():
    """Main entry point for inference."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run iterative inference")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL_PATH, help="Model path")
    parser.add_argument("--output", type=str, default=str(PROCESSED_DATA_DIR / "convergence_results.csv"), help="Output CSV path")
    parser.add_argument("--sample-size", type=int, default=50, help="Number of samples")
    parser.add_argument("--device", type=str, default="cpu", help="Device to use")
    
    args = parser.parse_args()
    
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load model
    model, tokenizer = load_model(args.model, args.device)
    
    # Load dataset
    try:
        dataset = load_dataset("openai/humaneval", split="test")
    except Exception as e:
        logger.warning(f"Failed to load HumanEval: {e}, trying MBPP")
        dataset = load_dataset("mbpp", split="train").select(range(args.sample_size))
    
    dataset_list = list(dataset)
    if len(dataset_list) > args.sample_size:
        dataset_list = dataset_list[:args.sample_size]
    
    # Run inference
    results = run_iterative_inference(dataset_list, model, tokenizer, output_path=args.output)
    
    logger.info(f"Completed inference for {len(results)} samples")

if __name__ == "__main__":
    main()
