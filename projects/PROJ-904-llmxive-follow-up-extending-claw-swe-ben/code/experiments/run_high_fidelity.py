import os
import sys
import json
import logging
import time
import random
import argparse
from pathlib import Path

from config import set_global_seeds, get_data_dir, get_output_dir, get_log_level, StrategyType
from data.loader import ClawSweBenchLoader
from data.context_processors import process_context, fallback_strategy
from models.runner import ModelRunner, GenerationConfig
from models.execution_result import ExecutionResult, ExecutionStatus
from experiments.batch_executor import GlobalTimeBudgetEnforcer
from utils.logger import setup_logger, log_error

def get_strategy_function(strategy_name: str):
    """Map strategy name to processing function."""
    # Placeholder for actual strategy logic
    def dummy_strategy(instance, runner, logger):
        return ExecutionResult(
            instance_id=instance['instance_id'],
            status=ExecutionStatus.PENDING,
            strategy=strategy_name,
            model_size="1b",
            pass_at_1=0,
            error=None,
            context_stats={}
        )
    return dummy_strategy

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
    """Process a single instance with a specific strategy."""
    logger.info(f"Processing instance {instance['instance_id']} with strategy {strategy_name}")
    return ExecutionResult(
        instance_id=instance['instance_id'],
        status=ExecutionStatus.PENDING,
        strategy=strategy_name,
        model_size="1b",
        pass_at_1=0,
        error=None,
        context_stats={"lines": len(instance.get('files_in_context', []))}
    )

def run_strategy(args, logger: logging.Logger):
    """Main execution loop for high-fidelity experiments."""
    set_global_seeds(42)
    
    data_dir = get_data_dir()
    output_dir = get_output_dir()
    
    filter_path = os.path.join(data_dir, "filtered_swe_bench_v1.parquet")
    output_path = os.path.join(output_dir, "intermediate", "hf_run_1b.jsonl")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    logger.info(f"Loading filtered instances from {filter_path}")
    instances = load_filtered_instances(filter_path)
    logger.info(f"Loaded {len(instances)} instances")
    
    if args.dry_run:
        logger.info("DRY RUN MODE: Processing only first 2 instances without model execution")
        instances = instances[:2]
        dry_run_output = os.path.join(output_dir, "intermediate", "hf_dry_run.jsonl")
        logger.info(f"Dry run output will be written to {dry_run_output}")
        output_path = dry_run_output

    # Initialize runner
    runner = ModelRunner(
        model_path="meta-llama/Llama-2-1b-hf",
        quantization="q4_k_m",
        device="cpu"
    )
    
    strategies = args.strategies.split(',') if args.strategies else ["baseline", "tfidf", "diff_aware", "summarization"]
    
    results = []
    
    for i, instance in enumerate(instances):
        for strategy in strategies:
            if args.dry_run:
                logger.info(f"[DRY RUN] Simulating processing for {instance['instance_id']} with strategy {strategy}")
                result = ExecutionResult(
                    instance_id=instance['instance_id'],
                    status=ExecutionStatus.SKIPPED,
                    strategy=strategy,
                    model_size="1b",
                    pass_at_1=-1,
                    error="Dry run: model inference skipped",
                    context_stats={"lines": len(instance.get('files_in_context', []))}
                )
            else:
                result = process_instance(instance, strategy, runner, logger)
            
            results.append(result)
        
        if (i + 1) % 10 == 0:
            logger.info(f"Processed {i + 1}/{len(instances)} instances")
    
    with open(output_path, 'w') as f:
        for r in results:
            f.write(json.dumps(r.__dict__) + '\n')
    
    logger.info(f"High-fidelity run complete. Results written to {output_path}")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Run high-fidelity experiments")
    parser.add_argument("--models", type=str, default="1b,7b", help="Model sizes to test")
    parser.add_argument("--strategies", type=str, default="baseline,tfidf,diff_aware,summarization", help="Strategies to test")
    parser.add_argument("--output", type=str, default=None, help="Output file path")
    parser.add_argument("--dry-run", action="store_true", help="Run data loading and context processing only, skip model inference")
    
    args = parser.parse_args()
    
    logger = setup_logger("run_high_fidelity", get_log_level())
    
    try:
        sys.exit(run_strategy(args, logger))
    except Exception as e:
        log_error(f"High-fidelity run failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
