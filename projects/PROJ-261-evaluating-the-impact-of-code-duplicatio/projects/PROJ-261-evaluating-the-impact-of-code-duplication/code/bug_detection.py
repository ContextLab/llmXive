"""
Bug Detection Module - HumanEval pass@1 Accuracy Computation

This module loads the HumanEval dataset (50-problem subset),
generates code solutions using the quantized model, and computes
pass@1 accuracy metrics.

Outputs:
    data/processed/bug_detection_results.csv - Per-problem accuracy data
    data/processed/bug_detection_summary.csv - Aggregate accuracy statistics
"""

import logging
import json
import csv
import os
import sys
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Import shared configuration
from config import (
    get_random_seed,
    get_model_name,
    get_quantization_bits,
    get_checksum_algorithm,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/bug_detection.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
HUMAN_EVAL_DATASET = "openai_humaneval"
PROBLEM_COUNT = 50
OUTPUT_RESULTS_PATH = Path("data/processed/bug_detection_results.csv")
OUTPUT_SUMMARY_PATH = Path("data/processed/bug_detection_summary.csv")


def load_humaneval_dataset() -> List[Dict[str, Any]]:
    """
    Load the HumanEval dataset (50-problem subset).

    Returns:
        List of problem dictionaries with problem_id, prompt, test, entry_point
    """
    try:
        from datasets import load_dataset

        logger.info(f"Loading HumanEval dataset from {HUMAN_EVAL_DATASET}")
        dataset = load_dataset(HUMAN_EVAL_DATASET, split="test")

        # Convert to list of dicts and limit to 50 problems
        problems = []
        for idx, item in enumerate(dataset):
            if idx >= PROBLEM_COUNT:
                break
            problems.append({
                "problem_id": item["task_id"],
                "prompt": item["prompt"],
                "test": item["test"],
                "entry_point": item["entry_point"]
            })

        logger.info(f"Loaded {len(problems)} problems from HumanEval")
        return problems

    except ImportError as e:
        logger.error(f"Failed to import datasets library: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to load HumanEval dataset: {e}")
        raise


def prepare_prompt(prompt: str, entry_point: str) -> str:
    """
    Prepare the completion prompt for the model.

    Args:
        prompt: The function docstring and signature
        entry_point: The function name to complete

    Returns:
        Formatted prompt string for code generation
    """
    full_prompt = f"""def {entry_point}{prompt}"""
    return full_prompt


def generate_solution(prompt: str, model_name: str = None) -> Optional[str]:
    """
    Generate a code solution using the quantized model.

    Args:
        prompt: The prepared prompt string
        model_name: Optional model name override

    Returns:
        Generated code solution string or None on failure
    """
    if model_name is None:
        model_name = get_model_name()

    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        import torch

        logger.info(f"Loading model: {model_name}")

        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_name)

        # Load model in 8-bit quantization
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto",
            load_in_8bit=True,
            torch_dtype=torch.float16,
        )
        model.eval()

        # Tokenize input
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

        # Generate completion
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=256,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )

        # Decode output
        full_output = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract the generated code (after the prompt)
        generated_code = full_output[len(prompt):].strip()

        # Clean up the generated code
        generated_code = generated_code.split("\n\n")[0].strip()

        logger.info(f"Generated solution for prompt (length: {len(generated_code)})")
        return generated_code

    except Exception as e:
        logger.error(f"Failed to generate solution: {e}")
        return None


def extract_code_from_solution(solution: str, entry_point: str) -> str:
    """
    Extract the complete code block from a solution string.

    Args:
        solution: The raw generated solution
        entry_point: The function entry point name

    Returns:
        Cleaned code string
    """
    if solution is None:
        return ""

    # Remove any leading/trailing whitespace
    code = solution.strip()

    # Ensure the code starts with the function definition
    if not code.startswith(f"def {entry_point}"):
        # Try to find the function definition
        import re
        pattern = rf"def\s+{re.escape(entry_point)}\s*\([^)]*\):"
        match = re.search(pattern, code)
        if match:
            code = code[match.start():]

    return code


def run_tests(code: str, test_code: str, entry_point: str, timeout: int = 10) -> Tuple[bool, str]:
    """
    Run the test cases against the generated code.

    Args:
        code: The generated code solution
        test_code: The test cases
        entry_point: The function entry point name
        timeout: Timeout in seconds for test execution

    Returns:
        Tuple of (passed, error_message)
    """
    if not code or not test_code:
        return False, "Empty code or test"

    # Combine code and tests
    full_code = f"{code}\n{test_code}"

    # Create a temporary test script
    import tempfile
    import traceback

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(full_code)
        temp_path = f.name

    try:
        # Run the test
        result = subprocess.run(
            [sys.executable, temp_path],
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode == 0:
            return True, ""
        else:
            error_msg = result.stderr or result.stdout or "Test failed"
            return False, error_msg

    except subprocess.TimeoutExpired:
        return False, "Test execution timed out"
    except Exception as e:
        return False, str(e)
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)


