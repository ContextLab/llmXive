"""
Bug Detection Module - HumanEval Pass@1 Accuracy Computation

Implements T031: Load the 50-problem HumanEval subset and compute pass@1 accuracy
for the Salesforce/codegen-350M-mono model.

This module integrates with the llmXive automated science pipeline to evaluate
how code duplication density correlates with LLM bug detection accuracy.
"""
import logging
import json
import csv
import os
import sys
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import torch
import numpy as np
from datasets import load_dataset
from transformers import AutoTokenizer
from tqdm import tqdm

# Import from existing project modules
from model_metrics import load_model_8bit
from checksum_manifest import compute_file_checksum, record_artifact_checksums
from main import setup_logging


# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
HUMAN_EVAL_DATASET_NAME = "openai_humaneval"
MODEL_NAME = "Salesforce/codegen-350M-mono"
OUTPUT_FILE = PROCESSED_DIR / "bug_detection_results.csv"
LOG_FILE = DATA_DIR / "bug_detection.log"
BATCH_SIZE = 1  # pass@1 requires 1 sample per problem
MAX_NEW_TOKENS = 256
RANDOM_SEED = 42


def load_humaneval_dataset() -> List[Dict[str, Any]]:
    """
    Load the HumanEval dataset from HuggingFace.

    Returns:
        List of problem dictionaries with 'task_id', 'prompt', 'canonical_solution',
        'test', and 'entry_point' keys.

    Note:
        Uses streaming mode for efficient loading of the 50-problem subset.
    """
    logging.info(f"Loading HumanEval dataset: {HUMAN_EVAL_DATASET_NAME}")

    try:
        dataset = load_dataset(
            HUMAN_EVAL_DATASET_NAME,
            split="test",
            trust_remote_code=True
        )

        # Convert to list of dicts for easier processing
        problems = list(dataset)
        logging.info(f"Loaded {len(problems)} HumanEval problems")

        return problems

    except Exception as e:
        logging.error(f"Failed to load HumanEval dataset: {e}")
        raise


def prepare_prompt(problem: Dict[str, Any]) -> str:
    """
    Prepare the prompt for code generation from a HumanEval problem.

    Args:
        problem: Dictionary containing 'prompt' and other problem metadata.

    Returns:
        Formatted prompt string for the model.
    """
    # HumanEval prompts are already in the correct format for codegen models
    prompt = problem.get("prompt", "")

    # Ensure prompt ends with proper continuation marker
    if not prompt.endswith("\n"):
        prompt += "\n"

    return prompt


def generate_solution(
    model,
    tokenizer,
    prompt: str,
    max_new_tokens: int = MAX_NEW_TOKENS
) -> str:
    """
    Generate a code solution using the loaded model.

    Args:
        model: The loaded transformer model.
        tokenizer: The model tokenizer.
        prompt: The input prompt string.
        max_new_tokens: Maximum number of tokens to generate.

    Returns:
        Generated code solution as a string.
    """
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True)

    # Move inputs to device
    device = next(model.parameters()).device
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,  # Deterministic for pass@1
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id
        )

    # Decode and extract solution
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Extract just the generated portion (after the prompt)
    solution = generated_text[len(prompt):]

    return solution


def extract_code_from_solution(solution: str) -> str:
    """
    Extract clean code from the generated solution.

    Args:
        solution: Raw generated text that may include prompt repetition.

    Returns:
        Cleaned code block.
    """
    # Remove any repeated prompt at the beginning
    lines = solution.split("\n")
    code_lines = []
    in_code = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("def ") or stripped.startswith("class "):
            in_code = True
        if in_code:
            code_lines.append(line)

    if not code_lines:
        # Fallback: return original solution
        return solution

    return "\n".join(code_lines)


