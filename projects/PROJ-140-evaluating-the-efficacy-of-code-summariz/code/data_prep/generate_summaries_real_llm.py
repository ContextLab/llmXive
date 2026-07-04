"""
Real LLM generation script for code summarization.

Uses HuggingFace `codellama/CodeLlama-7b-hf` with 8-bit quantization.
Designed for non-CI environments with GPU/CUDA availability.

Falls back to rule-based summaries if generation fails (timeout, empty output).

Output: data/summaries/real_llm_summaries.csv
"""
import os
import sys
import csv
import time
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_utils import setup_logging, get_logger
from utils.config_manager import get_config
from data_prep.generate_summaries import generate_rule_summary, load_stratified_methods

# Configure logging
logger = get_logger("generate_summaries_real_llm")

# Constants
MODEL_NAME = "codellama/CodeLlama-7b-hf"
MAX_NEW_TOKENS = 128
TIMEOUT_SECONDS = 300  # 5 minutes per generation
OUTPUT_PATH = project_root / "data" / "summaries" / "real_llm_summaries.csv"
FALLBACK_PATH = project_root / "data" / "summaries" / "rule_fallback_log.json"

def load_model():
    """
    Load the CodeLlama model with 8-bit quantization.
    Returns None if GPU is unavailable or model loading fails.
    """
    try:
        logger.info(f"Attempting to load {MODEL_NAME} with 8-bit quantization...")
        
        # Check for CUDA availability
        import torch
        if not torch.cuda.is_available():
            logger.warning("CUDA not available. Real LLM generation requires GPU. Falling back to rule-based.")
            return None, None
        
        from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
        
        # Configure 8-bit quantization
        bnb_config = BitsAndBytesConfig(
            load_in_8bit=True,
            llm_int8_threshold=6.0,
            llm_int8_has_fp16_weight=False,
        )
        
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
        
        # Set pad token if not set
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
            torch_dtype=torch.float16
        )
        
        logger.info("Model loaded successfully.")
        return model, tokenizer
        
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return None, None

def generate_llm_summary(model, tokenizer, method_data: Dict[str, Any]) -> Optional[str]:
    """
    Generate a summary using the real LLM.
    
    Args:
        model: The loaded model
        tokenizer: The loaded tokenizer
        method_data: Dictionary containing method details (name, params, return_type, code, comments)
        
    Returns:
        Generated summary string or None if generation fails
    """
    if model is None or tokenizer is None:
        return None
    
    try:
        # Construct prompt
        method_name = method_data.get("name", "unknown")
        params = method_data.get("params", [])
        return_type = method_data.get("return_type", "void")
        comments = method_data.get("comments", [])
        code_snippet = method_data.get("code", "")
        
        prompt = f"""
        You are a code summarization assistant. Provide a concise, natural language summary of the following method.
        
        Method Name: {method_name}
        Parameters: {', '.join(params) if params else 'No parameters'}
        Return Type: {return_type}
        
        Code:
        ```python
        {code_snippet}
        ```
        
        Existing Comments:
        {chr(10).join(comments) if comments else 'No existing comments.'}
        
        Summary:
        """
        
        # Tokenize
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        
        # Generate with timeout
        start_time = time.time()
        
        # Use a simple timeout mechanism
        import threading
        result = [None]
        error = [None]
        
        def generate_thread():
            try:
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=MAX_NEW_TOKENS,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id,
                    eos_token_id=tokenizer.eos_token_id
                )
                generated_ids = outputs[0][inputs['input_ids'].shape[1]:]
                result[0] = tokenizer.decode(generated_ids, skip_special_tokens=True)
            except Exception as e:
                error[0] = e
        
        thread = threading.Thread(target=generate_thread)
        thread.daemon = True
        thread.start()
        thread.join(timeout=TIMEOUT_SECONDS)
        
        if thread.is_alive():
            logger.warning(f"Generation timed out after {TIMEOUT_SECONDS} seconds for method {method_name}")
            return None
        
        if error[0]:
            logger.error(f"Generation error for {method_name}: {error[0]}")
            return None
        
        summary = result[0]
        
        # Clean up summary
        if summary:
            # Remove prompt repetition if any
            summary = summary.strip()
            if prompt.strip() in summary:
                summary = summary.replace(prompt.strip(), "").strip()
            
            # Basic validation
            if len(summary) < 5 or summary.lower() in ["no summary", "n/a", ""]:
                logger.warning(f"Generated summary too short or empty for {method_name}")
                return None
            
            return summary
        
        return None
      
    except Exception as e:
        logger.error(f"Unexpected error during generation for {method_data.get('name', 'unknown')}: {e}")
        return None

def save_summaries(summaries: List[Dict[str, Any]], fallback_log: List[Dict[str, Any]]):
    """
    Save summaries to CSV and log fallbacks to JSON.
    """
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Save main summaries
    with open(OUTPUT_PATH, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['method_id', 'method_name', 'summary', 'source', 'generation_time_ms']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summaries)
    
    logger.info(f"Saved {len(summaries)} summaries to {OUTPUT_PATH}")
    
    # Save fallback log
    FALLBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(FALLBACK_PATH, 'w', encoding='utf-8') as f:
        json.dump(fallback_log, f, indent=2)
    
    logger.info(f"Logged {len(fallback_log)} fallbacks to {FALLBACK_PATH}")

def main():
    """
    Main entry point for real LLM summary generation.
    """
    logger.info("Starting real LLM summary generation (T014a)")
    
    # Load stratified methods
    methods = load_stratified_methods()
    if not methods:
        logger.error("No methods found. Run T013 first.")
        return
    
    logger.info(f"Loaded {len(methods)} methods for summarization")
    
    # Load model
    model, tokenizer = load_model()
    
    summaries = []
    fallback_log = []
    
    for i, method in enumerate(methods):
        method_id = method.get("id", f"method_{i}")
        method_name = method.get("name", "unknown")
        
        logger.info(f"Processing {i+1}/{len(methods)}: {method_name}")
        
        start_time = time.time()
        
        # Try real LLM generation
        summary = None
        if model and tokenizer:
            summary = generate_llm_summary(model, tokenizer, method)
        
        # Fallback to rule-based if LLM failed
        if not summary:
            logger.info(f"LLM generation failed or skipped for {method_name}. Using rule-based fallback.")
            summary = generate_rule_summary(method)
            fallback_entry = {
                "method_id": method_id,
                "method_name": method_name,
                "reason": "llm_failed_or_unavailable" if not model else "llm_generation_failed",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            fallback_log.append(fallback_entry)
        
        generation_time = int((time.time() - start_time) * 1000)
        
        summaries.append({
            "method_id": method_id,
            "method_name": method_name,
            "summary": summary,
            "source": "real_llm" if model and not any(f["method_id"] == method_id for f in fallback_log) else "rule_fallback",
            "generation_time_ms": generation_time
        })
    
    # Save results
    save_summaries(summaries, fallback_log)
    
    logger.info("Real LLM summary generation completed.")

if __name__ == "__main__":
    main()
