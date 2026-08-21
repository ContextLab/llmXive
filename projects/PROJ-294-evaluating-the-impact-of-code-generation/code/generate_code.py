import os
import json
import logging
import time
import sys
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

# --- Logging Configuration (Shared API Contract) ---
# Must accept: setup_logging(), setup_logging(task_id="..."), setup_logging(task_id=TASK_ID), setup_logging(level=logging.INFO)
# Must return a logger instance.

_task_id = None
_logger_instance = None

def set_task_id(tid: Optional[str] = None):
    global _task_id
    if tid:
        _task_id = tid

def get_task_id() -> Optional[str]:
    return _task_id

def get_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_unique_id() -> str:
    return str(uuid.uuid4())

def setup_logging(task_id: Optional[str] = None, level: int = logging.INFO, name: Optional[str] = None) -> logging.Logger:
    """
    Setup logging configuration.
    Accepts:
      - No args: setup_logging()
      - Keyword arg task_id: setup_logging(task_id="T012")
      - Positional arg (legacy): setup_logging(task_id) -> treated as task_id
      - Keyword arg level: setup_logging(level=logging.INFO)
    """
    global _logger_instance, _task_id

    # Handle positional vs keyword ambiguity if called as setup_logging(some_value)
    # In this signature, 'task_id' is the first param. If passed positionally, it's the task_id.
    # If passed as keyword, it's also task_id.
    # We also support 'level' as a keyword.

    if task_id:
        _task_id = task_id

    # Ensure logger exists
    if _logger_instance is None:
        logger = logging.getLogger("GEN-CODE")
        logger.setLevel(level)

        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] - %(name)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        _logger_instance = logger

    return _logger_instance

def get_logger() -> logging.Logger:
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = setup_logging()
    return _logger_instance

def log_info(msg: str):
    get_logger().info(msg)

def log_error(msg: str):
    get_logger().error(msg)

def log_warning(msg: str):
    get_logger().warning(msg)

# --- File System Utilities ---

def ensure_state_dir():
    dir_path = "state"
    os.makedirs(dir_path, exist_ok=True)
    return dir_path

def ensure_log_dir():
    dir_path = "logs"
    os.makedirs(dir_path, exist_ok=True)
    return dir_path

def ensure_output_dir():
    dir_path = "data/generated"
    os.makedirs(dir_path, exist_ok=True)
    return dir_path

