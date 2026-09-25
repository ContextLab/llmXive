"""
High-Fidelity Experiment Runner for US2.
Executes the model against TF-IDF, Diff-Aware, and Semantic Summarization strategies.
"""
import os
import sys
import json
import logging
import time
import random
import argparse
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional

# Project imports based on API surface
from config import (
    set_global_seeds,
    get_env_var,
    get_model_path,
    get_data_dir,
    get_output_dir,
    StrategyType,
    get_log_level
)
from models.runner import ModelRunner, GenerationConfig
from models.execution_result import ExecutionResult, ExecutionStatus, FailureCategory
from models.task_instance import TaskInstance, TaskStatus
from models.context_config import ContextConfiguration
from data.context_processors import (
    retrieve_tfidf_snippets,
    retrieve_diff_aware_snippets,
    retrieve_semantic_summaries,
    process_context,
    fallback_strategy
)
from experiments.batch_executor import GlobalTimeBudgetEnforcer, BatchExecutor
from utils.logger import setup_logger, log_error, safe_execute

# Configure logging
logger = setup_logger("run_high_fidelity", get_log_level())

# Strategy mapping
STRATEGY_MAP: Dict[str, Callable] = {
    "tfidf": retrieve_tfidf_snippets,
    "diff_aware": retrieve_diff_aware_snippets,
    "summarization": retrieve_semantic_summaries
}

def get_strategy_function(strategy_name: str) -> Callable:
    """
    Returns the context retrieval function for the given strategy name.
    """
    if strategy_name not in STRATEGY_MAP:
        raise ValueError(f"Unknown strategy: {strategy_name}. Available: {list(STRATEGY_MAP.keys())}")
    return STRATEGY_MAP[strategy_name]

def load_filtered_instances(input_path: str) -> List[Dict[str, Any]]:
    """
    Loads the filtered dataset from the parquet file produced by T012c.
    """
    import pandas as pd
    try:
        df = pd.read_parquet(input_path)
        logger.info(f"Loaded {len(df)} instances from {input_path}")
        return df.to_dict(orient='records')
    except Exception as e:
        log_error(logger, f"Failed to load filtered instances from {input_path}", e)
        raise

def process_instance(
    instance: Dict[str, Any],
    strategy_func: Callable,
    model_runner: ModelRunner,
    timeout_seconds: int = 3600
) -> Optional[ExecutionResult]:
    """
    Executes a single instance with the given strategy and model.
    Enforces per-instance timeout.
    """
    start_time = time.time()
    try:
        # 1. Prepare Context
        # Extract relevant fields from the instance
        issue_desc = instance.get('issue_description', '')
        repo_files = instance.get('repo_files', [])
        # Assuming 'repo_files' is a list of dicts with 'path' and 'content' or similar
        # Adjust based on actual schema of filtered_swe_bench_v1.parquet if different
        
        # Use the strategy function to get context snippets
        # The strategy function expects (issue_desc, repo_files, ...)
        # We assume the loader provides these in the instance dict
        snippets = strategy_func(issue_desc, repo_files)
        
        # If empty, use fallback
        if not snippets:
            logger.warning(f"Strategy returned empty snippets for instance {instance.get('instance_id')}. Using fallback.")
            snippets = fallback_strategy(issue_desc, repo_files)

        # Build ContextConfiguration
        context_config = ContextConfiguration(
            strategy=StrategyType(strategy_func.__name__.replace('retrieve_', '')),
            snippets=snippets
        )

        # 2. Run Model
        # Construct the prompt (simplified for this implementation)
        prompt = f"Issue: {issue_desc}\n\nContext:\n{context_config.format_context()}"
        
        # Run with timeout guard (internal to runner or external)
        # Assuming ModelRunner.run() handles the inference
        response = model_runner.run(prompt, timeout=timeout_seconds)

        end_time = time.time()
        duration = end_time - start_time

        # Determine pass/fail (simplified logic - in real scenario, parse response)
        # For this task, we assume the model returns a "PASS" or "FAIL" in the response or we simulate a check
        # Since we are running real code, we must have a deterministic way to check.
        # Assuming the model response contains a solution or a specific marker.
        # For the purpose of this implementation, we will check if 'solution' key exists in response or similar.
        # If the model fails to generate a valid solution, we mark as failure.
        
        # Placeholder for actual evaluation logic
        is_pass = False
        if isinstance(response, dict) and response.get('status') == 'success':
            is_pass = True # Simplified
        
        result = ExecutionResult(
            instance_id=instance.get('instance_id'),
            strategy=str(context_config.strategy),
            model_size="1b", # US2 uses 1B model
            passed=is_pass,
            duration_seconds=duration,
            status=ExecutionStatus.SUCCESS if is_pass else ExecutionStatus.FAILURE,
            failure_category=FailureCategory.REASONING_ERROR if not is_pass else None,
            raw_response=str(response)
        )
        return result

    except Exception as e:
        logger.error(f"Error processing instance {instance.get('instance_id')}: {e}")
        log_error(logger, f"Instance processing failed", e)
        return ExecutionResult(
            instance_id=instance.get('instance_id'),
            strategy=strategy_func.__name__.replace('retrieve_', ''),
            model_size="1b",
            passed=False,
            duration_seconds=time.time() - start_time,
            status=ExecutionStatus.ERROR,
            failure_category=FailureCategory.SYSTEM_ERROR,
            raw_response=str(e)
        )

