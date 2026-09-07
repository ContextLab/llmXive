"""
Prompt-Based Cohort Generation (GPU Offload)

Implements T014b: Generate a small synthetic cohort of code snippets using natural language
prompts derived from commit messages. Uses a quantized CodeLlama-7B model with auto-offload.

Constraints:
- Timeout <= 30s per snippet
- Small sample size (limited to 5 snippets for feasibility)
- Output: data/processed/prompt_cohort.parquet (success) or data/processed/generation_failure_log.json (failure)
- NO synthetic fallback: if generation fails, log and exit with failure report.
"""
import os
import sys
import time
import signal
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer
from threading import Thread

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.config import get_config, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MODEL_NAME = "codellama/CodeLlama-7b-Instruct-hf"
TIMEOUT_SECONDS = 30
MAX_SNIPPETS = 5  # Small sample for feasibility test
OUTPUT_PARQUET = "data/processed/prompt_cohort.parquet"
FAILURE_LOG = "data/processed/generation_failure_log.json"

class TimeoutError(Exception):
    """Custom timeout exception for generation."""
    pass

def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError(f"Generation timed out after {TIMEOUT_SECONDS} seconds")

def create_prompt_from_commit_message(commit_message: str) -> str:
    """
    Create a code generation prompt from a commit message.
    Converts the commit message into a natural language instruction.
    """
    # Simple heuristic: use commit message as the core instruction
    # In a real scenario, this might involve more sophisticated NLP
    prompt = f"""<s>[INST] Write a Python function that implements the following: {commit_message}. 
    The code should be clean, well-documented, and follow PEP 8. [/INST]"""
    return prompt

def generate_snippet_with_timeout(prompt: str, model, tokenizer, timeout: int = TIMEOUT_SECONDS) -> Optional[str]:
    """
    Generate a code snippet with a strict timeout.
    Uses signal-based timeout for Unix-like systems.
    """
    # Set up timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)
    
    try:
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        
        # Use streaming for faster response and early termination
        streamer = TextIteratorStreamer(tokenizer, timeout=timeout, skip_prompt=True)
        
        generation_kwargs = dict(
            inputs,
            streamer=streamer,
            max_new_tokens=100,  # Limit output size
            temperature=0.7,
            do_sample=True,
        )
        
        # Run generation in a separate thread
        thread = Thread(target=model.generate, kwargs=generation_kwargs)
        thread.start()
        
        # Collect output
        generated_text = ""
        for new_text in streamer:
            generated_text += new_text
            # Early termination if we see end-of-sequence token
            if tokenizer.eos_token in new_text:
                break
        
        signal.alarm(0)  # Cancel alarm
        return generated_text.strip()
        
    except TimeoutError as e:
        signal.alarm(0)  # Cancel alarm
        logger.warning(f"Generation timed out: {e}")
        return None
    except Exception as e:
        signal.alarm(0)  # Cancel alarm
        logger.error(f"Generation failed with error: {e}")
        return None
    finally:
        # Reset signal handler
        signal.signal(signal.SIGALRM, signal.SIG_DFL)

def load_model_and_tokenizer() -> Tuple[Any, Any]:
    """
    Load the CodeLlama model with quantization and auto-offload.
    """
    logger.info(f"Loading model: {MODEL_NAME}")
    
    try:
        # Check for GPU availability
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {device}")
        
        if device == "cpu":
            logger.warning("No GPU detected. Generation will be very slow or may timeout.")
        
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            MODEL_NAME,
            trust_remote_code=True,
            use_fast=True
        )
        
        # Load model with quantization and auto-offload
        if device == "cuda":
            model = AutoModelForCausalLM.from_pretrained(
                MODEL_NAME,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True,
                load_in_8bit=True  # Quantize to save memory
            )
        else:
            model = AutoModelForCausalLM.from_pretrained(
                MODEL_NAME,
                torch_dtype=torch.float32,
                device_map="auto",
                trust_remote_code=True
            )
        
        logger.info("Model loaded successfully")
        return model, tokenizer
        
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def run_prompt_cohort_generation(
    commit_messages: List[str],
    model: Any,
    tokenizer: Any,
    max_snippets: int = MAX_SNIPPETS
) -> pd.DataFrame:
    """
    Generate code snippets from commit messages.
    Returns a DataFrame with generated snippets and metadata.
    """
    results = []
    failed_count = 0
    
    # Limit to max_snippets
    messages_to_process = commit_messages[:max_snippets]
    
    for i, commit_msg in enumerate(messages_to_process):
        logger.info(f"Generating snippet {i+1}/{len(messages_to_process)}")
        
        prompt = create_prompt_from_commit_message(commit_msg)
        start_time = time.time()
        
        snippet = generate_snippet_with_timeout(prompt, model, tokenizer)
        elapsed_time = time.time() - start_time
        
        if snippet:
            results.append({
                "snippet_id": f"prompt_{i:03d}",
                "source_prompt": prompt,
                "generated_code": snippet,
                "generation_time_seconds": elapsed_time,
                "status": "success"
            })
            logger.info(f"Generated snippet {i+1} in {elapsed_time:.2f}s")
        else:
            failed_count += 1
            results.append({
                "snippet_id": f"prompt_{i:03d}",
                "source_prompt": prompt,
                "generated_code": None,
                "generation_time_seconds": elapsed_time,
                "status": "failed",
                "failure_reason": "timeout_or_error"
            })
            logger.warning(f"Failed to generate snippet {i+1}")
    
    df = pd.DataFrame(results)
    logger.info(f"Generation complete: {len(results) - failed_count} succeeded, {failed_count} failed")
    return df

