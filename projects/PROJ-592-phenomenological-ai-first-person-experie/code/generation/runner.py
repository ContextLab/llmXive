"""
Phenomenological AI Generation Runner (CPU-Only).

Implements the primary generation pipeline for User Story 1.
Uses TinyLlama-1.1B-GGUF via llama-cpp-python on CPU.
Includes timeout handling and sample-size logging to ensure >=80 successful samples per condition.
"""
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

# Local imports
from config import get_config, get_marker_list
from utils.logging import get_logger, log_operation, retry_on_failure
from utils.io import safe_write_json, archive_artifact
from generation.prompt_engineering import load_base_prompts, apply_strategy

# Configure logging
logger = get_logger("generation_runner")

class GenerationTimeoutError(Exception):
    """Raised when generation exceeds the configured timeout."""
    pass

def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise GenerationTimeoutError("Generation timed out")

def load_model(config: Dict[str, Any]) -> Any:
    """
    Load the TinyLlama model using llama-cpp-python.
    Configures for CPU-only execution.
    """
    try:
        from llama_cpp import Llama
        
        model_path = config.get("model_path")
        if not model_path or not os.path.exists(model_path):
            # Fallback to expected GGUF path if not specified
            base_dir = Path(__file__).parent.parent.parent
            model_path = str(base_dir / "data" / "models" / "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model not found at {model_path}")
        
        logger.log("model_load", path=model_path, type="tinyllama")
        
        model = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_threads=config.get("n_threads", 4),
            n_batch=512,
            use_mmap=True,
            use_mlock=False,
            verbose=False  # Suppress llama.cpp verbose output
        )
        return model
    except ImportError:
        logger.log("model_load_error", error="llama_cpp not installed")
        raise
    except Exception as e:
        logger.log("model_load_error", error=str(e))
        raise

