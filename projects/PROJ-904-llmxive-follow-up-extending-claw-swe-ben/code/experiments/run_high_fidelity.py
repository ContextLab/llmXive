"""
High-Fidelity execution script for Claw-SWE-Bench.
Executes context compression strategies (TF-IDF, Diff-Aware, Semantic) with scaled models.
Implements explicit random seed pinning (Constitution Principle I).
"""
import os
import sys
import json
import logging
import time
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import random
import numpy as np
import torch

from config import set_global_seeds, get_env_var, get_hf_token, get_model_path, get_data_dir, get_output_dir, get_log_level
from data.loader import ClawSweBenchLoader
from data.context_processors import (
    TFIDFProcessor, 
    DiffAwareProcessor, 
    SemanticSummarizationProcessor,
    NaiveTruncationProcessor
)
from models.runner import ModelRunner
from experiments.batch_executor import BatchExecutor

# --- Explicit Random Seed Pinning (Constitution Principle I) ---
# Even if config.py sets global seeds, we pin them explicitly here
# to ensure reproducibility even if this script is run in isolation
# or if the config is decoupled.
SEED = 42
set_global_seeds(SEED)

# Double-pinning for safety in this specific script context
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)

# Ensure deterministic behavior in CUDA operations
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False
# ----------------------------------------------------------------

def run_strategy(strategy_name, processor, loader, runner, executor, output_file, seed):
    """Helper to run a specific strategy."""
    logger = logging.getLogger(__name__)
    logger.info(f"Starting Strategy: {strategy_name}")
    
    count = 0
    dataset_stream = loader.get_stream()
    
    # Reset file for this strategy if we want separate files, 
    # but task T023 says output hf_run_1b.jsonl. 
    # We will append to the same file but tag with strategy.
    
    for instance in dataset_stream:
        instance_id = instance.get("instance_id", "unknown")
        try:
            context = processor.process(instance)
            result = runner.run(context, instance)
            
            result["instance_id"] = instance_id
            result["strategy"] = strategy_name
            result["model"] = runner.model_name
            result["seed"] = seed
            
            with open(output_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(result) + "\n")
            
            count += 1
            if count % 10 == 0:
                logger.info(f"Strategy {strategy_name}: Processed {count} instances.")
                
        except Exception as e:
            logger.error(f"Strategy {strategy_name} failed for {instance_id}: {e}", exc_info=True)
            error_result = {
                "instance_id": instance_id,
                "status": "failed",
                "error": str(e),
                "strategy": strategy_name,
                "model": runner.model_name,
                "seed": seed
            }
            with open(output_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(error_result) + "\n")
                
    return count

def main():
    logger = logging.getLogger(__name__)
    logger.setLevel(get_log_level())
    
    # Setup logging
    log_dir = Path(get_output_dir()) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "run_high_fidelity.log"
    
    handler = logging.FileHandler(log_file)
    handler.setLevel(get_log_level())
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    console = logging.StreamHandler()
    console.setLevel(get_log_level())
    console.setFormatter(formatter)
    logger.addHandler(console)

    logger.info(f"Starting High-Fidelity Execution with Seed: {SEED}")
    logger.info(f"Data Directory: {get_data_dir()}")
    logger.info(f"Output Directory: {get_output_dir()}")

    try:
        # 1. Initialize Components
        loader = ClawSweBenchLoader()
        
        # Define Strategies
        strategies = {
            "tfidf": TFIDFProcessor(),
            "diff_aware": DiffAwareProcessor(),
            "semantic": SemanticSummarizationProcessor(),
            "naive": NaiveTruncationProcessor() # For comparison
        }
        
        # Load Model (e.g., Llama-3-8B or 1B depending on config)
        # T023 mentions 1B model, T027 mentions 7B. This script is T023 (US2).
        model_path = get_model_path("high_fidelity") 
        runner = ModelRunner(model_path=model_path, quantization="Q4_K_M")
        
        executor = BatchExecutor(
            instance_timeout_minutes=60,
            total_wall_clock_limit_hours=72
        )

        # 2. Output Path
        output_dir = Path(get_output_dir())
        output_dir.mkdir(parents=True, exist_ok=True)
        # T023 Output: data/intermediate/hf_run_1b.jsonl
        output_file = output_dir / "intermediate" / "hf_run_1b.jsonl"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Clear previous run if exists to avoid duplicates in single run
        if output_file.exists():
            output_file.unlink()

        total_processed = 0
        start_time = time.time()

        # 3. Execute Each Strategy
        for name, processor in strategies.items():
            if time.time() - start_time > (72 * 3600):
                logger.warning("Total wall-clock limit reached. Stopping strategies.")
                break
            
            count = run_strategy(
                strategy_name=name,
                processor=processor,
                loader=loader,
                runner=runner,
                executor=executor,
                output_file=output_file,
                seed=SEED
            )
            total_processed += count
            logger.info(f"Completed strategy {name}. Total processed: {total_processed}")

        elapsed = time.time() - start_time
        logger.info(f"High-Fidelity execution complete. Processed {total_processed} total instances across strategies in {elapsed:.2f}s.")

    except Exception as e:
        logger.critical(f"Fatal error in high-fidelity execution: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()