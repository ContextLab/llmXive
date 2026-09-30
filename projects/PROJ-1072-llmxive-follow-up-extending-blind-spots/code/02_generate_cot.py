import argparse
import json
import sys
import time
import logging
import signal
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timezone

# Local imports matching the API surface
from utils.logging_config import get_logger, setup_root_logger
from utils.runtime_monitor import create_monitor, RuntimeMonitor
from utils.hashing_utils import compute_dict_hash

# Configuration and helper imports
CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"
THRESHOLD_PATH = Path(__file__).parent.parent / "data/pilot/tuned_threshold.json"
OUTPUT_DIR = Path(__file__).parent.parent / "data/traces"
OUTPUT_FILE = OUTPUT_DIR / "cot_traces.jsonl"

def load_config(config_path: Path) -> Dict[str, Any]:
    """Load YAML config using standard library (simple parser for this project)."""
    import yaml
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def save_config(config: Dict[str, Any], config_path: Path):
    import yaml
    with open(config_path, 'w') as f:
        yaml.dump(config, f)

def load_threshold(threshold_path: Path) -> float:
    """Load the tuned threshold from the pilot study artifact."""
    if not threshold_path.exists():
        raise FileNotFoundError(f"Tuned threshold file not found at {threshold_path}. "
                                "Run code/tune_threshold.py (T019) first.")
    with open(threshold_path, 'r') as f:
        data = json.load(f)
    return data.get("optimal_threshold", 0.85)

def set_all_seeds(seed: int = 42):
    """Set seeds for reproducibility."""
    import random
    import numpy as np
    import torch
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def check_memory_usage():
    """Check current memory usage. If high, log warning."""
    # Simple check using psutil if available, otherwise skip
    try:
        import psutil
        mem = psutil.virtual_memory()
        if mem.percent > 90:
            get_logger(__name__).warning("High memory usage detected: >90%")
    except ImportError:
        pass

def load_quantized_model(model_name: str, device: str):
    """Load a 4-bit quantized model. Returns model and tokenizer."""
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16
    )
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto" if device == "cuda" else None,
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True
    )
    if device == "cpu":
        model = model.to("cpu")
    return model, tokenizer

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Inference timed out after 10 minutes")

def generate_prompt(task_record: Dict[str, Any]) -> str:
    """Construct the prompt for the LLM based on the task record."""
    # Assuming task_record has 'question' and 'constraint' fields based on context
    question = task_record.get("question", "")
    constraint = task_record.get("constraint", "")
    
    prompt = f"""Task: {question}
    
    Constraint: {constraint}
    
    Please think step-by-step to solve the task while explicitly adhering to the constraint.
    Start your response with "Step 1:"."""
    
    return prompt

def generate_cot_trace(model, tokenizer, prompt: str, timeout_seconds: int = 600) -> str:
    """Generate a Chain-of-Thought trace with a hard timeout."""
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    
    try:
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        # Temperature 0.0 for deterministic output
        outputs = model.generate(
            **inputs,
            max_new_tokens=512,
            temperature=0.0,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )
        # Decode and clean
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Remove the prompt from the output if it was echoed
        if generated_text.startswith(prompt):
            generated_text = generated_text[len(prompt):]
        return generated_text.strip()
    except TimeoutError:
        raise
    finally:
        signal.alarm(0)

def write_trace_to_file(trace_record: Dict[str, Any], output_file: Path, logger: logging.Logger):
    """Write a single trace record to the JSONL file immediately."""
    # Ensure directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Append to file
    with open(output_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(trace_record) + '\n')
    
    logger.info(f"Trace written to {output_file}: ID={trace_record.get('task_id')}")

