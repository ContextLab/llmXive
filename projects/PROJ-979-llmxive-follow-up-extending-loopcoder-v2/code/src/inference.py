import os
import sys
import json
import logging
import tempfile
import shutil
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from src.models import InputProblem, ConvergenceStatus, ConvergenceTrajectory
from src.utils import calculate_flops, get_model_param_count

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Model configuration (relying on T008 for env setup)
MODEL_PATH = os.getenv("MODEL_PATH", "codellama/CodeLlama-1.3b-Instruct-hf")
DEVICE = os.getenv("DEVICE", "cpu")
MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "256"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
TOP_P = float(os.getenv("TOP_P", "0.95"))

# Docker sandbox configuration (relying on T009)
DOCKER_SANDBOX_ENABLED = os.getenv("DOCKER_SANDBOX_ENABLED", "true").lower() == "true"
DOCKER_IMAGE = os.getenv("DOCKER_IMAGE", "llmxive-sandbox:latest")

def load_model():
    """
    Loads the CodeLlama model for inference.
    Uses CPU for validation (1.3b) or GPU for full analysis.
    """
    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM

        logger.info(f"Loading model from {MODEL_PATH} on {DEVICE}...")
        tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
        
        # Determine dtype based on device
        if DEVICE == "cuda" and torch.cuda.is_available():
            dtype = torch.float16
            logger.info("Using float16 on GPU")
        else:
            dtype = torch.float32
            logger.info("Using float32 on CPU")

        model = AutoModelForCausalLM.from_pretrained(
            MODEL_PATH,
            torch_dtype=dtype,
            device_map="auto" if DEVICE == "cuda" else None,
            trust_remote_code=True
        )
        
        if DEVICE == "cpu":
            model = model.to("cpu")
        
        logger.info("Model loaded successfully.")
        return model, tokenizer
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def generate_solution(model, tokenizer, problem: InputProblem, k: int) -> str:
    """
    Generates a code solution for a given problem using the model.
    
    Args:
        model: The loaded transformer model.
        tokenizer: The loaded tokenizer.
        problem: The InputProblem containing prompt and test cases.
        k: The current iteration count (1, 2, or 3).
        
    Returns:
        The generated code string.
    """
    # Construct prompt based on problem description
    # HumanEval format: prompt + problem statement + "def "
    prompt = problem.prompt + "\n"
    
    # Add refinement context if k > 1 (conceptually, though we don't read previous output here)
    # In a real iterative loop, we might append "Previous attempt failed because..."
    # But for this task, we strictly use the input problem as per Principle VI.
    
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
    
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Extract code block if present (heuristic: look for ```python ... ```)
    if "```python" in generated_text:
        start = generated_text.find("```python") + len("```python")
        end = generated_text.find("```", start)
        code = generated_text[start:end].strip()
    elif "```" in generated_text:
        start = generated_text.find("```") + len("```")
        end = generated_text.find("```", start)
        code = generated_text[start:end].strip()
    else:
        # Fallback: assume the whole text is code or just the last part
        code = generated_text.strip()
        
    return code

def load_input_problems(filepath: str) -> List[InputProblem]:
    """
    Loads input problems from a JSON file.
    Expects a list of dictionaries with 'prompt', 'test', and 'task_id'.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Input problems file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    problems = []
    for item in data:
        # Handle HumanEval/MBPP structure
        prompt = item.get("prompt", item.get("text", ""))
        test_code = item.get("test", "")
        task_id = item.get("task_id", str(item.get("index", 0)))
        
        problems.append(InputProblem(
            task_id=task_id,
            prompt=prompt,
            test=test_code,
            difficulty=item.get("difficulty", "unknown")
        ))
    
    logger.info(f"Loaded {len(problems)} input problems from {filepath}")
    return problems

def execute_code_in_sandbox(code: str, test_code: str, task_id: str) -> Tuple[bool, str]:
    """
    Executes the generated code against the test cases using the Docker sandbox.
    
    Args:
        code: The generated solution code.
        test_code: The test cases to run against.
        task_id: Identifier for logging.
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    if not DOCKER_SANDBOX_ENABLED:
        # Fallback to local execution (DANGEROUS, only for trusted dev env)
        logger.warning("Docker sandbox disabled. Running locally. WARNING: Security risk.")
        return _execute_locally(code, test_code)

    try:
        import subprocess
        import uuid

        # Create a temporary directory for the sandbox run
        run_id = str(uuid.uuid4())
        work_dir = Path(tempfile.mkdtemp(prefix=f"llmxive_run_{run_id}_"))
        
        # Write the solution
        solution_file = work_dir / "solution.py"
        with open(solution_file, 'w') as f:
            f.write(code)
        
        # Write the test harness
        # We need to wrap the test code to capture the result
        # HumanEval tests usually call the function and assert
        test_file = work_dir / "test.py"
        with open(test_file, 'w') as f:
            f.write(code + "\n\n")
            f.write(test_code)
            f.write("\n\n# Run the tests\n")
            f.write("if __name__ == '__main__':\n")
            f.write("    import sys\n")
            f.write("    try:\n")
            f.write("        # We assume the test code defines a main function or runs assertions\n")
            f.write("        # For HumanEval, the test code usually calls the function directly\n")
            f.write("        exec(open('solution.py').read())\n") # Re-import to be safe
            f.write("        # Execute the test logic\n")
            f.write(f"        exec(compile(open('{test_file.name}').read(), '{test_file.name}', 'exec'))\n")
            f.write("        print('PASSED')\n")
            f.write("    except Exception as e:\n")
            f.write("        print(f'FAILED: {{e}}')\n")
            f.write("        sys.exit(1)\n")

        # Prepare Docker command
        # Assuming the image has python and necessary deps
        cmd = [
            "docker", "run", "--rm",
            "-v", f"{work_dir}:/app",
            "-w", "/app",
            DOCKER_IMAGE,
            "python", "test.py"
        ]

        logger.debug(f"Running sandbox command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30 # 30s timeout per execution
        )
        
        # Cleanup
        shutil.rmtree(work_dir, ignore_errors=True)
        
        output = result.stdout + result.stderr
        
        if result.returncode == 0 and "PASSED" in output:
            return True, "Tests passed"
        else:
            return False, output.strip()
            
    except subprocess.TimeoutExpired:
        return False, "Execution timed out"
    except FileNotFoundError:
        raise RuntimeError("Docker not found or sandbox image missing. Ensure T009 is complete.")
    except Exception as e:
        logger.error(f"Sandbox execution error for {task_id}: {e}")
        return False, str(e)

