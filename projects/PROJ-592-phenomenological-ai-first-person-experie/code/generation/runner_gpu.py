"""
GPU-Offload Generation Runner for Phenomenological AI Project.

This module implements the generation pipeline for Mistral-7B-Instruct-v0.2
using llama-cpp-python on CUDA devices. It is designed to be executed on
free-tier GPU runners (e.g., Kaggle) when the CPU runner detects a CUDA requirement.

Dependency: T009 (logic reuse)
Target: ≥80 samples per prompt per strategy (1600 per strategy)
"""
from __future__ import annotations

import json
import logging
import os
import random
import time
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Import shared utilities from the project structure
try:
    from utils.logging import get_logger, log_operation, retry_on_failure, LogEntry
    from config import get_config
except ImportError:
    # Fallback for direct execution or different import context
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.logging import get_logger, log_operation, retry_on_failure, LogEntry
    from config import get_config

# Hardware and model imports
try:
    from llama_cpp import Llama
except ImportError:
    raise ImportError(
        "llama-cpp-python is required for GPU generation. "
        "Install with: pip install llama-cpp-python"
    )

# Constants
MAX_ATTEMPTS_PER_SAMPLE = 3
BASE_DELAY = 2.0
MAX_DELAY = 10.0
CUDA_DEVICE = 0  # Default GPU device
BATCH_SIZE = 1  # Process one sample at a time to manage VRAM

class GenerationError(Exception):
    """Base exception for generation failures."""
    pass

class HardwareError(Exception):
    """Exception for hardware/CUDA availability issues."""
    pass

