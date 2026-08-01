import json
import logging
import sys
import re
import time
import os
import random
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Import from local utils
from utils.config import set_seed, ensure_dirs_exist, get_config_summary
from utils.env_loader import load_env_vars, get_model_path, validate_token, ensure_required_vars

# Configure logging
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Constants
MAX_TOKENS = 200
TIMEOUT = 300
MIN_SNIPPETS = 20
FALLBACK_THRESHOLD = 0.20  # 20%

# Setup logging for the module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    logger.addHandler(ch)

def ensure_dirs():
    """Ensure required directories exist."""
    dirs = [
        "data/raw",
        "data/intermediate",
        "data/processed",
        "figures"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    logger.info("Ensured directories exist.")

def get_memory_usage_gb():
    """Get current memory usage in GB (approximate)."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem = process.memory_info().rss / (1024 ** 3)
        return mem
    except ImportError:
        logger.warning("psutil not found. Memory usage estimation skipped.")
        return 0.0

def fetch_code_search_net():
    """Fetch Python subset from CodeSearchNet via streaming."""
    try:
        from datasets import load_dataset
        logger.info("Fetching CodeSearchNet dataset (streaming)...")
        dataset = load_dataset("codeparrot/code-search-net", "python", streaming=True)
        return dataset
    except Exception as e:
        logger.error(f"Failed to fetch CodeSearchNet: {e}")
        raise RuntimeError(f"Data fetch failed: {e}")

def calculate_cyclomatic_complexity(code: str) -> float:
    """Calculate raw cyclomatic complexity using radon."""
    try:
        from radon.complexity import cc_visit
        results = cc_visit(code)
        if not results:
            return 1.0
        # Return max complexity found in the snippet
        return max(r.complexity for r in results)
    except ImportError:
        logger.warning("radon not installed. Defaulting complexity to 1.0.")
        return 1.0
    except Exception as e:
        logger.warning(f"Radon error for snippet: {e}")
        return 1.0

def label_complexity(score: float) -> str:
    """Label complexity based on score ranges."""
    if score < 5:
        return "low"
    elif score <= 10:
        return "medium"
    else:
        return "high"

def calculate_cyclomatic_complexity_wrapper(snippet: Dict[str, Any]) -> Dict[str, Any]:
    """Wrapper to calculate complexity and label for a snippet."""
    code = snippet.get("code", "")
    raw_score = calculate_cyclomatic_complexity(code)
    label = label_complexity(raw_score)
    return {
        **snippet,
        "complexity_score": raw_score,
        "complexity": label
    }

def label_complexity_wrapper(snippet: Dict[str, Any]) -> Dict[str, Any]:
    """Wrapper to label complexity (assumes score already present)."""
    score = snippet.get("complexity_score", 1.0)
    label = label_complexity(score)
    snippet["complexity"] = label
    return snippet

def process_complexity(dataset_iter):
    """Process dataset iterator to add complexity metrics."""
    processed = []
    count = 0
    for item in dataset_iter:
        processed.append(calculate_cyclomatic_complexity_wrapper(item))
        count += 1
        if count % 100 == 0:
            logger.info(f"Processed {count} snippets.")
    return processed

def save_snippets(snippets: List[Dict[str, Any]], path: str):
    """Save snippets to JSON."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(snippets, f, indent=2)
    logger.info(f"Saved {len(snippets)} snippets to {path}")

def generate_explanation(code: str, model_name: str, tokenizer, model, max_tokens: int = MAX_TOKENS) -> Tuple[str, int, bool]:
    """
    Generate explanation for a code snippet.
    Returns: (explanation_text, token_count, success)
    """
    prompt = f"Explain the following Python code:\n{code}\nExplanation:"
    
    try:
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
        
        # Check memory before generation
        mem_gb = get_memory_usage_gb()
        if mem_gb > 7.0:
            logger.warning(f"Memory usage high ({mem_gb:.2f}GB). Attempting generation anyway.")
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id
            )
        
        generated_text = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        token_count = len(tokenizer(generated_text).input_ids)
        
        if token_count > max_tokens:
            generated_text = generated_text[:max_tokens] # Truncate if needed
            token_count = max_tokens
        
        return generated_text.strip(), token_count, True
        
    except Exception as e:
        logger.error(f"Generation failed for snippet: {e}")
        return "", 0, False

