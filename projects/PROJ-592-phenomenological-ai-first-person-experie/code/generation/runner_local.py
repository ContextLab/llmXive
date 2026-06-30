"""
Local Runner for 7B Model Execution (Mistral-7B / Llama-7B)

This script implements the second checkpoint for phenomenological report generation
using larger models (7B parameters) via llama-cpp-python.

NOTE: This script is designed for local execution only on machines with >= 16GB RAM.
It is NOT used in the primary CI path.
"""
import os
import sys
import time
import json
import random
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import shared utilities
from config import get_config, get_logger
from utils.logging import retry_on_failure, log_retry_attempts
from utils.io import safe_write_json, ensure_dir

# Configure logging
logger = get_logger(__name__)

# Hardware check constants
MIN_RAM_GB = 16
MODEL_PATH_7B = os.getenv("MODEL_PATH_7B", "models/mistral-7b-instruct-v0.2.Q4_K_M.gguf")

class HardwareError(Exception):
    """Raised when hardware requirements are not met."""
    pass

def check_hardware_requirements() -> bool:
    """
    Check if the system has sufficient RAM for 7B model inference.
    Returns True if requirements are met, raises HardwareError otherwise.
    """
    try:
        if sys.platform == "linux":
            with open('/proc/meminfo', 'r') as mem:
                for line in mem:
                    if line.startswith('MemTotal:'):
                        total_kb = int(line.split()[1])
                        total_gb = total_kb / (1024 * 1024)
                        if total_gb < MIN_RAM_GB:
                            raise HardwareError(
                                f"Insufficient RAM: {total_gb:.1f}GB available. "
                                f"Requires >= {MIN_RAM_GB}GB for 7B model inference."
                            )
                        logger.info(f"RAM check passed: {total_gb:.1f}GB available.")
                        return True
        elif sys.platform == "darwin":
            # macOS: use sysctl (simplified check)
            import subprocess
            try:
                result = subprocess.run(['sysctl', '-n', 'hw.memsize'], capture_output=True, text=True)
                total_bytes = int(result.stdout.strip())
                total_gb = total_bytes / (1024 ** 3)
                if total_gb < MIN_RAM_GB:
                    raise HardwareError(
                        f"Insufficient RAM: {total_gb:.1f}GB available. "
                        f"Requires >= {MIN_RAM_GB}GB for 7B model inference."
                    )
                logger.info(f"RAM check passed: {total_gb:.1f}GB available.")
                return True
            except Exception as e:
                logger.warning(f"Could not determine RAM on macOS: {e}")
                # Proceed with warning on macOS if check fails
                return True
        else:
            logger.warning(f"Hardware check not implemented for {sys.platform}. Proceeding with caution.")
            return True
    except HardwareError:
        raise
    except Exception as e:
        logger.warning(f"Hardware check failed: {e}. Proceeding with caution.")
        return True

def load_model(model_path: Optional[str] = None):
    """
    Load the 7B model using llama-cpp-python.
    """
    if model_path is None:
        model_path = MODEL_PATH_7B

    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model file not found at {model_path}. "
            f"Please download a 7B GGUF model (e.g., Mistral-7B or Llama-2-7B) "
            f"and set the MODEL_PATH_7B environment variable."
        )

    try:
        from llama_cpp import Llama
        logger.info(f"Loading model from {model_path}...")
        # Use 4-bit quantization settings compatible with most GGUF files
        llm = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_threads=4,
            n_batch=512,
            use_mmap=True,
            use_mlock=True,
        )
        logger.info("Model loaded successfully.")
        return llm
    except ImportError:
        raise ImportError(
            "llama-cpp-python is required for local 7B execution. "
            "Install with: pip install llama-cpp-python"
        )
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

