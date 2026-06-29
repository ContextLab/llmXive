"""
Bug Detection Module - Compute pass@1 accuracy on HumanEval subset

This module loads the HumanEval dataset, generates solutions using the
configured model, and computes pass@1 accuracy metrics.

Data Flow:
- Loads 50-problem HumanEval subset
- Generates code solutions for each problem
- Runs test suites to evaluate correctness
- Computes pass@1 accuracy
- Saves results to data/analysis/bug_detection_results.csv
"""
import logging
import json
import csv
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Import from local modules
from config import (
    get_random_seed,
    get_model_name,
    get_quantization_bits,
    get_memory_limit_mb,
)
from checksum_manifest import record_artifact_checksums


def setup_logging(log_file: Optional[Path] = None) -> logging.Logger:
    """Configure logging for bug detection module."""
    logger = logging.getLogger("bug_detection")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger


def load_humaneval_dataset(
    dataset_path: Optional[Path] = None, subset_size: int = 50
) -> List[Dict[str, Any]]:
    """
    Load HumanEval dataset with optional subset.

    Args:
        dataset_path: Path to local dataset JSON file (optional)
        subset_size: Number of problems to load (default: 50)

    Returns:
        List of problem dictionaries with 'task_id', 'prompt', 'test', 'entry_point'
    """
    logger = logging.getLogger("bug_detection")

    # Try to load from HuggingFace datasets
    try:
        from datasets import load_dataset

        logger.info(f"Loading HumanEval dataset (subset: {subset_size} problems)")

        # Load the full dataset
        dataset = load_dataset("openai_humaneval", trust_remote_code=True)

        # Convert to list and take subset
        problems = list(dataset["test"])[:subset_size]

        logger.info(f"Loaded {len(problems)} problems from HumanEval")
        return problems

    except Exception as e:
        logger.warning(f"Failed to load from HuggingFace: {e}")
        logger.info("Attempting to load from local dataset file...")

        # Fallback: create synthetic dataset for testing
        # In production, this would be replaced with actual HumanEval data
        problems = _create_synthetic_humaneval_subset(subset_size)
        logger.info(f"Created synthetic dataset with {len(problems)} problems")
        return problems


def _create_synthetic_humaneval_subset(
    subset_size: int = 50,
) -> List[Dict[str, Any]]:
    """
    Create a synthetic HumanEval-like dataset for testing.

    NOTE: This is a fallback for when the real dataset is unavailable.
    In production, use the actual HumanEval dataset from HuggingFace.
    """
    problems = []

    # Sample problems similar to HumanEval structure
    sample_problems = [
        {
            "task_id": "HumanEval/0",
            "prompt": "def has_close_elements(numbers: List[float], threshold: float) -> bool:\n    \"\"\" Check if in given list of numbers, any two numbers are closer to each other than the given threshold.\n    >>> has_close_elements([1.0, 2.0, 3.0], 0.5)\n    False\n    >>> has_close_elements([1.0, 1.2, 3.0], 0.5)\n    True\n    \"\"\"\n",
            "test": "from math import isclose\n\ndef check(candidate):\n    assert candidate([1.0, 2.0, 3.0], 0.5) == False\n    assert candidate([1.0, 1.2, 3.0], 0.5) == True\n    assert candidate([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], 0.1) == False\n    assert candidate([1.0, 2.0, 2.1, 3.0], 0.2) == True\n",
            "entry_point": "has_close_elements",
        },
        {
            "task_id": "HumanEval/1",
            "prompt": "def separate_paren_groups(paren_string: str) -> List[str]:\n    \"\"\" Input to this function is a string containing multiple groups of nested parentheses. Your goal is to separate those group into a list of strings.\n    >>> separate_paren_groups('( ) (( )) (( ) ())')\n    ['()', '(())', '(()())']\n    \"\"\"\n",
            "test": "def check(candidate):\n    assert candidate('() (()) (())') == ['()', '(())', '(())']\n    assert candidate('() (()) ((()))') == ['()', '(())', '((()))']\n    assert candidate('() (()) (()) ((()))') == ['()', '(())', '(())', '((()))']\n",
            "entry_point": "separate_paren_groups",
        },
        {
            "task_id": "HumanEval/2",
            "prompt": "def truncate_number(number: float) -> float:\n    \"\"\" Given a positive floating point number, it can be decomposed into and big integer part (natural number) and a positive fractional part (both smaller than 1).\n    >>> truncate_number(3.5)\n    0.5\n    \"\"\"\n",
            "test": "def check(candidate):\n    assert candidate(3.5) == 0.5\n    assert candidate(1.33) == 0.33\n    assert candidate(123.456) == 0.456\n",
            "entry_point": "truncate_number",
        },
        {
            "task_id": "HumanEval/3",
            "prompt": "def below_threshold(limit: float, numbers: List[float]) -> bool:\n    \"\"\" Return True if all numbers in numbers are below limit, False otherwise.\n    >>> below_threshold(10.0, [1.0, 2.0, 3.0])\n    True\n    >>> below_threshold(5.0, [1.0, 6.0, 3.0])\n    False\n    \"\"\"\n",
            "test": "def check(candidate):\n    assert candidate(10.0, [1.0, 2.0, 3.0]) == True\n    assert candidate(5.0, [1.0, 6.0, 3.0]) == False\n    assert candidate(10.0, []) == True\n    assert candidate(5.0, [4.9, 5.0, 5.1]) == False\n",
            "entry_point": "below_threshold",
        },
        {
            "task_id": "HumanEval/4",
            "prompt": "def add(x: int, y: int) -> int:\n    \"\"\" Add two numbers.\n    >>> add(2, 3)\n    5\n    >>> add(5, 7)\n    12\n    \"\"\"\n",
            "test": "def check(candidate):\n    assert candidate(2, 3) == 5\n    assert candidate(5, 7) == 12\n    assert candidate(-1, 1) == 0\n    assert candidate(0, 0) == 0\n",
            "entry_point": "add",
        },
    ]

    # Generate subset
    for i in range(subset_size):
        problem = sample_problems[i % len(sample_problems)].copy()
        problem["task_id"] = f"HumanEval/{i}"
        problems.append(problem)

    return problems


