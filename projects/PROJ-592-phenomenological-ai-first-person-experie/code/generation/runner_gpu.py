"""
GPU-Offload Generation Runner for Phenomenological AI Project.

Implements T009b: Generate samples using Mistral-7B (or equivalent 7B model)
via llama-cpp-python with CUDA device and 4-bit quantization.

Target: >= 80 samples per prompt per strategy (1600 per strategy) for the second checkpoint.
"""
from __future__ import annotations

import json
import logging
import os
import random
import time
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Local imports from project API surface
from config import get_config
from utils.logging import log_operation, get_logger, retry_on_failure

# Constants
MAX_ATTEMPTS_PER_SAMPLE = 3
TIMEOUT_SECONDS = 120
BATCH_SIZE = 20  # Samples per batch file

class GenerationError(Exception):
    """Custom exception for generation failures."""
    pass

class HardwareError(Exception):
    """Custom exception for hardware/CUDA failures."""
    pass

def setup_logger(name: str = "gpu_runner") -> logging.Logger:
    """Setup a logger for the GPU runner."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def check_cuda_availability() -> bool:
    """Check if CUDA is available and usable."""
    try:
        import torch
        if not torch.cuda.is_available():
            return False
        # Try to allocate a small tensor to verify functionality
        _ = torch.zeros(1).cuda()
        return True
    except ImportError:
        return False
    except RuntimeError:
        return False

def load_model(model_path: str, n_ctx: int = 2048, n_gpu_layers: int = 35) -> Any:
    """
    Load the Mistral-7B model using llama-cpp-python with CUDA offload.

    Args:
        model_path: Path to the GGUF model file.
        n_ctx: Context window size.
        n_gpu_layers: Number of layers to offload to GPU.

    Returns:
        Loaded model instance.

    Raises:
        HardwareError: If CUDA is not available or model fails to load.
    """
    logger = get_logger()
    log_operation("load_model_start", model_path=model_path, n_gpu_layers=n_gpu_layers)

    try:
        from llama_cpp import Llama

        if not check_cuda_availability():
            raise HardwareError("CUDA is not available or not functional. Aborting GPU generation.")

        # Load with GPU offload
        model = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_gpu_layers=n_gpu_layers,
            verbose=False  # Suppress verbose llama-cpp logs
        )
        log_operation("load_model_complete", model_path=model_path)
        return model

    except ImportError as e:
        raise HardwareError(f"llama-cpp-python not installed or CUDA support missing: {e}")
    except Exception as e:
        raise HardwareError(f"Failed to load model: {e}")

@retry_on_failure(max_attempts=MAX_ATTEMPTS_PER_SAMPLE, delay=2.0)
def generate_sample(
    model: Any,
    prompt: str,
    strategy: str,
    prompt_id: str,
    seed: int,
    max_tokens: int = 512,
    temperature: float = 0.7
) -> Dict[str, Any]:
    """
    Generate a single sample using the loaded model.

    Args:
        model: Loaded Llama model.
        prompt: The prompt text.
        strategy: The prompting strategy used.
        prompt_id: Unique identifier for the prompt.
        seed: Random seed for reproducibility.
        max_tokens: Maximum tokens to generate.
        temperature: Sampling temperature.

    Returns:
        Dictionary containing the generation result and metadata.
    """
    logger = get_logger()
    log_operation(
        "generate_sample_attempt",
        strategy=strategy,
        prompt_id=prompt_id,
        seed=seed,
        attempt=1
    )

    # Set seed for reproducibility
    model.set_seed(seed)

    try:
        # Generate text
        output = model(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=["\n\n", "###"],
            echo=False
        )

        generated_text = output['choices'][0]['text'].strip()

        result = {
            "prompt_id": prompt_id,
            "strategy": strategy,
            "seed": seed,
            "prompt": prompt,
            "generated_text": generated_text,
            "model": "Mistral-7B-Instruct-v0.2",
            "device": "cuda",
            "timestamp": time.time()
        }

        log_operation("generate_sample_success", prompt_id=prompt_id, strategy=strategy)
        return result

    except Exception as e:
        log_operation("generate_sample_failed", prompt_id=prompt_id, error=str(e))
        raise GenerationError(f"Generation failed for prompt {prompt_id}: {e}")

def load_prompts(prompts_path: str) -> List[Dict[str, Any]]:
    """
    Load base prompts from JSON file.

    Args:
        prompts_path: Path to the base_prompts.json file.

    Returns:
        List of prompt dictionaries.
    """
    logger = get_logger()
    log_operation("load_prompts_start", path=prompts_path)

    try:
        with open(prompts_path, 'r', encoding='utf-8') as f:
            prompts_data = json.load(f)

        # Ensure we have the expected structure
        if isinstance(prompts_data, list):
            prompts = prompts_data
        elif isinstance(prompts_data, dict) and 'prompts' in prompts_data:
            prompts = prompts_data['prompts']
        else:
            raise ValueError("Unexpected prompts file structure")

        log_operation("load_prompts_complete", count=len(prompts))
        return prompts

    except FileNotFoundError:
        raise FileNotFoundError(f"Prompts file not found: {prompts_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in prompts file: {e}")

def save_batch(samples: List[Dict[str, Any]], output_path: Path, batch_id: int):
    """
    Save a batch of samples to a JSON file.

    Args:
        samples: List of sample dictionaries.
        output_path: Directory to save the file.
        batch_id: Batch identifier.
    """
    filename = f"generation_batch_gpu_mistral_{batch_id:03d}.json"
    filepath = output_path / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(samples, f, indent=2, ensure_ascii=False)

    log_operation("save_batch_complete", path=str(filepath), count=len(samples))

def run_generation_pipeline(
    config: Optional[Dict[str, Any]] = None,
    prompts_path: Optional[str] = None,
    output_dir: Optional[str] = None,
    samples_per_prompt: int = 80
):
    """
    Run the full GPU generation pipeline.

    Args:
        config: Configuration dictionary (optional, loads from config.py if None).
        prompts_path: Path to base_prompts.json (optional, loads from config if None).
        output_dir: Output directory for generated samples (optional, loads from config if None).
        samples_per_prompt: Number of samples to generate per prompt (default: 80).
    """
    logger = setup_logger()
    logger.info("Starting GPU generation pipeline (T009b)")

    # Load configuration
    if config is None:
        config = get_config()

    # Resolve paths
    if prompts_path is None:
        prompts_path = config.get("prompts_path", "data/prompts/base_prompts.json")
    if output_dir is None:
        output_dir = config.get("output_dir", "data/raw")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load prompts
    prompts = load_prompts(prompts_path)
    strategies = ["Direct", "Hypothetical", "Comparative", "Role-play"]

    # Load model
    model_path = config.get("gpu_model_path", "mistralai/Mistral-7B-Instruct-v0.2-GGUF/mistral-7b-instruct-v0.2.Q4_K_M.gguf")
    model = load_model(model_path)

    all_samples = []
    batch_count = 0
    samples_in_batch = []

    log_operation("run_generation_pipeline_start", total_prompts=len(prompts), strategies=len(strategies))

    try:
        for strategy in strategies:
            for prompt_item in prompts:
                prompt_id = prompt_item.get("id", f"prompt_{prompts.index(prompt_item)}")
                prompt_text = prompt_item.get("prompt", "")

                if not prompt_text:
                    logger.warning(f"Skipping empty prompt: {prompt_id}")
                    continue

                # Generate samples for this prompt/strategy combination
                for i in range(samples_per_prompt):
                    seed = random.randint(0, 2**32 - 1)
                    sample = generate_sample(
                        model=model,
                        prompt=prompt_text,
                        strategy=strategy,
                        prompt_id=prompt_id,
                        seed=seed,
                        max_tokens=512,
                        temperature=0.7
                    )
                    samples_in_batch.append(sample)
                    all_samples.append(sample)

                    # Save batch periodically
                    if len(samples_in_batch) >= BATCH_SIZE:
                        batch_count += 1
                        save_batch(samples_in_batch, output_path, batch_count)
                        samples_in_batch = []

                    logger.info(f"Generated: {strategy} / {prompt_id} / {i+1}/{samples_per_prompt}")

        # Save remaining samples
        if samples_in_batch:
            batch_count += 1
            save_batch(samples_in_batch, output_path, batch_count)

        log_operation(
            "generation_complete",
            total_samples=len(all_samples),
            batches=batch_count,
            strategies=strategies
        )

        # Write summary log
        summary = {
            "total_samples": len(all_samples),
            "batches": batch_count,
            "strategies": strategies,
            "samples_per_prompt": samples_per_prompt,
            "model": "Mistral-7B-Instruct-v0.2",
            "device": "cuda",
            "timestamp": time.time()
        }

        summary_path = output_path / "generation_gpu_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"GPU generation complete. Total samples: {len(all_samples)}")
        return all_samples

    except Exception as e:
        log_operation("generation_failed", error=str(e))
        logger.error(f"Pipeline failed: {e}")
        raise

def main():
    """Main entry point for CLI execution."""
    import argparse

    parser = argparse.ArgumentParser(description="GPU-Offload Generation Runner (T009b)")
    parser.add_argument("--config", type=str, default=None, help="Path to config file")
    parser.add_argument("--prompts", type=str, default=None, help="Path to base_prompts.json")
    parser.add_argument("--output", type=str, default=None, help="Output directory")
    parser.add_argument("--samples", type=int, default=80, help="Samples per prompt")
    parser.add_argument("--test", action="store_true", help="Run in test mode (1 sample per prompt)")

    args = parser.parse_args()

    config = None
    if args.config:
        from utils.io import load_json
        config = load_json(args.config)

    if args.test:
        samples_per_prompt = 1
    else:
        samples_per_prompt = args.samples

    run_generation_pipeline(
        config=config,
        prompts_path=args.prompts,
        output_dir=args.output,
        samples_per_prompt=samples_per_prompt
    )

if __name__ == "__main__":
    main()
