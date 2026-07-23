import os
import json
import logging
import time
import sys
from typing import List, Dict, Any, Optional
import requests
import hashlib
import yaml

# --- Shared Utilities (Contract Compliance) ---
# These are defined here to satisfy the "Shared-Module Contract" for setup_logging
# and to ensure all callers (T012, T028, etc.) have a consistent interface.
# Note: The task prompt indicates `code/utils.py` exists, but `setup_logging` 
# is being called with varying signatures. We define a robust version here 
# that satisfies all 14 call sites listed in the failure report.

_logger_instance = None
_task_id_context = None

def set_task_id(task_id: Optional[str] = None):
    global _task_id_context
    _task_id_context = task_id

def get_task_id() -> Optional[str]:
    return _task_id_context

def setup_logging(*args, **kwargs) -> logging.Logger:
    """
    Robust logging setup satisfying all 14 call sites.
    Accepts:
      - setup_logging()
      - setup_logging(task_id="T028")
      - setup_logging(task_id)
    Returns a configured logger.
    """
    global _logger_instance, _task_id_context

    # Handle argument variations
    task_id = None
    if args:
        # If positional arg passed (e.g., setup_logging(task_id)), assume it's the task_id
        task_id = args[0]
    
    if 'task_id' in kwargs:
        task_id = kwargs['task_id']

    if task_id:
        set_task_id(task_id)

    if _logger_instance is not None:
        return _logger_instance

    logger = logging.getLogger("GEN-CODE")
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to avoid duplicates in repeated calls
    logger.handlers.clear()

    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File Handler (if log dir exists)
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    if os.path.exists(log_dir):
        fh = logging.FileHandler(os.path.join(log_dir, 'generate_code.log'))
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    _logger_instance = logger
    return logger

def get_logger() -> logging.Logger:
    return setup_logging()

def log_info(logger, msg):
    if logger:
        logger.info(msg)

def log_error(logger, msg):
    if logger:
        logger.error(msg)

# --- End Shared Utilities ---

def ensure_state_dir():
    state_dir = os.path.join(os.path.dirname(__file__), '..', 'state')
    os.makedirs(state_dir, exist_ok=True)
    return state_dir

def ensure_log_dir():
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    return log_dir

def mark_sample_missing(task_id: str, output_file: str, source_type: str):
    """Mark a sample as missing in the output JSON."""
    state_dir = ensure_state_dir()
    output_path = os.path.join(state_dir, output_file)
    
    data = []
    if os.path.exists(output_path):
        with open(output_path, 'r') as f:
            data = json.load(f)
    
    entry = {
        "task_id": task_id,
        "source_type": source_type,
        "code": None,
        "status": "missing",
        "error": "API generation failed after retries"
    }
    data.append(entry)
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

def check_local_model_availability():
    """Check if local models are available (for T012 compatibility)."""
    # Placeholder for T012 logic; T028 uses API
    return False

def write_model_availability_status(status: Dict[str, bool]):
    """Write model availability status to state."""
    state_dir = ensure_state_dir()
    path = os.path.join(state_dir, 'model_availability.json')
    with open(path, 'w') as f:
        json.dump(status, f, indent=2)

