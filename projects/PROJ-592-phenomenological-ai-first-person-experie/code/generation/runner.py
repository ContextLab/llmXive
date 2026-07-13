"""
Generation runner for Phenomenological AI pipeline.

Implements T009 and T010:
- T009: Generates samples using TinyLlama-1.1B-Chat-v1.0 (GGUF) on CPU.
- T010: Implements retry logic for failed samples.
- T013: Adds timeout handling and sample-size logging.
"""
from __future__ import annotations

import json
import logging
import os
import random
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from llama_cpp import Llama

from utils.logging import log_operation, get_logger, retry_on_failure
from generation.timeout_monitor import (
    SampleCounter,
    TimeoutContext,
    log_sample_status,
    save_summary,
    enforce_minimum_samples,
    GenerationTimeoutError,
    run_with_timeout
)
from generation.prompt_engineering import load_base_prompts, apply_strategy
from config import get_config

logger = get_logger(__name__)

MAX_ATTEMPTS_PER_SAMPLE = 5
GENERATION_TIMEOUT = 120  # seconds

# Model constraint: Only TinyLlama for CI
MODEL_ID = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
MODEL_FILE = "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"


class GenerationError(Exception):
    """Raised when generation fails after all retries."""
    pass


class GenerationTimeoutError(Exception):
    """Raised when generation times out."""
    pass


def setup_logger() -> logging.Logger:
    """Configures the logger for the generation phase."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger("generation_runner")


@retry_on_failure(max_attempts=MAX_ATTEMPTS_PER_SAMPLE, delay=2.0, logger=logger)
def generate_sample(
    model: Llama,
    prompt: str,
    seed: int,
    strategy: str,
    prompt_id: str,
    temperature: float = 0.7
) -> Dict[str, Any]:
    """
    Generates a single sample with timeout and retry logic.

    Args:
        model: Loaded Llama model.
        prompt: The full prompt text.
        seed: Random seed for reproducibility.
        strategy: The prompting strategy used.
        prompt_id: Unique ID for the prompt.
        temperature: Sampling temperature.

    Returns:
        Dictionary containing the generated text and metadata.
    """
    random.seed(seed)
    start_time = time.time()
    success = False
    result_text = ""
    error_msg = None

    try:
        with TimeoutContext(timeout_seconds=GENERATION_TIMEOUT):
            output = model(
                prompt,
                max_tokens=512,
                temperature=temperature,
                stop=["</s>", "User:"],
                echo=False
            )
            result_text = output['choices'][0]['text']
            success = True
    except GenerationTimeoutError as e:
        error_msg = str(e)
        logger.warning(f"Timeout for {prompt_id}: {error_msg}")
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Generation error for {prompt_id}: {error_msg}")

    duration = time.time() - start_time
    log_sample_status(strategy, prompt_id, 1, success, duration, error_msg)

    if not success:
        raise GenerationError(f"Failed to generate sample: {error_msg}")

    return {
        "text": result_text.strip(),
        "metadata": {
            "strategy": strategy,
            "prompt_id": prompt_id,
            "seed": seed,
            "model": MODEL_FILE,
            "timestamp": time.time(),
            "duration": duration
        }
    }


def load_model(config: Dict[str, Any]) -> Llama:
    """
    Loads the TinyLlama model from GGUF.

    Args:
        config: Configuration dictionary.

    Returns:
        Loaded Llama model instance.
    """
    model_path = config.get("model_path")
    if not model_path:
        # Fallback to default path if not in config
        model_path = Path("models") / MODEL_FILE
        if not model_path.exists():
            raise FileNotFoundError(
                f"Model not found at {model_path}. "
                f"Please download {MODEL_FILE} or set model_path in config."
            )

    logger.info(f"Loading model from {model_path}")
    try:
        model = Llama(
            model_path=str(model_path),
            n_ctx=2048,
            n_threads=4,  # CPU-optimized
            verbose=False
        )
        logger.info("Model loaded successfully")
        return model
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise


def run_generation_pipeline(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Orchestrates the full generation pipeline.

    Args:
        config: Configuration dictionary.

    Returns:
        List of generated samples.
    """
    log_operation("run_generation_phase", config_path=str(config.get("config_path", "N/A")))

    # Initialize counters for each strategy
    strategies = ["direct", "hypothetical", "comparative", "role-play"]
    counters = {s: SampleCounter(condition=s, target_count=80) for s in strategies}

    # Load prompts
    prompts_path = Path(config.get("prompts_path", "data/prompts/base_prompts.json"))
    base_prompts = load_base_prompts(prompts_path)

    # Load model
    model = load_model(config)

    all_samples = []
    total_prompts = len(base_prompts)
    target_per_prompt = 2  # 2 samples per prompt per strategy = 80 total for 20 prompts

    for strategy in strategies:
        logger.info(f"Starting generation for strategy: {strategy}")
        condition_counter = counters[strategy]

        for prompt_id, prompt_text in base_prompts.items():
            if condition_counter.is_complete():
                logger.info(f"Target reached for {strategy}, skipping remaining prompts.")
                break

            # Generate multiple attempts per prompt to ensure target
            for attempt_idx in range(target_per_prompt):
                if condition_counter.is_complete():
                    break

                seed = random.randint(0, 2**31 - 1)
                full_prompt = apply_strategy(strategy, prompt_text)

                try:
                    sample = generate_sample(
                        model=model,
                        prompt=full_prompt,
                        seed=seed,
                        strategy=strategy,
                        prompt_id=prompt_id,
                        temperature=0.7
                    )
                    all_samples.append(sample)
                    condition_counter.record_attempt(True)
                except (GenerationError, Exception) as e:
                    condition_counter.record_attempt(False)
                    logger.warning(f"Failed attempt {attempt_idx+1} for {prompt_id} ({strategy}): {e}")

        logger.info(f"Completed {strategy}: {condition_counter.successes}/{condition_counter.target_count} samples")

    # Save summary
    summary_path = Path("data/processed/generation_summary.json")
    save_summary(list(counters.values()), summary_path)

    # Check minimums
    if not enforce_minimum_samples(list(counters.values()), min_samples=80):
        logger.warning("Not all conditions met the 80-sample minimum.")

    log_operation("generation_complete", total_samples=len(all_samples))
    return all_samples


def main():
    """Entry point for the generation pipeline."""
    config_path = os.getenv("CONFIG_PATH", "code/config.py")
    config = get_config(config_path)
    config["config_path"] = config_path

    samples = run_generation_pipeline(config)

    output_path = Path("data/raw/generated_samples.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(samples, f, indent=2)

    logger.info(f"Saved {len(samples)} samples to {output_path}")


if __name__ == "__main__":
    main()