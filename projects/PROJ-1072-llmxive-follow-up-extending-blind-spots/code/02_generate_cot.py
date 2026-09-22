import argparse
import json
import sys
import time
import logging
import signal
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone

# Import from sibling modules
from utils.logging_config import get_logger, setup_root_logger
from utils.hashing_utils import compute_dict_hash
from utils.dataset_integrity import load_and_validate_jsonl

# Local imports for model handling
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    import torch
except ImportError:
    print("Error: transformers, torch, or bitsandbytes required. Install via requirements.txt")
    sys.exit(1)

class TimeoutError(Exception):
    """Custom timeout exception for generation tasks."""
    pass

def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError("Generation timeout: 10 minutes exceeded")

def check_memory_usage():
    """Check memory usage and return True if critical levels are reached."""
    if torch.cuda.is_available():
        mem_allocated = torch.cuda.memory_allocated()
        mem_total = torch.cuda.total_memory()
        usage_ratio = mem_allocated / mem_total
        if usage_ratio > 0.95:
            return True
    else:
        # Basic CPU memory check (approximate)
        try:
            import psutil
            process = psutil.Process(os.pid)
            mem_info = process.memory_info()
            # Assuming 1GB limit for safety on CPU
            if mem_info.rss > 1024 * 1024 * 1024:
                return True
        except ImportError:
            pass # Skip if psutil not available
    return False

def load_quantized_model(model_name: str = "meta-llama/Llama-3-8B-Int4", device: str = "cpu"):
    """Load a 4-bit quantized model."""
    logger = get_logger(__name__)
    logger.info(f"Loading model: {model_name} on {device}")
    
    try:
        n_bytes_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=False
        )
        
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=n_bytes_config,
            device_map="auto" if device == "cuda" else None,
            torch_dtype=torch.float16
        )
        if device == "cpu":
            model = model.to(device)
        
        logger.info("Model loaded successfully.")
        return model, tokenizer
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def generate_prompt(task_record: Dict[str, Any]) -> str:
    """Generate the prompt for the task."""
    task_id = task_record.get("id", "unknown")
    category = task_record.get("category", "unknown")
    constraint = task_record.get("constraint", "")
    problem_text = task_record.get("problem_text", "")
    
    prompt = (
        f"Task ID: {task_id}\n"
        f"Category: {category}\n"
        f"Constraint: {constraint}\n\n"
        f"Problem:\n{problem_text}\n\n"
        f"Please solve the problem step-by-step, explicitly adhering to the constraint."
    )
    return prompt

def generate_cot_trace(
    model,
    tokenizer,
    prompt: str,
    timeout_seconds: int = 600,
    logger: logging.Logger = None
) -> Tuple[Optional[str], bool]:
    """
    Generate a CoT trace with a fixed 10-minute timeout.
    Returns (trace_text, is_timeout).
    """
    if logger is None:
        logger = get_logger(__name__)
    
    # Set timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    
    try:
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        start_time = time.time()
        
        outputs = model.generate(
            **inputs,
            max_new_tokens=512,
            temperature=0.0,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )
        
        elapsed = time.time() - start_time
        trace = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        
        signal.alarm(0) # Cancel alarm
        logger.info(f"Generation completed in {elapsed:.2f}s")
        return trace, False

    except TimeoutError:
        signal.alarm(0)
        logger.error("Timeout occurred during generation.")
        return None, True
    except Exception as e:
        signal.alarm(0)
        logger.error(f"Generation failed: {e}")
        return None, False

def process_tasks(
    input_path: Path,
    output_path: Path,
    model_name: str,
    device: str = "cpu",
    timeout_per_task: int = 600
):
    """
    Process tasks, generate traces, and enforce stopping rule.
    """
    logger = setup_root_logger("cot_generation")
    logger.info(f"Starting CoT generation pipeline. Input: {input_path}, Output: {output_path}")
    
    # Load filtered tasks
    try:
        tasks = load_and_validate_jsonl(input_path)
        logger.info(f"Loaded {len(tasks)} tasks.")
    except FileNotFoundError:
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    # Load model
    try:
        model, tokenizer = load_quantized_model(model_name, device)
    except Exception as e:
        logger.error(f"Failed to initialize model: {e}")
        sys.exit(1)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    successful_count = 0
    failed_count = 0
    timeout_count = 0
    
    with open(output_path, "w", encoding="utf-8") as f_out:
        for idx, task in enumerate(tasks):
            task_id = task.get("id", f"task_{idx}")
            logger.info(f"Processing {task_id} ({idx+1}/{len(tasks)})")
            
            # Memory Guard Check
            if check_memory_usage():
                logger.warning("Memory usage critical. Attempting fallback or stopping.")
                # In a real scenario, we might switch to a smaller model here.
                # For this implementation, we log and skip to prevent crash.
                failed_count += 1
                continue

            prompt = generate_prompt(task)
            trace, is_timeout = generate_cot_trace(
                model, tokenizer, prompt, timeout_per_task, logger
            )
            
            if is_timeout:
                timeout_count += 1
                logger.warning(f"Task {task_id} timed out. Skipping.")
                continue
            
            if trace is None:
                failed_count += 1
                logger.warning(f"Task {task_id} failed generation.")
                continue
            
            if len(trace.strip()) == 0:
                failed_count += 1
                logger.warning(f"Task {task_id} generated empty trace.")
                continue
            
            # Write immediately (Constitution Principle VI)
            record = {
                "task_id": task_id,
                "trace": trace,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "success"
            }
            f_out.write(json.dumps(record) + "\n")
            successful_count += 1
    
    # Stopping Rule Check (T057)
    effective_sample_size = successful_count
    min_valid_sample = 40
    
    logger.info(f"Generation complete. Success: {successful_count}, Timeout: {timeout_count}, Failed: {failed_count}")
    
    if effective_sample_size < min_valid_sample:
        msg = (
            f"STOPPING RULE TRIGGERED: Effective sample size ({effective_sample_size}) "
            f"is less than minimum valid sample ({min_valid_sample}). "
            f"Analysis would be underpowered. Halting pipeline."
        )
        logger.error(msg)
        # Write a stopping rule report
        report_path = output_path.parent / "stopping_rule_report.json"
        report = {
            "effective_sample_size": effective_sample_size,
            "minimum_valid_sample": min_valid_sample,
            "status": "underpowered",
            "message": msg,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        # Halt execution
        raise SystemExit(1)
    else:
        logger.info(f"Stopping rule check passed. Effective sample size ({effective_sample_size}) >= {min_valid_sample}.")

def main():
    parser = argparse.ArgumentParser(description="Generate CoT traces for Blind-Spots-Bench tasks.")
    parser.add_argument("--input", type=str, required=True, help="Path to filtered tasks JSONL")
    parser.add_argument("--output", type=str, required=True, help="Path to output traces JSONL")
    parser.add_argument("--model", type=str, default="meta-llama/Llama-3-8B-Int4", help="Model name")
    parser.add_argument("--device", type=str, default="cpu", help="Device (cpu or cuda)")
    parser.add_argument("--timeout", type=int, default=600, help="Timeout per task in seconds")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        print(f"Error: Input file {input_path} not found.")
        sys.exit(1)
    
    try:
        process_tasks(
            input_path=input_path,
            output_path=output_path,
            model_name=args.model,
            device=args.device,
            timeout_per_task=args.timeout
        )
    except SystemExit as e:
        if e.code == 1:
            # Stopping rule triggered
            sys.exit(1)
        raise
    except Exception as e:
        print(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
