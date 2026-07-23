import os
import json
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

# Importing existing utilities from the project API surface
try:
    from utils import setup_logging, get_logger, set_task_id, get_task_id
except ImportError:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from utils import setup_logging, get_logger, set_task_id, get_task_id

# State directory path constant
STATE_DIR = "state"
MODEL_AVAILABILITY_FILE = os.path.join(STATE_DIR, "model_availability.json")
LOG_DIR = "logs"
ERRORS_LOG = os.path.join(LOG_DIR, "errors.log")

def ensure_state_dir():
    """Ensure the state directory exists."""
    if not os.path.exists(STATE_DIR):
        os.makedirs(STATE_DIR)
    return STATE_DIR

def ensure_log_dir():
    """Ensure the log directory exists."""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

def log_error(message: str):
    """Log an error message to both logger and errors.log file."""
    logger = logging.getLogger(__name__)
    logger.error(message)
    ensure_log_dir()
    with open(ERRORS_LOG, 'a') as f:
        f.write(f"{datetime.now().isoformat()} - ERROR - {message}\n")

def mark_sample_missing(task_id: str, reason: str):
    """Mark a sample as missing in the generation log."""
    logger = logging.getLogger(__name__)
    logger.warning(f"Sample {task_id} marked as missing: {reason}")
    ensure_log_dir()
    with open(ERRORS_LOG, 'a') as f:
        f.write(f"{datetime.now().isoformat()} - MISSING - Task {task_id}: {reason}\n")

def check_local_model_availability(model_name: str = "Salesforce/codegen-mono") -> Dict[str, Any]:
    """
    Checks if a local model is available by attempting to import the transformers
    library and checking for the model files or simply verifying the library presence.
    """
    result = {
        "model_name": model_name,
        "available": False,
        "reason": "",
        "timestamp": datetime.now().isoformat()
    }

    try:
        import transformers
        from transformers import AutoModelForCausalLM, AutoTokenizer
        
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
            result["available"] = True
            result["reason"] = "Model accessible (config/tokenizer loaded)"
            result["details"] = {
                "tokenizer_class": tokenizer.__class__.__name__,
                "vocab_size": tokenizer.vocab_size if hasattr(tokenizer, 'vocab_size') else None
            }
        except Exception as e:
            result["available"] = False
            result["reason"] = f"Failed to access model {model_name}: {str(e)}"
        
    except ImportError:
        result["available"] = False
        result["reason"] = "transformers library not installed"
    
    return result

def write_model_availability_status(status_data: Dict[str, Any]):
    """Write the model availability status to the state file."""
    ensure_state_dir()
    with open(MODEL_AVAILABILITY_FILE, 'w') as f:
        json.dump(status_data, f, indent=2)
    logging.getLogger(__name__).info(f"Model availability status written to {MODEL_AVAILABILITY_FILE}")

def generate_code_via_hf_api(task: Dict[str, Any], model_name: str) -> Optional[str]:
    """
    Placeholder for HuggingFace Inference API call.
    Implemented in T028/T029.
    """
    log_error("HuggingFace Inference API generation not implemented in this task scope.")
    return None

def _load_model_and_tokenizer(model_name: str) -> tuple:
    """
    Helper to load model and tokenizer locally.
    Raises RuntimeError if loading fails.
    """
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch
        
        logger = logging.getLogger(__name__)
        logger.info(f"Attempting to load local model: {model_name}")
        
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        
        # Load model on CPU to avoid OOM on machines with limited GPU memory
        # If GPU is available and memory permits, this could be optimized, 
        # but for robustness in a generic environment, CPU is safer for availability.
        # We use torch.float32 to avoid compatibility issues with older transformers versions.
        model = AutoModelForCausalLM.from_pretrained(
            model_name, 
            trust_remote_code=True,
            torch_dtype=torch.float32,
            device_map="cpu" 
        )
        
        logger.info(f"Successfully loaded model: {model_name}")
        return model, tokenizer
    except Exception as e:
        raise RuntimeError(f"Failed to load local model {model_name}: {str(e)}")

