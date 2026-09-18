import os
import sys
import json
import logging
import time
import random
import argparse
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional

# Import from sibling modules based on API surface
from config import set_global_seeds, get_data_dir, get_output_dir, StrategyType
from data.loader import ClawSweBenchLoader, filter_dataset, write_parquet_and_checksum, record_derivation
from models.runner import ModelRunner, GenerationConfig
from data.context_processors import (
    retrieve_tfidf_snippets,
    retrieve_diff_aware_snippets,
    retrieve_semantic_summaries,
    process_context,
    ContextSnippet,
    ProcessedContext
)
from experiments.batch_executor import BatchExecutor, TimeoutGuard
from utils.logger import setup_logger, log_error, safe_execute, ModelExecutionError

# --- Configuration Constants ---
# Defined to ensure reproducibility and adherence to Constitution Principle I
DEFAULT_SEED = 42
DEFAULT_MAX_INSTANCES = 50  # Sufficient for initial statistical power validation
DEFAULT_TIMEOUT_SECONDS = 600  # 10 minutes per instance
DEFAULT_OUTPUT_FILE = "data/intermediate/hf_run_1b.jsonl"

# Strategy mapping for high-fidelity experiments
STRATEGY_MAP = {
    "baseline": None,  # No processing, raw context
    "tfidf": retrieve_tfidf_snippets,
    "diff_aware": retrieve_diff_aware_snippets,
    "summarization": retrieve_semantic_summaries
}

def get_strategy_function(strategy_name: str) -> Optional[Callable]:
    """
    Retrieve the context processing function for a given strategy name.
    
    Args:
        strategy_name: Name of the strategy (baseline, tfidf, diff_aware, summarization)
        
    Returns:
        Callable function for context processing or None for baseline
        
    Raises:
        ValueError: If strategy name is unknown
    """
    if strategy_name not in STRATEGY_MAP:
        raise ValueError(f"Unknown strategy: {strategy_name}. Valid options: {list(STRATEGY_MAP.keys())}")
    return STRATEGY_MAP[strategy_name]

def load_filtered_instances(input_path: str) -> List[Dict[str, Any]]:
    """
    Load filtered instances from the parquet file produced by T012.
    
    Args:
        input_path: Path to the filtered parquet file
        
    Returns:
        List of task instance dictionaries
    """
    try:
        import pandas as pd
        df = pd.read_parquet(input_path)
        # Convert to list of dicts for processing
        instances = df.to_dict('records')
        logging.info(f"Loaded {len(instances)} filtered instances from {input_path}")
        return instances
    except Exception as e:
        log_error(f"Failed to load filtered instances from {input_path}: {e}")
        raise

