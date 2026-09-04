"""
T016: Execute the filtered dataset with the 1B model and naive strategy.

This script loads the pre-filtered Claw-SWE-Bench instances (instances with
>500 lines of relevant file history), applies the naive "first-N-lines"
truncation strategy, and executes the baseline model (Llama-3-1B) against them.

Output: data/intermediate/baseline_run.jsonl
"""
import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import set_global_seeds, get_model_path, get_data_dir, get_output_dir
from data.loader import ClawSweBenchLoader
from data.context_processors import process_context, StrategyType, ContextConfiguration
from models.runner import ModelRunner, GenerationConfig
from experiments.batch_executor import BatchExecutor, ExecutionStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Hardcoded configuration for T016
MODEL_SIZE = "1b"
STRATEGY = StrategyType.NAIVE_TRUNCATION
TIME_BUDGET_PER_INSTANCE_SECONDS = 3600  # 60 minutes per instance
TOTAL_WALL_CLOCK_BUDGET_SECONDS = 259200  # 72 hours total (enforced by BatchExecutor)
OUTPUT_FILE = "data/intermediate/baseline_run.jsonl"
FILTERED_DATASET_PATH = "data/filtered_swe_bench_v1.parquet"

def load_filtered_instances() -> List[Dict[str, Any]]:
    """
    Loads the filtered dataset from the versioned parquet file.
    Falls back to streaming from HF if the local file doesn't exist,
    but strictly enforces real data only (no synthetic generation).
    """
    data_dir = get_data_dir()
    parquet_path = Path(data_dir) / FILTERED_DATASET_PATH

    if not parquet_path.exists():
        logger.error(f"Filtered dataset not found at {parquet_path}. "
                     "Please run T012b to generate the filtered dataset first.")
        raise FileNotFoundError(
            f"Filtered dataset missing: {parquet_path}. "
            "Run T012b to generate data/filtered_swe_bench_v1.parquet."
        )

    logger.info(f"Loading filtered instances from {parquet_path}")
    try:
        import pandas as pd
        df = pd.read_parquet(parquet_path)
        # Convert to list of dicts
        instances = df.to_dict(orient='records')
        logger.info(f"Loaded {len(instances)} filtered instances.")
        return instances
    except Exception as e:
        logger.error(f"Failed to load parquet file: {e}")
        raise