def generate_code_for_task(task: Dict[str, Any], model_name: str) -> Optional[str]:
    """
    Generate code for a single task using a local model.
    Implements fallback logic for T029.
    """
    logger = logging.getLogger(__name__)
    task_id = task.get("task_id", "unknown")
    prompt = task.get("prompt", "")
    
    if not prompt:
        log_error(f"Task {task_id} has no prompt.")
        return None

    try:
        model, tokenizer = _load_model_and_tokenizer(model_name)
        
        # Prepare inputs
        inputs = tokenizer(prompt, return_tensors="pt")
        
        # Generate
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=256,
                do_sample=False, # Greedy decoding for consistency in research
                temperature=None,
                top_p=None
            )
        
        # Decode
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract the generated code part (usually after the prompt)
        # Simple heuristic: take the part after the last occurrence of the prompt if it repeats,
        # or just return the full text minus the prompt prefix.
        if prompt in generated_text:
            code = generated_text.split(prompt, 1)[-1].strip()
        else:
            code = generated_text.strip()
        
        logger.info(f"Generated code for {task_id} using {model_name}")
        return code

    except RuntimeError as e:
        log_error(f"Generation failed for {task_id} with {model_name}: {str(e)}")
        return None
    except Exception as e:
        log_error(f"Unexpected error generating code for {task_id}: {str(e)}")
        return None

def generate_code_batch(tasks: List[Dict[str, Any]], model_name: str) -> List[Dict[str, Any]]:
    """
    Generate code for a batch of tasks.
    Implements T029 fallback logic:
    1. Try primary model.
    2. If API fails (not implemented here, but logic placeholder) or local model unavailable,
       check for CodeLlama-3B fallback.
    """
    logger = logging.getLogger(__name__)
    results = []
    
    # Check availability of primary model
    primary_check = check_local_model_availability(model_name)
    
    if not primary_check["available"]:
        logger.warning(f"Primary model {model_name} not available. Checking fallback...")
        fallback_model = "codellama/CodeLlama-3b-Instruct-hf"
        
        fallback_check = check_local_model_availability(fallback_model)
        
        if fallback_check["available"]:
            logger.info(f"Falling back to {fallback_model}")
            model_name = fallback_model
        else:
            logger.error(f"Fallback model {fallback_model} also unavailable. Cannot generate code.")
            # Mark all tasks as missing
            for task in tasks:
                mark_sample_missing(task.get("task_id", "unknown"), "No model available (primary and fallback)")
            return results

    # Generate code for each task
    for task in tasks:
        code = generate_code_for_task(task, model_name)
        if code:
            results.append({
                "task_id": task.get("task_id"),
                "source_type": "local_model",
                "model_used": model_name,
                "generated_code": code,
                "status": "success"
            })
        else:
            results.append({
                "task_id": task.get("task_id"),
                "source_type": "local_model",
                "model_used": model_name,
                "generated_code": None,
                "status": "failed"
            })
    
    return results

def main():
    """
    Main entry point for T029: Implement fallback logic.
    Demonstrates the fallback mechanism by checking availability and attempting generation.
    """
    task_id = get_task_id()
    setup_logging(task_id=task_id)
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting task {task_id}: Fallback logic implementation")
    
    # Define models
    primary_model = "Salesforce/codegen-mono"
    fallback_model = "codellama/CodeLlama-3b-Instruct-hf"
    
    # Check primary
    primary_status = check_local_model_availability(primary_model)
    logger.info(f"Primary model {primary_model} available: {primary_status['available']}")
    
    if not primary_status['available']:
        # Check fallback
        fallback_status = check_local_model_availability(fallback_model)
        logger.info(f"Fallback model {fallback_model} available: {fallback_status['available']}")
        
        if fallback_status['available']:
            logger.info(f"Fallback logic triggered: {fallback_model} is available.")
            # In a real pipeline, we would now switch the model_name variable
            # and proceed with generation.
        else:
            logger.warning("Neither primary nor fallback model available.")
    else:
        logger.info("Primary model available, no fallback needed.")
    
    # Update the global availability file to reflect current status of both
    # This allows downstream tasks to know what was attempted/available
    availability_data = {
        "primary_model": primary_model,
        "primary_available": primary_status['available'],
        "fallback_model": fallback_model,
        "fallback_available": check_local_model_availability(fallback_model)['available'],
        "timestamp": datetime.now().isoformat()
    }
    write_model_availability_status(availability_data)
    
    logger.info(f"Task {task_id} completed.")
    return 0

if __name__ == "__main__":
    main()