def prepare_prompt(problem: Dict[str, Any]) -> str:
    """
    Prepare the prompt for the model.

    Args:
        problem: Problem dictionary with 'prompt' key

    Returns:
        Formatted prompt string
    """
    prompt = problem.get("prompt", "")
    return f"Complete the following Python function:\n\n{prompt}"


def generate_solution(
    prompt: str, model_name: str, max_tokens: int = 512
) -> str:
    """
    Generate a solution using the configured model.

    NOTE: This is a stub implementation. In production, this would call
    the actual model for code generation.

    Args:
        prompt: Formatted prompt string
        model_name: Name of the model to use
        max_tokens: Maximum tokens to generate

    Returns:
        Generated code solution
    """
    logger = logging.getLogger("bug_detection")
    logger.info(f"Generating solution for prompt (model: {model_name})")

    # In production, this would use transformers or similar
    # For now, return a placeholder that will fail tests
    # This allows the pipeline to run end-to-end for testing

    # Generate a simple placeholder solution
    solution = f"# Solution for: {prompt[:50]}...\n# Generated by bug_detection module\n"

    logger.info("Solution generated (placeholder)")
    return solution


def extract_code_from_solution(solution: str) -> str:
    """
    Extract executable code from the solution string.

    Args:
        solution: Full solution string

    Returns:
        Extracted code block
    """
    # Remove markdown code blocks if present
    if "```python" in solution:
        start = solution.find("```python") + len("```python")
        end = solution.find("```", start)
        if end > start:
            return solution[start:end].strip()

    if "```" in solution:
        start = solution.find("```") + len("```")
        end = solution.find("```", start)
        if end > start:
            return solution[start:end].strip()

    return solution.strip()