def process_instance(
    instance: Dict[str, Any],
    runner: ModelRunner,
    strategy: StrategyType,
    timeout_seconds: int
) -> Dict[str, Any]:
    """
    Processes a single instance:
    1. Applies the context processing strategy.
    2. Executes the model generation.
    3. Records the result.
    """
    start_time = time.time()
    instance_id = instance.get("instance_id", "unknown")
    logger.info(f"Processing instance: {instance_id}")

    try:
        # 1. Prepare Context
        # The instance dict from SWE-bench usually contains 'repo', 'issue', 'patches', etc.
        # We need to construct the full context based on the issue.
        # For this baseline, we assume the loader has already provided the relevant file content
        # or we reconstruct it from the instance data if available.
        # Given T013 logic, we expect 'file_history' or similar in the instance.
        
        # Fallback: If the filtered instance doesn't have full file history, 
        # we might need to re-fetch or assume the loader included it.
        # Assuming T012b included the necessary context in the parquet.
        if "file_history" not in instance:
            # If not present, we cannot proceed with context processing.
            # This should not happen if T012b was done correctly.
            raise ValueError(f"Instance {instance_id} missing 'file_history' data.")

        file_history = instance["file_history"]
        
        # Configure context processor
        # For naive strategy, we just take the first N lines of the target file(s)
        ctx_config = ContextConfiguration(
            strategy=strategy,
            max_tokens=4096, # Approximate limit for 1B model context
            truncate_lines=500 # Naive truncation threshold
        )

        processed_ctx = process_context(
            file_history=file_history,
            issue_description=instance.get("problem_statement", ""),
            config=ctx_config
        )

        # 2. Execute Model
        # Construct prompt
        prompt = f"""
        Task: {instance.get('problem_statement', 'Fix the issue.')}
        Relevant Code Context:
        {processed_ctx.snippets[0].content if processed_ctx.snippets else "No context available."}
        
        Provide the fixed code block:
        """.strip()

        generation_config = GenerationConfig(
            max_new_tokens=512,
            temperature=0.0, # Deterministic for baseline
            top_p=1.0
        )

        logger.debug(f"Running inference for {instance_id} with prompt length: {len(prompt)}")
        
        # Run with timeout handled by BatchExecutor, but we can also add local safety
        result = runner.generate(prompt, config=generation_config)

        elapsed = time.time() - start_time

        # 3. Construct Result
        return {
            "instance_id": instance_id,
            "strategy": strategy.value,
            "model_size": MODEL_SIZE,
            "status": "success",
            "execution_time_seconds": elapsed,
            "prompt_length": len(prompt),
            "generated_text": result.get("generated_text", ""),
            "context_used_lines": sum(len(s.content.splitlines()) for s in processed_ctx.snippets),
            "metadata": {
                "repo": instance.get("repo"),
                "problem_statement_preview": instance.get("problem_statement", "")[:100]
            }
        }

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Failed to process instance {instance_id}: {e}", exc_info=True)
        return {
            "instance_id": instance_id,
            "strategy": strategy.value,
            "model_size": MODEL_SIZE,
            "status": "failed",
            "error": str(e),
            "execution_time_seconds": elapsed
        }

def main():
    """Main entry point for the baseline experiment."""
    logger.info("Starting Baseline Experiment (T016)")
    
    # 1. Setup
    set_global_seeds(42)
    model_path = get_model_path(MODEL_SIZE)
    output_dir = get_output_dir()
    output_path = Path(output_dir) / OUTPUT_FILE
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 2. Initialize Components
    logger.info(f"Initializing ModelRunner with {model_path}")
    runner = ModelRunner(model_path=model_path, device="cpu") # Force CPU for 1B baseline stability

    logger.info("Loading filtered instances...")
    instances = load_filtered_instances()

    if not instances:
        logger.warning("No instances loaded. Exiting.")
        return

    # 3. Setup Batch Executor
    # The BatchExecutor handles the 72h wall-clock limit and per-instance timeout
    executor = BatchExecutor(
        total_timeout_seconds=TOTAL_WALL_CLOCK_BUDGET_SECONDS,
        per_instance_timeout_seconds=TIME_BUDGET_PER_INSTANCE_SECONDS
    )

    # 4. Execute
    logger.info(f"Executing {len(instances)} instances with strategy {STRATEGY}")
    
    # We run sequentially or with small batch size for CPU stability
    # The BatchExecutor can wrap the process_instance function
    results = []
    
    # Simple loop with executor logic embedded or via map
    # Since we need to stream results to file, we process one by one
    for i, instance in enumerate(instances):
        if executor.is_expired():
            logger.warning("Total wall-clock budget exceeded. Stopping.")
            break
        
        # Check per-instance timeout (BatchExecutor usually handles this via signal/timeout, 
        # but here we just pass the budget to the function logic if needed. 
        # The BatchExecutor class in T016b handles the hard timeout via signal.)
        
        result = process_instance(
            instance=instance,
            runner=runner,
            strategy=STRATEGY,
            timeout_seconds=TIME_BUDGET_PER_INSTANCE_SECONDS
        )
        
        results.append(result)
        
        # Write intermediate result immediately to avoid data loss on crash
        with open(output_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(result) + '\n')
        
        logger.info(f"Completed {i+1}/{len(instances)} instances. Status: {result['status']}")

    logger.info(f"Experiment finished. Results written to {output_path}")

if __name__ == "__main__":
    main()