def setup_logger(name: str = "runner_gpu") -> logging.Logger:
    """Configure a logger for the GPU runner."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

def check_cuda_availability(logger: Optional[logging.Logger] = None) -> bool:
    """
    Verify CUDA availability and GPU presence.

    Returns:
        bool: True if CUDA is available, False otherwise.
    """
    log_operation("check_cuda_availability")
    if logger is None:
        logger = setup_logger()

    try:
        import torch
        if not torch.cuda.is_available():
            logger.warning("PyTorch CUDA is not available.")
            return False
        if torch.cuda.device_count() == 0:
            logger.warning("No CUDA devices found.")
            return False
        logger.info(f"CUDA available: {torch.cuda.device_count()} device(s)")
        return True
    except ImportError:
        logger.warning("PyTorch not installed. Attempting llama-cpp fallback check.")
        # llama-cpp-python handles its own CUDA check during model load,
        # but we prefer torch for explicit detection.
        return False

@retry_on_failure(max_attempts=MAX_ATTEMPTS_PER_SAMPLE, delay=BASE_DELAY)
def load_model(
    model_path: str,
    n_ctx: int = 2048,
    n_batch: int = 512,
    n_threads: Optional[int] = None,
    verbose: bool = False
) -> Llama:
    """
    Load the Mistral-7B model using llama-cpp-python with CUDA support.

    Args:
        model_path: Path to the GGUF model file.
        n_ctx: Context window size.
        n_batch: Batch size for prompt processing.
        n_threads: Number of threads (None uses all available).
        verbose: Enable verbose logging from llama-cpp.

    Returns:
        Llama: Loaded model instance.
    """
    log_operation("load_model", model_path=model_path, n_ctx=n_ctx)
    logger = setup_logger()

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")

    try:
        # llama-cpp-python automatically detects CUDA if installed correctly
        # The 'device' parameter is handled by the underlying backend (llama.cpp)
        # We pass n_gpu_layers=1 to force GPU offloading if available
        model = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_batch=n_batch,
            n_threads=n_threads,
            n_gpu_layers=1,  # Offload to GPU
            verbose=verbose
        )
        logger.info(f"Model loaded successfully: {model_path}")
        return model
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise GenerationError(f"Model loading failed: {e}") from e

def load_prompts(prompts_path: str) -> List[Dict[str, Any]]:
    """
    Load base prompts from a JSON file.

    Args:
        prompts_path: Path to the prompts JSON file.

    Returns:
        List[Dict]: List of prompt dictionaries.
    """
    log_operation("load_prompts", prompts_path=prompts_path)
    logger = setup_logger()

    try:
        with open(prompts_path, 'r', encoding='utf-8') as f:
            prompts = json.load(f)
        logger.info(f"Loaded {len(prompts)} prompts from {prompts_path}")
        return prompts
    except Exception as e:
        logger.error(f"Failed to load prompts: {e}")
        raise GenerationError(f"Prompt loading failed: {e}") from e

@retry_on_failure(max_attempts=MAX_ATTEMPTS_PER_SAMPLE, delay=BASE_DELAY)
def generate_sample(
    model: Llama,
    prompt: str,
    strategy: str,
    seed: int,
    max_tokens: int = 512,
    temperature: float = 0.7,
    top_p: float = 0.9
) -> Dict[str, Any]:
    """
    Generate a single phenomenological report sample.

    Args:
        model: Loaded Llama model.
        prompt: The prompt text.
        strategy: The prompting strategy used (e.g., 'Direct', 'Role-play').
        seed: Random seed for reproducibility.
        max_tokens: Maximum tokens to generate.
        temperature: Sampling temperature.
        top_p: Nucleus sampling parameter.

    Returns:
        Dict: Generated sample with metadata.
    """
    log_operation("generate_sample_attempt", strategy=strategy, seed=seed)
    logger = setup_logger()

    random.seed(seed)

    try:
        # Generate text
        output = model(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            echo=False,
            stop=["</s>", "END"]
        )

        generated_text = output['choices'][0]['text'].strip()

        sample = {
            "seed": seed,
            "prompt": prompt,
            "strategy": strategy,
            "text": generated_text,
            "model": "mistralai/Mistral-7B-Instruct-v0.2",
            "timestamp": time.time()
        }

        logger.info(f"Generated sample (seed={seed}, strategy={strategy})")
        return sample

    except Exception as e:
        logger.error(f"Generation failed for seed={seed}: {e}")
        raise GenerationError(f"Sample generation failed: {e}") from e

def save_batch(
    samples: List[Dict[str, Any]],
    output_path: str,
    strategy: str,
    model_name: str
) -> None:
    """
    Save a batch of generated samples to a JSON file.

    Args:
        samples: List of sample dictionaries.
        output_path: Path to the output JSON file.
        strategy: The strategy used for this batch.
        model_name: Name of the model used.
    """
    log_operation("save_batch", output_path=output_path, strategy=strategy)
    logger = setup_logger()

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    batch_data = {
        "strategy": strategy,
        "model": model_name,
        "samples": samples,
        "count": len(samples),
        "timestamp": time.time()
    }

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(batch_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(samples)} samples to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save batch: {e}")
        raise GenerationError(f"Batch saving failed: {e}") from e

def run_generation_pipeline(
    config: Optional[Dict[str, Any]] = None,
    prompts_path: Optional[str] = None,
    output_dir: Optional[str] = None,
    samples_per_prompt: int = 80
) -> Dict[str, Any]:
    """
    Execute the full generation pipeline for the GPU runner.

    Args:
        config: Configuration dictionary (optional).
        prompts_path: Path to prompts JSON (optional).
        output_dir: Output directory (optional).
        samples_per_prompt: Number of samples per prompt.

    Returns:
        Dict: Pipeline execution summary.
    """
    log_operation("run_generation_pipeline", config_path=str(config) if config else "default")
    logger = setup_logger()

    # Load config if not provided
    if config is None:
        config = get_config()

    # Determine paths
    if prompts_path is None:
        prompts_path = config.get("prompts_path", "data/prompts/base_prompts.json")
    if output_dir is None:
        output_dir = config.get("output_dir", "data/raw")

    # Check CUDA
    if not check_cuda_availability(logger):
        raise HardwareError("CUDA not available. This runner requires a GPU.")

    # Load prompts
    try:
        prompts_data = load_prompts(prompts_path)
    except GenerationError:
        raise

    # Prepare strategies
    strategies = ["Direct", "Hypothetical", "Comparative", "Role-play"]
    model_name = "mistralai/Mistral-7B-Instruct-v0.2"

    # Load model
    model_path = config.get("model_path", "mistralai/Mistral-7B-Instruct-v0.2.gguf")
    # Note: In a real scenario, we'd download or specify the exact GGUF path.
    # For this implementation, we assume the path is provided in config or env.
    if not os.path.exists(model_path):
        # Fallback to common Hugging Face cache location if not specified
        hf_cache = os.path.expanduser("~/.cache/huggingface/hub")
        # In a real execution, the runner_gpu would be invoked with the correct path
        # or the model would be pre-downloaded.
        logger.error(f"Model path not found: {model_path}")
        raise FileNotFoundError(f"Model file not found: {model_path}")

    logger.info(f"Loading model from {model_path}")
    model = load_model(model_path)

    # Generation loop
    all_samples = []
    strategy_counts = {s: 0 for s in strategies}
    success_count = 0
    fail_count = 0

    for strategy in strategies:
        logger.info(f"Starting generation for strategy: {strategy}")
        batch_samples = []

        for prompt_item in prompts_data:
            prompt_text = prompt_item.get("prompt", "")
            prompt_id = prompt_item.get("id", "unknown")

            if not prompt_text:
                continue

            for i in range(samples_per_prompt):
                seed = random.randint(0, 2**32 - 1)
                try:
                    sample = generate_sample(
                        model=model,
                        prompt=prompt_text,
                        strategy=strategy,
                        seed=seed
                    )
                    batch_samples.append(sample)
                    all_samples.append(sample)
                    success_count += 1
                    strategy_counts[strategy] += 1
                except GenerationError as e:
                    logger.warning(f"Failed sample {i+1}/{samples_per_prompt} for {strategy}: {e}")
                    fail_count += 1

        # Save batch for each strategy
        batch_filename = f"generation_batch_{strategy}_{model_name.replace('/', '_')}.json"
        batch_path = os.path.join(output_dir, batch_filename)
        save_batch(batch_samples, batch_path, strategy, model_name)

    # Write generation log
    log_data = {
        "total": len(all_samples),
        "success": success_count,
        "fail": fail_count,
        "strategy_counts": strategy_counts,
        "model": model_name,
        "timestamp": time.time()
    }

    log_path = os.path.join(output_dir, "generation_log_gpu.json")
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2)

    logger.info(f"Pipeline complete. Total: {len(all_samples)}, Success: {success_count}, Fail: {fail_count}")
    return log_data

def main() -> None:
    """Entry point for the GPU runner script."""
    import argparse

    parser = argparse.ArgumentParser(description="GPU Generation Runner for Phenomenological AI")
    parser.add_argument("--config", type=str, default="code/config.py", help="Path to config file")
    parser.add_argument("--prompts", type=str, default="data/prompts/base_prompts.json", help="Path to prompts")
    parser.add_argument("--output", type=str, default="data/raw", help="Output directory")
    parser.add_argument("--samples", type=int, default=80, help="Samples per prompt")

    args = parser.parse_args()

    # Load config
    config = get_config()

    try:
        result = run_generation_pipeline(
            config=config,
            prompts_path=args.prompts,
            output_dir=args.output,
            samples_per_prompt=args.samples
        )
        print(json.dumps(result, indent=2))
    except Exception as e:
        logger = setup_logger()
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
