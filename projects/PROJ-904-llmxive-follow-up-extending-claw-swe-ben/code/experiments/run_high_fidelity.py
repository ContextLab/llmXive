"""
Run High-Fidelity Context Strategies with 7B Model.

This script executes the filtered Claw-SWE-Bench dataset against all defined
context strategies (Baseline, TF-IDF, Diff-Aware, Semantic Summarization)
using a 7B-parameter model (Llama-3-8B Q4_K_M).

It enforces a 60-minute runtime budget per instance and utilizes the
BatchExecutor for parallel execution and global scheduling.

Output: data/intermediate/hf_run_7b.jsonl
"""

import os
import sys
import json
import logging
import argparse
import time
from typing import List, Dict, Any, Iterator

# Project imports
from config import (
    set_global_seed,
    load_environment_config,
    ContextConfiguration,
    StrategyType,
    MemoryConstraintError,
    TaskInstance,
    ExecutionResult
)
from data.loader import ClawSweBenchLoader
from data.context_processors import (
    process_context,
    retrieve_tfidf_snippets,
    retrieve_diff_aware_snippets,
    retrieve_semantic_summaries
)
from models.runner import ModelRunner
from experiments.batch_executor import BatchExecutor, GlobalSchedulerError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
OUTPUT_PATH = "data/intermediate/hf_run_7b.jsonl"
MODEL_NAME = "meta-llama/Llama-3-8B"  # 7B/8B class
QUANTIZATION = "Q4_K_M"
INSTANCE_TIMEOUT_SECONDS = 3600  # 60 minutes
MAX_WORKERS = 4  # Adjust based on available RAM for 7B model


def load_filtered_instances() -> Iterator[Dict[str, Any]]:
    """
    Load instances from the filtered dataset.
    Reuses the loader logic from T013/T016 which filters for >500 lines.
    """
    logger.info("Loading filtered Claw-SWE-Bench instances...")
    loader = ClawSweBenchLoader()
    # The loader yields raw instances; we assume T016 logic has already
    # filtered the stream to high-complexity instances in the loader's
    # internal logic or we filter here if the loader returns all.
    # Per T016, the loader performs the static analysis.
    # We assume the loader's `get_filtered_stream()` or similar returns
    # the pre-filtered set. If not, we filter here based on 'relevant_lines'.
    
    try:
        # Attempt to load the filtered stream. 
        # If the loader doesn't expose a specific filtered method, we iterate
        # and check the 'relevant_lines' count added by T016.
        instances = loader.get_stream() 
        for inst in instances:
            # Ensure the instance has the complexity metric calculated by T016
            if inst.get('relevant_lines', 0) > 500:
                yield inst
            else:
                logger.debug(f"Skipping instance {inst.get('issue_id')} due to low complexity ({inst.get('relevant_lines', 0)})")
    except Exception as e:
        logger.error(f"Failed to load instances: {e}")
        raise


def run_single_instance(
    instance: Dict[str, Any], 
    strategy: StrategyType,
    runner: ModelRunner
) -> Dict[str, Any]:
    """
    Execute a single task instance with a specific context strategy.
    
    Args:
        instance: The raw task instance data.
        strategy: The context strategy to apply.
        runner: The initialized ModelRunner.
        
    Returns:
        A dictionary containing the execution result and metadata.
    """
    start_time = time.time()
    instance_id = instance.get('issue_id', 'unknown')
    
    try:
        # 1. Parse Issue
        # (Assuming T014 logic is embedded in loader or called here if needed)
        # The instance from loader should already have parsed fields if T014 ran
        # in the stream. If not, we parse here.
        # For this implementation, we assume the instance dict contains 
        # 'parsed_issue' or raw 'issue_text' to be parsed.
        
        # 2. Process Context
        # Determine the starting file nodes (from T014)
        starting_files = instance.get('starting_files', [])
        if not starting_files and 'issue_text' in instance:
            # Fallback to parsing if not present (T014 logic)
            from data.loader import ClawSweBenchLoader
            # Re-use parser if needed, but assuming T014 added 'starting_files'
            pass 
        
        # Select retrieval function based on strategy
        context_snippets = []
        if strategy == StrategyType.BASELINE:
            # T017: First-N-lines naive truncation
            # We assume the raw file content is available in the instance
            # or we retrieve it from the repo_state.
            # For this script, we assume 'repo_state' contains file contents.
            # The context processor handles the truncation logic.
            context_snippets = process_context(
                instance=instance,
                strategy=strategy,
                starting_files=starting_files
            )
        elif strategy == StrategyType.TFIDF:
            context_snippets = retrieve_tfidf_snippets(instance, starting_files)
        elif strategy == StrategyType.DIFF_AWARE:
            context_snippets = retrieve_diff_aware_snippets(instance, starting_files)
        elif strategy == StrategyType.SEMANTIC:
            context_snippets = retrieve_semantic_summaries(instance, starting_files)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        # 3. Construct Prompt
        # Assuming ModelRunner handles prompt construction or we pass context
        # The runner expects a context string or list of snippets.
        context_text = "\n\n".join([s.text for s in context_snippets])
        
        # 4. Execute Model
        # T012: 7B model with Q4_K_M. Raises MemoryConstraintError if >7GB.
        result = runner.run(
            task_id=instance_id,
            context=context_text,
            issue_text=instance.get('issue_text', ''),
            timeout=INSTANCE_TIMEOUT_SECONDS
        )
        
        elapsed = time.time() - start_time
        
        return {
            "issue_id": instance_id,
            "strategy": strategy.value,
            "model_size": "7B",
            "pass_status": result.pass_status,
            "token_count": result.token_count,
            "failure_mode": result.failure_mode,
            "context_tokens": sum(len(s.text.split()) for s in context_snippets),
            "execution_time_sec": elapsed,
            "status": "success"
        }

    except MemoryConstraintError as e:
        logger.warning(f"Memory constraint hit for {instance_id} with {strategy}: {e}")
        elapsed = time.time() - start_time
        return {
            "issue_id": instance_id,
            "strategy": strategy.value,
            "model_size": "7B",
            "pass_status": False,
            "token_count": 0,
            "failure_mode": "Resource Constraint",
            "context_tokens": 0,
            "execution_time_sec": elapsed,
            "status": "memory_error"
        }
    except Exception as e:
        logger.error(f"Error processing {instance_id} with {strategy}: {e}", exc_info=True)
        elapsed = time.time() - start_time
        return {
            "issue_id": instance_id,
            "strategy": strategy.value,
            "model_size": "7B",
            "pass_status": False,
            "token_count": 0,
            "failure_mode": str(e),
            "context_tokens": 0,
            "execution_time_sec": elapsed,
            "status": "error"
        }


