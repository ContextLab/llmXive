import json
import logging
import sys
import re
import time
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Import utilities from sibling modules as per API surface
from utils.config import set_seed, ensure_dirs_exist
from utils.env_loader import load_env_vars
from utils.metrics import parse_latency_to_ms
import curation_utils
from datasets import load_dataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/intermediate/curation.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
MAX_TOKENS = 200
TIMEOUT_SECONDS = 300
MEMORY_THRESHOLD_GB = 7.0

def ensure_dirs():
    """Ensure required directories exist."""
    ensure_dirs_exist()

def get_memory_usage_gb():
    """Get current memory usage in GB."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 ** 3)
    except ImportError:
        logger.warning("psutil not installed, skipping memory check")
        return 0.0

def fetch_code_search_net():
    """Fetch Python subset from CodeSearchNet dataset with streaming."""
    logger.info("Fetching CodeSearchNet Python subset...")
    try:
        dataset = load_dataset(
            "codeparrot/code-search-net",
            split="train",
            streaming=True,
            trust_remote_code=True
        )
        # Filter for Python code
        python_dataset = dataset.filter(lambda x: x["language"] == "python")
        logger.info("Successfully loaded CodeSearchNet Python subset")
        return python_dataset
    except Exception as e:
        logger.error(f"Failed to load CodeSearchNet: {e}")
        raise

def calculate_cyclomatic_complexity_wrapper(code: str) -> float:
    """Wrapper for cyclomatic complexity calculation."""
    return curation_utils.calculate_cyclomatic_complexity(code)

def label_complexity_wrapper(score: float) -> str:
    """Wrapper for complexity labeling."""
    return curation_utils.label_complexity(score)

def process_complexity(snippet: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single snippet to calculate complexity metrics."""
    code = snippet.get("code", "")
    if not code:
        return None

    raw_score = calculate_cyclomatic_complexity_wrapper(code)
    label = label_complexity_wrapper(raw_score)

    return {
        "snippet_id": snippet.get("repo", "") + "/" + snippet.get("path", ""),
        "code": code,
        "complexity": label,
        "complexity_score": raw_score
    }