@retry_on_failure(max_attempts=3, delay=5)
def generate_sample(
    llm,
    prompt: str,
    strategy: str,
    prompt_id: str,
    seed: int,
    max_tokens: int = 512,
    temperature: float = 0.7
) -> Dict[str, Any]:
    """
    Generate a single phenomenological report sample.
    """
    try:
        # Set seed for reproducibility
        # Note: llama-cpp-python handles seeding via seed parameter in generate
        output = llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=["</s>", "END"],
            seed=seed,
            echo=False
        )

        generated_text = output['choices'][0]['text'].strip()

        sample = {
            "id": f"{strategy}_{prompt_id}_{seed}",
            "strategy": strategy,
            "prompt_id": prompt_id,
            "prompt": prompt,
            "generated_text": generated_text,
            "seed": seed,
            "model": "7B-local",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

        return sample
    except Exception as e:
        logger.error(f"Generation failed for {prompt_id}: {e}")
        raise

def run_generation_pipeline(
    model_path: Optional[str] = None,
    output_dir: str = "data/raw/local_7b",
    num_samples_per_prompt: int = 5,
    strategies: Optional[List[str]] = None,
    prompts_file: Optional[str] = None
):
    """
    Run the full generation pipeline for local 7B models.
    """
    # Verify hardware
    check_hardware_requirements()

    # Load config
    config = get_config()
    if strategies is None:
        strategies = config.get("strategies", ["Direct", "Hypothetical", "Comparative", "Role-play"])
    
    if prompts_file is None:
        prompts_file = "data/prompts/base_prompts.json"

    # Ensure output directory exists
    ensure_dir(output_dir)

    # Load model
    llm = load_model(model_path)

    # Load prompts
    try:
        with open(prompts_file, 'r') as f:
            base_prompts = json.load(f)
    except FileNotFoundError:
        logger.error(f"Prompts file not found: {prompts_file}")
        # Fallback to empty prompts if file missing (should not happen in normal flow)
        base_prompts = {}

    all_samples = []
    total_attempts = 0
    successful_samples = 0

    logger.info(f"Starting generation pipeline with {len(base_prompts)} prompts and {len(strategies)} strategies.")

    for strategy in strategies:
        logger.info(f"Processing strategy: {strategy}")
        for prompt_id, prompt_text in base_prompts.items():
            for i in range(num_samples_per_prompt):
                seed = random.randint(10000, 99999)
                total_attempts += 1
                try:
                    sample = generate_sample(
                        llm=llm,
                        prompt=prompt_text,
                        strategy=strategy,
                        prompt_id=prompt_id,
                        seed=seed,
                        temperature=0.7
                    )
                    all_samples.append(sample)
                    successful_samples += 1
                    logger.info(f"Generated sample {successful_samples}/{total_attempts}: {sample['id']}")
                except Exception as e:
                    logger.error(f"Failed to generate sample {prompt_id}/{strategy}/{i}: {e}")
                    # Mark as failed but continue
                    all_samples.append({
                        "id": f"{strategy}_{prompt_id}_{seed}_FAILED",
                        "strategy": strategy,
                        "prompt_id": prompt_id,
                        "error": str(e)
                    })

    # Save results
    output_file = os.path.join(output_dir, f"local_7b_corpus_{int(time.time())}.json")
    safe_write_json(all_samples, output_file)
    logger.info(f"Saved {len(all_samples)} samples to {output_file}")

    return all_samples

def main():
    """
    Entry point for the local 7B generation runner.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Local 7B Model Generation Runner")
    parser.add_argument("--model", type=str, default=None, help="Path to 7B GGUF model")
    parser.add_argument("--output", type=str, default="data/raw/local_7b", help="Output directory")
    parser.add_argument("--samples", type=int, default=5, help="Samples per prompt")
    parser.add_argument("--prompts", type=str, default="data/prompts/base_prompts.json", help="Prompts file")
    parser.add_argument("--strategies", type=str, nargs="+", default=None, help="Strategies to use")
    
    args = parser.parse_args()

    try:
        run_generation_pipeline(
            model_path=args.model,
            output_dir=args.output,
            num_samples_per_prompt=args.samples,
            strategies=args.strategies,
            prompts_file=args.prompts
        )
        logger.info("Generation pipeline completed successfully.")
    except HardwareError as e:
        logger.error(f"Hardware requirement not met: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
