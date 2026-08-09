import os
import json
import logging
import time
import sys
from typing import List, Dict, Any, Optional
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from datasets import load_dataset
from datetime import datetime
import threading

# Task ID tracking (shared state for logging)
_task_id = None
_logger = None

def set_task_id(tid: str) -> None:
    global _task_id
    _task_id = tid

def get_task_id() -> Optional[str]:
    return _task_id

def get_logger() -> Optional[logging.Logger]:
    return _logger

def log_info(msg: str) -> None:
    if _logger:
        _logger.info(msg)
    else:
        print(f"[INFO] {msg}")

def log_error(msg: str) -> None:
    if _logger:
        _logger.error(msg)
    else:
        print(f"[ERROR] {msg}")

def ensure_state_dir() -> None:
    state_dir = os.path.join("projects", "PROJ-294-evaluating-the-impact-of-code-generation", "state")
    os.makedirs(state_dir, exist_ok=True)

def ensure_log_dir() -> None:
    log_dir = os.path.join("projects", "PROJ-294-evaluating-the-impact-of-code-generation", "state", "logs")
    os.makedirs(log_dir, exist_ok=True)

def setup_logging(task_id: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Flexible logging setup compatible with all callers:
    - setup_logging()
    - setup_logging(task_id="T012")
    - setup_logging(task_id=TASK_ID)
    - setup_logging(level=logging.INFO)
    """
    global _logger, _task_id
    if task_id is not None:
        _task_id = task_id
    elif level is not None and isinstance(level, str):
        # Handle case where caller passed task_id as first positional arg but named it level by mistake?
        # Based on call sites, level is usually passed as keyword or not at all.
        pass

    logger_name = f"GEN-CODE-{_task_id}" if _task_id else "GEN-CODE"
    _logger = logging.getLogger(logger_name)
    _logger.setLevel(level)

    if not _logger.handlers:
        ensure_log_dir()
        log_file = os.path.join("projects", "PROJ-294-evaluating-the-impact-of-code-generation", "state", "logs", f"{logger_name}.log")
        
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s - %(message)s')
        fh.setFormatter(formatter)
        _logger.addHandler(fh)

        # Also print to stdout for immediate feedback
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        ch.setFormatter(formatter)
        _logger.addHandler(ch)

    return _logger

def mark_sample_missing(task_id: str, reason: str) -> Dict[str, Any]:
    return {
        "task_id": task_id,
        "source_type": "codegen_350m",
        "generated_code": None,
        "error": reason,
        "timestamp": datetime.now().isoformat()
    }

def check_local_model_availability(model_name: str) -> bool:
    """Check if model can be loaded (basic check)."""
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        return True
    except Exception:
        return False

def write_model_availability_status(model_name: str, available: bool) -> None:
    ensure_state_dir()
    status_file = os.path.join("projects", "PROJ-294-evaluating-the-impact-of-code-generation", "state", "model_availability.json")
    status = {
        "model": model_name,
        "available": available,
        "timestamp": datetime.now().isoformat()
    }
    with open(status_file, 'w') as f:
        json.dump(status, f, indent=2)

def generate_code_via_hf_api(prompt: str, model_name: str, max_tokens: int = 1024, temperature: float = 0.0) -> Optional[str]:
    """
    Fallback generation via HuggingFace API if local model fails.
    Note: This is a placeholder for the actual API call logic if needed.
    For this task, we prioritize local generation.
    """
    log_info(f"Attempting API generation for {model_name} (not implemented for local run)")
    return None

def generate_code_for_task(
    task: Dict[str, Any],
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    device: str
) -> Optional[str]:
    """Generate code for a single HumanEval task."""
    prompt = task["prompt"]
    task_id = task["task_id"]
    
    # Format prompt for CodeGen
    # CodeGen expects specific formatting, usually just the prompt
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    
    try:
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=1024,
                do_sample=False, # Temperature 0.0 equivalent
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id
            )
        
        generated_ids = outputs[0][inputs['input_ids'].shape[1]:]
        generated_text = tokenizer.decode(generated_ids, skip_special_tokens=True)
        
        # Clean up: sometimes models repeat the prompt or include extra whitespace
        generated_text = generated_text.strip()
        return generated_text
    except Exception as e:
        log_error(f"Generation failed for {task_id}: {str(e)}")
        return None

def generate_code_batch(
    tasks: List[Dict[str, Any]],
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    device: str,
    batch_size: int = 8
) -> List[Dict[str, Any]]:
    """Generate code for a batch of tasks."""
    results = []
    for i in range(0, len(tasks), batch_size):
        batch = tasks[i:i+batch_size]
        log_info(f"Processing batch {i//batch_size + 1}/{(len(tasks)+batch_size-1)//batch_size} ({len(batch)} tasks)")
        
        for task in batch:
            generated_code = generate_code_for_task(task, model, tokenizer, device)
            if generated_code:
                results.append({
                    "task_id": task["task_id"],
                    "source_type": "codegen_350m",
                    "generated_code": generated_code,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                results.append(mark_sample_missing(task["task_id"], "Generation failed"))
    return results

def main():
    """Main entry point for T012: Generate code using Salesforce/codegen-350M-mono."""
    # Setup logging
    logger = setup_logging(task_id="T012")
    log_info("Starting T012: Code Generation (CodeGen-350M-mono)")

    # Paths
    project_root = "projects/PROJ-294-evaluating-the-impact-of-code-generation"
    input_path = os.path.join(project_root, "data/raw/humaneval.parquet")
    output_path = os.path.join(project_root, "data/generated/codegen_samples.json")
    
    # Check input exists
    if not os.path.exists(input_path):
        log_error(f"Raw HumanEval data not found: {input_path}. Run T010 first.")
        sys.exit(1)

    # Load dataset
    try:
        import pandas as pd
        df = pd.read_parquet(input_path)
        tasks = df.to_dict('records')
        log_info(f"Loaded {len(tasks)} tasks from {input_path}")
    except Exception as e:
        log_error(f"Failed to load parquet: {str(e)}")
        sys.exit(1)

    # Model configuration
    model_name = "Salesforce/codegen-350M-mono"
    batch_size = 8
    max_retries = 3
    base_delay = 2  # seconds

    # Determine device
    device = "cpu"
    if torch.cuda.is_available():
        log_info("GPU detected, but task requires CPU execution for T012 (or fallback)")
        # Force CPU for this specific task as per spec, unless T012b logic triggers
        # For now, we respect the task constraint: "load ... on CPU"
        device = "cpu"

    log_info(f"Loading model {model_name} on {device.upper()}...")
    
    model = None
    tokenizer = None
    model_loaded = False

    # Retry logic for model loading
    for attempt in range(max_retries):
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float32, # Use float32 for CPU stability
                device_map="auto" if device == "cuda" else None,
                trust_remote_code=True
            )
            if device == "cpu":
                model = model.to("cpu")
            model_loaded = True
            log_info("Model loaded successfully.")
            break
        except Exception as e:
            delay = base_delay * (2 ** attempt)
            log_error(f"Model load attempt {attempt+1}/{max_retries} failed: {str(e)}")
            if attempt < max_retries - 1:
                log_info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                log_error("Failed to load model after max retries.")
                # Check if it's an OOM error to trigger GPU escape hatch (T012b)
                if "CUDA" in str(e) or "OutOfMemory" in str(e):
                    log_error("GPU_RETRY_SIGNAL: OOM on CPU/GPU. Exiting with code 184.")
                    sys.exit(184) # EXIT_GPU_RETRY
                sys.exit(1)

    if not model_loaded:
        sys.exit(1)

    # Generate code
    log_info(f"Starting generation for {len(tasks)} tasks (batch_size={batch_size})...")
    all_results = []

    # Retry logic for generation (exponential backoff per batch if needed)
    generation_retries = 3
    for attempt in range(generation_retries):
        try:
            all_results = generate_code_batch(tasks, model, tokenizer, device, batch_size)
            break
        except Exception as e:
            delay = base_delay * (2 ** attempt)
            log_error(f"Generation attempt {attempt+1}/{generation_retries} failed: {str(e)}")
            if attempt < generation_retries - 1:
                log_info(f"Retrying generation in {delay} seconds...")
                time.sleep(delay)
            else:
                log_error("Generation failed after max retries.")
                sys.exit(1)

    # Save results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    log_info(f"Generated code saved to {output_path}")
    log_info(f"Total samples: {len(all_results)}")
    success_count = sum(1 for r in all_results if r.get("generated_code") is not None)
    log_info(f"Successful generations: {success_count}/{len(all_results)}")

    # Cleanup
    del model
    del tokenizer
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    log_info("T012 completed successfully.")

if __name__ == "__main__":
    main()
