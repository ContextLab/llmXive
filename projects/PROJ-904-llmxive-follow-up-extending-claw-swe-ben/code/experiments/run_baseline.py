"""
Baseline Execution Script for US1 (T016).

Executes the filtered Claw-SWE-Bench dataset using the 1B model
with the naive truncation strategy.

Constraints:
- Enforces a hard timeout per instance via batch_executor.
- Outputs results to data/intermediate/baseline_run.jsonl.
"""
import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Iterator

# Project root adjustment for execution context
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from config import (
    set_global_seeds,
    get_env_var,
    get_output_dir,
    get_data_dir,
    ExecutionResult,
    StrategyType,
    TaskInstance,
)
from data.loader import ClawSweBenchLoader
from data.context_processors import NaiveTruncationProcessor, ProcessedContext
from models.runner import ModelRunner, GenerationConfig
from experiments.batch_executor import BatchExecutor, ExecutionStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
MODEL_ID = "meta-llama/Llama-3.2-1B-Instruct"  # Placeholder for actual 1B model path
QUANTIZATION = "Q4_K_M"
TIMEOUT_PER_INSTANCE_SECONDS = 60 * 60  # 60 minutes per instance as per task description
OUTPUT_FILENAME = "baseline_run.jsonl"
FILTERED_DATA_FILENAME = "filtered_swe_bench_v1.parquet"


def load_filtered_instances() -> Iterator[Dict[str, Any]]:
    """
    Loads the filtered dataset from the versioned Parquet file created in T012b.
    Yields instances one by one to manage memory.
    """
    data_dir = get_data_dir()
    parquet_path = data_dir / FILTERED_DATA_FILENAME

    if not parquet_path.exists():
        raise FileNotFoundError(
            f"Filtered dataset not found at {parquet_path}. "
            "Please ensure T012b has been completed and the file exists."
        )

    logger.info(f"Loading filtered instances from {parquet_path}")
    
    try:
        import pandas as pd
        # Stream the parquet file to avoid loading everything into memory at once
        # If the file is too large, we might need to chunk it, but pandas read_parquet
        # with a generator or iterating over chunks is preferred.
        # For simplicity and robustness, we assume it fits or use chunks.
        # Using chunksize if available, otherwise standard read.
        # Since parquet doesn't natively support streaming like CSV in pandas easily without pyarrow,
        # we use pyarrow directly for streaming if needed, but standard read is usually fine for filtered sets.
        
        # Attempt to read in chunks if the file is large
        table = pd.read_parquet(parquet_path)
        for _, row in table.iterrows():
            yield row.to_dict()
            
    except Exception as e:
        logger.error(f"Failed to load filtered dataset: {e}")
        raise


