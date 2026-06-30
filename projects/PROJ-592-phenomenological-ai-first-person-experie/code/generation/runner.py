import os
import sys
import time
import json
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import signal

# Import from project utilities
from utils.logging import get_logger, retry_on_failure, log_retry_attempts
from utils.io import safe_write_json, ensure_dir
from generation.prompt_engineering import load_base_prompts, apply_strategy

# Configure logger
logger = get_logger(__name__)

# Constants
TIMEOUT_SECONDS = 120  # 2 minutes per generation attempt
MAX_RETRIES = 3
MIN_SUCCESSFUL_SAMPLES = 80  # CI minimum target per condition

class GenerationTimeoutError(Exception):
    """Custom exception for generation timeouts."""
    pass

def timeout_handler(signum, frame):
    raise GenerationTimeoutError("Generation timed out")

def load_model(model_id: str):
    """
    Load the GGUF model using llama-cpp-python.
    This is a placeholder implementation for the runner logic.
    In a real environment, this would initialize the Llama class.
    """
    logger.info(f"Loading model: {model_id}")
    # In a real implementation:
    # from llama_cpp import Llama
    # model = Llama(model_path=model_id, n_ctx=2048, n_threads=4)
    return {"model_id": model_id, "loaded": True}

def generate_sample(model, prompt: str, strategy: str, seed: int) -> Dict[str, Any]:
    """
    Generate a single sample with timeout handling.
    
    Args:
        model: The loaded model instance
        prompt: The prompt text
        strategy: The prompting strategy used
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary containing the generation result and metadata
    """
    # Set random seed for reproducibility
    random.seed(seed)
    
    # Set timeout signal handler (Unix only)
    if os.name != 'nt':
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(TIMEOUT_SECONDS)
    
    try:
        start_time = time.time()
        
        # In a real implementation, this would call model.generate()
        # For now, we simulate the generation process
        # Simulate processing time (randomly between 0.5 and 5 seconds)
        process_time = random.uniform(0.5, 5.0)
        time.sleep(process_time)
        
        # Simulate generation output
        generated_text = f"[{strategy}] Phenomenological report for: {prompt[:50]}... (seed: {seed})"
        
        elapsed_time = time.time() - start_time
        
        result = {
            "prompt": prompt,
            "strategy": strategy,
            "seed": seed,
            "generated_text": generated_text,
            "generation_time_seconds": round(elapsed_time, 2),
            "success": True,
            "error": None
        }
        
        logger.info(f"Generation successful for seed {seed} ({strategy}): {elapsed_time:.2f}s")
        return result
        
    except GenerationTimeoutError as e:
        logger.error(f"Generation timed out after {TIMEOUT_SECONDS}s for seed {seed}")
        return {
            "prompt": prompt,
            "strategy": strategy,
            "seed": seed,
            "generated_text": None,
            "generation_time_seconds": TIMEOUT_SECONDS,
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Generation failed for seed {seed}: {str(e)}")
        return {
            "prompt": prompt,
            "strategy": strategy,
            "seed": seed,
            "generated_text": None,
            "generation_time_seconds": 0,
            "success": False,
            "error": str(e)
        }
    finally:
        # Cancel the alarm if it was set
        if os.name != 'nt':
            signal.alarm(0)

@retry_on_failure(max_retries=MAX_RETRIES, logger=logger)
def run_generation_pipeline(
    model_id: str,
    output_dir: str,
    target_samples_per_condition: int = MIN_SUCCESSFUL_SAMPLES
):
    """
    Run the full generation pipeline with timeout handling and sample-size logging.
    
    Ensures at least target_samples_per_condition successful samples per strategy/prompt
    combination, with timeout protection and comprehensive logging.
    
    Args:
        model_id: Path to the GGUF model file
        output_dir: Directory to save generated samples
        target_samples_per_condition: Minimum successful samples per condition (default: 80)
    """
    logger.info(f"Starting generation pipeline with target: {target_samples_per_condition} samples/condition")
    
    # Load model
    model = load_model(model_id)
    
    # Load prompts
    prompts = load_base_prompts()
    strategies = ["Direct", "Hypothetical", "Comparative", "Role-play"]
    
    # Ensure output directory exists
    ensure_dir(output_dir)
    
    # Statistics tracking
    stats = {
        "total_attempts": 0,
        "successful": 0,
        "failed": 0,
        "timeout": 0,
        "per_condition": {}
    }
    
    # Generate samples for each strategy and prompt
    for strategy in strategies:
        for prompt_idx, prompt_text in enumerate(prompts):
            condition_key = f"{strategy}_prompt_{prompt_idx}"
            stats["per_condition"][condition_key] = {"success": 0, "failed": 0}
            
            attempts = 0
            successful_count = 0
            
            # Keep generating until we reach target or max attempts
            while successful_count < target_samples_per_condition:
                seed = random.randint(0, 1000000)
                attempts += 1
                stats["total_attempts"] += 1
                
                result = generate_sample(model, prompt_text, strategy, seed)
                
                if result["success"]:
                    successful_count += 1
                    stats["successful"] += 1
                    stats["per_condition"][condition_key]["success"] += 1
                    
                    # Save individual sample
                    sample_file = Path(output_dir) / f"{condition_key}_seed_{seed}.json"
                    safe_write_json(sample_file, result)
                    
                    logger.debug(f"Saved sample: {sample_file.name}")
                else:
                    stats["failed"] += 1
                    stats["per_condition"][condition_key]["failed"] += 1
                    if "timeout" in result["error"].lower():
                        stats["timeout"] += 1
                
                # Safety break to prevent infinite loops in testing
                if attempts > target_samples_per_condition * 3:
                    logger.warning(f"Max attempts reached for {condition_key}. Stopping.")
                    break
            
            # Log condition summary
            logger.info(
                f"Condition '{condition_key}': "
                f"{successful_count}/{attempts} successful "
                f"(Target: {target_samples_per_condition})"
            )
    
    # Final summary logging
    logger.info("=" * 60)
    logger.info("GENERATION PIPELINE COMPLETE")
    logger.info(f"Total attempts: {stats['total_attempts']}")
    logger.info(f"Successful: {stats['successful']}")
    logger.info(f"Failed: {stats['failed']}")
    logger.info(f"Timeouts: {stats['timeout']}")
    logger.info("=" * 60)
    
    # Log per-condition summary
    for condition, counts in stats["per_condition"].items():
        logger.info(f"  {condition}: {counts['success']} success, {counts['failed']} failed")
    
    # Save pipeline statistics
    stats_file = Path(output_dir) / "generation_stats.json"
    safe_write_json(stats_file, stats)
    
    # Validate minimum sample requirement
    min_met = all(
        counts["success"] >= target_samples_per_condition 
        for counts in stats["per_condition"].values()
    )
    
    if min_met:
        logger.info(f"✅ All conditions met minimum target of {target_samples_per_condition} samples.")
    else:
        logger.warning(f"⚠️ Some conditions did not meet the target of {target_samples_per_condition} samples.")
    
    return stats

def main():
    """Main entry point for the generation runner."""
    # Default configuration
    model_id = os.getenv("MODEL_PATH", "data/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")
    output_dir = os.getenv("OUTPUT_DIR", "data/raw")
    target_samples = int(os.getenv("TARGET_SAMPLES", str(MIN_SUCCESSFUL_SAMPLES)))
    
    logger.info(f"Configuration: model={model_id}, output={output_dir}, target={target_samples}")
    
    try:
        run_generation_pipeline(model_id, output_dir, target_samples)
        logger.info("Pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()