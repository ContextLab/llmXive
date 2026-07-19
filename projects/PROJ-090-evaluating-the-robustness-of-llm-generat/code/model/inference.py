import os
import sys
import time
import threading
import logging
import json
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from datasets import load_dataset

from config import (
    get_model_path,
    get_timeout_inference,
    get_seed_global,
    get_semantic_threshold,
    get_budget_generations,
    ensure_directories,
)
from utils.logging import get_inference_logger, log_inference_event
from utils.state import get_state, increment_generations, is_exhausted, save_state
from model.sandbox import execute_code, ExecutionStatus

# --- Logger Setup ---
_logger: Optional[logging.Logger] = None

def get_logger() -> logging.Logger:
    global _logger
    if _logger is None:
        _logger = get_inference_logger()
    return _logger

# --- Model Loading ---
_model = None
_tokenizer = None
_model_lock = threading.Lock()

def load_model():
    """
    Loads the StarCoder2-3B model with 4-bit quantization on CPU.
    Implements OOM handling at the loading stage if necessary, though
    the primary OOM handling for this task is during generation.
    """
    global _model, _tokenizer
    with _model_lock:
        if _model is not None:
            return _model, _tokenizer

        logger = get_logger()
        model_path = get_model_path()
        logger.info(f"Loading model from {model_path} with CPU device and 4-bit quantization...")

        try:
            # Configure 4-bit quantization for CPU compatibility
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float32, # CPU compatible
            )

            _tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
            _model = AutoModelForCausalLM.from_pretrained(
                model_path,
                quantization_config=bnb_config,
                device_map="cpu", # Force CPU as per US2
                trust_remote_code=True,
                torch_dtype=torch.float32,
            )
            _model.eval()
            logger.info("Model loaded successfully.")
            return _model, _tokenizer

        except MemoryError as e:
            logger.error(f"CRITICAL: Out of Memory (OOM) during model loading: {e}")
            # If we can't load the model, we cannot proceed.
            # We raise to fail the pipeline loudly rather than returning None.
            raise RuntimeError("Model loading failed due to OOM. Cannot proceed.") from e
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise e

# --- Code Generation ---
def generate_code(
    prompt: str,
    max_new_tokens: int = 256,
    temperature: float = 0.2,
    do_sample: bool = True,
    top_p: float = 0.95,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Generates code for a given prompt.
    Returns (generated_code, error_message).
    If generation fails due to OOM, raises MemoryError.
    """
    model, tokenizer = load_model()
    logger = get_logger()

    try:
        inputs = tokenizer(prompt, return_tensors="pt")
        
        # Move inputs to CPU explicitly
        input_ids = inputs.input_ids.to("cpu")
        
        with torch.no_grad():
            # Generate
            output = model.generate(
                input_ids,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=do_sample,
                top_p=top_p,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id,
                # No CUDA specific settings
            )
        
        generated_text = tokenizer.decode(output[0], skip_special_tokens=True)
        
        # Extract code block if present (simple heuristic)
        if "```python" in generated_text:
            start = generated_text.find("```python") + len("```python")
            end = generated_text.find("```", start)
            if end != -1:
                generated_text = generated_text[start:end].strip()
        
        return generated_text, None

    except MemoryError as e:
        logger.error(f"OOM during generation for prompt length {len(prompt)}: {e}")
        raise e
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        return None, str(e)

# --- Main Execution Loop with OOM Handling ---
def run_generation_loop(
    tasks: List[Dict[str, Any]],
    output_path: str,
) -> List[Dict[str, Any]]:
    """
    Iterates through tasks, generates code, and handles OOM errors.
    OOM events result in the sample being skipped and logged with an 'OOM' flag.
    """
    logger = get_logger()
    results = []
    
    # Ensure output directory exists
    ensure_directories()
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting generation loop for {len(tasks)} tasks.")

    for idx, task in enumerate(tasks):
        task_id = task.get("task_id", f"task_{idx}")
        prompt = task.get("prompt", "")
        
        # Check budget state
        if is_exhausted():
            logger.warning("Budget exhausted. Stopping generation loop.")
            break

        logger.info(f"Processing task {task_id} ({idx+1}/{len(tasks)})...")

        try:
            # Attempt generation
            generated_code, error = generate_code(prompt)
            
            if error:
                # Non-OOM error
                results.append({
                    "task_id": task_id,
                    "status": "error",
                    "error_type": "generation_error",
                    "error_message": error,
                    "generated_code": None,
                    "oom_flag": False
                })
                log_inference_event(task_id, "error", error)
            else:
                # Success
                results.append({
                    "task_id": task_id,
                    "status": "success",
                    "error_type": None,
                    "error_message": None,
                    "generated_code": generated_code,
                    "oom_flag": False
                })
                log_inference_event(task_id, "success", None)
                increment_generations()

        except MemoryError as e:
            # SPECIFIC OOM HANDLING FOR T025
            # Skip sample, log "OOM" flag, and continue to next task.
            logger.error(f"OOM encountered for task {task_id}. Skipping sample and logging OOM flag.")
            
            results.append({
                "task_id": task_id,
                "status": "skipped",
                "error_type": "oom",
                "error_message": "Out of Memory during generation",
                "generated_code": None,
                "oom_flag": True
            })
            
            log_inference_event(task_id, "oom", str(e))
            # Do NOT increment_generations() for skipped tasks
            continue

        except Exception as e:
            # Catch-all for unexpected errors
            logger.error(f"Unexpected error for task {task_id}: {traceback.format_exc()}")
            results.append({
                "task_id": task_id,
                "status": "error",
                "error_type": "unexpected",
                "error_message": str(e),
                "generated_code": None,
                "oom_flag": False
            })

    # Save results
    save_results_to_json(results, output_file)
    logger.info(f"Generation loop completed. Results saved to {output_file}.")
    
    return results

def save_results_to_json(results: List[Dict[str, Any]], path: Path):
    """Saves the results list to a JSON file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

def main():
    """
    Entry point for the inference script.
    Loads HumanEval tasks (or perturbed tasks) and runs the generation loop.
    """
    logger = get_logger()
    logger.info("Inference pipeline starting...")

    # Load tasks from data/processed (assuming T017/T018 produced them)
    # If T017 hasn't run, this will fail loudly, which is correct behavior.
    tasks_path = Path("data/processed/perturbed_tasks.json")
    
    if not tasks_path.exists():
        # Fallback to original if perturbed not found, but prefer perturbed
        tasks_path = Path("data/raw/humaneval.json")
    
    if not tasks_path.exists():
        logger.error("No tasks found. Please run download_humaneval.py and generate_perturbations.py first.")
        sys.exit(1)

    with open(tasks_path, "r") as f:
        tasks = json.load(f)

    logger.info(f"Loaded {len(tasks)} tasks from {tasks_path}.")

    output_path = "data/processed/inference_results.json"
    run_generation_loop(tasks, output_path)

if __name__ == "__main__":
    main()