def run_tests(solution: str, test_code: str, entry_point: str) -> bool:
    """
    Run unit tests on the generated solution.

    Args:
        solution: The generated code solution.
        test_code: The test code from HumanEval.
        entry_point: The function name to test.

    Returns:
        True if all tests pass, False otherwise.
    """
    # Combine solution and tests
    full_code = f"{solution}\n{test_code}"

    # Create temporary file for execution
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(full_code)
        temp_path = f.name

    try:
        # Run tests with timeout
        result = subprocess.run(
            [sys.executable, temp_path],
            capture_output=True,
            text=True,
            timeout=10,
            env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT)}
        )

        # Check if tests passed (exit code 0)
        return result.returncode == 0

    except subprocess.TimeoutExpired:
        logging.warning(f"Test execution timed out for {entry_point}")
        return False
    except Exception as e:
        logging.warning(f"Test execution failed for {entry_point}: {e}")
        return False
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def compute_pass1_accuracy(
    problems: List[Dict[str, Any]],
    model,
    tokenizer,
    num_problems: int = 50
) -> Dict[str, Any]:
    """
    Compute pass@1 accuracy on the HumanEval benchmark.

    Args:
        problems: List of HumanEval problem dictionaries.
        model: The loaded transformer model.
        tokenizer: The model tokenizer.
        num_problems: Number of problems to evaluate (default 50).

    Returns:
        Dictionary with accuracy metrics and per-problem results.
    """
    results = []
    passed = 0

    logging.info(f"Evaluating pass@1 accuracy on {min(num_problems, len(problems))} problems")

    for idx, problem in enumerate(tqdm(problems[:num_problems], desc="Evaluating")):
        task_id = problem.get("task_id", f"task_{idx}")
        prompt = prepare_prompt(problem)
        test_code = problem.get("test", "")
        entry_point = problem.get("entry_point", "")
        canonical_solution = problem.get("canonical_solution", "")

        try:
            # Generate solution
            solution = generate_solution(model, tokenizer, prompt)
            cleaned_solution = extract_code_from_solution(solution)

            # Run tests
            test_passed = run_tests(cleaned_solution, test_code, entry_point)

            if test_passed:
                passed += 1

            results.append({
                "task_id": task_id,
                "prompt_length": len(prompt),
                "solution_length": len(cleaned_solution),
                "test_passed": test_passed,
                "entry_point": entry_point,
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            logging.error(f"Error processing {task_id}: {e}")
            results.append({
                "task_id": task_id,
                "prompt_length": len(prompt),
                "solution_length": 0,
                "test_passed": False,
                "entry_point": entry_point,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

    # Calculate accuracy
    total = len(results)
    accuracy = (passed / total) * 100 if total > 0 else 0.0

    return {
        "total_problems": total,
        "passed": passed,
        "accuracy_percent": accuracy,
        "results": results,
        "timestamp": datetime.now().isoformat()
    }


def save_results(results: Dict[str, Any], output_path: Path) -> None:
    """
    Save bug detection results to CSV file.

    Args:
        results: Dictionary containing accuracy metrics and per-problem results.
        output_path: Path to save the CSV file.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write per-problem results to CSV
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "task_id", "prompt_length", "solution_length", "test_passed",
            "entry_point", "accuracy_percent", "total_problems", "passed",
            "timestamp"
        ])
        writer.writeheader()

        for result in results["results"]:
            writer.writerow({
                "task_id": result["task_id"],
                "prompt_length": result["prompt_length"],
                "solution_length": result["solution_length"],
                "test_passed": result["test_passed"],
                "entry_point": result["entry_point"],
                "accuracy_percent": results["accuracy_percent"],
                "total_problems": results["total_problems"],
                "passed": results["passed"],
                "timestamp": result["timestamp"]
            })

    logging.info(f"Saved results to {output_path}")


def save_summary(results: Dict[str, Any], summary_path: Path) -> None:
    """
    Save summary metrics to JSON file.

    Args:
        results: Dictionary containing accuracy metrics.
        summary_path: Path to save the JSON summary file.
    """
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    summary = {
        "total_problems": results["total_problems"],
        "passed": results["passed"],
        "accuracy_percent": results["accuracy_percent"],
        "timestamp": results["timestamp"],
        "model": MODEL_NAME,
        "benchmark": HUMAN_EVAL_DATASET_NAME
    }

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    logging.info(f"Saved summary to {summary_path}")


def main() -> Dict[str, Any]:
    """
    Main entry point for bug detection computation.

    Returns:
        Dictionary with accuracy metrics and per-problem results.
    """
    # Setup logging
    logger = setup_logging(LOG_FILE)

    logging.info("=" * 60)
    logging.info("Starting Bug Detection - HumanEval Pass@1 Computation")
    logging.info("=" * 60)

    try:
        # Load dataset
        problems = load_humaneval_dataset()

        # Load model in 8-bit quantization
        logging.info(f"Loading model: {MODEL_NAME} (8-bit)")
        model, tokenizer = load_model_8bit(MODEL_NAME)

        # Compute pass@1 accuracy
        results = compute_pass1_accuracy(problems, model, tokenizer)

        # Save results
        save_results(results, OUTPUT_FILE)

        # Save summary
        summary_path = PROCESSED_DIR / "bug_detection_summary.json"
        save_summary(results, summary_path)

        # Compute checksums for output files
        checksums = {
            "bug_detection_results.csv": compute_file_checksum(OUTPUT_FILE),
            "bug_detection_summary.json": compute_file_checksum(summary_path)
        }

        # Record checksums in manifest
        record_artifact_checksums(checksums, "bug_detection")

        logging.info(f"Bug detection complete. Accuracy: {results['accuracy_percent']:.2f}%")
        logging.info(f"Results saved to: {OUTPUT_FILE}")

        return results

    except Exception as e:
        logging.error(f"Bug detection failed: {e}")
        raise


if __name__ == "__main__":
    results = main()
    print(f"\nPass@1 Accuracy: {results['accuracy_percent']:.2f}%")
    print(f"Problems Passed: {results['passed']}/{results['total_problems']}")