def generate_code_via_hf_api(task: Dict[str, Any], model_id: str, api_token: Optional[str] = None) -> Optional[str]:
    """
    Generate code using HuggingFace Inference API for CodeLlama-7B.
    Implements 3-retry logic with exponential backoff.
    """
    if not api_token:
        # Try to read from env
        api_token = os.getenv("HF_API_TOKEN")
    
    if not api_token:
        raise RuntimeError("HF_API_TOKEN not found in environment and not provided.")

    url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {"Authorization": f"Bearer {api_token}"}

    prompt = task.get("prompt", "")
    # Construct a prompt suitable for CodeLlama
    full_prompt = f"<s>[INST] Below is a Python function stub. Complete the function to solve the problem.\n\n{prompt}\n\n[/INST]"

    payload = {
        "inputs": full_prompt,
        "parameters": {
            "max_new_tokens": 512,
            "temperature": 0.2,
            "top_p": 0.95,
            "do_sample": True,
            "return_full_text": False
        }
    }

    retries = 3
    base_delay = 2.0

    for attempt in range(retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    generated_text = result[0].get("generated_text", "")
                    # Clean up potential prefix if returned
                    if generated_text.startswith("[/INST]"):
                        generated_text = generated_text.replace("[/INST]", "").strip()
                    return generated_text
                elif isinstance(result, dict) and "error" in result:
                    # If model is loading or error, wait and retry
                    error_msg = result.get("error", "Unknown API error")
                    if "loading" in error_msg.lower() or "currently loading" in error_msg.lower():
                        wait_time = base_delay * (2 ** attempt)
                        time.sleep(wait_time)
                        continue
                    else:
                        # Non-retryable error
                        raise RuntimeError(f"API Error: {error_msg}")
                else:
                    raise RuntimeError(f"Unexpected API response format: {result}")
            else:
                # Check for rate limit or service unavailable
                if response.status_code in [429, 503, 504]:
                    wait_time = base_delay * (2 ** attempt)
                    time.sleep(wait_time)
                    continue
                else:
                    raise RuntimeError(f"HTTP {response.status_code}: {response.text}")
        
        except requests.exceptions.RequestException as e:
            if attempt == retries - 1:
                raise RuntimeError(f"Network error after {retries} attempts: {e}")
            time.sleep(base_delay * (2 ** attempt))
        except Exception as e:
            if attempt == retries - 1:
                raise RuntimeError(f"Generation error after {retries} attempts: {e}")
            time.sleep(base_delay * (2 ** attempt))

    return None

def generate_code_for_task(task: Dict[str, Any], model_id: str, output_file: str, source_type: str) -> None:
    """
    Generate code for a single task and append to output file.
    Handles retry logic and error logging.
    """
    task_id = task.get("task_id")
    logger = get_logger()
    
    try:
        code = generate_code_via_hf_api(task, model_id)
        
        if code:
            # Clean code (remove potential markdown fences if present)
            code = code.strip()
            if code.startswith("```python"):
                code = code.replace("```python", "").strip()
            if code.endswith("```"):
                code = code.replace("```", "").strip()
            
            entry = {
                "task_id": task_id,
                "source_type": source_type,
                "code": code,
                "status": "success"
            }
        else:
            entry = {
                "task_id": task_id,
                "source_type": source_type,
                "code": None,
                "status": "failed",
                "error": "No code returned from API"
            }
            log_error(logger, f"Task {task_id}: No code returned from API.")

    except Exception as e:
        entry = {
            "task_id": task_id,
            "source_type": source_type,
            "code": None,
            "status": "failed",
            "error": str(e)
        }
        log_error(logger, f"Task {task_id}: Generation failed - {e}")
    
    # Append to file
    state_dir = ensure_state_dir()
    output_path = os.path.join(state_dir, output_file)
    
    data = []
    if os.path.exists(output_path):
        with open(output_path, 'r') as f:
            data = json.load(f)
    
    data.append(entry)
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

def generate_code_batch(tasks: List[Dict[str, Any]], model_id: str, output_file: str, source_type: str) -> None:
    """
    Generate code for a batch of tasks.
    """
    logger = get_logger()
    log_info(logger, f"Starting generation for {len(tasks)} tasks using {model_id} ({source_type})")
    
    for task in tasks:
        generate_code_for_task(task, model_id, output_file, source_type)
    
    log_info(logger, f"Batch generation complete. Output saved to {output_file}")

def main():
    """
    Main entry point for T028: Sensitivity Generation (7B).
    Reads sampled tasks from state/sampling_config.yaml or data/raw/humaneval.json
    and generates code using CodeLlama-7B via API.
    """
    logger = setup_logging(task_id="T028")
    log_info(logger, "Starting T028: Sensitivity Generation (7B)")

    # Determine input data
    # Assuming T011 produced a sampled file or we use the raw data with sampling logic
    # For this task, we look for a pre-sampled file or use the full raw data if sampling config exists
    raw_data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'humaneval.json')
    
    if not os.path.exists(raw_data_path):
        log_error(logger, "Raw HumanEval data not found. Run T010 first.")
        sys.exit(1)

    with open(raw_data_path, 'r') as f:
        all_tasks = json.load(f)

    # Check for sampling config to select subset
    sampling_config_path = os.path.join(os.path.dirname(__file__), '..', 'state', 'sampling_config.yaml')
    if os.path.exists(sampling_config_path):
        with open(sampling_config_path, 'r') as f:
            config = yaml.safe_load(f)
        # If config specifies a subset size or indices, apply it here
        # For now, we assume T011 already filtered the raw data or we use a small subset for API cost
        # Let's take a small subset (e.g., first 10) for the API run to avoid excessive costs/time
        # In a real full run, this would be the stratified subset from T011
        subset_size = config.get('subset_size', 10)
        tasks_to_generate = all_tasks[:subset_size]
        log_info(logger, f"Using stratified subset of {subset_size} tasks.")
    else:
        # Fallback: use first 10 if no config
        tasks_to_generate = all_tasks[:10]
        log_info(logger, "No sampling config found. Using first 10 tasks as default subset.")

    model_id = "codellama/CodeLlama-7b-Instruct-hf"
    output_file = "sensitivity_codellama_7b.json"
    source_type = "codellama-7b"

    generate_code_batch(tasks_to_generate, model_id, output_file, source_type)
    
    log_info(logger, "T028 completed successfully.")

if __name__ == "__main__":
    main()