def process_instance(
    instance: Dict[str, Any],
    strategy_func: Optional[Callable],
    model_runner: ModelRunner,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
) -> Dict[str, Any]:
    """
    Process a single task instance with the specified context strategy and model.
    
    Args:
        instance: The task instance dictionary
        strategy_func: Context processing function (None for baseline)
        model_runner: The ModelRunner instance
        timeout_seconds: Execution timeout per instance
        
    Returns:
        Dictionary containing execution result
    """
    start_time = time.time()
    instance_id = instance.get("instance_id", "unknown")
    
    try:
        # Apply context strategy if not baseline
        if strategy_func:
            # Extract necessary fields for context processing
            # Assuming instance contains 'files' (list of dicts with path, content) and 'issue'
            files = instance.get("files", [])
            issue = instance.get("issue", "")
            
            if not files:
                logging.warning(f"Instance {instance_id} has no files, skipping context processing")
                processed_context = []
            else:
                # Process context using the strategy
                processed_context = process_context(
                    files=files,
                    issue=issue,
                    strategy_func=strategy_func
                )
        else:
            # Baseline: use raw context (all files)
            processed_context = instance.get("files", [])

        # Prepare prompt (simplified logic for demonstration)
        # In a real scenario, this would involve prompt engineering
        prompt = f"Issue: {instance.get('issue', '')}\n\nContext:\n"
        for snippet in processed_context:
            if isinstance(snippet, dict):
                prompt += f"File: {snippet.get('path', 'unknown')}\n{snippet.get('content', '')}\n---\n"
            else:
                prompt += f"{snippet}\n---\n"
        
        prompt += "\nPlease provide a solution patch."

        # Execute model generation with timeout guard
        @TimeoutGuard(seconds=timeout_seconds)
        def run_generation():
            return model_runner.generate(prompt)

        generation = run_generation()
        
        end_time = time.time()
        duration = end_time - start_time

        return {
            "instance_id": instance_id,
            "strategy": "baseline" if strategy_func is None else strategy_func.__name__,
            "model": model_runner.model_name,
            "status": "success",
            "generation": generation,
            "duration_seconds": duration,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

    except TimeoutError as e:
        log_error(f"Timeout for instance {instance_id}: {e}")
        return {
            "instance_id": instance_id,
            "strategy": "baseline" if strategy_func is None else strategy_func.__name__,
            "model": model_runner.model_name,
            "status": "timeout",
            "error": str(e),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        log_error(f"Error processing instance {instance_id}: {e}")
        return {
            "instance_id": instance_id,
            "strategy": "baseline" if strategy_func is None else strategy_func.__name__,
            "model": model_runner.model_name,
            "status": "error",
            "error": str(e),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

def run_strategy(
    instances: List[Dict[str, Any]],
    strategy_name: str,
    model_runner: ModelRunner,
    output_path: str,
    max_instances: int = DEFAULT_MAX_INSTANCES
) -> None:
    """
    Execute the high-fidelity strategy on a batch of instances.
    
    Args:
        instances: List of task instances
        strategy_name: Name of the strategy to apply
        model_runner: The ModelRunner instance
        output_path: Path to write JSONL results
        max_instances: Maximum number of instances to process
    """
    strategy_func = get_strategy_function(strategy_name)
    logging.info(f"Starting strategy '{strategy_name}' with model '{model_runner.model_name}'")
    
    results = []
    batch_executor = BatchExecutor(max_workers=4) # Parallelize if needed, though model might be single-threaded

    # Limit instances for the run
    instances_to_process = instances[:max_instances]
    logging.info(f"Processing {len(instances_to_process)} instances for strategy {strategy_name}")

    for i, instance in enumerate(instances_to_process):
        logging.info(f"Processing instance {i+1}/{len(instances_to_process)}: {instance.get('instance_id')}")
        result = process_instance(instance, strategy_func, model_runner)
        results.append(result)
        
        # Optional: Save incrementally to avoid data loss on crash
        if (i + 1) % 10 == 0:
            with open(output_path, 'a', encoding='utf-8') as f:
                for res in results:
                    f.write(json.dumps(res) + '\n')
            results = [] # Clear batch

    # Write remaining results
    if results:
        with open(output_path, 'a', encoding='utf-8') as f:
            for res in results:
                f.write(json.dumps(res) + '\n')
    
    logging.info(f"Strategy '{strategy_name}' complete. Results written to {output_path}")

def main():
    """
    Main entry point for the high-fidelity experiment runner.
    Orchestrates loading data, initializing the model, and running strategies.
    """
    parser = argparse.ArgumentParser(description="Run high-fidelity context strategies")
    parser.add_argument("--model", type=str, default="1b", help="Model size (1b or 7b)")
    parser.add_argument("--strategies", type=str, default="baseline,tfidf,diff_aware,summarization",
                        help="Comma-separated list of strategies to run")
    parser.add_argument("--input", type=str, default=None, help="Path to filtered parquet file")
    parser.add_argument("--output", type=str, default=DEFAULT_OUTPUT_FILE, help="Output JSONL path")
    parser.add_argument("--max-instances", type=int, default=DEFAULT_MAX_INSTANCES, help="Max instances to process")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed")
    
    args = parser.parse_args()

    # Setup logging
    log_dir = Path(get_output_dir()) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = setup_logger("run_high_fidelity", log_dir / "run_high_fidelity.log")

    # Set seeds
    set_global_seeds(args.seed)
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    logging.info("Starting High-Fidelity Experiment Runner")
    logging.info(f"Configuration: Model={args.model}, Strategies={args.strategies}, MaxInstances={args.max_instances}")

    # 1. Load Data
    # Default input path if not specified, derived from T012 output
    input_path = args.input or str(Path(get_data_dir()) / "filtered_swe_bench.parquet")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Filtered dataset not found at {input_path}. Run T012 first.")
    
    instances = load_filtered_instances(input_path)
    
    # 2. Initialize Model Runner
    model_path = get_model_path(args.model)
    logging.info(f"Initializing ModelRunner for {args.model} at {model_path}")
    
    # Configure generation parameters
    gen_config = GenerationConfig(
        max_new_tokens=512,
        temperature=0.0, # Deterministic for benchmarking
        top_p=1.0,
        do_sample=False
    )
    
    runner = ModelRunner(
        model_name=args.model,
        model_path=model_path,
        config=gen_config
    )
    
    # 3. Run Strategies
    strategies = [s.strip() for s in args.strategies.split(",")]
    output_dir = Path(get_output_dir())
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for strategy in strategies:
        # Construct output path per strategy
        strategy_output = output_dir / f"hf_run_{args.model}_{strategy}.jsonl"
        
        try:
            run_strategy(
                instances=instances,
                strategy_name=strategy,
                model_runner=runner,
                output_path=str(strategy_output),
                max_instances=args.max_instances
            )
        except Exception as e:
            log_error(f"Failed to run strategy {strategy}: {e}")
            raise

    logging.info("All high-fidelity experiments completed successfully.")

if __name__ == "__main__":
    main()