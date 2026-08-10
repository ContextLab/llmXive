import os
import json
import logging
import time
import sys
import re
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional

import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

# Constants
EXIT_GPU_RETRY = 184
MAX_RETRIES = 3
INITIAL_DELAY = 1
MAX_DELAY = 60
BATCH_SIZE = 8
TIMEOUT_SECONDS = 300

# Global task ID state
_task_id = None

def set_task_id(tid: str) -> None:
    global _task_id
    _task_id = tid

def get_task_id() -> Optional[str]:
    return _task_id

def setup_logging(*args, **kwargs) -> logging.Logger:
    """
    Flexible logging setup compatible with all call sites.
    Accepts:
      - setup_logging()
      - setup_logging(task_id="T012")
      - setup_logging(task_id)
      - setup_logging(level=logging.INFO)
      - setup_logging(task_id="T012", level=logging.INFO)
    """
    global _task_id

    task_id = None
    level = logging.INFO
    logger_name = "GEN-CODE"

    # Handle positional args
    if args:
        # If it looks like a task_id string or variable passed positionally
        if isinstance(args[0], str):
            task_id = args[0]
        elif len(args) > 1:
            # setup_logging(task_id, level) or similar
            task_id = args[0]
            if len(args) > 1:
                level = args[1]

    # Handle keyword args
    if 'task_id' in kwargs:
        task_id = kwargs['task_id']
    if 'level' in kwargs:
        level = kwargs['level']

    # Update global if provided
    if task_id:
        _task_id = task_id

    # Construct logger name with task ID if available
    if _task_id:
        logger_name = f"GEN-CODE-{_task_id}"

    # Configure logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] - %(name)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

def get_logger() -> logging.Logger:
    return setup_logging()

def log_info(msg: str) -> None:
    logger = get_logger()
    logger.info(msg)

def log_error(msg: str) -> None:
    logger = get_logger()
    logger.error(msg)

def log_warning(msg: str) -> None:
    logger = get_logger()
    logger.warning(msg)

def ensure_state_dir() -> None:
    state_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'state')
    if not os.path.exists(state_dir):
        os.makedirs(state_dir)

def ensure_log_dir() -> None:
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

