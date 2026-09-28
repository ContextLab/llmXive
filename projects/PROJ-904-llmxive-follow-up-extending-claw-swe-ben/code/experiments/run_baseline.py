import os
import sys
import json
import logging
import time
import random
import argparse
from pathlib import Path

from config import set_global_seeds, get_data_dir, get_output_dir, get_log_level
from data.loader import ClawSweBenchLoader
from data.context_processors import process_context, fallback_strategy
from models.runner import ModelRunner, GenerationConfig
from models.execution_result import ExecutionResult, ExecutionStatus
from experiments.batch_executor import GlobalTimeBudgetEnforcer
from utils.logger import setup_logger, log_error

def load_filtered_instances(filter_path: str):
    """Load instances from the filtered parquet file."""
    try:
        import pyarrow.parquet as pq
        table = pq.read_table(filter_path)
        return table.to_pandas().to_dict('records')
    except Exception as e:
        log_error(f"Failed to load filtered instances from {filter_path}: {e}")
        raise

def process_instance(instance: dict, strategy_name: str, runner: ModelRunner, logger: logging.Logger):
    """Process a single instance with the baseline strategy."""
    logger.info(f"Processing instance {instance['instance_id']}")
    
    # Context processing logic (dry-run or full)
    # For dry-run, we might skip actual model generation
    return ExecutionResult(
        instance_id=instance['instance_id'],
        status=ExecutionStatus.PENDING,
        strategy=strategy_name,
        model_size="1b",
        pass_at_1=0,
        error=None,
        context_stats={"lines": len(instance.get('files_in_context', []))}
    )

def run_baseline(args, logger: logging.Logger):
    """Main execution loop for baseline experiments."""
    set_global_seeds(42)
    
    data_dir = get_data_dir()
    output_dir = get_output_dir()
    
    filter_path = os.path.join(data_dir, "filtered_swe_bench_v1.parquet")
    output_path = os.path.join(output_dir, "intermediate", "baseline_run.jsonl")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    loader = ClawSweBLoader() # Placeholder for actual loader usage if needed
    
    logger.info(f"Loading filtered instances from {filter_path}")
    instances = load_filtered_instances(filter_path)
    logger.info(f"Loaded {len(instances)} instances")
    
    if args.dry_run:
        logger.info("DRY RUN MODE: Processing only first 2 instances without model execution")
        instances = instances[:2]
        dry_run_output = os.path.join(output_dir, "intermediate", "baseline_dry_run.jsonl")
        logger.info(f"Dry run output will be written to {dry_run_output}")
        output_path = dry_run_output

    # Initialize runner (configurable)
    runner = ModelRunner(
        model_path="meta-llama/Llama-2-1b-hf", # Example path
        quantization="q4_k_m",
        device="cpu"
    )
    
    budget_enforcer = GlobalTimeBudgetEnforcer(
        max_duration_seconds=72 * 3600,
        logger=logger
    )
    
    results = []
    
    for i, instance in enumerate(instances):
        if args.dry_run:
            # In dry run, we just process context and skip model inference
            logger.info(f"[DRY RUN] Simulating processing for {instance['instance_id']}")
            result = ExecutionResult(
                instance_id=instance['instance_id'],
                status=ExecutionStatus.SKIPPED, # Mark as skipped for dry run
                strategy="baseline",
                model_size="1b",
                pass_at_1=-1, # Indicator for dry run
                error="Dry run: model inference skipped",
                context_stats={"lines": len(instance.get('files_in_context', []))}
            )
        else:
            # Normal execution
            result = process_instance(instance, "baseline", runner, logger)
        
        results.append(result)
        
        # Log progress
        if (i + 1) % 10 == 0:
            logger.info(f"Processed {i + 1}/{len(instances)} instances")
    
    # Write results
    with open(output_path, 'w') as f:
        for r in results:
            f.write(json.dumps(r.__dict__) + '\n')
    
    logger.info(f"Baseline run complete. Results written to {output_path}")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Run baseline experiments")
    parser.add_argument("--model", type=str, default="1b", help="Model size (1b, 7b)")
    parser.add_argument("--strategy", type=str, default="baseline", help="Strategy name")
    parser.add_argument("--max-instances", type=int, default=None, help="Max instances to process")
    parser.add_argument("--dry-run", action="store_true", help="Run data loading and context processing only, skip model inference")
    
    args = parser.parse_args()
    
    logger = setup_logger("run_baseline", get_log_level())
    
    try:
        sys.exit(run_baseline(args, logger))
    except Exception as e:
        log_error(f"Baseline run failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