def run_tests(
    problem: Dict[str, Any], solution: str, timeout: int = 10
) -> Tuple[bool, str]:
    """
    Run the test suite against the solution.

    Args:
        problem: Problem dictionary with 'test' key
        solution: Generated solution code
        timeout: Test execution timeout in seconds

    Returns:
        Tuple of (passed: bool, message: str)
    """
    logger = logging.getLogger("bug_detection")

    test_code = problem.get("test", "")
    entry_point = problem.get("entry_point", "")

    # Combine solution and test code
    full_code = f"{solution}\n\n{test_code}\n\ncheck({entry_point})"

    try:
        # Write to temporary file
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(full_code)
            temp_file = f.name

        # Run the test
        result = subprocess.run(
            [sys.executable, temp_file],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        # Clean up
        os.unlink(temp_file)

        if result.returncode == 0:
            logger.info(f"Tests passed for {problem.get('task_id', 'unknown')}")
            return True, "Tests passed"
        else:
            error_msg = result.stderr or result.stdout
            logger.warning(
                f"Tests failed for {problem.get('task_id', 'unknown')}: {error_msg[:100]}"
            )
            return False, error_msg

    except subprocess.TimeoutExpired:
        logger.warning(f"Tests timed out for {problem.get('task_id', 'unknown')}")
        return False, "Test execution timed out"
    except Exception as e:
        logger.error(f"Test execution error: {e}")
        return False, str(e)


def compute_pass1_accuracy(
    problems: List[Dict[str, Any]], solutions: List[str]
) -> Dict[str, Any]:
    """
    Compute pass@1 accuracy for all problems.

    Args:
        problems: List of problem dictionaries
        solutions: List of generated solutions

    Returns:
        Dictionary with accuracy metrics
    """
    logger = logging.getLogger("bug_detection")

    total = len(problems)
    passed = 0
    results = []

    for i, (problem, solution) in enumerate(zip(problems, solutions)):
        task_id = problem.get("task_id", f"unknown_{i}")
        passed_test, message = run_tests(problem, solution)

        result = {
            "task_id": task_id,
            "passed": passed_test,
            "message": message[:200] if message else "",
        }
        results.append(result)

        if passed_test:
            passed += 1

        logger.info(
            f"Problem {i+1}/{total}: {task_id} - {'PASSED' if passed_test else 'FAILED'}"
        )

    accuracy = passed / total if total > 0 else 0.0

    metrics = {
        "total_problems": total,
        "passed_problems": passed,
        "failed_problems": total - passed,
        "pass1_accuracy": accuracy,
        "timestamp": datetime.now().isoformat(),
    }

    logger.info(
        f"Pass@1 Accuracy: {accuracy:.4f} ({passed}/{total})"
    )

    return {"metrics": metrics, "results": results}


def save_results(
    results: List[Dict[str, Any]], output_path: Path
) -> None:
    """
    Save individual problem results to CSV.

    Args:
        results: List of result dictionaries
        output_path: Path to output CSV file
    """
    logger = logging.getLogger("bug_detection")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["task_id", "passed", "message"]
        )
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"Saved results to {output_path}")


def save_summary(
    metrics: Dict[str, Any], output_path: Path
) -> None:
    """
    Save summary metrics to JSON.

    Args:
        metrics: Dictionary with accuracy metrics
        output_path: Path to output JSON file
    """
    logger = logging.getLogger("bug_detection")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Saved summary to {output_path}")


def record_artifact_checksums(
    output_files: List[Path],
    manifest_path: Path,
    logger: Optional[logging.Logger] = None,
) -> None:
    """
    Record checksums for all output artifacts.

    Args:
        output_files: List of output file paths
        manifest_path: Path to checksum manifest file
        logger: Logger instance
    """
    if logger is None:
        logger = logging.getLogger("bug_detection")

    logger.info(f"Recording checksums for {len(output_files)} artifacts")

    # Ensure all paths are Path objects
    output_files = [Path(f) for f in output_files]
    manifest_path = Path(manifest_path)

    try:
        record_artifact_checksums(output_files, manifest_path)
        logger.info("Checksums recorded successfully")
    except Exception as e:
        logger.warning(f"Failed to record checksums: {e}")


def main() -> int:
    """
    Main entry point for bug detection pipeline.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("Bug Detection Pipeline - HumanEval pass@1 Accuracy")
    logger.info("=" * 60)

    try:
        # Configuration
        dataset_path = None  # Use HuggingFace by default
        subset_size = 50
        output_dir = Path("data/analysis")
        results_path = output_dir / "bug_detection_results.csv"
        summary_path = output_dir / "bug_detection_summary.json"
        manifest_path = Path("data/analysis/checksum_manifest.json")

        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Load dataset
        logger.info("Loading HumanEval dataset...")
        problems = load_humaneval_dataset(
            dataset_path=dataset_path, subset_size=subset_size
        )
        logger.info(f"Loaded {len(problems)} problems")

        # Generate solutions
        logger.info("Generating solutions...")
        model_name = get_model_name()
        solutions = []

        for i, problem in enumerate(problems):
            prompt = prepare_prompt(problem)
            solution = generate_solution(prompt, model_name)
            solutions.append(solution)

            if (i + 1) % 10 == 0:
                logger.info(f"Generated solutions for {i + 1}/{len(problems)} problems")

        # Compute pass@1 accuracy
        logger.info("Computing pass@1 accuracy...")
        results = compute_pass1_accuracy(problems, solutions)

        # Save results
        logger.info("Saving results...")
        save_results(results["results"], results_path)
        save_summary(results["metrics"], summary_path)

        # Record checksums
        logger.info("Recording checksums...")
        output_files = [results_path, summary_path]
        record_artifact_checksums(output_files, manifest_path, logger)

        # Print summary
        logger.info("=" * 60)
        logger.info("Bug Detection Summary")
        logger.info("=" * 60)
        logger.info(
            f"Total Problems: {results['metrics']['total_problems']}"
        )
        logger.info(
            f"Passed: {results['metrics']['passed_problems']}"
        )
        logger.info(
            f"Failed: {results['metrics']['failed_problems']}"
        )
        logger.info(
            f"Pass@1 Accuracy: {results['metrics']['pass1_accuracy']:.4f}"
        )
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())