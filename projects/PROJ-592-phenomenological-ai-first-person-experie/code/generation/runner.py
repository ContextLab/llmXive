"""
Phenomenological Report Generation Runner.

Implements the generation pipeline using TinyLlama-1.1B-Chat-v1.0-GGUF on CPU.
Includes robust retry logic as per FR-001.
"""
from __future__ import annotations

import json
import logging
import os
import random
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from llama_cpp import Llama

from config import get_config
from utils.logging import get_logger, log_operation, retry_on_failure
from utils.io import safe_write_json, safe_write_csv

# Constants
MAX_ATTEMPTS_PER_SAMPLE = 3
TIMEOUT_SECONDS = 300  # 5 minutes per generation
MODEL_ID = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
MODEL_FILE = "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"

class GenerationError(Exception):
    """Base exception for generation failures."""
    pass

class GenerationTimeoutError(GenerationError):
    """Raised when generation exceeds timeout."""
    pass

def setup_logger() -> logging.Logger:
    """Configure the module logger."""
    logger = logging.getLogger("generation.runner")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

logger = setup_logger()

@retry_on_failure(max_attempts=MAX_ATTEMPTS_PER_SAMPLE, delay=2.0, logger=logger)
def load_model(model_path: str) -> Llama:
    """
    Load the GGUF model with retry logic.
    
    Args:
        model_path: Path to the GGUF file.
        
    Returns:
        Loaded Llama instance.
        
    Raises:
        GenerationError: If model loading fails after retries.
    """
    log_operation("load_model_attempt", path=model_path)
    try:
        llm = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_threads=4,
            n_batch=512,
            use_mmap=True,
            verbose=False
        )
        log_operation("model_loaded_successfully", path=model_path)
        return llm
    except Exception as e:
        log_operation("model_load_failed", error=str(e), path=model_path)
        raise GenerationError(f"Failed to load model: {e}") from e

@retry_on_failure(max_attempts=MAX_ATTEMPTS_PER_SAMPLE, delay=2.0, logger=logger)
def generate_sample(
    llm: Llama,
    prompt: str,
    strategy: str,
    seed: int,
    max_tokens: int = 512
) -> Dict[str, Any]:
    """
    Generate a single sample with retry logic.
    
    Args:
        llm: Loaded Llama instance.
        prompt: The prompt text.
        strategy: The prompting strategy used.
        seed: Random seed for reproducibility.
        max_tokens: Maximum tokens to generate.
        
    Returns:
        Dictionary containing the generation result and metadata.
        
    Raises:
        GenerationTimeoutError: If generation times out.
        GenerationError: If generation fails after retries.
    """
    log_operation(
        "generate_sample_attempt",
        strategy=strategy,
        seed=seed,
        prompt_length=len(prompt)
    )
    
    random.seed(seed)
    generation_kwargs = {
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": 0.7,
        "top_p": 0.9,
        "seed": seed,
        "stop": ["\n\n", "User:", "Human:"]
    }
    
    try:
        start_time = time.time()
        output = llm(**generation_kwargs)
        elapsed = time.time() - start_time
        
        result = {
            "prompt": prompt,
            "generated_text": output["choices"][0]["text"],
            "strategy": strategy,
            "seed": seed,
            "model_id": MODEL_ID,
            "generation_time": elapsed,
            "tokens_generated": len(output["usage"]["completion_tokens"]) if "usage" in output else 0,
            "status": "success"
        }
        
        log_operation(
            "generation_complete",
            strategy=strategy,
            seed=seed,
            tokens=result["tokens_generated"],
            elapsed=elapsed
        )
        return result
        
    except Exception as e:
        log_operation(
            "generation_failed",
            strategy=strategy,
            seed=seed,
            error=str(e)
        )
        raise GenerationError(f"Generation failed: {e}") from e

