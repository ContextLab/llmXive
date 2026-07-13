"""Generation runner with timeout handling and sample-size logging."""
import os
import sys
import time
import json
import random
import signal
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.logging import get_logger, retry_on_failure

logger = get_logger("generation_runner")

# Constants
DEFAULT_SEED = 42
DEFAULT_NUM_SAMPLES_PER_PROMPT = 80
DEFAULT_TIMEOUT_SECONDS = 30
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "generation_output.json"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

class GenerationTimeoutError(Exception):
    """Raised when a generation times out."""
    pass

def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise GenerationTimeoutError("Generation timed out")

@retry_on_failure(max_retries=3, logger=logger)
def load_model(model_path: str = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf") -> Any:
    """Load the TinyLlama model using llama-cpp-python.
    
    Args:
        model_path: Path to the GGUF model file.
        
    Returns:
        The loaded model object.
    """
    logger.log("load_model_start", model_path=model_path)
    
    try:
        from llama_cpp import Llama
        
        model = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_threads=4,
            n_batch=512,
            use_mmap=True
        )
        
        logger.log("model_loaded", model_path=model_path)
        return model
    except ImportError:
        logger.log("llama_cpp_not_found", message="llama-cpp-python not installed")
        raise
    except Exception as e:
        logger.log("model_load_failed", error=str(e))
        raise

@retry_on_failure(max_attempts=3, delay=5, logger=logger)
def generate_sample(
    model: Any,
    prompt: str,
    strategy: str,
    seed: int,
    max_tokens: int = 512,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
) -> Dict[str, Any]:
    """Generate a single sample from the model.
    
    Args:
        model: The loaded Llama model.
        prompt: The input prompt.
        strategy: The prompting strategy used.
        seed: Random seed for reproducibility.
        max_tokens: Maximum tokens to generate.
        timeout_seconds: Timeout for generation.
        
    Returns:
        Dictionary containing the generated text and metadata.
    """
    logger.log("generate_sample_start", 
               prompt_length=len(prompt),
               strategy=strategy,
               seed=seed)
    
    # Set timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    
    try:
        random.seed(seed)
        output = model(
            prompt,
            max_tokens=max_tokens,
            temperature=0.7,
            top_p=0.9,
            seed=seed,
            echo=False
        )
        
        # Cancel timeout
        signal.alarm(0)
        
        generated_text = output['choices'][0]['text']
        
        result = {
            "id": f"{strategy}_{seed}",
            "prompt": prompt,
            "strategy": strategy,
            "generated_text": generated_text,
            "seed": seed,
            "status": "success"
        }
        
        logger.log("generate_sample_complete", 
                   strategy=strategy,
                   seed=seed,
                   text_length=len(generated_text))
        
        return result
        
    except GenerationTimeoutError as e:
        signal.alarm(0)
        logger.log("generation_timeout", 
                   strategy=strategy,
                   seed=seed,
                   error=str(e))
        return {
            "id": f"{strategy}_{seed}",
            "prompt": prompt,
            "strategy": strategy,
            "generated_text": "",
            "seed": seed,
            "status": "timeout"
        }
    except Exception as e:
        signal.alarm(0)
        logger.log("generation_failed", 
                   strategy=strategy,
                   seed=seed,
                   error=str(e))
        return {
            "id": f"{strategy}_{seed}",
            "prompt": prompt,
            "strategy": strategy,
            "generated_text": "",
            "seed": seed,
            "status": "error",
            "error": str(e)
        }

def run_generation_pipeline(
    model: Any,
    prompts: List[str],
    strategies: List[str],
    num_samples_per_prompt: int = DEFAULT_NUM_SAMPLES_PER_PROMPT,
    seed_start: int = DEFAULT_SEED,
    output_path: Path = OUTPUT_FILE
) -> List[Dict[str, Any]]:
    """Run the full generation pipeline.
    
    Args:
        model: The loaded model.
        prompts: List of base prompts.
        strategies: List of prompting strategies.
        num_samples_per_prompt: Number of samples per prompt-strategy combination.
        seed_start: Starting seed value.
        output_path: Path to save the output.
        
    Returns:
        List of all generated samples.
    """
    logger.log("pipeline_start", 
               num_prompts=len(prompts),
               num_strategies=len(strategies),
               num_samples_per_prompt=num_samples_per_prompt)
    
    all_samples = []
    successful_count = 0
    failed_count = 0
    
    for strategy in strategies:
        for prompt in prompts:
            for i in range(num_samples_per_prompt):
                seed = seed_start + i
                sample = generate_sample(
                    model=model,
                    prompt=prompt,
                    strategy=strategy,
                    seed=seed
                )
                
                if sample["status"] == "success":
                    successful_count += 1
                else:
                    failed_count += 1
                
                all_samples.append(sample)
                
                # Log progress
                if len(all_samples) % 20 == 0:
                    logger.log("pipeline_progress", 
                               total=len(all_samples),
                               successful=successful_count,
                               failed=failed_count)
    
    # Save results
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_samples, f, indent=2, ensure_ascii=False)
    
    # Log final sample sizes per condition (T013 requirement)
    logger.log("sample_size_log", 
               total_samples=len(all_samples),
               successful=successful_count,
               failed=failed_count)
    
    for strategy in strategies:
        strategy_samples = [s for s in all_samples if s["strategy"] == strategy]
        strategy_success = [s for s in strategy_samples if s["status"] == "success"]
        logger.log("strategy_sample_size", 
                   strategy=strategy,
                   total=len(strategy_samples),
                   successful=len(strategy_success),
                   target=num_samples_per_prompt * len(prompts),
                   status="PASS" if len(strategy_success) >= num_samples_per_prompt * len(prompts) else "WARN")
    
    logger.log("pipeline_complete", 
               total=len(all_samples),
               successful=successful_count,
               failed=failed_count,
               output_path=str(output_path))
    
    return all_samples

def main() -> None:
    """Main entry point for generation runner."""
    logger.log("main_start")
    
    # Load model
    model = load_model()
    
    # Load prompts (assuming they are loaded from data/prompts/base_prompts.json by prompt_engineering.py)
    # For this runner, we'll use a placeholder list; in reality, this would be passed or loaded
    base_prompts = [
        "Describe your first-person experience of seeing a red apple.",
        "Describe your first-person experience of hearing a bird sing.",
        "Describe your first-person experience of feeling the sun on your skin."
    ]
    strategies = ["direct", "hypothetical", "comparative", "roleplay"]
    
    # Run pipeline
    run_generation_pipeline(
        model=model,
        prompts=base_prompts,
        strategies=strategies,
        num_samples_per_prompt=80,
        seed_start=42,
        output_path=OUTPUT_FILE
    )
    
    logger.log("main_complete")

if __name__ == "__main__":
    main()