def save_snippets(snippets: List[Dict[str, Any]], output_path: str):
    """Save processed snippets to JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(snippets, f, indent=2)
    logger.info(f"Saved {len(snippets)} snippets to {output_path}")

def generate_explanation(code: str, complexity: str, model_name: str = "codellama") -> Tuple[Optional[str], int, str]:
    """
    Generate LLM explanation for code snippet.
    
    Returns:
        Tuple of (explanation_text, token_count, model_used)
    """
    logger.info(f"Generating explanation for {complexity} complexity code using {model_name}")
    
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        import torch
        
        # Configure quantization for 4-bit loading
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16
        )
        
        # Try to load CodeLlama-7B first
        if model_name == "codellama":
            model_id = "codellama/CodeLlama-7b-hf"
            logger.info(f"Attempting to load {model_id}...")
            
            try:
                tokenizer = AutoTokenizer.from_pretrained(model_id)
                model = AutoModelForCausalLM.from_pretrained(
                    model_id,
                    quantization_config=bnb_config,
                    device_map="auto",
                    torch_dtype=torch.float16,
                    trust_remote_code=True
                )
                logger.info("Successfully loaded CodeLlama-7B")
            except (OutOfMemoryError, RuntimeError) as e:
                logger.warning(f"CodeLlama-7B failed: {e}. Falling back to TinyLlama.")
                model_name = "tinyllama"
            except Exception as e:
                logger.warning(f"CodeLlama-7B failed unexpectedly: {e}. Falling back to TinyLlama.")
                model_name = "tinyllama"
        
        # Fallback to TinyLlama
        if model_name == "tinyllama":
            model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
            logger.info(f"Loading fallback model: {model_id}")
            
            try:
                tokenizer = AutoTokenizer.from_pretrained(model_id)
                model = AutoModelForCausalLM.from_pretrained(
                    model_id,
                    device_map="auto",
                    torch_dtype=torch.float16,
                    trust_remote_code=True
                )
                logger.info("Successfully loaded TinyLlama")
            except Exception as e:
                logger.error(f"Failed to load TinyLlama: {e}")
                return None, 0, "failed"
        
        # Prepare prompt
        prompt = f"Explain the following Python code snippet concisely (max {MAX_TOKENS} tokens):\n\n{code}"
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        
        # Generate with token limit
        start_time = time.time()
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=MAX_TOKENS,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        elapsed = time.time() - start_time
        if elapsed > TIMEOUT_SECONDS:
            logger.warning(f"Generation timeout ({elapsed}s > {TIMEOUT_SECONDS}s)")
            return None, 0, model_name
        
        # Decode and clean
        generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
        explanation = generated.split(prompt)[-1].strip()
        
        # Count tokens
        token_count = len(tokenizer.encode(explanation))
        
        if token_count > MAX_TOKENS:
            logger.warning(f"Explanation exceeded token limit: {token_count} > {MAX_TOKENS}")
            # Truncate to MAX_TOKENS
            truncated_tokens = tokenizer.encode(explanation)[:MAX_TOKENS]
            explanation = tokenizer.decode(truncated_tokens)
            token_count = len(truncated_tokens)
        
        logger.info(f"Generated explanation with {token_count} tokens using {model_name}")
        return explanation, token_count, model_name
        
    except Exception as e:
        logger.error(f"Explanation generation failed: {e}")
        return None, 0, "failed"

def main():
    """Main entry point for data curation pipeline."""
    logger.info("Starting data curation pipeline...")
    
    # Setup
    set_seed(42)
    ensure_dirs()
    load_env_vars()
    
    # Fetch dataset
    dataset = fetch_code_search_net()
    
    # Process snippets
    snippets = []
    explanations_data = []
    skipped_count = 0
    fallback_count = 0
    failed_count = 0
    
    logger.info("Processing snippets...")
    for idx, snippet in enumerate(dataset):
        if idx >= 100:  # Limit for demo purposes
            break
            
        processed = process_complexity(snippet)
        if not processed:
            skipped_count += 1
            logger.debug(f"Skipped snippet {idx}: invalid code")
            continue
        
        # Generate explanation
        explanation, token_count, model_used = generate_explanation(
            processed["code"], 
            processed["complexity"],
            "codellama"
        )
        
        if explanation is None:
            failed_count += 1
            logger.warning(f"Failed to generate explanation for snippet {idx}")
            continue
        
        # Track fallback usage
        if model_used == "tinyllama":
            fallback_count += 1
            logger.info(f"Fallback to TinyLlama triggered for snippet {idx}")
        
        # Add to explanations data
        explanation_record = {
            "snippet_id": processed["snippet_id"],
            "code": processed["code"],
            "complexity": processed["complexity"],
            "complexity_score": processed["complexity_score"],
            "explanation": explanation,
            "token_count": token_count,
            "model_used": model_used,
            "status": "success"
        }
        explanations_data.append(explanation_record)
        
        snippets.append(processed)
        
        if idx % 10 == 0:
            logger.info(f"Processed {idx} snippets...")
    
    # Save outputs
    save_snippets(snippets, "data/intermediate/snippets.json")
    
    with open("data/intermediate/explanations.json", "w", encoding="utf-8") as f:
        json.dump(explanations_data, f, indent=2)
    
    # Log summary statistics including skipped and fallback counts
    logger.info("=" * 50)
    logger.info("CURATION PIPELINE SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Total snippets processed: {len(snippets)}")
    logger.info(f"Skipped snippets (invalid code): {skipped_count}")
    logger.info(f"Failed explanations: {failed_count}")
    logger.info(f"Fallback triggers (TinyLlama): {fallback_count}")
    logger.info(f"Success rate: {len(snippets) / (len(snippets) + skipped_count + failed_count) * 100:.2f}%")
    logger.info("=" * 50)
    
    # Write skipped/fallback log
    with open("data/intermediate/skipped_fallback_log.txt", "w", encoding="utf-8") as f:
        f.write("Skipped Snippets Log\n")
        f.write("=" * 40 + "\n")
        f.write(f"Total skipped: {skipped_count}\n")
        f.write(f"Total fallbacks: {fallback_count}\n")
        f.write(f"Total failures: {failed_count}\n")
        f.write("\nFallback Triggers:\n")
        for i, exp in enumerate(explanations_data):
            if exp["model_used"] == "tinyllama":
                f.write(f"  Snippet {i}: {exp['snippet_id']} -> TinyLlama\n")
    
    logger.info("Data curation pipeline completed successfully")
    return explanations_data

if __name__ == "__main__":
    main()