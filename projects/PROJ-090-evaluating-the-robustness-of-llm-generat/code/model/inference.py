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
from peft import PeftModel
from utils.logging import get_inference_logger, log_inference_event
from config import ensure_directories
from model.sandbox import execute_code, ExecutionStatus
from model.execution_results import ExecutionTag, tag_execution_result

# Global logger
logger = None

def get_logger():
    global logger
    if logger is None:
        logger = get_inference_logger()
    return logger

def load_model(model_name: str = "starcoder2-3b", quantize: bool = True, device: str = "cpu") -> Tuple[Any, Any]:
    """
    Load StarCoder2-3B with 4-bit quantization on CPU.
    Returns (model, tokenizer).
    """
    ensure_directories()
    log = get_logger()
    log.info(f"Loading model {model_name} on {device} with quantization={quantize}")

    if quantize:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16 if device == "cuda" else torch.float32
        )
    else:
        bnb_config = None

    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=bnb_config if quantize else None,
            device_map="auto" if device == "cuda" else None,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            trust_remote_code=True
        )
        
        if device == "cpu":
            model = model.to("cpu")
        
        log.info("Model loaded successfully.")
        return model, tokenizer
    except Exception as e:
        log.error(f"Failed to load model: {e}")
        raise

def generate_code(
    model: Any,
    tokenizer: Any,
    prompt: str,
    max_new_tokens: int = 256,
    temperature: float = 0.2,
    top_p: float = 0.95,
    timeout_seconds: int = 60
) -> Tuple[Optional[str], str]:
    """
    Generate code from a prompt.
    Returns (generated_code, status) where status is 'success', 'timeout', 'oom', or 'error'.
    """
    log = get_logger()
    log.info(f"Generating code for prompt length {len(prompt)}")

    try:
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        
        start_time = time.time()
        with torch.no_grad():
            # Use a thread to enforce timeout if the model hangs
            generated_ids = None
            error_occurred = None
            
            def run_generation():
                nonlocal generated_ids, error_occurred
                try:
                    generated_ids = model.generate(
                        **inputs,
                        max_new_tokens=max_new_tokens,
                        temperature=temperature,
                        top_p=top_p,
                        do_sample=True,
                        pad_token_id=tokenizer.eos_token_id
                    )
                except Exception as e:
                    error_occurred = e

            thread = threading.Thread(target=run_generation)
            thread.start()
            thread.join(timeout=timeout_seconds)

            if thread.is_alive():
                log.warning("Generation timed out")
                return None, "timeout"
            
            if error_occurred:
                if "CUDA out of memory" in str(error_occurred) or "OOM" in str(error_occurred):
                    return None, "oom"
                log.error(f"Generation error: {error_occurred}")
                return None, "error"

        output_text = tokenizer.decode(generated_ids[0], skip_special_tokens=True)
        
        # Extract code block if present
        if "```python" in output_text:
            start = output_text.find("```python") + len("```python")
            end = output_text.find("```", start)
            if end == -1:
                end = len(output_text)
            code = output_text[start:end].strip()
        else:
            code = output_text.strip()

        elapsed = time.time() - start_time
        log.info(f"Generated {len(code)} chars in {elapsed:.2f}s")
        return code, "success"

    except RuntimeError as e:
        err_str = str(e)
        if "out of memory" in err_str.lower() or "oom" in err_str.lower():
            log.error("OOM detected during generation")
            return None, "oom"
        log.error(f"Runtime error during generation: {e}")
        return None, "error"
    except Exception as e:
        log.error(f"Unexpected error during generation: {e}")
        traceback.print_exc()
        return None, "error"

def run_generation_loop(
    model: Any,
    tokenizer: Any,
    tasks: List[Dict[str, Any]],
    output_path: str,
    timeout_per_task: int = 60
) -> List[Dict[str, Any]]:
    """
    Run inference on a list of tasks, executing the generated code in the sandbox.
    Handles OOM by skipping the sample and logging the flag.
    """
    log = get_logger()
    results = []
    ensure_directories()

    for i, task in enumerate(tasks):
        task_id = task.get("task_id", f"task_{i}")
        prompt = task.get("prompt", "")
        
        log.info(f"Processing task {i+1}/{len(tasks)}: {task_id}")

        # Generate code
        generated_code, gen_status = generate_code(
            model, tokenizer, prompt, timeout_seconds=timeout_per_task
        )

        if gen_status == "oom":
            # OOM Handling: Skip sample and log "OOM" flag
            log.warning(f"OOM detected for task {task_id}. Skipping sample.")
            result_entry = {
                "task_id": task_id,
                "status": "skipped",
                "reason": "OOM",
                "generated_code": None,
                "execution_status": None,
                "execution_tag": ExecutionTag.OOM.value
            }
            results.append(result_entry)
            log_inference_event("OOM_SKIP", {"task_id": task_id})
            continue

        if gen_status != "success":
            log.error(f"Generation failed for {task_id} with status: {gen_status}")
            result_entry = {
                "task_id": task_id,
                "status": "failed",
                "reason": f"Generation {gen_status}",
                "generated_code": None,
                "execution_status": None,
                "execution_tag": ExecutionTag.GENERATION_ERROR.value
            }
            results.append(result_entry)
            continue

        # Execute code in sandbox
        try:
            exec_result = execute_code(generated_code, task.get("tests", []), timeout=timeout_per_task)
            exec_status = exec_result.status.value
            execution_tag = tag_execution_result(exec_result)
            
            result_entry = {
                "task_id": task_id,
                "status": "completed",
                "reason": None,
                "generated_code": generated_code,
                "execution_status": exec_status,
                "execution_tag": execution_tag,
                "execution_details": {
                    "passed_tests": exec_result.passed,
                    "total_tests": exec_result.total,
                    "error_message": exec_result.error
                }
            }
        except Exception as e:
            log.error(f"Sandbox execution failed for {task_id}: {e}")
            result_entry = {
                "task_id": task_id,
                "status": "failed",
                "reason": f"Sandbox error: {str(e)}",
                "generated_code": generated_code,
                "execution_status": "error",
                "execution_tag": ExecutionTag.SANDBOX_ERROR.value
            }

        results.append(result_entry)

        # Log progress
        log_inference_event("TASK_COMPLETE", {
            "task_id": task_id,
            "status": result_entry["status"],
            "execution_tag": result_entry["execution_tag"]
        })

    # Save results
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    
    log.info(f"Saved {len(results)} results to {output_path}")
    return results

def main():
    """
    Entry point for the inference pipeline.
    Expects tasks in data/processed/perturbed_tasks.json (or similar)
    and outputs to data/processed/inference_results.json.
    """
    ensure_directories()
    log = get_logger()
    
    # Load tasks
    tasks_path = Path("data/processed/perturbed_tasks.json")
    if not tasks_path.exists():
        log.error(f"Tasks file not found: {tasks_path}")
        sys.exit(1)

    with open(tasks_path, "r", encoding="utf-8") as f:
        tasks = json.load(f)

    log.info(f"Loaded {len(tasks)} tasks")

    # Load model
    model, tokenizer = load_model()

    # Run loop
    output_path = "data/processed/inference_results.json"
    results = run_generation_loop(model, tokenizer, tasks, output_path)

    log.info("Inference pipeline completed.")

if __name__ == "__main__":
    main()