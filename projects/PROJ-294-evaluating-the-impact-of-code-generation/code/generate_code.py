"""
Generate code samples using Salesforce/codegen-350M-mono.

Loads the model on CPU and generates code for all tasks in HumanEval.
Implements retry logic with exponential backoff as mandated by FR-002.

Output: data/generated/codegen_samples.json
Dependency: T010 (HumanEval dataset)
"""
import os
import json
import logging
import time
import sys
from typing import List, Dict, Any, Optional

# Import utilities from utils
try:
    from utils import setup_logging, get_logger, set_task_id, get_task_id
except ImportError:
    # Fallback for direct execution
    def setup_logging(task_id=None):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        return logging.getLogger(__name__)
    
    def get_logger(name):
        return logging.getLogger(name)
    
    def set_task_id(tid):
        pass
    
    def get_task_id():
        return None

TASK_ID = "T012"
MODEL_NAME = "Salesforce/codegen-350M-mono"
OUTPUT_PATH = "data/generated/codegen_samples.json"
INPUT_PATH = "data/raw/humaneval.parquet"
MAX_RETRIES = 3
BASE_DELAY = 2

def set_task_id(tid):
    """Set the global task ID."""
    global _task_id
    _task_id = tid

def get_task_id():
    """Get the current global task ID."""
    return _task_id

def setup_logging(task_id: Optional[str] = None):
    """
    Setup logging with optional task_id.
    
    Args:
        task_id: Optional task ID
    """
    if task_id:
        set_task_id(task_id)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(task_id)s - %(levelname)s - %(message)s')
    return logging.getLogger(__name__)

def get_logger(name: str):
    """Get a logger by name."""
    return logging.getLogger(name)

def log_info(logger, message: str):
    """Log an info message."""
    logger.info(message)

def log_error(logger, message: str):
    """Log an error message."""
    logger.error(message)

def ensure_state_dir():
    """Ensure the state directory exists."""
    state_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "state")
    os.makedirs(state_dir, exist_ok=True)
    return state_dir

def ensure_log_dir():
    """Ensure the log directory exists."""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir

def mark_sample_missing(task_id: str, reason: str, samples: List[Dict]):
    """Mark a sample as missing due to generation failure."""
    samples.append({
        "task_id": task_id,
        "prompt": "",
        "generated_code": None,
        "source_type": "codegen_350M",
        "model_name": MODEL_NAME,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "success": False,
        "error": reason
    })

def check_local_model_availability(model_name: str) -> bool:
    """Check if the model is available locally."""
    # For this implementation, we assume the model can be loaded from HuggingFace
    # In a real scenario, this would check local cache
    return True

def write_model_availability_status(model_name: str, available: bool):
    """Write model availability status to a file."""
    status_dir = ensure_state_dir()
    status_file = os.path.join(status_dir, "model_availability.json")
    
    status = {
        "model_name": model_name,
        "available": available,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(status_file, "w") as f:
        json.dump(status, f, indent=2)

def generate_code_via_hf_api(prompt: str, model_name: str) -> Optional[str]:
    """
    Generate code using HuggingFace API (fallback).
    
    Args:
        prompt: Task prompt
        model_name: Model name
        
    Returns:
        Generated code or None
    """
    # This is a placeholder for API-based generation
    # In practice, we would use the transformers library directly
    return None

def generate_code_for_task(task_prompt: str, model, tokenizer, max_new_tokens: int = 512) -> Optional[str]:
    """
    Generate code for a single task prompt.
    
    Args:
        task_prompt: Task prompt
        model: Loaded model
        tokenizer: Loaded tokenizer
        max_new_tokens: Maximum tokens to generate
        
    Returns:
        Generated code or None
    """
    try:
        inputs = tokenizer(task_prompt, return_tensors="pt")
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=0.8,
                top_p=0.95,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id
            )
        
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract code if present
        if "```python" in generated_text:
            start_idx = generated_text.find("```python") + len("```python")
            end_idx = generated_text.find("```", start_idx)
            if end_idx != -1:
                return generated_text[start_idx:end_idx].strip()
        
        return generated_text.strip()
    except Exception as e:
        logging.error(f"Generation failed: {e}")
        return None