def run_strategy(
    instances: List[Dict[str, Any]],
    strategy_name: str,
    model_runner: ModelRunner,
    output_path: Path,
    per_instance_timeout: int = 3600,
    total_timeout: int = 259200 # 72 hours
) -> List[ExecutionResult]:
    """
    Executes the model against a specific strategy for all instances.
    """
    logger.info(f"Starting strategy: {strategy_name}")
    strategy_func = get_strategy_function(strategy_name)
    
    results = []
    batch_executor = BatchExecutor()
    time_enforcer = GlobalTimeBudgetEnforcer(total_timeout_seconds=total_timeout)

    for idx, instance in enumerate(instances):
        if time_enforcer.is_expired():
            logger.warning("Global time budget exceeded. Terminating batch.")
            break

        # Create a task for the batch executor
        # We process sequentially here for safety, but the BatchExecutor handles parallelism if configured
        # For this script, we iterate and submit to the executor's queue if parallelism is desired.
        # Given the 60min per instance constraint, we run them one by one or in small batches.
        
        result = process_instance(
            instance, 
            strategy_func, 
            model_runner, 
            timeout_seconds=per_instance_timeout
        )
        
        if result:
            results.append(result)
            # Save intermediate state every 10 instances to avoid data loss on crash
            if (idx + 1) % 10 == 0:
                save_results(results, output_path)
                logger.info(f"Saved {len(results)} results to {output_path}")

    save_results(results, output_path)
    logger.info(f"Strategy {strategy_name} complete. Total results: {len(results)}")
    return results

def save_results(results: List[ExecutionResult], output_path: Path):
    """
    Saves the list of ExecutionResult objects to a JSONL file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for res in results:
            f.write(res.to_json() + '\n')

def main():
    parser = argparse.ArgumentParser(description="Run High-Fidelity Experiments (US2)")
    parser.add_argument("--input", type=str, default="data/filtered_swe_bench_v1.parquet", help="Path to filtered dataset")
    parser.add_argument("--output", type=str, default="data/intermediate/hf_run_1b.jsonl", help="Output JSONL path")
    parser.add_argument("--strategies", type=str, nargs='+', default=["tfidf", "diff_aware", "summarization"], help="Strategies to run")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    set_global_seeds(args.seed)
    
    # Initialize ModelRunner for 1B model (US2)
    # Configured in T015 to use Q4_K_M on CPU
    model_path = get_model_path("1b")
    runner = ModelRunner(model_path=model_path, device="cpu", quantization="Q4_K_M")

    # Load data
    instances = load_filtered_instances(args.input)
    
    output_path = Path(args.output)
    all_results = []

    for strategy in args.strategies:
        # Run the strategy
        strategy_results = run_strategy(
            instances, 
            strategy, 
            runner, 
            output_path,
            per_instance_timeout=3600, # 60 mins per instance
            total_timeout=259200      # 72 hours total
        )
        all_results.extend(strategy_results)

    # Ensure the final file contains all strategies
    save_results(all_results, output_path)
    logger.info(f"All strategies complete. Final output saved to {output_path}")

if __name__ == "__main__":
    main()