def main():
    logger = setup_root_logger()
    logger.info("Starting CoT Generation (T022/T026)")
    
    # Load config
    config = load_config(CONFIG_PATH)
    model_name = config.get("inference", {}).get("model_name", "mistralai/Mistral-7B-v0.1-4bit")
    device = config.get("inference", {}).get("device", "cpu")
    sample_size = config.get("study", {}).get("min_sample_size", 10)
    
    # Load threshold
    threshold = load_threshold(THRESHOLD_PATH)
    logger.info(f"Loaded threshold: {threshold}")
    
    # Setup seeds
    set_all_seeds(42)
    
    # Initialize Runtime Monitor for global limit (T023a)
    # Global limit: 6 hours = 21600 seconds
    monitor = create_monitor(limit_seconds=21600, logger=logger)
    
    # Load model
    logger.info(f"Loading model {model_name} on {device}...")
    try:
        model, tokenizer = load_quantized_model(model_name, device)
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        sys.exit(1)
    
    # Load input data (filtered tasks)
    input_path = Path(__file__).parent.parent / "data/filtered/filtered_tasks.jsonl"
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}. Run T012 first.")
        sys.exit(1)
    
    tasks = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            tasks.append(json.loads(line))
    
    logger.info(f"Loaded {len(tasks)} tasks.")
    
    # Check underpowered condition before starting (T027 logic)
    # If we have fewer tasks than min_sample_size, we can't proceed meaningfully
    # However, the spec says "If count of *successfully generated* traces < min_sample_size, halt"
    # We check available tasks first. If 0, we can't even try.
    if len(tasks) == 0:
        logger.error("No tasks available for generation.")
        sys.exit(1)
    
    # If the available tasks are fewer than the minimum required sample size,
    # we still attempt to generate, but we will check the final count later.
    # For now, we proceed.
    
    # Output file
    output_file = OUTPUT_FILE
    
    # Clear existing output if any (fresh run)
    if output_file.exists():
        output_file.unlink()
    
    generated_count = 0
    
    for idx, task in enumerate(tasks):
        task_id = task.get("id", f"task_{idx}")
        
        # Check global runtime limit (T023a)
        if not monitor.can_proceed(10 * 60): # 10 min per task
            logger.warning("Global runtime limit reached. Halting generation.")
            # Generate underpowered report if we haven't met the minimum
            effective_sample = generated_count
            if effective_sample < sample_size:
                report = {
                    "effective_sample_size": effective_sample,
                    "threshold": threshold,
                    "reason": f"Global runtime limit exceeded before reaching min_sample_size ({sample_size}).",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                report_path = Path(__file__).parent.parent / "data/results/underpowered_report.json"
                report_path.parent.mkdir(parents=True, exist_ok=True)
                with open(report_path, 'w') as f:
                    json.dump(report, f, indent=2)
                logger.error(f"Underpowered report written to {report_path}")
            sys.exit(0) # Exit cleanly, but report generated
        
        logger.info(f"Processing task {idx+1}/{len(tasks)}: {task_id}")
        
        try:
            prompt = generate_prompt(task)
            trace_text = generate_cot_trace(model, tokenizer, prompt, timeout_seconds=600)
            
            # Construct trace record
            trace_record = {
                "task_id": task_id,
                "original_task": task,
                "cot_trace": trace_text,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "hash": compute_dict_hash(trace_record)
            }
            
            # T026: Write raw CoT traces immediately to data/traces/cot_traces.jsonl
            write_trace_to_file(trace_record, output_file, logger)
            generated_count += 1
            
            # Log progress
            logger.info(f"Successfully generated trace for {task_id}. Total: {generated_count}")
            
        except TimeoutError:
            logger.warning(f"ERR_TIMEOUT: Task {task_id} timed out. Skipping.")
            # Skip task, do not crash
        except Exception as e:
            logger.error(f"ERR_UNKNOWN: Error processing task {task_id}: {e}")
            # Skip task
    
    # Post-run check: T027 - Stopping Rule Check
    if generated_count < sample_size:
        logger.warning(f"Effective sample size ({generated_count}) is less than min_sample_size ({sample_size}).")
        report = {
            "effective_sample_size": generated_count,
            "threshold": threshold,
            "reason": f"Generated {generated_count} traces, which is less than required {sample_size}.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        report_path = Path(__file__).parent.parent / "data/results/underpowered_report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.error(f"Underpowered report written to {report_path}")
        sys.exit(1)
    
    logger.info(f"Generation complete. {generated_count} traces written to {output_file}")

if __name__ == "__main__":
    main()