def compute_pass1_accuracy(problems: List[Dict[str, Any]], model_name: str = None) -> List[Dict[str, Any]]:
    """
    Compute pass@1 accuracy for all problems.

    Args:
        problems: List of HumanEval problems
        model_name: Optional model name override

    Returns:
        List of result dictionaries with problem_id, passed, code, error
    """
    results = []
    passed_count = 0

    logger.info(f"Computing pass@1 accuracy for {len(problems)} problems")

    for idx, problem in enumerate(problems):
        problem_id = problem["problem_id"]
        prompt = problem["prompt"]
        test = problem["test"]
        entry_point = problem["entry_point"]

        logger.info(f"[{idx+1}/{len(problems)}] Processing {problem_id}")

        try:
            # Prepare and generate solution
            prepared_prompt = prepare_prompt(prompt, entry_point)
            solution = generate_solution(prepared_prompt, model_name)

            if solution is None:
                results.append({
                    "problem_id": problem_id,
                    "passed": False,
                    "code": "",
                    "error": "Generation failed"
                })
                continue

            # Extract and run tests
            extracted_code = extract_code_from_solution(solution, entry_point)
            passed, error_msg = run_tests(extracted_code, test, entry_point)

            if passed:
                passed_count += 1

            results.append({
                "problem_id": problem_id,
                "passed": passed,
                "code": extracted_code,
                "error": error_msg if not passed else ""
            })

        except Exception as e:
            logger.error(f"Error processing {problem_id}: {e}")
            results.append({
                "problem_id": problem_id,
                "passed": False,
                "code": "",
                "error": str(e)
            })

    logger.info(f"Pass@1 accuracy: {passed_count}/{len(problems)} = {passed_count/len(problems):.4f}")
    return results


def save_results(results: List[Dict[str, Any]], output_path: Path = None) -> Path:
    """
    Save pass@1 results to CSV.

    Args:
        results: List of result dictionaries
        output_path: Optional output path override

    Returns:
        Path to the saved file
    """
    if output_path is None:
        output_path = OUTPUT_RESULTS_PATH

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["problem_id", "passed", "code", "error"])
        writer.writeheader()
        for result in results:
            writer.writerow(result)

    logger.info(f"Saved results to {output_path}")
    return output_path


def save_summary(results: List[Dict[str, Any]], output_path: Path = None) -> Path:
    """
    Save summary statistics to CSV.

    Args:
        results: List of result dictionaries
        output_path: Optional output path override

    Returns:
        Path to the saved file
    """
    if output_path is None:
        output_path = OUTPUT_SUMMARY_PATH

    # Calculate summary statistics
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed
    accuracy = passed / total if total > 0 else 0

    summary = {
        "metric": "pass@1_accuracy",
        "total_problems": total,
        "passed_count": passed,
        "failed_count": failed,
        "accuracy": accuracy,
        "model_name": get_model_name(),
        "dataset": HUMAN_EVAL_DATASET,
        "problem_subset": PROBLEM_COUNT
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=summary.keys())
        writer.writeheader()
        writer.writerow(summary)

    logger.info(f"Saved summary to {output_path}")
    logger.info(f"Summary: {summary}")
    return output_path


def main():
    """
    Main entry point for bug detection pipeline.
    """
    logger.info("=" * 60)
    logger.info("Starting Bug Detection Pipeline")
    logger.info("=" * 60)

    try:
        # Load HumanEval dataset
        problems = load_humaneval_dataset()

        if not problems:
            logger.error("No problems loaded from HumanEval dataset")
            sys.exit(1)

        # Compute pass@1 accuracy
        results = compute_pass1_accuracy(problems)

        # Save results
        results_path = save_results(results)
        summary_path = save_summary(results)

        logger.info("=" * 60)
        logger.info("Bug Detection Pipeline Complete")
        logger.info(f"Results: {results_path}")
        logger.info(f"Summary: {summary_path}")
        logger.info("=" * 60)

        # Return paths for downstream use
        return {
            "results_path": str(results_path),
            "summary_path": str(summary_path)
        }

    except Exception as e:
        logger.error(f"Bug detection pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()