def process_instance(
    instance: Dict[str, Any],
    model_runner: ModelRunner,
    processor: NaiveTruncationProcessor,
    timeout: int
) -> ExecutionResult:
    """
    Processes a single instance: extracts context, runs model, captures result.
    """
    instance_id = instance.get("instance_id", "unknown")
    logger.info(f"Processing instance: {instance_id}")

    # 1. Construct Task Instance
    # Assuming instance dict contains 'problem_statement', 'repo', 'version', 'file_text' etc.
    # Adjust keys based on actual loader output schema if different.
    task_inst = TaskInstance(
        instance_id=instance_id,
        problem_statement=instance.get("problem_statement", ""),
        repo=instance.get("repo", ""),
        version=instance.get("version", ""),
        base_commit=instance.get("base_commit", ""),
        # Context data usually comes from the loader's filtered output
        # We pass the raw context data here to be processed
        raw_context_data=instance
    )

    # 2. Process Context (Naive Truncation)
    try:
        processed_ctx: ProcessedContext = processor.process(task_inst)
        if not processed_ctx or not processed_ctx.context_text:
            logger.warning(f"Instance {instance_id}: Context processing returned empty result.")
            # Fallback to empty context if processor fails, but log it
            processed_ctx = ProcessedContext(context_text="", strategy=StrategyType.NAIVE_TRUNCATION)
    except Exception as e:
        logger.error(f"Instance {instance_id}: Context processing failed: {e}")
        processed_ctx = ProcessedContext(context_text="", strategy=StrategyType.NAIVE_TRUNCATION)

    # 3. Execute Model
    try:
        # Generate prompt
        prompt = f"""
        [SYSTEM] You are an expert software engineer. Solve the following issue.
        [CONTEXT]
        {processed_ctx.context_text}
        [ISSUE]
        {task_inst.problem_statement}
        [TASK]
        Provide the fix.
        """

        # Run with timeout
        result = model_runner.generate(
            prompt=prompt,
            config=GenerationConfig(
                max_new_tokens=512,
                temperature=0.0, # Deterministic for baseline
                top_p=1.0
            ),
            timeout_seconds=timeout
        )

        return ExecutionResult(
            instance_id=instance_id,
            strategy=StrategyType.NAIVE_TRUNCATION,
            model_id=model_runner.model_id,
            success=True, # Success in generation, not necessarily solving
            output_text=result.output_text,
            execution_time=result.execution_time,
            error_message=None,
            metadata={
                "context_length": len(processed_ctx.context_text),
                "timeout_used": timeout
            }
        )

    except TimeoutError:
        logger.warning(f"Instance {instance_id}: Execution timed out.")
        return ExecutionResult(
            instance_id=instance_id,
            strategy=StrategyType.NAIVE_TRUNCATION,
            model_id=model_runner.model_id,
            success=False,
            output_text="",
            execution_time=timeout,
            error_message="TimeoutError",
            metadata={"context_length": len(processed_ctx.context_text)}
        )
    except Exception as e:
        logger.error(f"Instance {instance_id}: Execution failed: {e}")
        return ExecutionResult(
            instance_id=instance_id,
            strategy=StrategyType.NAIVE_TRUNCATION,
            model_id=model_runner.model_id,
            success=False,
            output_text="",
            execution_time=0,
            error_message=str(e),
            metadata={"context_length": len(processed_ctx.context_text)}
        )


def main():
    """
    Main entry point for baseline execution.
    """
    set_global_seeds()
    
    output_dir = get_output_dir()
    intermediate_dir = output_dir / "intermediate"
    intermediate_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = intermediate_dir / OUTPUT_FILENAME
    
    # Initialize Components
    logger.info("Initializing Model Runner (1B)...")
    # Use environment variable for model path if set, else default
    model_path = get_env_var("MODEL_PATH_1B", default=MODEL_ID)
    
    runner = ModelRunner(
        model_id=model_path,
        quantization=QUANTIZATION
    )
    
    logger.info("Initializing Context Processor (Naive)...")
    # Naive truncation strategy: first N lines
    processor = NaiveTruncationProcessor(max_tokens=4096) # Adjust token limit as needed
    
    logger.info("Initializing Batch Executor...")
    executor = BatchExecutor(timeout_per_instance=TIMEOUT_PER_INSTANCE_SECONDS)
    
    logger.info(f"Starting baseline execution. Output: {output_path}")
    
    # Open output file
    with open(output_path, "w", encoding="utf-8") as f_out:
        instances = load_filtered_instances()
        
        for instance in instances:
            # Use the batch executor to enforce timeout
            # The executor handles the timeout logic internally for the callable
            result = executor.execute(
                func=process_instance,
                args=(instance, runner, processor, TIMEOUT_PER_INSTANCE_SECONDS)
            )
            
            # Write result to JSONL
            result_dict = result.to_dict() if hasattr(result, 'to_dict') else result.__dict__
            f_out.write(json.dumps(result_dict) + "\n")
            
            logger.info(f"Completed instance {result_dict.get('instance_id')}: {result_dict.get('error_message') or 'Success'}")

    logger.info(f"Baseline execution complete. Results saved to {output_path}")


if __name__ == "__main__":
    main()