def main():
    """Main entry point for data curation and explanation generation."""
    set_seed(42)
    ensure_dirs()
    ensure_required_vars()
    
    # Load dataset
    dataset = fetch_code_search_net()
    snippets = process_complexity(dataset)
    
    # Filter for valid Python code
    valid_snippets = [s for s in snippets if s.get("code") and len(s["code"]) > 20]
    
    # Save raw snippets for reference
    raw_path = "data/intermediate/raw_snippets.json"
    save_snippets(valid_snippets, raw_path)
    
    # Setup logging for generation
    gen_log_path = "data/intermediate/generation.log"
    file_handler = logging.FileHandler(gen_log_path, mode='w')
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)
    
    logger.info("Starting explanation generation...")
    
    explanations = []
    tinyllama_success_count = 0
    fallback_triggered = False
    fallback_count = 0
    
    # Try TinyLlama first
    tinyllama_model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    codellama_model_name = "codellama/CodeLlama-7b-Instruct-hf"
    
    model = None
    tokenizer = None
    model_name_used = "TinyLlama"
    
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        import torch
        
        logger.info(f"Loading {tinyllama_model_name}...")
        tokenizer = AutoTokenizer.from_pretrained(tinyllama_model_name, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            tinyllama_model_name,
            torch_dtype=torch.float32,
            device_map="cpu",
            trust_remote_code=True
        )
        logger.info("TinyLlama loaded successfully.")
        
    except Exception as e:
        logger.error(f"Failed to load TinyLlama: {e}")
        logger.warning("Attempting fallback to CodeLlama-7b (4-bit)...")
        fallback_triggered = True
        fallback_count += 1
        model_name_used = "CodeLlama"
        
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch
            from transformers import BitsAndBytesConfig
            
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16
            )
            
            tokenizer = AutoTokenizer.from_pretrained(codellama_model_name, trust_remote_code=True)
            model = AutoModelForCausalLM.from_pretrained(
                codellama_model_name,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True
            )
            logger.info("CodeLlama loaded successfully (fallback).")
            
        except Exception as e2:
            logger.critical(f"Failed to load CodeLlama fallback: {e2}")
            raise RuntimeError("Both models failed to load.")
    
    # Generate explanations
    skipped_snippets = []
    
    for i, snippet in enumerate(valid_snippets):
        snippet_id = snippet.get("snippet_id", f"snippet_{i}")
        code = snippet.get("code", "")
        
        if not code:
            skipped_snippets.append({
                "snippet_id": snippet_id,
                "reason": "Empty code"
            })
            logger.warning(f"[SKIPPED] {snippet_id}: Empty code")
            continue
        
        logger.info(f"Processing {snippet_id}...")
        
        explanation, token_count, success = generate_explanation(code, model_name_used, tokenizer, model)
        
        if success:
            explanations.append({
                "snippet_id": snippet_id,
                "code": code,
                "complexity": snippet["complexity"],
                "complexity_score": snippet["complexity_score"],
                "explanation": explanation,
                "token_count": token_count,
                "model_used": model_name_used,
                "status": "success"
            })
            if model_name_used == "TinyLlama":
                tinyllama_success_count += 1
            logger.info(f"[SUCCESS] {snippet_id}: {token_count} tokens")
        else:
            skipped_snippets.append({
                "snippet_id": snippet_id,
                "reason": "Generation failed"
            })
            logger.error(f"[SKIPPED] {snippet_id}: Generation failed")
    
    # Log skipped snippets and fallback triggers
    logger.info(f"Total snippets processed: {len(valid_snippets)}")
    logger.info(f"Successful explanations: {len(explanations)}")
    logger.info(f"Skipped snippets: {len(skipped_snippets)}")
    if fallback_triggered:
        logger.warning(f"FALLBACK TRIGGERED: Switched to {model_name_used}")
    
    # Check fallback threshold
    if fallback_triggered:
        total_attempts = len(valid_snippets)
        if total_attempts > 0 and (fallback_count / total_attempts) > FALLBACK_THRESHOLD:
            logger.critical(f"Fallback threshold exceeded ({fallback_count}/{total_attempts} > {FALLBACK_THRESHOLD})")
            raise RuntimeError("Fallback threshold exceeded. Pipeline halted.")
    
    # Save results
    output_path = "data/intermediate/explanations.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(explanations, f, indent=2)
    
    logger.info(f"Saved {len(explanations)} explanations to {output_path}")
    logger.info("Data curation and explanation generation complete.")

if __name__ == "__main__":
    main()