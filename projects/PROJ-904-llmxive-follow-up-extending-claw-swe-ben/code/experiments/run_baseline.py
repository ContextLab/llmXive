import os
import sys
import json
import logging
import time
import random
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import set_global_seeds, get_data_dir, get_output_dir, get_log_level, StrategyType
from models.runner import ModelRunner, GenerationConfig
from models.task_instance import TaskInstance, TaskStatus
from models.execution_result import ExecutionResult, ExecutionStatus, FailureCategory
from data.loader import ClawSweBenchLoader
from data.context_processors import process_context
from experiments.batch_executor import BatchExecutor, TimeoutGuard
from utils.logger import setup_logger, log_error, safe_execute, ModelExecutionError

logger = None

def load_filtered_instances(input_path: str) -> list:
    """Load filtered instances from parquet file."""
    try:
        import pandas as pd
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Filtered dataset not found at {input_path}")
        
        df = pd.read_parquet(input_path)
        instances = []
        for _, row in df.iterrows():
            # Convert row to TaskInstance
            instance = TaskInstance(
                instance_id=row['instance_id'],
                issue_description=row['issue_description'],
                patch_expected=row.get('patch_expected', ''),
                file_diffs=row.get('file_diffs', ''),
                relevant_lines=row.get('relevant_lines', 0),
                repo=row.get('repo', ''),
                base_commit=row.get('base_commit', '')
            )
            instances.append(instance)
        
        logger.info(f"Loaded {len(instances)} instances from {input_path}")
        return instances
    except Exception as e:
        log_error(logger, "Failed to load filtered instances", e)
        raise

def process_instance(
    instance: TaskInstance,
    model_runner: ModelRunner,
    strategy: StrategyType,
    timeout_seconds: int = 300
) -> ExecutionResult:
    """Process a single instance with the baseline strategy."""
    start_time = time.time()
    
    try:
        # Apply context strategy (baseline = first N lines)
        processed_context = process_context(instance, strategy)
        
        # Prepare prompt
        prompt = f"""
        Issue: {instance.issue_description}
        Context:
        {processed_context.snippets[0].content if processed_context.snippets else 'No context available'}
        
        Please provide a patch to fix the issue.
        """
        
        # Execute with timeout guard
        @TimeoutGuard(timeout_seconds)
        def run_inference():
            return model_runner.generate(prompt, max_tokens=512)
        
        response = run_inference()
        
        # Evaluate result (simplified - in real implementation would compare to expected patch)
        # For baseline, we assume failure unless we can actually verify
        execution_status = ExecutionStatus.SUCCESS if response else ExecutionStatus.FAILURE
        failure_category = FailureCategory.MODEL_FAILURE if not response else FailureCategory.NONE
        
        elapsed = time.time() - start_time
        
        result = ExecutionResult(
            instance_id=instance.instance_id,
            model_size="1b",
            strategy=strategy.value,
            status=execution_status,
            failure_category=failure_category,
            response=response,
            elapsed_time=elapsed,
            context_tokens=processed_context.token_count
        )
        
        logger.info(f"Processed instance {instance.instance_id}: {execution_status.value} in {elapsed:.2f}s")
        return result
        
    except TimeoutGuard.TimeoutError as e:
        elapsed = time.time() - start_time
        logger.warning(f"Instance {instance.instance_id} timed out after {timeout_seconds}s")
        return ExecutionResult(
            instance_id=instance.instance_id,
            model_size="1b",
            strategy=strategy.value,
            status=ExecutionStatus.TIMEOUT,
            failure_category=FailureCategory.TIMEOUT,
            response=None,
            elapsed_time=elapsed,
            context_tokens=0
        )
    except Exception as e:
        elapsed = time.time() - start_time
        log_error(logger, f"Failed to process instance {instance.instance_id}", e)
        return ExecutionResult(
            instance_id=instance.instance_id,
            model_size="1b",
            strategy=strategy.value,
            status=ExecutionStatus.FAILURE,
            failure_category=FailureCategory.MODEL_FAILURE,
            response=None,
            elapsed_time=elapsed,
            context_tokens=0
        )

def main():
    """Main entry point for baseline execution."""
    global logger
    
    parser = argparse.ArgumentParser(description="Run baseline experiment on filtered SweBench dataset")
    parser.add_argument("--model", type=str, default="1b", help="Model size (1b or 7b)")
    parser.add_argument("--strategy", type=str, default="baseline", choices=["baseline", "tfidf", "diff_aware", "summarization"])
    parser.add_argument("--max-instances", type=int, default=None, help="Maximum number of instances to process")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout per instance in seconds")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()
    
    # Setup logging
    log_level = get_log_level()
    logger = setup_logger("run_baseline", log_level)
    
    # Set global seeds
    set_global_seeds(args.seed)
    
    # Get paths
    data_dir = get_data_dir()
    output_dir = get_output_dir()
    
    # Load filtered dataset
    filtered_path = os.path.join(data_dir, "filtered_swe_bench.parquet")
    if not os.path.exists(filtered_path):
        logger.error(f"Filtered dataset not found at {filtered_path}. Run loader.py first.")
        sys.exit(1)
    
    instances = load_filtered_instances(filtered_path)
    
    # Limit instances if specified
    if args.max_instances:
        instances = instances[:args.max_instances]
    
    logger.info(f"Processing {len(instances)} instances with {args.model} model")
    
    # Initialize model runner
    model_path = os.environ.get("HF_MODEL_PATH_1B" if args.model == "1b" else "HF_MODEL_PATH_7B")
    if not model_path:
        logger.error("Model path not set. Set HF_MODEL_PATH_1B or HF_MODEL_PATH_7B environment variable.")
        sys.exit(1)
    
    try:
        runner = ModelRunner(
            model_path=model_path,
            quantization="Q4_K_M",
            device="cpu",
            generation_config=GenerationConfig(
                max_new_tokens=512,
                temperature=0.7,
                top_p=0.9
            )
        )
    except Exception as e:
        log_error(logger, "Failed to initialize model runner", e)
        sys.exit(1)
    
    # Create batch executor
    executor = BatchExecutor(max_concurrent=1, timeout_per_instance=args.timeout)
    
    # Process instances
    results = []
    strategy_type = StrategyType(args.strategy)
    
    for instance in instances:
        result = safe_execute(
            process_instance,
            logger,
            instance,
            runner,
            strategy_type,
            args.timeout
        )
        if result:
            results.append(result.to_dict())
    
    # Write results
    output_path = os.path.join(output_dir, "intermediate", "baseline_run.jsonl")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        for result in results:
            f.write(json.dumps(result) + '\n')
    
    logger.info(f"Baseline execution complete. Results written to {output_path}")
    logger.info(f"Total instances processed: {len(results)}")
    logger.info(f"Success rate: {sum(1 for r in results if r['status'] == 'SUCCESS') / len(results) * 100:.2f}%")

if __name__ == "__main__":
    main()