"""
LLM Invocation Wrapper for Multi-LCB.

This module implements the runner that invokes LLMs to generate code solutions.
It supports temperature, seed, ten independent runs per task, and token-usage logging.
"""

import json
import logging
import os
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import configuration from project
from config import get_config, get_models, get_temperatures, get_seed, get_logs_path
from data.preprocess import load_and_count_tasks

# Try to import a real LLM client. We support OpenAI as the primary source.
# If the environment variable OPENAI_API_KEY is not set, we raise an error at runtime
# rather than fabricating data.
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# Setup logging
def setup_logging(log_file: Optional[Path] = None) -> logging.Logger:
    logger = logging.getLogger("llm_runner")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)

        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            logger.addHandler(file_handler)

    return logger

@dataclass
class RunResult:
    """Result of a single LLM run."""
    task_id: str
    model_id: str
    temperature: float
    seed: int
    run_index: int
    generated_code: str
    success: bool
    error_message: Optional[str]
    tokens_used: int
    duration_seconds: float
    timestamp: str

def _get_client() -> Any:
    """Initialize the OpenAI client using environment variables."""
    if not HAS_OPENAI:
        raise RuntimeError(
            "OpenAI library not installed. Install with: pip install openai"
        )
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY environment variable is not set. "
            "Please set it to a valid API key."
        )
    return OpenAI(api_key=api_key)

def _build_prompt(task: Dict[str, Any]) -> str:
    """
    Build the prompt for the LLM based on the task definition.
    We expect the task to have 'problem_statement' and optionally 'language'.
    """
    prompt = task.get("problem_statement", "")
    language = task.get("language", "python")
    if language:
        prompt = f"Please solve the following problem in {language}:\n\n{prompt}\n\nProvide only the code solution."
    else:
        prompt = f"Please solve the following problem:\n\n{prompt}\n\nProvide only the code solution."
    return prompt

def run_single_inference(
    client: Any,
    model_id: str,
    temperature: float,
    seed: int,
    task: Dict[str, Any],
    run_index: int,
    logger: logging.Logger
) -> RunResult:
    """
    Execute a single LLM inference for a given task.
    """
    start_time = time.time()
    prompt = _build_prompt(task)
    task_id = task.get("task_id", "unknown")

    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": "You are a code generation assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            seed=seed,
            max_tokens=2048,
            stop=["\n\n```", "```"]
        )

        generated_code = response.choices[0].message.content
        tokens_used = response.usage.total_tokens
        success = True
        error_message = None

    except Exception as e:
        generated_code = ""
        success = False
        error_message = str(e)
        tokens_used = 0
        logger.warning(f"Run failed for task {task_id}: {error_message}")

    duration = time.time() - start_time
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    return RunResult(
        task_id=task_id,
        model_id=model_id,
        temperature=temperature,
        seed=seed,
        run_index=run_index,
        generated_code=generated_code,
        success=success,
        error_message=error_message,
        tokens_used=tokens_used,
        duration_seconds=duration,
        timestamp=timestamp
    )

def run_task_batch(
    tasks: List[Dict[str, Any]],
    model_ids: List[str],
    temperatures: List[float],
    num_runs: int = 10,
    seed: Optional[int] = None,
    output_path: Optional[Path] = None,
    log_path: Optional[Path] = None
) -> List[RunResult]:
    """
    Run the LLM on a batch of tasks across multiple models and temperatures.
    Each task is run `num_runs` times independently.
    """
    if not HAS_OPENAI:
        raise RuntimeError(
            "Cannot run inference: OpenAI library not installed. "
            "Install with: pip install openai"
        )

    config = get_config()
    if seed is None:
        seed = config.seed

    logger = setup_logging(log_path)
    client = _get_client()
    results: List[RunResult] = []

    logger.info(f"Starting batch run for {len(tasks)} tasks.")
    logger.info(f"Models: {model_ids}, Temperatures: {temperatures}, Runs per task: {num_runs}")

    for task in tasks:
        task_id = task.get("task_id", "unknown")
        logger.info(f"Processing task: {task_id}")

        for model_id in model_ids:
            for temp in temperatures:
                for run_idx in range(num_runs):
                    # Use a deterministic seed per run to ensure reproducibility
                    # We combine the global seed with run index and a hash of task_id
                    run_seed = seed + run_idx + hash(task_id) % 10000

                    result = run_single_inference(
                        client=client,
                        model_id=model_id,
                        temperature=temp,
                        seed=run_seed,
                        task=task,
                        run_index=run_idx,
                        logger=logger
                    )
                    results.append(result)

    # Save results if output path is provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            # Convert dataclasses to dicts for JSON serialization
            json_results = [asdict(r) for r in results]
            json.dump(json_results, f, indent=2)
        logger.info(f"Results saved to {output_path}")

    return results

def main():
    """
    Entry point for the runner.
    Loads tasks from the preprocessed dataset and runs the LLM.
    """
    config = get_config()
    data_path = config.data_path
    output_dir = config.results_path / "artifacts"
    log_path = get_logs_path() / "runner.log"

    # Load preprocessed tasks
    logger = setup_logging(log_path)
    logger.info("Loading preprocessed tasks...")

    if not data_path.exists():
        logger.error(f"Data path does not exist: {data_path}")
        logger.error("Please run the download and preprocess scripts first.")
        sys.exit(1)

    tasks = load_and_count_tasks(data_path)
    if not tasks:
        logger.warning("No tasks found in the dataset.")
        sys.exit(0)

    logger.info(f"Loaded {len(tasks)} tasks.")

    # Get models and temperatures from config
    model_ids = get_models()
    temperatures = get_temperatures()

    output_file = output_dir / "execution_log.json"

    # Run the batch
    results = run_task_batch(
        tasks=tasks,
        model_ids=model_ids,
        temperatures=temperatures,
        num_runs=10,
        seed=config.seed,
        output_path=output_file,
        log_path=log_path
    )

    logger.info(f"Completed {len(results)} total runs.")

    # Summary statistics
    total_tokens = sum(r.tokens_used for r in results)
    total_duration = sum(r.duration_seconds for r in results)
    success_count = sum(1 for r in results if r.success)

    logger.info(f"Total tokens used: {total_tokens}")
    logger.info(f"Total duration: {total_duration:.2f} seconds")
    logger.info(f"Successful runs: {success_count}/{len(results)}")

if __name__ == "__main__":
    main()