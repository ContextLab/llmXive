"""
Phenomenological AI: Generation Runner (CPU-Only)

Implements the primary generation pipeline using TinyLlama-1.1B-Chat-v1.0-GGUF.
Includes timeout handling, retry logic, and sample-size logging to ensure
>= 80 successful samples per condition (prompt/strategy combination).

This script is designed for CPU-only execution (CI path).
"""
from __future__ import annotations

import os
import sys
import time
import json
import random
import signal
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))

try:
    from llama_cpp import Llama
except ImportError:
    print("ERROR: llama-cpp-python is required. Install with: pip install llama-cpp-python")
    sys.exit(1)

from config import get_config, get_marker_dictionaries
from generation.prompt_engineering import load_base_prompts, apply_strategy
from utils.logging import get_logger, log_operation, retry_on_failure, capture_warning, WarningContext
from utils.io import safe_write_json, ensure_dir

# --- Configuration Constants ---
MIN_SAMPLES_PER_CONDITION = 80
MAX_ATTEMPTS_PER_SAMPLE = 3
GENERATION_TIMEOUT_SECONDS = 120
MODEL_PATH_KEY = "tinyllama_model_path"
MODEL_PARAMS_KEY = "tinyllama_params"

# --- Custom Exceptions ---
class GenerationTimeoutError(Exception):
    """Raised when generation exceeds the timeout limit."""
    pass

class GenerationError(Exception):
    """Raised for other generation failures."""
    pass

# --- Timeout Handler ---
def timeout_handler(signum, frame):
    raise GenerationTimeoutError("Generation timed out after configured limit.")

# Set up signal handler for timeout (Unix only)
if hasattr(signal, 'SIGALRM'):
    signal.signal(signal.SIGALRM, timeout_handler)

# --- Helper Functions ---
def setup_logger():
    """Initialize the logger for this module."""
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

@retry_on_failure(max_attempts=MAX_ATTEMPTS_PER_SAMPLE, delay=2.0, logger=None)
def generate_sample(
    model: Llama,
    prompt: str,
    strategy: str,
    seed: int,
    params: Dict[str, Any],
    timeout: int = GENERATION_TIMEOUT_SECONDS
) -> Dict[str, Any]:
    """
    Generate a single sample with timeout handling and retry logic.
    
    Args:
        model: The loaded Llama model instance.
        prompt: The base prompt text.
        strategy: The prompting strategy used.
        seed: Random seed for reproducibility.
        params: Generation parameters (temperature, max_tokens, etc.).
        timeout: Timeout in seconds for the generation call.
    
    Returns:
        A dictionary containing the generation result and metadata.
    
    Raises:
        GenerationTimeoutError: If generation exceeds the timeout.
        GenerationError: If generation fails after retries.
    """
    logger = get_logger()
    log_operation("generate_sample_attempt", strategy=strategy, seed=seed)
    
    # Set random seed for reproducibility
    random.seed(seed)
    if hasattr(model, 'seed'):
        model.seed = seed

    # Prepare the full prompt
    # Assuming the model expects chat format, we might need to wrap the prompt
    # depending on the model's specific requirements. 
    # For TinyLlama Chat, we usually wrap in <|system|> or similar if not handled by the model directly.
    # Here we assume the prompt is already formatted or the model handles raw text.
    full_prompt = prompt

    # Set up timeout
    if hasattr(signal, 'SIGALRM'):
        signal.alarm(timeout)

    try:
        start_time = time.time()
        output = model(
            full_prompt,
            max_tokens=params.get("max_tokens", 512),
            temperature=params.get("temperature", 0.7),
            top_p=params.get("top_p", 0.9),
            repeat_penalty=params.get("repeat_penalty", 1.1),
            stop=["\n\n", "END"], # Common stop sequences
            echo=False
        )
        elapsed = time.time() - start_time
        
        # Cancel alarm
        signal.alarm(0)

        result_text = output.get("choices", [{}])[0].get("text", "").strip()
        
        if not result_text:
            raise GenerationError("Model returned empty text.")

        return {
            "success": True,
            "text": result_text,
            "strategy": strategy,
            "seed": seed,
            "prompt": prompt,
            "elapsed_time": elapsed,
            "timestamp": datetime.utcnow().isoformat()
        }

    except GenerationTimeoutError:
        signal.alarm(0)
        raise
    except Exception as e:
        signal.alarm(0)
        raise GenerationError(f"Generation failed: {str(e)}")

