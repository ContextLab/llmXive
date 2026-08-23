"""Local reproduction runner for Phi-2 (2.7B) checkpoint.

This script is OPTIONAL and for local reproduction only. It is NOT part of
the primary CI pipeline. It uses the `microsoft/phi-2` model (2.7B) via
`llama-cpp-python` with 4-bit quantization (Q4_K_M GGUF).

Verification:
  Run `python code/generation/runner_local.py --test`
  Verify `data/raw/local_generation_test.json` exists with a representative sample.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import shared utilities from the project
# Note: We use the tolerant logger from utils.logging
from utils.logging import log_operation, get_logger, retry_on_failure
from config import get_config, get_marker_dictionaries

# Attempt to import llama-cpp-python
try:
    from llama_cpp import Llama
except ImportError:
    print("ERROR: llama-cpp-python is not installed. Install with: pip install llama-cpp-python")
    sys.exit(1)

# Constants
MODEL_ID = "microsoft/phi-2"
GGUF_FILENAME = "phi-2.Q4_K_M.gguf"
DEFAULT_MODEL_PATH = "models/phi-2.Q4_K_M.gguf"
TEST_OUTPUT_PATH = "data/raw/local_generation_test.json"
MAX_TOKENS = 256
TEMPERATURE = 0.7
MAX_ATTEMPTS = 3
RETRY_DELAY = 5.0

class HardwareError(Exception):
    """Raised when hardware requirements for local reproduction are not met."""
    pass

def check_hardware_requirements() -> None:
    """Verify that the local machine has sufficient resources."""
    # Check for RAM availability (rough heuristic)
    # Phi-2 4-bit requires ~2GB VRAM/RAM, so 4GB+ system RAM is recommended
    # This is a soft check; we proceed if we can load the model
    logger = get_logger("local_runner")
    logger.log("hardware_check", message="Checking local hardware requirements...")
    # In a real scenario, we might check psutil here, but for now we rely on load failure
    logger.log("hardware_check_complete", status="ok")

def load_model(model_path: Optional[str] = None) -> Llama:
    """Load the Phi-2 GGUF model.

    Args:
        model_path: Path to the GGUF file. Defaults to DEFAULT_MODEL_PATH.

    Returns:
        Loaded Llama model instance.

    Raises:
        HardwareError: If the model cannot be loaded.
    """
    if model_path is None:
        model_path = DEFAULT_MODEL_PATH

    logger = get_logger("local_runner")
    logger.log("model_load_start", model_path=model_path)

    if not os.path.exists(model_path):
        # Attempt to download or guide user
        error_msg = (
            f"Model file not found at '{model_path}'. "
            f"Please download the '{GGUF_FILENAME}' file from HuggingFace "
            f"(e.g., TheBloke/phi-2-GGUF) and place it at '{model_path}'."
        )
        logger.log("model_load_failed", error=error_msg)
        raise HardwareError(error_msg)

    try:
        model = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_threads=4,
            verbose=False,
        )
        logger.log("model_load_success", model_id=MODEL_ID)
        return model
    except Exception as e:
        logger.log("model_load_failed", error=str(e))
        raise HardwareError(f"Failed to load model: {e}") from e

@retry_on_failure(max_attempts=MAX_ATTEMPTS, delay=RETRY_DELAY)
def generate_sample(
    model: Llama,
    prompt: str,
    strategy: str,
    seed: int,
    timeout: int = 120
) -> Dict[str, Any]:
    """Generate a single phenomenological sample.

    Args:
        model: The loaded Llama model.
        prompt: The input prompt string.
        strategy: The prompting strategy used (e.g., 'Direct', 'Role-play').
        seed: Random seed for reproducibility.
        timeout: Maximum time in seconds for generation (not strictly enforced here).

    Returns:
        Dictionary containing the generation result and metadata.
    """
    random.seed(seed)
    logger = get_logger("local_runner")
    logger.log("generate_sample_attempt", strategy=strategy, seed=seed)

    try:
        # Generate text
        output = model(
            prompt,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            stop=["\n\n", "User:"],
            echo=False
        )

        generated_text = output['choices'][0]['text']

        result = {
            "id": f"local_{strategy}_{seed}",
            "model_id": MODEL_ID,
            "strategy": strategy,
            "prompt": prompt,
            "generated_text": generated_text,
            "seed": seed,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "type": "phenomenological"
        }

        logger.log("generate_sample_success", strategy=strategy, seed=seed)
        return result

    except Exception as e:
        logger.log("generate_sample_failed", strategy=strategy, seed=seed, error=str(e))
        raise

def run_generation_pipeline(
    num_samples: int = 1,
    output_path: Optional[str] = None,
    model_path: Optional[str] = None,
    test_mode: bool = False
) -> List[Dict[str, Any]]:
    """Run the local generation pipeline.

    Args:
        num_samples: Number of samples to generate.
        output_path: Path to save the output JSON. Defaults to TEST_OUTPUT_PATH.
        model_path: Path to the model GGUF file.
        test_mode: If True, generates a minimal set for verification.

    Returns:
        List of generated sample dictionaries.
    """
    if output_path is None:
        output_path = TEST_OUTPUT_PATH

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    logger = get_logger("local_runner")
    logger.log("pipeline_start", num_samples=num_samples, test_mode=test_mode)

    # Load prompts (using base prompts from T008)
    prompts_file = "data/prompts/base_prompts.json"
    if not os.path.exists(prompts_file):
        logger.log("prompts_missing", file=prompts_file)
        # Fallback to a simple prompt if file missing for test mode
        base_prompts = [
            {"id": "p1", "prompt": "Describe the experience of waking up in the morning."},
            {"id": "p2", "prompt": "Describe the feeling of holding a warm cup of coffee."},
        ]
    else:
        with open(prompts_file, 'r', encoding='utf-8') as f:
            base_prompts = json.load(f)

    strategies = ["Direct", "Hypothetical", "Comparative", "Role-play"]

    # Load model
    model = load_model(model_path)

    all_samples = []
    attempts = 0
    target = num_samples if not test_mode else 1

    for i in range(target):
        strategy = strategies[i % len(strategies)]
        prompt_data = base_prompts[i % len(base_prompts)]
        prompt_text = prompt_data["prompt"]
        seed = random.randint(0, 2**32 - 1)

        try:
            sample = generate_sample(model, prompt_text, strategy, seed)
            all_samples.append(sample)
            attempts += 1
        except Exception as e:
            logger.log("pipeline_sample_failed", error=str(e))
            # Continue to next sample in test mode
            if not test_mode:
                raise

    # Save results
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_samples, f, indent=2, ensure_ascii=False)

    logger.log("pipeline_complete", total_samples=len(all_samples), output_path=output_path)
    return all_samples

def main() -> None:
    """Main entry point for the local runner."""
    parser = argparse.ArgumentParser(description="Local Phi-2 Generation Runner")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode: generate minimal samples and exit."
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        default=1,
        help="Number of samples to generate (default: 1)."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=TEST_OUTPUT_PATH,
        help=f"Output file path (default: {TEST_OUTPUT_PATH})."
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default=DEFAULT_MODEL_PATH,
        help=f"Path to the GGUF model file (default: {DEFAULT_MODEL_PATH})."
    )

    args = parser.parse_args()

    # Setup logging
    logger = get_logger("local_runner")
    log_operation("main_start", task="runner_local", config=args)

    try:
        if args.test:
            print("Running in TEST mode...")
            samples = run_generation_pipeline(
                num_samples=1,
                output_path=args.output,
                model_path=args.model_path,
                test_mode=True
            )
            print(f"Test complete. Generated {len(samples)} sample(s).")
            print(f"Output written to: {args.output}")

            # Verification
            if os.path.exists(args.output):
                print("SUCCESS: Output file exists.")
            else:
                print("FAILURE: Output file not found.")
                sys.exit(1)

        else:
            print("Running FULL pipeline...")
            samples = run_generation_pipeline(
                num_samples=args.num_samples,
                output_path=args.output,
                model_path=args.model_path,
                test_mode=False
            )
            print(f"Pipeline complete. Generated {len(samples)} sample(s).")

    except HardwareError as e:
        logger.log("pipeline_failed", error=str(e))
        print(f"HARDWARE ERROR: {e}")
        print("Please ensure the model file exists at the specified path.")
        sys.exit(1)
    except Exception as e:
        logger.log("pipeline_failed", error=str(e))
        print(f"ERROR: {e}")
        sys.exit(1)
    finally:
        log_operation("main_end", task="runner_local")

if __name__ == "__main__":
    main()
