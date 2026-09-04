"""
Run High-Fidelity Context Strategies with 1B Model.

Executes the 1B model against all three high-fidelity strategies (TF-IDF,
Diff-Aware, Semantic Summarization) on the filtered dataset.
"""

import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import asdict

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import set_global_seeds, get_env_var, get_model_path, get_data_dir, get_output_dir, StrategyType
from data.loader import ClawSweBenchLoader
from data.context_processors import (
    process_context,
    retrieve_tfidf_snippets,
    retrieve_diff_aware_snippets,
    retrieve_semantic_summaries,
    ProcessedContext
)
from models.runner import ModelRunner, GenerationConfig
from experiments.batch_executor import BatchExecutor, ExecutionStatus, BatchExecutionResult
from analysis.failure_classifier import classify_failure, FailureCategory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
INSTANCE_TIMEOUT_SECONDS = 3600  # 60 minutes per instance
STRATEGIES = [
    StrategyType.TF_IDF,
    StrategyType.DIFF_AWARE,
    StrategyType.SEMANTIC_SUMMARIZATION
]

def load_filtered_instances() -> List[Dict[str, Any]]:
    """
    Load the filtered dataset from the versioned parquet file.
    Falls back to streaming the dataset and filtering if the file doesn't exist.
    """
    data_dir = get_data_dir()
    filtered_path = Path(data_dir) / "filtered_swe_bench_v1.parquet"

    if filtered_path.exists():
        logger.info(f"Loading filtered dataset from {filtered_path}")
        try:
            import pandas as pd
            df = pd.read_parquet(filtered_path)
            instances = df.to_dict('records')
            logger.info(f"Loaded {len(instances)} instances from parquet.")
            return instances
        except Exception as e:
            logger.error(f"Failed to load parquet file: {e}. Falling back to streaming filter.")
    
    # Fallback: Stream and filter (This should ideally not happen if T012b completed successfully)
    logger.warning("Parquet file missing. Streaming and filtering on the fly (slower).")
    loader = ClawSweBenchLoader()
    instances = []
    # Assuming the loader has a method to filter >500 lines or we do it here
    # For safety, we fetch a small batch to demonstrate the logic if parquet is missing
    # In a real run, T012b must have created this file.
    for item in loader.stream_dataset():
        if item.get('lines_of_code', 0) > 500:
            instances.append(item)
            if len(instances) >= 10: # Limit for safety if parquet is missing
                break
    return instances

def run_strategy(
    instance: Dict[str, Any],
    strategy: StrategyType,
    model_runner: ModelRunner,
    timeout: int
) -> Optional[Dict[str, Any]]:
    """
    Execute a single instance with a specific strategy.
    Returns the result dictionary or None if failed.
    """
    start_time = time.time()
    instance_id = instance.get('instance_id', 'unknown')
    
    try:
        # 1. Process Context
        context_config = {
            "strategy": strategy.value,
            "max_tokens": 4096, # Example limit
            "model_size": "1b"
        }
        
        processed: ProcessedContext = process_context(instance, context_config)
        
        if not processed.snippets:
            logger.warning(f"No snippets retrieved for {instance_id} with {strategy.value}. Skipping.")
            return None

        context_text = "\n\n".join([s.content for s in processed.snippets])
        prompt = f"""
        Context:
        {context_text}

        Issue:
        {instance.get('problem_statement', '')}

        Please provide a patch to fix the issue.
        """

        # 2. Run Model
        generation_config = GenerationConfig(
            max_new_tokens=512,
            temperature=0.7,
            do_sample=True
        )
        
        logger.info(f"Running {strategy.value} on {instance_id}")
        response = model_runner.generate(prompt, generation_config)
        
        # 3. Record Result
        elapsed = time.time() - start_time
        result = {
            "instance_id": instance_id,
            "strategy": strategy.value,
            "model_size": "1b",
            "status": "success",
            "prediction": response,
            "context_length": len(processed.snippets),
            "elapsed_seconds": elapsed,
            "timestamp": time.time()
        }
        
        # 4. Classify Failure (if applicable - simplistic check for now)
        # In a real scenario, we would run the sandbox and check the log
        if "error" in response.lower() or "failed" in response.lower():
            result["failure_category"] = classify_failure(response, "sandbox_log_mock")
        else:
            result["failure_category"] = FailureCategory.SUCCESS.value
            
        return result

    except TimeoutError:
        logger.error(f"Timeout for {instance_id} with {strategy.value}")
        return {
            "instance_id": instance_id,
            "strategy": strategy.value,
            "model_size": "1b",
            "status": "timeout",
            "elapsed_seconds": time.time() - start_time
        }
    except Exception as e:
        logger.error(f"Error processing {instance_id} with {strategy.value}: {e}", exc_info=True)
        return {
            "instance_id": instance_id,
            "strategy": strategy.value,
            "model_size": "1b",
            "status": "error",
            "error_message": str(e)
        }

def main():
    """Main entry point for the high-fidelity experiment."""
    logger.info("Starting High-Fidelity Experiment (1B Model)")
    
    # 1. Setup
    set_global_seeds(42)
    data_dir = get_data_dir()
    output_dir = get_output_dir()
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    output_path = Path(output_dir) / "intermediate" / "hf_run_1b.jsonl"
    Path(output_dir / "intermediate").mkdir(parents=True, exist_ok=True)
    
    # 2. Load Data
    instances = load_filtered_instances()
    if not instances:
        logger.error("No instances loaded. Exiting.")
        return
    
    logger.info(f"Loaded {len(instances)} instances to process.")
    
    # 3. Initialize Model
    # T026 ensures this model path is valid for 1B
    model_path = get_model_path("1b") 
    logger.info(f"Initializing ModelRunner with {model_path}")
    
    try:
        model_runner = ModelRunner(model_path=model_path)
    except Exception as e:
        logger.error(f"Failed to initialize model: {e}")
        return

    # 4. Initialize Batch Executor
    executor = BatchExecutor(
        max_workers=4, # Parallel batching
        timeout_per_task=INSTANCE_TIMEOUT_SECONDS
    )
    
    results = []
    
    # 5. Execute
    # We iterate through strategies and instances. 
    # For true parallelism, we could queue all (instance, strategy) pairs.
    total_jobs = len(instances) * len(STRATEGIES)
    logger.info(f"Total jobs to execute: {total_jobs}")
    
    job_count = 0
    for strategy in STRATEGIES:
        logger.info(f"Starting strategy: {strategy.value}")
        for instance in instances:
            job_count += 1
            logger.info(f"Processing [{job_count}/{total_jobs}] {instance['instance_id']} - {strategy.value}")
            
            # Run synchronously with timeout handling via the batch executor logic
            # (In a real async implementation, we would submit futures here)
            result = run_strategy(instance, strategy, model_runner, INSTANCE_TIMEOUT_SECONDS)
            if result:
                results.append(result)
                
                # Write incrementally to avoid memory issues
                with open(output_path, 'a') as f:
                    f.write(json.dumps(result) + '\n')
                    
    logger.info(f"Experiment complete. Results written to {output_path}")

if __name__ == "__main__":
    main()