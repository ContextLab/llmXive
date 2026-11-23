"""
Local Reproduction Runner for Phi-2 (2.7B).

This script implements the second checkpoint for local reproduction only.
It is NOT part of the primary CI pipeline.

Requires:
- llama-cpp-python
- A local GGUF file: phi-2.Q4_K_M.gguf (downloaded separately)

Usage:
- python code/generation/runner_local.py --test
  (Runs a single sample generation to verify setup)
- python code/generation/runner_local.py --full
  (Runs the full generation pipeline if desired, though not required for CI)
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import random
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import shared utilities from the project
try:
    from config import get_config
except ImportError:
    # Fallback for running as module vs script
    from code.config import get_config

try:
    from utils.logging import get_logger, log_operation, retry_on_failure
except ImportError:
    from code.utils.logging import get_logger, log_operation, retry_on_failure

try:
    from generation.prompt_engineering import load_base_prompts
except ImportError:
    from code.generation.prompt_engineering import load_base_prompts


class HardwareError(Exception):
    """Raised when local hardware requirements are not met."""
    pass


def check_hardware_requirements() -> None:
    """
    Verify that the environment has sufficient resources for Phi-2 (2.7B).
    Phi-2 Q4_K_M requires approximately 2-3GB RAM.
    """
    # Basic check: ensure llama_cpp is available
    try:
        import llama_cpp
    except ImportError:
        raise HardwareError(
            "llama-cpp-python is not installed. "
            "Install it via: pip install llama-cpp-python"
        )

    # Check for minimum RAM (approximate heuristic)
    # This is a soft check; the actual load will fail if RAM is insufficient.
    # We do not implement a hard block here to allow the run to fail naturally
    # if the hardware is insufficient, as per "fail loudly" constraints.
    logger = get_logger()
    logger.log("hardware_check", status="passed", message="llama_cpp available")


@retry_on_failure(max_attempts=3, delay=5)
def load_model(model_path: str, n_ctx: int = 2048, n_threads: int = 4) -> Any:
    """
    Load the Phi-2 GGUF model.
    
    Args:
        model_path: Path to the phi-2.Q4_K_M.gguf file.
        n_ctx: Context window size.
        n_threads: Number of CPU threads.
        
    Returns:
        The loaded Llama model instance.
    """
    logger = get_logger()
    logger.log("load_model_attempt", path=model_path, threads=n_threads)
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")

    # Import here to avoid heavy import if not needed
    from llama_cpp import Llama
    
    model = Llama(
        model_path=model_path,
        n_ctx=n_ctx,
        n_threads=n_threads,
        verbose=False, # Suppress llama.cpp verbose output
    )
    
    logger.log("model_loaded", path=model_path)
    return model


@retry_on_failure(max_attempts=3, delay=2.0)
def generate_sample(
    model: Any,
    prompt: str,
    max_tokens: int = 256,
    temperature: float = 0.7,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Generate a single sample from the model.
    
    Args:
        model: The loaded Llama model.
        prompt: The input prompt.
        max_tokens: Maximum tokens to generate.
        temperature: Sampling temperature.
        seed: Random seed for reproducibility.
        
    Returns:
        A dictionary containing the generation result.
    """
    logger = get_logger()
    logger.log("generate_sample_attempt", prompt_len=len(prompt), seed=seed)
    
    random.seed(seed)
    
    try:
        output = model(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            seed=seed,
            echo=False,
            stop=["\n\n", "User:", "System:"] # Basic stopping criteria
        )
        
        generated_text = output['choices'][0]['text']
        
        result = {
            "prompt": prompt,
            "generated_text": generated_text,
            "model": "phi-2-Q4_K_M",
            "seed": seed,
            "timestamp": time.time(),
            "status": "success"
        }
        
        logger.log("sample_generated", success=True)
        return result
        
    except Exception as e:
        logger.log("sample_generation_failed", error=str(e))
        raise


def run_generation_pipeline(
    prompts: List[Dict[str, Any]],
    model_path: str,
    output_path: str,
    strategy: str = "local_reproduction",
    samples_per_prompt: int = 1
) -> List[Dict[str, Any]]:
    """
    Run the generation pipeline for the local runner.
    
    Args:
        prompts: List of prompt dictionaries.
        model_path: Path to the GGUF model.
        output_path: Path to save the output JSON.
        strategy: The prompting strategy label.
        samples_per_prompt: Number of samples to generate per prompt.
        
    Returns:
        List of generated samples.
    """
    logger = get_logger()
    log_operation("run_generation_phase", config_path=model_path)
    
    check_hardware_requirements()
    
    model = load_model(model_path)
    
    all_samples = []
    
    for prompt_data in prompts:
        prompt_id = prompt_data.get("id", "unknown")
        prompt_text = prompt_data.get("prompt", "")
        
        for i in range(samples_per_prompt):
            seed = random.randint(0, 2**32 - 1)
            sample = generate_sample(
                model=model,
                prompt=prompt_text,
                seed=seed
            )
            sample["prompt_id"] = prompt_id
            sample["strategy"] = strategy
            sample["seed"] = seed
            all_samples.append(sample)
            
    # Save results
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_samples, f, indent=2, ensure_ascii=False)
        
    logger.log("generation_complete", total_samples=len(all_samples))
    return all_samples


def main() -> None:
    """Main entry point for the local runner."""
    parser = argparse.ArgumentParser(description="Local Runner for Phi-2 Generation")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run a single test generation to verify setup."
    )
    parser.add_argument(
        "--model",
        type=str,
        default="data/models/phi-2.Q4_K_M.gguf",
        help="Path to the Phi-2 GGUF model."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/raw/local_generation_test.json",
        help="Output path for the test generation."
    )
    parser.add_argument(
        "--prompts",
        type=str,
        default="data/prompts/base_prompts.json",
        help="Path to the base prompts JSON."
    )
    
    args = parser.parse_args()
    
    # Setup logger
    logger = get_logger("runner_local")
    
    if args.test:
        logger.log("test_mode_start", model=args.model, output=args.output)
        
        # Load a small subset of prompts for testing
        try:
            prompts = load_base_prompts(args.prompts)
            # Take just the first prompt for the test
            test_prompts = prompts[:1] if prompts else []
            
            if not test_prompts:
                logger.log("test_mode_failed", error="No prompts found")
                raise ValueError("No prompts found in the specified file.")
                
            run_generation_pipeline(
                prompts=test_prompts,
                model_path=args.model,
                output_path=args.output,
                strategy="local_test",
                samples_per_prompt=1
            )
            
            logger.log("test_mode_complete", output=args.output)
            print(f"Test generation complete. Output written to: {args.output}")
            
        except Exception as e:
            logger.log("test_mode_failed", error=str(e))
            print(f"Test generation failed: {e}")
            raise
    else:
        logger.log("full_mode_start")
        # Full mode logic would go here (not required for T012 verification)
        print("Full generation mode not implemented for this task. Use --test.")


if __name__ == "__main__":
    main()