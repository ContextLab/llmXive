"""
Baseline experiment runner for llmXive follow-up study.

Executes a naive baseline (first-N-lines truncation) on filtered Claw-SWE-Bench
instances using a 1B-parameter model with Q4_K_M quantization on CPU.

Constitution Principle I: Random seeds are explicitly pinned here to ensure
reproducibility even if the global config is decoupled.
"""
import os
import sys
import json
import logging
import time
import random
import numpy as np
import torch
from pathlib import Path
from typing import List, Dict, Any, Optional

# Project imports
from config import set_global_seeds, get_data_dir, get_output_dir, get_log_level
from data.loader import ClawSweBenchLoader
from models.runner import ModelRunner, GenerationConfig
from experiments.batch_executor import BatchExecutor, ExecutionStatus
from analysis.failure_classifier import classify_failure

# ============================================================================
# Constitution Principle I: Explicit Random Seed Pinning
# ============================================================================
# Even if config.py sets seeds globally, we pin them here explicitly to ensure
# reproducibility regardless of execution context or config decoupling.
# This satisfies the requirement: "Implement explicit random seed pinning...
# to ensure reproducibility even if config is decoupled."
_RANDOM_SEED = 42
random.seed(_RANDOM_SEED)
np.random.seed(_RANDOM_SEED)
torch.manual_seed(_RANDOM_SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(_RANDOM_SEED)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False
# ============================================================================

logger = logging.getLogger(__name__)

def load_filtered_instances() -> List[Dict[str, Any]]:
    """
    Load the filtered dataset from the versioned Parquet file.
    
    Returns:
        List of filtered task instances.
    
    Raises:
        FileNotFoundError: If the filtered dataset does not exist.
    """
    data_dir = get_data_dir()
    filtered_path = data_dir / "filtered_swe_bench_v1.parquet"
    
    if not filtered_path.exists():
        raise FileNotFoundError(
            f"Filtered dataset not found at {filtered_path}. "
            "Run data filtering task first."
        )
    
    logger.info(f"Loading filtered instances from {filtered_path}")
    import pandas as pd
    df = pd.read_parquet(filtered_path)
    instances = df.to_dict('records')
    logger.info(f"Loaded {len(instances)} filtered instances")
    return instances

def process_instance(
    instance: Dict[str, Any], 
    runner: ModelRunner, 
    batch_executor: BatchExecutor
) -> Dict[str, Any]:
    """
    Process a single instance: apply baseline context strategy and run model.
    
    Args:
        instance: The task instance dictionary.
        runner: The configured ModelRunner.
        batch_executor: The batch executor for timeout enforcement.
    
    Returns:
        Dictionary containing the execution result.
    """
    instance_id = instance.get('instance_id', 'unknown')
    logger.info(f"Processing instance: {instance_id}")
    
    # Apply naive baseline strategy: first-N-lines truncation
    # (Simplified for baseline - in production, use context_processors.py)
    context_text = instance.get('file_history', '')
    if isinstance(context_text, list):
        context_text = '\n'.join(context_text)
    
    # Truncate to first 4096 tokens (simplified approximation)
    max_tokens = 4096
    tokens = context_text.split()
    if len(tokens) > max_tokens:
        truncated_context = ' '.join(tokens[:max_tokens])
        logger.warning(f"Truncated context for {instance_id} from {len(tokens)} to {max_tokens} tokens")
    else:
        truncated_context = context_text
    
    prompt = f"""Solve the following issue based on the provided code context:

Issue: {instance.get('issue_text', '')}

Code Context:
{truncated_context}

Provide your solution as a diff patch:"""
    
    # Execute with timeout protection
    start_time = time.time()
    try:
        result = batch_executor.submit(
            task_id=instance_id,
            task_func=runner.generate,
            prompt=prompt,
            config=GenerationConfig(
                max_new_tokens=512,
                temperature=0.0,  # Deterministic for baseline
                do_sample=False
            )
        )
        
        if result.status == ExecutionStatus.SUCCESS:
            execution_time = time.time() - start_time
            return {
                'instance_id': instance_id,
                'strategy': 'baseline_first_n_lines',
                'model_size': '1B',
                'success': True,
                'response': result.output,
                'execution_time': execution_time,
                'timestamp': time.time()
            }
        elif result.status == ExecutionStatus.TIMEOUT:
            return {
                'instance_id': instance_id,
                'strategy': 'baseline_first_n_lines',
                'model_size': '1B',
                'success': False,
                'error': 'timeout',
                'execution_time': result.duration,
                'timestamp': time.time()
            }
        else:
            return {
                'instance_id': instance_id,
                'strategy': 'baseline_first_n_lines',
                'model_size': '1B',
                'success': False,
                'error': str(result.error),
                'execution_time': result.duration,
                'timestamp': time.time()
            }
            
    except Exception as e:
        logger.error(f"Exception processing {instance_id}: {e}")
        return {
            'instance_id': instance_id,
            'strategy': 'baseline_first_n_lines',
            'model_size': '1B',
            'success': False,
            'error': str(e),
            'execution_time': time.time() - start_time,
            'timestamp': time.time()
        }

def main():
    """Main entry point for baseline experiment."""
    # Setup logging
    log_level = get_log_level()
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting baseline experiment run")
    logger.info(f"Random seed pinned to {_RANDOM_SEED}")
    
    # Load filtered instances
    try:
        instances = load_filtered_instances()
    except FileNotFoundError as e:
        logger.error(f"Failed to load instances: {e}")
        sys.exit(1)
    
    if not instances:
        logger.warning("No instances to process")
        return
    
    # Initialize ModelRunner (1B model with Q4_K_M quantization)
    try:
        runner = ModelRunner(
            model_name="meta-llama/Llama-3.2-1B",
            quantization="Q4_K_M",
            device="cpu"
        )
        logger.info("ModelRunner initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize ModelRunner: {e}")
        sys.exit(1)
    
    # Initialize BatchExecutor with timeout budget
    batch_executor = BatchExecutor(
        timeout_per_instance=300,  # 5 minutes per instance
        total_timeout=72 * 3600    # 72 hours total
    )
    
    # Process all instances
    output_dir = get_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "intermediate" / "baseline_run.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Writing results to {output_path}")
    
    results = []
    for i, instance in enumerate(instances):
        result = process_instance(instance, runner, batch_executor)
        results.append(result)
        
        # Write incrementally to handle large datasets
        with open(output_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(result) + '\n')
        
        logger.info(f"Progress: {i+1}/{len(instances)} completed")
    
    # Classify failures
    logger.info("Classifying failure modes...")
    annotated_results = []
    for result in results:
        if not result.get('success', True):
            error_log = result.get('error', '')
            failure_category = classify_failure(error_log)
            result['failure_category'] = failure_category
        annotated_results.append(result)
    
    # Write final annotated results
    with open(output_path, 'w', encoding='utf-8') as f:
        for result in annotated_results:
            f.write(json.dumps(result) + '\n')
    
    logger.info(f"Baseline experiment completed. Results written to {output_path}")
    logger.info(f"Total instances processed: {len(annotated_results)}")
    logger.info(f"Success rate: {sum(1 for r in annotated_results if r.get('success')) / len(annotated_results):.2%}")

if __name__ == "__main__":
    main()