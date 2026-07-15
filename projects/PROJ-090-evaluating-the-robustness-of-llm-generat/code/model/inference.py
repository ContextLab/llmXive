import os
import sys
import time
import threading
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel
from utils.logging import get_inference_logger, log_inference_event
from config import get_config_summary
from model.sandbox import execute_code, ExecutionStatus, ExecutionResult
from model.execution_results import ExecutionTag, tag_execution_result, classify_error_message, save_results_to_json

# Global model and tokenizer instances
_model = None
_tokenizer = None
_model_lock = threading.Lock()

def load_model(model_name: str = "bigcode/starcoder2-3b", device: str = "cpu", load_4bit: bool = True) -> Tuple[Any, Any]:
    """
    Load StarCoder2-3B with 4-bit quantization for CPU compatibility.
    Returns (model, tokenizer).
    """
    global _model, _tokenizer

    with _model_lock:
        if _model is not None and _tokenizer is not None:
            return _model, _tokenizer

        logger = get_inference_logger()
        logger.info(f"Loading model {model_name} on {device} with 4-bit quantization: {load_4bit}")

        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token

            if load_4bit:
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.float32,
                    llm_int8_skip_modules=["lm_head"]
                )
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    quantization_config=bnb_config,
                    device_map="cpu",
                    trust_remote_code=True,
                    torch_dtype=torch.float32
                )
            else:
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    device_map="cpu",
                    trust_remote_code=True,
                    torch_dtype=torch.float32
                )

            model.eval()
            _model = model
            _tokenizer = tokenizer
            logger.info("Model loaded successfully.")
            return model, tokenizer

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

def generate_code(
    prompt: str,
    model: Any,
    tokenizer: Any,
    max_new_tokens: int = 512,
    temperature: float = 0.2,
    do_sample: bool = True,
    timeout_seconds: int = 300
) -> Tuple[Optional[str], ExecutionTag]:
    """
    Generate code from a prompt using the loaded model.
    Returns (generated_code, tag).
    tag can be ExecutionTag.SUCCESS or ExecutionTag.OOM if out of memory.
    """
    logger = get_inference_logger()

    try:
        inputs = tokenizer(prompt, return_tensors="pt")
        input_len = inputs["input_ids"].shape[1]

        with torch.no_grad():
            # Check for potential OOM before generation by monitoring memory
            # For CPU, we rely on the OS OOM killer or explicit checks if needed.
            # However, we wrap in try/except for robustness.
            start_time = time.time()
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=do_sample,
                top_p=0.95,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id
            )
            elapsed = time.time() - start_time

            generated_text = tokenizer.decode(outputs[0][input_len:], skip_special_tokens=True)
            # Extract code block if present
            if "```python" in generated_text:
                start_idx = generated_text.find("```python") + len("```python")
                end_idx = generated_text.find("```", start_idx)
                if end_idx != -1:
                    generated_text = generated_text[start_idx:end_idx].strip()
                else:
                    generated_text = generated_text[start_idx:].strip()

            log_inference_event("generation_complete", {
                "prompt_length": len(prompt),
                "generated_length": len(generated_text),
                "time_elapsed": elapsed
            })
            return generated_text, ExecutionTag.SUCCESS

    except RuntimeError as e:
        error_msg = str(e).lower()
        if "out of memory" in error_msg or "oom" in error_msg:
            logger.warning(f"Out of Memory (OOM) detected during generation: {e}")
            log_inference_event("oom_detected", {"prompt": prompt[:100]})
            return None, ExecutionTag.OOM
        else:
            logger.error(f"Runtime error during generation: {e}")
            raise
    except MemoryError as e:
        logger.warning(f"MemoryError detected during generation: {e}")
        log_inference_event("oom_detected", {"prompt": prompt[:100], "error": str(e)})
        return None, ExecutionTag.OOM
    except Exception as e:
        logger.error(f"Unexpected error during generation: {e}")
        raise

def run_generation_loop(
    tasks: List[Dict[str, Any]],
    output_path: str,
    max_generations: Optional[int] = None,
    timeout_per_task: int = 300
) -> List[Dict[str, Any]]:
    """
    Run generation loop over a list of tasks.
    Handles OOM by skipping the sample and logging.
    Returns list of results.
    """
    logger = get_inference_logger()
    model, tokenizer = load_model()
    
    results = []
    processed_count = 0

    for task in tasks:
        if max_generations and processed_count >= max_generations:
            logger.info(f"Reached max generations limit ({max_generations}). Stopping.")
            break

        task_id = task.get("task_id", "unknown")
        prompt = task.get("prompt", "")
        
        logger.info(f"Processing task {task_id}")
        
        generated_code, tag = generate_code(
            prompt, model, tokenizer, timeout_seconds=timeout_per_task
        )

        if tag == ExecutionTag.OOM:
            # OOM handling: skip sample and log "OOM" flag
            logger.warning(f"Task {task_id} skipped due to OOM.")
            log_inference_event("task_skipped_oom", {"task_id": task_id})
            
            # Record the skip in results
            results.append({
                "task_id": task_id,
                "status": "skipped",
                "tag": "OOM",
                "generated_code": None,
                "error": "Out of Memory"
            })
            continue

        if generated_code is None:
            # Should not happen if tag is not OOM, but handle gracefully
            logger.error(f"Task {task_id} generated no code and no OOM tag.")
            results.append({
                "task_id": task_id,
                "status": "failed",
                "tag": "unknown",
                "generated_code": None
            })
            continue

        # Execute the generated code in sandbox
        test_code = task.get("test_code", "")
        execution_result = execute_code(generated_code, test_code, timeout=timeout_per_task)
        
        # Tag the execution result
        exec_tag = tag_execution_result(execution_result)
        
        result_entry = {
            "task_id": task_id,
            "prompt": prompt,
            "generated_code": generated_code,
            "execution_status": execution_result.status.value,
            "execution_tag": exec_tag.value,
            "execution_time": execution_result.time_taken,
            "error_message": execution_result.error_message
        }
        results.append(result_entry)
        processed_count += 1

    # Save results
    save_results_to_json(results, output_path)
    logger.info(f"Completed {processed_count} tasks. Results saved to {output_path}")
    return results

def main():
    """
    Entry point for running the inference pipeline.
    Expects tasks to be loaded from a JSON file specified in config or environment.
    """
    logger = get_inference_logger()
    logger.info("Starting inference pipeline main.")
    
    # Example usage - in a real scenario, load tasks from data/processed/tasks.json
    # and configure output path
    try:
        # Placeholder for task loading logic
        tasks = [
            {
                "task_id": "example_001",
                "prompt": "Write a function to add two numbers.",
                "test_code": "assert add(1, 2) == 3"
            }
        ]
        
        results = run_generation_loop(tasks, output_path="data/processed/inference_results.json")
        logger.info(f"Pipeline finished. Processed {len(results)} items.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()