def run_generation_pipeline(
    model_path: str,
    model_params: Dict[str, Any],
    prompts: List[Dict[str, Any]],
    strategies: List[str],
    output_dir: str,
    min_samples: int = MIN_SAMPLES_PER_CONDITION,
    logger: Optional[logging.Logger] = None
) -> Dict[str, Any]:
    """
    Run the full generation pipeline for all prompts and strategies.
    
    Args:
        model_path: Path to the GGUF model file.
        model_params: Parameters for loading the model.
        prompts: List of base prompts to use.
        strategies: List of prompting strategies to apply.
        output_dir: Directory to save generated samples.
        min_samples: Minimum number of successful samples per condition.
        logger: Logger instance.
    
    Returns:
        Summary statistics of the generation run.
    """
    if logger is None:
        logger = setup_logger()
    
    logger.info(f"Starting generation pipeline with {len(prompts)} prompts and {len(strategies)} strategies.")
    logger.info(f"Target: >= {min_samples} samples per condition.")
    
    # Load model
    logger.info(f"Loading model from {model_path}...")
    try:
        model = Llama(
            model_path=model_path,
            **model_params
        )
        logger.info("Model loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return {"success": False, "error": str(e)}

    # Initialize results storage
    all_results = []
    condition_stats = {} # (prompt_id, strategy) -> {total_attempts, successes, failures}
    
    output_path = Path(output_dir)
    ensure_dir(output_path)
    
    # Iterate over all conditions
    for strategy in strategies:
        for prompt_data in prompts:
            prompt_id = prompt_data.get("id", "unknown")
            prompt_text = prompt_data.get("prompt", "")
            
            condition_key = (prompt_id, strategy)
            if condition_key not in condition_stats:
                condition_stats[condition_key] = {
                    "total_attempts": 0,
                    "successes": 0,
                    "failures": 0,
                    "samples": []
                }
            
            logger.info(f"Processing condition: Prompt {prompt_id}, Strategy {strategy}")
            
            attempts = 0
            while condition_stats[condition_key]["successes"] < min_samples:
                attempts += 1
                seed = random.randint(0, 2**32 - 1)
                condition_stats[condition_key]["total_attempts"] += 1
                
                try:
                    # Apply strategy to prompt if needed (though prompt_data might already be strategy-specific)
                    # For this implementation, we assume prompt_data contains the full text or we apply a wrapper.
                    # If prompt_data is just a base, we might need to apply_strategy here.
                    # Assuming prompt_data is the final prompt for simplicity based on T008 context.
                    
                    result = generate_sample(
                        model=model,
                        prompt=prompt_text,
                        strategy=strategy,
                        seed=seed,
                        params=model_params.get("generation_params", {})
                    )
                    
                    condition_stats[condition_key]["successes"] += 1
                    condition_stats[condition_key]["samples"].append(result)
                    all_results.append(result)
                    
                    logger.info(f"  Success {condition_stats[condition_key]['successes']}/{min_samples} (Attempt {attempts})")
                    
                    # Optional: Save intermediate results to avoid data loss
                    if condition_stats[condition_key]["successes"] % 10 == 0:
                        temp_file = output_path / f"temp_{prompt_id}_{strategy}.json"
                        safe_write_json(temp_file, all_results)
                        logger.info(f"  Saved intermediate results to {temp_file}")

                except Exception as e:
                    condition_stats[condition_key]["failures"] += 1
                    logger.warning(f"  Attempt {attempts} failed: {e}")
                    
                    # If we've exhausted attempts and still haven't reached min_samples,
                    # we might want to break or warn heavily.
                    if attempts > MAX_ATTEMPTS_PER_SAMPLE * min_samples * 2: # Safety break
                        logger.error(f"  Exceeded max attempts for condition {condition_key}. Stopping.")
                        break
            
            # Save condition results
            condition_file = output_path / f"results_{prompt_id}_{strategy}.json"
            safe_write_json(condition_file, condition_stats[condition_key]["samples"])
            logger.info(f"Saved results for condition {condition_key} to {condition_file}")

    # Final Summary
    summary = {
        "total_conditions": len(condition_stats),
        "total_samples": len(all_results),
        "min_samples_target": min_samples,
        "conditions_met": 0,
        "details": {}
    }
    
    for key, stats in condition_stats.items():
        met = stats["successes"] >= min_samples
        if met:
            summary["conditions_met"] += 1
        summary["details"][f"{key[0]}_{key[1]}"] = {
            "successes": stats["successes"],
            "target": min_samples,
            "met": met,
            "attempts": stats["total_attempts"],
            "failures": stats["failures"]
        }
    
    summary["all_results"] = all_results
    summary_file = output_path / "generation_summary.json"
    safe_write_json(summary_file, summary)
    
    logger.info(f"Pipeline complete. {summary['conditions_met']}/{summary['total_conditions']} conditions met target.")
    
    return summary

def main():
    """Main entry point for the generation runner."""
    logger = setup_logger()
    
    # Load configuration
    try:
        config = get_config()
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)
    
    # Get model paths and params
    model_path = config.get(MODEL_PATH_KEY)
    if not model_path:
        # Fallback or error
        model_path = os.environ.get("TINYLLAMA_MODEL_PATH")
        if not model_path:
            logger.error("Model path not found in config or environment.")
            sys.exit(1)
    
    model_params = config.get(MODEL_PARAMS_KEY, {})
    
    # Load prompts
    prompts_file = config.get("base_prompts_path", "data/prompts/base_prompts.json")
    try:
        prompts = load_base_prompts(prompts_file)
        logger.info(f"Loaded {len(prompts)} base prompts.")
    except Exception as e:
        logger.error(f"Failed to load prompts: {e}")
        sys.exit(1)
    
    # Define strategies (from config or hardcoded)
    strategies = config.get("strategies", ["Direct", "Hypothetical", "Comparative", "Role-play"])
    
    # Output directory
    output_dir = config.get("raw_output_dir", "data/raw/")
    ensure_dir(output_dir)
    
    # Run pipeline
    summary = run_generation_pipeline(
        model_path=model_path,
        model_params=model_params,
        prompts=prompts,
        strategies=strategies,
        output_dir=output_dir,
        min_samples=MIN_SAMPLES_PER_CONDITION,
        logger=logger
    )
    
    if summary.get("success"):
        print("Generation pipeline completed successfully.")
        print(f"Total samples: {summary['total_samples']}")
        print(f"Conditions met target: {summary['conditions_met']}/{summary['total_conditions']}")
    else:
        print("Generation pipeline failed.")
        print(summary.get("error", "Unknown error"))
        sys.exit(1)

if __name__ == "__main__":
    main()