def generate_code_batch(tasks: List[Dict], model, tokenizer) -> List[Dict]:
    """
    Generate code for a batch of tasks.
    
    Args:
        tasks: List of task dictionaries
        model: Loaded model
        tokenizer: Loaded tokenizer
        
    Returns:
        List of generated samples
    """
    samples = []
    errors_log = []
    
    for task in tasks:
        task_id = task["task_id"]
        prompt = task["prompt"]
        
        logging.info(f"Generating code for {task_id}")
        
        # Retry logic with exponential backoff
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                generated_code = generate_code_for_task(prompt, model, tokenizer)
                
                if generated_code:
                    sample = {
                        "task_id": task_id,
                        "prompt": prompt,
                        "generated_code": generated_code,
                        "source_type": "codegen_350M",
                        "model_name": MODEL_NAME,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "success": True
                    }
                    samples.append(sample)
                    break
                else:
                    raise RuntimeError("Generated code is empty")
                    
            except Exception as e:
                error_msg = f"Attempt {attempt} failed for {task_id}: {e}"
                logging.warning(error_msg)
                errors_log.append(error_msg)
                
                if attempt < MAX_RETRIES:
                    delay = BASE_DELAY * (2 ** (attempt - 1))
                    logging.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    # Mark as missing after max retries
                    mark_sample_missing(task_id, str(e), samples)
                    errors_log.append(f"Max retries exceeded for {task_id}")
    
    return samples, errors_log

def main():
    """Main entry point for code generation."""
    logger = setup_logging(task_id=TASK_ID)
    set_task_id(TASK_ID)
    
    logging.info(f"Starting CodeGen-350M code generation (Task: {TASK_ID})")
    
    # Ensure output directory exists
    output_dir = os.path.dirname(OUTPUT_PATH)
    os.makedirs(output_dir, exist_ok=True)
    
    # Load model
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        
        logging.info(f"Loading model: {MODEL_NAME}")
        
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            torch_dtype=torch.float32,
            device_map="cpu"
        )
        
        logging.info("Model loaded successfully.")
    except Exception as e:
        logging.error(f"Failed to load model: {e}")
        sys.exit(1)
    
    # Load HumanEval dataset
    try:
        from datasets import load_dataset
        import pandas as pd
        
        if os.path.exists(INPUT_PATH):
            ds = load_dataset("parquet", data_files={"test": INPUT_PATH}, split="test")
        else:
            logging.warning(f"Local file {INPUT_PATH} not found. Downloading from HuggingFace.")
            ds = load_dataset("openai/openai_humaneval", split="test")
        
        logging.info(f"Loaded {len(ds)} tasks from HumanEval dataset.")
    except Exception as e:
        logging.error(f"Failed to load HumanEval dataset: {e}")
        sys.exit(1)
    
    # Generate code
    samples, errors = generate_code_batch(ds, model, tokenizer)
    
    # Save results
    logging.info(f"Saving {len(samples)} samples to {OUTPUT_PATH}")
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(samples, f, indent=2, ensure_ascii=False)
    
    # Log errors
    if errors:
        error_log_path = os.path.join(ensure_log_dir(), "generation_errors.log")
        with open(error_log_path, "w") as f:
            f.write("\n".join(errors))
        logging.warning(f"Logged {len(errors)} errors to {error_log_path}")
    
    success_count = sum(1 for s in samples if s["success"])
    logging.info(f"Generation complete: {success_count}/{len(samples)} tasks succeeded")
    logging.info(f"Code generation completed successfully (Task: {TASK_ID})")

if __name__ == "__main__":
    main()