@retry_on_failure(max_attempts=3, delay=2.0, logger=logger)
def generate_sample(
    model: Any,
    prompt: str,
    strategy: str,
    config: Dict[str, Any],
    seed: int,
    timeout_seconds: int = 120
) -> Dict[str, Any]:
    """
    Generate a single phenomenological sample with timeout handling.
    
    Args:
        model: Loaded LLM instance
        prompt: The base prompt text
        strategy: Prompting strategy used
        config: Configuration dictionary
        seed: Random seed for reproducibility
        timeout_seconds: Maximum time allowed for generation
    
    Returns:
        Dictionary containing generation results and metadata
    """
    # Set timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    
    try:
        # Set seed for reproducibility
        random.seed(seed)
        if hasattr(model, 'seed'):
            model.seed = seed
        
        # Apply strategy-specific parameters if needed
        generation_params = {
            "max_tokens": config.get("max_tokens", 512),
            "temperature": config.get("temperature", 0.7),
            "top_p": config.get("top_p", 0.9),
            "stop": ["\n\n", "###"],
            "seed": seed
        }
        
        # Generate text
        start_time = time.time()
        output = model(
            prompt,
            **generation_params
        )
        elapsed_time = time.time() - start_time
        
        # Cancel alarm
        signal.alarm(0)
        
        # Extract generated text
        generated_text = output.get("choices", [{}])[0].get("text", "").strip()
        
        return {
            "success": True,
            "text": generated_text,
            "strategy": strategy,
            "prompt": prompt,
            "seed": seed,
            "elapsed_time": elapsed_time,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except GenerationTimeoutError as e:
        signal.alarm(0)
        logger.log("generation_timeout", strategy=strategy, prompt_len=len(prompt))
        return {
            "success": False,
            "error": "timeout",
            "strategy": strategy,
            "seed": seed,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        signal.alarm(0)
        logger.log("generation_error", strategy=strategy, error=str(e))
        return {
            "success": False,
            "error": str(e),
            "strategy": strategy,
            "seed": seed,
            "timestamp": datetime.utcnow().isoformat()
        }

def run_generation_pipeline(
    config_path: str,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the full generation pipeline with timeout handling and sample-size logging.
    
    Ensures >=80 successful samples per condition (prompt x strategy combination).
    
    Args:
        config_path: Path to configuration file
        output_dir: Optional output directory override
    
    Returns:
        Summary statistics of the generation run
    """
    config = get_config(config_path)
    output_dir = output_dir or config.get("output_dir", "data/raw")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    logger.log("pipeline_start", config_path=config_path, output_dir=str(output_path))
    
    # Load base prompts
    prompts = load_base_prompts(config.get("prompts_path", "data/prompts/base_prompts.json"))
    strategies = ["direct", "hypothetical", "comparative", "roleplay"]
    
    # Configuration for sample generation
    samples_per_condition = config.get("samples_per_condition", 80)
    timeout_seconds = config.get("timeout_seconds", 120)
    
    # Load model
    model = load_model(config)
    
    # Track results
    all_results = []
    condition_stats = {}
    
    total_attempts = 0
    successful_samples = 0
    failed_samples = 0
    
    for strategy in strategies:
        for prompt_idx, prompt_text in enumerate(prompts):
            condition_key = f"{strategy}_prompt_{prompt_idx}"
            condition_stats[condition_key] = {"success": 0, "failed": 0}
            
            attempts = 0
            while condition_stats[condition_key]["success"] < samples_per_condition:
                attempts += 1
                total_attempts += 1
                
                # Generate unique seed for this attempt
                seed = random.randint(1, 1000000)
                
                result = generate_sample(
                    model=model,
                    prompt=prompt_text,
                    strategy=strategy,
                    config=config,
                    seed=seed,
                    timeout_seconds=timeout_seconds
                )
                
                if result.get("success", False):
                    condition_stats[condition_key]["success"] += 1
                    successful_samples += 1
                    all_results.append(result)
                    
                    # Log progress every 10 samples
                    if condition_stats[condition_key]["success"] % 10 == 0:
                        logger.log(
                            "sample_progress",
                            condition=condition_key,
                            current=condition_stats[condition_key]["success"],
                            target=samples_per_condition
                        )
                else:
                    condition_stats[condition_key]["failed"] += 1
                    failed_samples += 1
                    
                    # Log failure
                    logger.log(
                        "sample_failed",
                        condition=condition_key,
                        error=result.get("error", "unknown"),
                        attempt=attempts
                    )
                
                # Safety break after too many failures
                if attempts > samples_per_condition * 3:
                    logger.log(
                        "condition_aborted",
                        condition=condition_key,
                        reason="excessive_failures",
                        success=condition_stats[condition_key]["success"],
                        target=samples_per_condition
                    )
                    break
    
    # Final logging of sample sizes
    logger.log(
        "pipeline_complete",
        total_attempts=total_attempts,
        successful_samples=successful_samples,
        failed_samples=failed_samples,
        condition_stats=condition_stats
    )
    
    # Verify minimum sample size requirement
    min_met = all(
        stats["success"] >= samples_per_condition 
        for stats in condition_stats.values()
    )
    
    if not min_met:
        logger.log(
            "warning",
            message="Minimum sample size (80) not met for all conditions",
            condition_stats=condition_stats
        )
    
    # Save results
    output_file = output_path / "phenomenological_reports.json"
    safe_write_json(output_file, all_results)
    
    # Save summary stats
    summary = {
        "total_attempts": total_attempts,
        "successful_samples": successful_samples,
        "failed_samples": failed_samples,
        "condition_stats": condition_stats,
        "min_sample_size_met": min_met,
        "timestamp": datetime.utcnow().isoformat()
    }
    summary_file = output_path / "generation_summary.json"
    safe_write_json(summary_file, summary)
    
    # Archive artifacts
    archive_artifact(
        artifacts=[output_file, summary_file],
        archive_path=output_path / "generation_archive.tar.gz"
    )
    
    return summary

def main():
    """CLI entry point for the generation runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Phenomenological AI Generation Runner")
    parser.add_argument(
        "--config",
        type=str,
        default="code/config.py",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Override output directory"
    )
    
    args = parser.parse_args()
    
    try:
        summary = run_generation_pipeline(
            config_path=args.config,
            output_dir=args.output_dir
        )
        
        print(json.dumps(summary, indent=2))
        logger.log("main_success", summary=summary)
        
    except Exception as e:
        logger.log("main_error", error=str(e))
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