def _execute_locally(code: str, test_code: str) -> Tuple[bool, str]:
    """
    Local execution fallback (unsafe for untrusted code).
    """
    try:
        # Create a restricted namespace
        namespace = {}
        
        # Execute the solution
        exec(code, namespace)
        
        # Execute the test code
        # This is risky if test_code contains malicious code, but we assume it's from HumanEval/MBPP
        exec(test_code, namespace)
        
        return True, "Local execution passed"
    except Exception as e:
        return False, str(e)

def save_convergence_results(results: List[ConvergenceTrajectory], filepath: str):
    """
    Saves convergence results to a JSON file.
    """
    output_dir = Path(filepath).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    data = [
        {
            "task_id": r.task_id,
            "converged_at": r.converged_at,
            "trajectory": [
                {"k": t.k, "passed": t.passed, "error": t.error}
                for t in r.trajectory
            ],
            "total_k": r.total_k
        }
        for r in results
    ]
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved convergence results to {filepath}")

def save_non_convergence_log(events: List[Dict], filepath: str):
    """
    Saves logs of non-convergence events (FR-007).
    """
    output_dir = Path(filepath).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w') as f:
        json.dump(events, f, indent=2)
    
    logger.info(f"Saved non-convergence log to {filepath}")

def run_iterative_inference(
    problems: List[InputProblem],
    model,
    tokenizer,
    k_values: List[int],
    output_path: str,
    non_convergence_log_path: str
) -> List[ConvergenceTrajectory]:
    """
    Runs iterative refinement execution for k in {1, 2, 3}.
    Detects the first correct solution by executing code in the Docker sandbox.
    
    Args:
        problems: List of InputProblem instances.
        model: Loaded model.
        tokenizer: Loaded tokenizer.
        k_values: List of k values to try (e.g., [1, 2, 3]).
        output_path: Path to save convergence_results.csv (or json).
        non_convergence_log_path: Path to save non-convergence events.
        
    Returns:
        List of ConvergenceTrajectory objects.
    """
    results = []
    non_convergence_events = []
    
    logger.info(f"Starting iterative inference for {len(problems)} problems with k={k_values}")
    
    for idx, problem in enumerate(problems):
        logger.info(f"Processing [{idx+1}/{len(problems)}] {problem.task_id}")
        
        trajectory = []
        converged_at = None
        
        for k in k_values:
            # Generate solution
            code = generate_solution(model, tokenizer, problem, k)
            
            # Execute and validate
            passed, error_msg = execute_code_in_sandbox(code, problem.test, problem.task_id)
            
            trajectory.append({
                "k": k,
                "passed": passed,
                "error": error_msg if not passed else None
            })
            
            if passed:
                converged_at = k
                break
        
        # Create trajectory object
        traj_obj = ConvergenceTrajectory(
            task_id=problem.task_id,
            converged_at=converged_at,
            trajectory=trajectory,
            total_k=converged_at if converged_at else max(k_values)
        )
        results.append(traj_obj)
        
        # Log non-convergence if it didn't converge within k_values
        if converged_at is None:
            non_convergence_events.append({
                "task_id": problem.task_id,
                "k_tried": k_values,
                "last_error": trajectory[-1].get("error", "Unknown error"),
                "reason": "Max iterations reached without passing tests"
            })
            logger.warning(f"Task {problem.task_id} did not converge in {k_values} iterations.")
        
        # Optional: Save progress periodically to avoid data loss
        if (idx + 1) % 10 == 0:
            save_convergence_results(results, output_path)
            save_non_convergence_log(non_convergence_events, non_convergence_log_path)
    
    # Final save
    save_convergence_results(results, output_path)
    save_non_convergence_log(non_convergence_events, non_convergence_log_path)
    
    logger.info(f"Iterative inference complete. Results saved to {output_path}")
    return results

def main():
    """
    Main entry point for T013.
    Expected to be run after T004 (data loading) and T012 (entropy extraction).
    """
    # Configuration
    input_path = os.getenv("INPUT_PROBLEMS_PATH", "data/processed/processed_problems.json")
    output_path = os.getenv("CONVERGENCE_OUTPUT_PATH", "data/processed/convergence_results.json")
    log_path = os.getenv("NON_CONVERGENCE_LOG_PATH", "data/processed/non_convergence_log.json")
    k_values = [1, 2, 3]
    
    # Load model
    model, tokenizer = load_model()
    
    # Load problems
    # Note: This MUST NOT read entropy_results.csv. It reads raw/processed problems only.
    try:
        problems = load_input_problems(input_path)
    except FileNotFoundError as e:
        logger.error(f"Input problems not found. Ensure T004 is complete and data is at {input_path}")
        raise
    
    # Run inference
    run_iterative_inference(
        problems=problems,
        model=model,
        tokenizer=tokenizer,
        k_values=k_values,
        output_path=output_path,
        non_convergence_log_path=log_path
    )

if __name__ == "__main__":
    main()