def run_generation_pipeline(config: Dict[str, Any]) -> None:
    """
    Execute the full generation pipeline with retry logic and missing sample handling.
    
    Args:
        config: Configuration dictionary containing paths, seeds, and model info.
    """
    log_operation("run_generation_phase", config_path=str(config.get("config_path", "")))
    
    # Extract configuration
    model_path = config.get("model_path")
    if not model_path:
        raise KeyError("model_path")
        
    output_dir = Path(config.get("output_dir", "data/raw"))
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load prompts
    prompts_file = Path(config.get("prompts_file", "data/prompts/base_prompts.json"))
    if not prompts_file.exists():
        raise FileNotFoundError(f"Prompts file not found: {prompts_file}")
        
    with open(prompts_file, "r", encoding="utf-8") as f:
        base_prompts = json.load(f)
        
    strategies = ["Direct", "Hypothetical", "Comparative", "Role-play"]
    samples_per_prompt_per_strategy = int(config.get("samples_per_prompt_per_strategy", 80))
    
    all_results = []
    missing_samples = []
    
    # Initialize model
    try:
        llm = load_model(model_path)
    except GenerationError as e:
        log_operation("pipeline_failed", error=str(e))
        raise
    
    try:
        for prompt_entry in base_prompts:
            prompt_id = prompt_entry.get("id", "unknown")
            prompt_text = prompt_entry.get("prompt", "")
            
            for strategy in strategies:
                for i in range(samples_per_prompt_per_strategy):
                    seed = random.randint(0, 2**32 - 1)
                    sample_key = f"{prompt_id}_{strategy}_{i}"
                    
                    success = False
                    attempt_count = 0
                    last_error = None
                    
                    # Retry loop with fixed attempts
                    while attempt_count < MAX_ATTEMPTS_PER_SAMPLE and not success:
                        attempt_count += 1
                        try:
                            result = generate_sample(
                                llm=llm,
                                prompt=prompt_text,
                                strategy=strategy,
                                seed=seed
                            )
                            result["sample_key"] = sample_key
                            result["attempt_count"] = attempt_count
                            all_results.append(result)
                            success = True
                            log_operation(
                                "sample_saved",
                                sample_key=sample_key,
                                attempts=attempt_count
                            )
                        except GenerationError as e:
                            last_error = str(e)
                            log_operation(
                                "retry_attempt",
                                sample_key=sample_key,
                                attempt=attempt_count,
                                max_attempts=MAX_ATTEMPTS_PER_SAMPLE,
                                error=last_error
                            )
                    
                    if not success:
                        missing_entry = {
                            "sample_key": sample_key,
                            "prompt_id": prompt_id,
                            "strategy": strategy,
                            "seed": seed,
                            "max_attempts": MAX_ATTEMPTS_PER_SAMPLE,
                            "final_error": last_error,
                            "status": "missing"
                        }
                        missing_samples.append(missing_entry)
                        log_operation(
                            "sample_marked_missing",
                            sample_key=sample_key,
                            reason=last_error
                        )
        
        # Save results
        results_file = output_dir / "generated_reports.json"
        safe_write_json(results_file, all_results)
        log_operation("results_saved", path=str(results_file), count=len(all_results))
        
        # Save missing samples log
        missing_file = output_dir / "missing_samples.json"
        safe_write_json(missing_file, missing_samples)
        log_operation("missing_samples_saved", path=str(missing_file), count=len(missing_samples))
        
        # Summary stats
        total_requested = len(base_prompts) * len(strategies) * samples_per_prompt_per_strategy
        success_rate = len(all_results) / total_requested if total_requested > 0 else 0
        
        log_operation(
            "generation_summary",
            total_requested=total_requested,
            successful=len(all_results),
            missing=len(missing_samples),
            success_rate=success_rate
        )
        
    finally:
        # Cleanup model
        del llm
        log_operation("model_unloaded")

def main() -> None:
    """Entry point for the generation runner."""
    config_path = os.environ.get("CONFIG_PATH", "code/config.py")
    config = get_config(config_path)
    run_generation_pipeline(config)

if __name__ == "__main__":
    main()