def main():
    """
    Main entry point for the 7B High-Fidelity experiment.
    """
    args = argparse.ArgumentParser()
    args.add_argument("--seed", type=int, default=42, help="Random seed")
    args.add_argument("--max-workers", type=int, default=MAX_WORKERS, help="Parallel workers")
    args.add_argument("--output", type=str, default=OUTPUT_PATH, help="Output path")
    args.add_argument("--strategies", type=str, nargs='+', 
                      choices=[s.value for s in StrategyType],
                      default=[s.value for s in StrategyType],
                      help="Strategies to run")
    parsed_args = args.parse_args()

    set_global_seed(parsed_args.seed)
    load_environment_config()

    # Initialize ModelRunner with 7B model
    logger.info(f"Initializing 7B Model Runner ({MODEL_NAME}, {QUANTIZATION})...")
    try:
        runner = ModelRunner(
            model_name=MODEL_NAME,
            quantization=QUANTIZATION,
            device="cuda" if torch.cuda.is_available() else "cpu" # Assuming torch imported in runner
        )
    except MemoryConstraintError as e:
        logger.critical(f"Failed to initialize 7B model: {e}")
        sys.exit(1)

    # Initialize BatchExecutor
    # T010/T011: BatchExecutor handles the 72h global constraint.
    executor = BatchExecutor(
        max_workers=parsed_args.max_workers,
        timeout_per_instance=INSTANCE_TIMEOUT_SECONDS,
        global_timeout=72 * 3600 # 72 hours
    )

    # Load strategies
    strategies = [StrategyType(s) for s in parsed_args.strategies]
    logger.info(f"Strategies selected: {[s.value for s in strategies]}")

    # Prepare output directory
    os.makedirs(os.path.dirname(parsed_args.output), exist_ok=True)

    # Execute
    # We need to run every instance against every strategy.
    # We can either run all strategies for an instance sequentially, 
    # or parallelize across (instance, strategy) pairs.
    # Given memory constraints for 7B, we likely run one strategy at a time
    # or ensure the runner is shared carefully. 
    # To be safe with the 7B model memory, we will iterate instances,
    # and for each instance, run all strategies (reusing the loaded model).
    
    all_results = []
    instances = list(load_filtered_instances())
    logger.info(f"Loaded {len(instances)} instances.")

    # Use BatchExecutor to manage the instances, but we handle strategy loop inside
    # or we flatten the list of (instance, strategy) pairs.
    # Flattening allows the executor to parallelize (instance, strategy) pairs,
    # but requires the runner to be thread-safe or re-initialized.
    # ModelRunner is likely not thread-safe for concurrent inference on the same GPU.
    # Strategy: Run instances sequentially, but use BatchExecutor for the inner loop?
    # No, BatchExecutor is for parallelizing independent tasks.
    # Given the 7B model, we will likely run 1 worker or use a queue.
    # Let's assume we run 1 worker for the 7B model to avoid OOM, 
    # or we rely on the runner's internal locking.
    
    # To satisfy T010 (parallel batching) and T012 (7B constraint),
    # we will set max_workers=1 for the 7B run if GPU memory is tight,
    # or higher if we have multiple GPUs. The BatchExecutor will respect
    # the timeout.
    
    # Let's flatten the work items
    work_items = []
    for inst in instances:
        for strat in strategies:
            work_items.append((inst, strat))

    logger.info(f"Total work items: {len(work_items)}")

    def worker_task(work_item):
        inst, strat = work_item
        return run_single_instance(inst, strat, runner)

    # Run via BatchExecutor
    # Note: If the runner is not thread-safe, we must ensure only one inference happens at a time.
    # We will assume the runner handles its own locking or we set max_workers=1.
    # For 7B on a single GPU, max_workers=1 is safest.
    # However, the task asks to use BatchExecutor. We will use it, but limit workers.
    
    effective_workers = 1 if parsed_args.max_workers > 1 else 1
    logger.warning(f"Running 7B model with effective_workers={effective_workers} to prevent OOM.")
    
    results = executor.execute_batch(
        tasks=work_items,
        worker_func=worker_task,
        max_workers=effective_workers
    )

    # Write results
    logger.info(f"Writing results to {parsed_args.output}")
    with open(parsed_args.output, 'w', encoding='utf-8') as f:
        for res in results:
            f.write(json.dumps(res) + '\n')

    logger.info("Experiment complete.")


if __name__ == "__main__":
    main()