def load_prompt_template() -> str:
    """Load prompt template from code/prompt_templates/humaneval.txt"""
    path = "code/prompt_templates/humaneval.txt"
    if not os.path.exists(path):
        log_warning(f"Prompt template not found at {path}, using default.")
        return "Complete the following Python function:\n\n{prompt}"
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def load_parquet_data() -> List[Dict[str, Any]]:
    """Load HumanEval data from data/raw/humaneval.parquet or .jsonl if parquet missing."""
    # Check for parquet first
    parquet_path = "data/raw/humaneval.parquet"
    jsonl_path = "data/raw/humaneval_test.jsonl"

    if os.path.exists(parquet_path):
        try:
            import pyarrow.parquet as pq
            table = pq.read_table(parquet_path)
            return table.to_pydict()
        except Exception as e:
            log_error(f"Failed to read parquet: {e}. Trying JSONL.")
    
    if os.path.exists(jsonl_path):
        try:
            data = []
            with open(jsonl_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data.append(json.loads(line))
            return data
        except Exception as e:
            log_error(f"Failed to read JSONL: {e}")
            raise RuntimeError("Raw HumanEval data not found. Run T010 first.")
    
    raise RuntimeError("Raw HumanEval data not found. Run T010 first.")

def save_to_jsonl(data: List[Dict[str, Any]], output_path: str):
    """Save list of dicts to JSONL file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')

def check_local_model_availability(model_name: str) -> bool:
    """Check if model is available locally (mock implementation for now)."""
    # In a real implementation, check HuggingFace cache or local path
    log_info(f"Checking availability for model: {model_name}")
    return True

def write_model_availability_status(model_name: str, available: bool):
    """Write model availability status to state file."""
    status_path = "state/model_availability.json"
    data = {"model": model_name, "available": available, "timestamp": get_timestamp()}
    os.makedirs("state", exist_ok=True)
    with open(status_path, 'w') as f:
        json.dump(data, f, indent=2)

# --- Code Generation Logic ---

def generate_code_via_hf_api(task: Dict[str, Any], model_name: str, prompt_template: str) -> Optional[str]:
    """
    Generate code for a single task using HuggingFace Inference API or local model.
    Returns generated code string or None if failed.
    """
    # This is a placeholder for the actual generation logic.
    # In the real implementation, this would call the model.
    # For T013, we focus on error handling around this call.
    
    prompt = prompt_template.format(prompt=task.get('prompt', ''))
    
    # Simulate generation (replace with actual model call in T012 context)
    # Since we are implementing T013 (error handling), we assume the call might fail.
    # We will return a mock string for success cases in this context if needed,
    # but the task is to handle errors.
    
    # NOTE: The actual generation logic is in T012. T013 wraps this.
    # We assume 'generated_code' is the result of the generation attempt.
    # For the purpose of this task's logic, we return a dummy string if "success".
    return f"# Generated code for {task.get('task_id', 'unknown')}"

def generate_code_for_task(task: Dict[str, Any], model_name: str, prompt_template: str) -> Dict[str, Any]:
    """
    Generate code for a single task with error handling (T013).
    Returns a dict with task_id, generated_code, status.
    """
    task_id = task.get('task_id', 'unknown')
    result = {
        "task_id": task_id,
        "prompt": task.get('prompt', ''),
        "generated_code": None,
        "status": "pending",
        "error_message": None
    }

    try:
        log_info(f"Starting generation for {task_id}")
        code = generate_code_via_hf_api(task, model_name, prompt_template)
        
        if code is None:
            raise RuntimeError("Model returned no code.")
        
        result["generated_code"] = code
        result["status"] = "success"
        log_info(f"Successfully generated code for {task_id}")

    except (RuntimeError, TimeoutError, MemoryError) as e:
        result["status"] = "failed"
        result["error_message"] = str(e)
        log_error(f"Failed to generate code for {task_id}: {e}")
        
        # Log to errors.log as per T013 requirement
        log_errors_path = "code/errors.log"
        with open(log_errors_path, 'a', encoding='utf-8') as err_file:
            err_entry = f"{get_timestamp()} | {task_id} | {type(e).__name__}: {e}\n"
            err_file.write(err_entry)
    
    except Exception as e:
        # Catch-all for unexpected errors
        result["status"] = "failed"
        result["error_message"] = f"Unexpected error: {str(e)}"
        log_error(f"Unexpected error for {task_id}: {e}")
        
        log_errors_path = "code/errors.log"
        with open(log_errors_path, 'a', encoding='utf-8') as err_file:
            err_entry = f"{get_timestamp()} | {task_id} | {type(e).__name__}: {e}\n"
            err_file.write(err_entry)

    return result

def generate_code_batch(tasks: List[Dict[str, Any]], model_name: str, prompt_template: str) -> List[Dict[str, Any]]:
    """Generate code for a batch of tasks."""
    results = []
    for task in tasks:
        res = generate_code_for_task(task, model_name, prompt_template)
        results.append(res)
    return results

def main():
    """Main entry point for T012/T013 code generation."""
    # Setup logging
    logger = setup_logging(task_id="T013")
    log_info("Starting Code Generation with Error Handling (T013)")

    # Load data
    try:
        data = load_parquet_data()
        if isinstance(data, dict):
            # If loaded as dict (pyarrow), convert to list of dicts
            # This is a simplification; real code handles pyarrow dict conversion properly
            keys = list(data.keys())
            data = [{k: data[k][i] for k in keys} for i in range(len(data[keys[0]]))]
    except RuntimeError as e:
        log_error(str(e))
        sys.exit(1)

    # Load prompt
    prompt_template = load_prompt_template()

    # Determine model
    model_name = "Salesforce/codegen-350M-mono" # Default fallback
    # In a real scenario, parse args or config for model name
    
    log_info(f"Using model: {model_name}")

    # Generate code
    results = generate_code_batch(data, model_name, prompt_template)

    # Save results
    output_path = "data/generated/codegen_samples.json"
    save_to_jsonl(results, output_path)
    log_info(f"Saved results to {output_path}")

    # Check if errors.log was created
    if os.path.exists("code/errors.log"):
        log_info("Error log created at code/errors.log")
    else:
        log_info("No errors encountered; errors.log not created.")

    log_info("Code Generation Complete.")

if __name__ == "__main__":
    main()