def load_parquet_data(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Raw HumanEval data not found at {path}. Run T010 first.")
    return pd.read_parquet(path)

def save_to_jsonl(data: List[Dict], path: str) -> None:
    ensure_state_dir() # Ensure output dir exists (data/generated is usually created by T008, but safe to ensure)
    output_dir = os.path.dirname(path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(path, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')

def load_prompt_template(template_path: str) -> str:
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Prompt template not found at {template_path}")
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

def check_local_model_availability(model_name: str) -> bool:
    # Simple check if model files exist locally (cache)
    try:
        from transformers import AutoConfig
        AutoConfig.from_pretrained(model_name)
        return True
    except Exception:
        return False

def write_model_availability_status(model_name: str, available: bool) -> None:
    ensure_state_dir()
    status_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'state', 'model_availability.json')
    status = {
        "model": model_name,
        "available": available,
        "timestamp": datetime.now().isoformat()
    }
    with open(status_path, 'w') as f:
        json.dump(status, f)

def generate_code_via_hf_api(prompt: str, model_name: str, tokenizer, model, max_new_tokens: int = 1024) -> str:
    """
    Generates code using the loaded model and tokenizer.
    Implements retry logic with exponential backoff.
    """
    device = "cpu"
    if torch.cuda.is_available():
        device = "cuda"

    # Prepare inputs
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    attention_mask = inputs['attention_mask']

    # Retry logic
    delay = INITIAL_DELAY
    last_exception = None

    for attempt in range(MAX_RETRIES):
        try:
            # Check for timeout simulation if needed, but here we rely on actual execution time
            start_time = time.time()

            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    num_return_sequences=1,
                    do_sample=False, # Deterministic for T012
                    pad_token_id=tokenizer.eos_token_id
                )

            elapsed = time.time() - start_time
            if elapsed > TIMEOUT_SECONDS:
                raise TimeoutError(f"Generation timed out after {elapsed:.2f}s")

            # Decode
            generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            return generated_text

        except (RuntimeError, TimeoutError) as e:
            last_exception = e
            error_msg = str(e)
            log_error(f"Attempt {attempt + 1} failed: {error_msg}")

            # Check for OOM
            if re.search(r"OutOfMemory|CUDA out of memory", error_msg, re.IGNORECASE):
                log_error("GPU Escape Hatch: OutOfMemory detected.")
                sys.exit(EXIT_GPU_RETRY)

            if attempt < MAX_RETRIES - 1:
                time.sleep(delay)
                delay = min(delay * 2, MAX_DELAY)
            else:
                raise

    if last_exception:
        raise last_exception

def generate_code_for_task(task: Dict, model_name: str, tokenizer, model, prompt_template: str) -> Dict[str, Any]:
    task_id = task['task_id']
    prompt = task['prompt']
    full_prompt = prompt_template.format(prompt=prompt)

    try:
        generated_code = generate_code_via_hf_api(full_prompt, model_name, tokenizer, model)
        return {
            "task_id": task_id,
            "source_type": "codegen_350m",
            "generated_code": generated_code,
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        error_msg = str(e)
        log_error(f"Failed to generate code for {task_id}: {error_msg}")
        return {
            "task_id": task_id,
            "source_type": "codegen_350m",
            "generated_code": None,
            "status": "failed",
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }

def generate_code_batch(tasks: List[Dict], model_name: str, tokenizer, model, prompt_template: str, batch_size: int = BATCH_SIZE) -> List[Dict[str, Any]]:
    results = []
    total = len(tasks)

    for i in range(0, total, batch_size):
        batch = tasks[i:i+batch_size]
        log_info(f"Processing batch {i//batch_size + 1}/{(total + batch_size - 1)//batch_size} ({len(batch)} tasks)")

        for task in batch:
            result = generate_code_for_task(task, model_name, tokenizer, model, prompt_template)
            results.append(result)

            # Log progress
            if result['status'] == 'success':
                log_info(f"Successfully generated code for {result['task_id']}")
            else:
                log_warning(f"Failed generation for {result['task_id']}")

    return results

def main():
    # Setup logging
    logger = setup_logging(task_id="T012")
    log_info("Starting T012: Code Generation")

    # Paths
    project_root = os.path.dirname(os.path.dirname(__file__))
    data_path = os.path.join(project_root, 'data', 'raw', 'humaneval.parquet')
    template_path = os.path.join(project_root, 'code', 'prompt_templates', 'humaneval.txt')
    output_path = os.path.join(project_root, 'data', 'generated', 'codegen_samples.json')

    model_name = "Salesforce/codegen-350M-mono"

    # Load Data
    log_info(f"Loading data from {data_path}")
    try:
        df = load_parquet_data(data_path)
    except FileNotFoundError as e:
        log_error(str(e))
        sys.exit(1)

    # Load Prompt Template
    log_info(f"Loading prompt template from {template_path}")
    try:
        prompt_template = load_prompt_template(template_path)
    except FileNotFoundError as e:
        log_error(str(e))
        sys.exit(1)

    # Load Model
    log_info(f"Loading model {model_name} on CPU")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float32)
        # Ensure model is in eval mode
        model.eval()
        log_info("Model loaded successfully.")
    except Exception as e:
        log_error(f"Failed to load model: {e}")
        # If OOM or similar, exit with GPU retry code
        if re.search(r"OutOfMemory|CUDA out of memory", str(e), re.IGNORECASE):
            sys.exit(EXIT_GPU_RETRY)
        sys.exit(1)

    # Convert DF to list of dicts
    tasks = df.to_dict('records')
    log_info(f"Loaded {len(tasks)} tasks for generation.")

    # Generate Code
    log_info(f"Starting batched generation (batch_size={BATCH_SIZE})")
    results = generate_code_batch(tasks, model_name, tokenizer, model, prompt_template)

    # Save Results
    log_info(f"Saving results to {output_path}")
    save_to_jsonl(results, output_path)

    # Summary
    success_count = sum(1 for r in results if r['status'] == 'success')
    fail_count = sum(1 for r in results if r['status'] == 'failed')
    log_info(f"Generation complete. Success: {success_count}, Failed: {fail_count}")

    # Log errors to errors.log if any failures
    if fail_count > 0:
        log_dir = os.path.join(project_root, 'code')
        errors_log_path = os.path.join(log_dir, 'errors.log')
        with open(errors_log_path, 'a') as f:
            for r in results:
                if r['status'] == 'failed':
                    f.write(f"{r['task_id']}: {r.get('error', 'Unknown error')}\n")

    log_info("T012 completed.")

if __name__ == "__main__":
    main()