def create_spec_amendment_request(failure_count: int, total_count: int) -> Dict[str, Any]:
    """
    Create a spec amendment request if generation fails significantly.
    """
    if failure_count > 0:
        return {
            "type": "spec_amendment_request",
            "reason": "Prompt-based cohort generation failed",
            "details": {
                "failed_count": failure_count,
                "total_count": total_count,
                "success_rate": (total_count - failure_count) / total_count if total_count > 0 else 0
            },
            "recommendation": "Consider reducing sample size, increasing timeout, or using a more powerful GPU"
        }
    return {}

def main():
    """
    Main entry point for prompt-based cohort generation.
    """
    # Ensure output directories exist
    ensure_directories([OUTPUT_PARQUET, FAILURE_LOG])
    
    # Load configuration
    config = get_config()
    seed = config.get("seed", 42)
    logger.info(f"Using random seed: {seed}")
    
    # Set random seeds for reproducibility
    import numpy as np
    import random
    np.random.seed(seed)
    random.seed(seed)
    if torch.cuda.is_available():
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    
    # Sample commit messages for demonstration
    # In a real scenario, these would come from the GitHub scraper
    sample_commit_messages = [
        "Add user authentication with JWT tokens",
        "Implement data validation for API endpoints",
        "Create database migration for user profiles",
        "Optimize query performance for dashboard",
        "Add error handling for network requests",
        "Implement caching layer for frequently accessed data",
        "Create unit tests for payment processing",
        "Refactor legacy code to use async/await",
        "Add logging for critical system events",
        "Implement rate limiting for API calls"
    ]
    
    try:
        # Load model and tokenizer
        model, tokenizer = load_model_and_tokenizer()
        
        # Generate cohort
        cohort_df = run_prompt_cohort_generation(
            sample_commit_messages,
            model,
            tokenizer,
            max_snippets=MAX_SNIPPETS
        )
        
        # Check if any generation succeeded
        success_count = (cohort_df["status"] == "success").sum()
        failure_count = (cohort_df["status"] == "failed").sum()
        
        if success_count == 0:
            # All generations failed - create failure log
            failure_log = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_snippets": len(cohort_df),
                "successful": 0,
                "failed": failure_count,
                "failure_reasons": cohort_df[cohort_df["status"] == "failed"]["failure_reason"].tolist(),
                "model": MODEL_NAME,
                "timeout_seconds": TIMEOUT_SECONDS,
                "spec_amendment": create_spec_amendment_request(failure_count, len(cohort_df))
            }
            
            with open(FAILURE_LOG, 'w') as f:
                json.dump(failure_log, f, indent=2)
            
            logger.error(f"All {failure_count} generations failed. Failure log written to {FAILURE_LOG}")
            sys.exit(1)
        
        # Save successful generations
        successful_df = cohort_df[cohort_df["status"] == "success"].copy()
        successful_df.to_parquet(OUTPUT_PARQUET, index=False)
        
        logger.info(f"Successfully generated {success_count} snippets. Output saved to {OUTPUT_PARQUET}")
        
        # Log summary
        logger.info(f"Generation summary:")
        logger.info(f"  Total requested: {len(sample_commit_messages)}")
        logger.info(f"  Processed: {len(cohort_df)}")
        logger.info(f"  Successful: {success_count}")
        logger.info(f"  Failed: {failure_count}")
        logger.info(f"  Success rate: {success_count/len(cohort_df)*100:.1f}%")
        
    except Exception as e:
        logger.error(f"Fatal error in generation pipeline: {e}")
        # Create failure log
        failure_log = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "error": str(e),
            "model": MODEL_NAME,
            "timeout_seconds": TIMEOUT_SECONDS,
            "spec_amendment": {
                "type": "spec_amendment_request",
                "reason": "Fatal error during generation",
                "details": {"error": str(e)},
                "recommendation": "Check system resources and model compatibility"
            }
        }
        
        with open(FAILURE_LOG, 'w') as f:
            json.dump(failure_log, f, indent=2)
        
        sys.exit(1)

if __name__ == "__main__":
    main()
