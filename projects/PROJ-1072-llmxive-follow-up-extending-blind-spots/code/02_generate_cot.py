import argparse
import json
import sys
import time
import logging
import signal
from pathlib import Path
from typing import Dict, List, Any, Optional
import random
import numpy as np
import torch
from transformers import set_seed

# Import from local utils as per API surface
from utils.logging_config import get_logger, setup_root_logger
from utils.hashing_utils import compute_file_hash
from utils.dataset_integrity import validate_record_fields
from utils.runtime_monitor import RuntimeMonitor, create_monitor

logger = get_logger(__name__)

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    import yaml
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def save_config(config: Dict[str, Any], config_path: str = "config.yaml") -> None:
    """Save configuration to YAML file."""
    import yaml
    with open(config_path, 'w') as f:
        yaml.dump(config, f)

def load_threshold(threshold_path: str = "data/pilot/tuned_threshold.json") -> float:
    """Load the tuned threshold from the pilot study."""
    try:
        with open(threshold_path, 'r') as f:
            data = json.load(f)
            return float(data.get('threshold', 0.75))
    except FileNotFoundError:
        logger.error(f"Threshold file not found: {threshold_path}. Run pilot study first.")
        raise FileNotFoundError(f"Threshold file not found: {threshold_path}. Run pilot study first.")

def set_all_seeds(seed: int = 42) -> None:
    """Set seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    set_seed(seed)

def check_memory_usage() -> Dict[str, float]:
    """Check current memory usage."""
    # Placeholder for memory check logic
    return {"cpu_percent": 0.0, "ram_percent": 0.0}

def load_quantized_model(model_name: str = "meta-llama/Llama-3-8B-Instruct-4bit", device: str = "cpu"):
    """Load a 4-bit quantized model."""
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
        torch_dtype=torch.float16
    )
    
    if device == "cpu":
        model = model.to("cpu")
        
    return model, tokenizer

def generate_prompt(task_record: Dict[str, Any]) -> str:
    """Generate the prompt for the model based on the task record."""
    # Assuming task_record has 'instruction' and 'input' fields
    instruction = task_record.get('instruction', '')
    input_text = task_record.get('input', '')
    
    # Format prompt according to Llama-3 template
    prompt = f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{instruction}\n\n{input_text}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
    return prompt

def generate_cot_trace(model, tokenizer, prompt: str, timeout_seconds: int = 600) -> Optional[str]:
    """Generate a Chain of Thought trace with timeout enforcement."""
    try:
        # Set alarm for timeout
        signal.signal(signal.SIGALRM, lambda s, f: (_ for _ in ()).throw(TimeoutError("Generation timed out")))
        signal.alarm(timeout_seconds)
        
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        
        # Generate with temperature=0.0 for determinism
        output = model.generate(
            **inputs,
            max_new_tokens=512,
            temperature=0.0,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )
        
        # Cancel alarm
        signal.alarm(0)
        
        # Decode and clean up
        full_response = tokenizer.decode(output[0], skip_special_tokens=True)
        
        # Extract assistant response
        if "<|start_header_id|>assistant<|end_header_id|>" in full_response:
            response = full_response.split("<|start_header_id|>assistant<|end_header_id|>")[1]
            if "<|eot_id|>" in response:
                response = response.split("<|eot_id|>")[0]
        else:
            response = full_response
        
        return response.strip()
        
    except TimeoutError as e:
        logger.warning(f"ERR_TIMEOUT: Generation timed out after {timeout_seconds} seconds")
        return None
    except Exception as e:
        logger.error(f"ERR_GENERATION: {str(e)}")
        return None
    finally:
        signal.alarm(0)

def write_trace_to_file(trace: Dict[str, Any], output_path: Path) -> None:
    """Append a trace to the output JSONL file immediately."""
    with open(output_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(trace) + '\n')

def write_runtime_status(status: Dict[str, Any], output_path: Path) -> None:
    """Write runtime status to a JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2)

def log_error(error_code: str, message: str, task_id: Optional[str] = None) -> None:
    """Log an error with a specific code."""
    logger.error(f"[{error_code}] {message} (Task ID: {task_id})")

def handle_oom_fallback() -> None:
    """Handle Out of Memory error by triggering fallback sequence."""
    logger.error("ERR_OOM: Out of memory detected. Triggering fallback sequence.")
    # Fallback logic is implemented in T051b (Kaggle runner)
    # This function serves as the trigger point
    raise MemoryError("Out of memory. Fallback sequence triggered.")

def main():
    """Main entry point for CoT trace generation."""
    parser = argparse.ArgumentParser(description="Generate CoT traces for filtered tasks.")
    parser.add_argument('--input', type=str, default='data/filtered/filtered_tasks.jsonl', help='Input filtered tasks file')
    parser.add_argument('--output', type=str, default='data/traces/cot_traces.jsonl', help='Output traces file')
    parser.add_argument('--config', type=str, default='config.yaml', help='Configuration file')
    parser.add_argument('--model', type=str, default='meta-llama/Llama-3-8B-Instruct-4bit', help='Model name')
    parser.add_argument('--device', type=str, default='cpu', help='Device to use (cpu/cuda)')
    parser.add_argument('--timeout', type=int, default=600, help='Per-task timeout in seconds')
    parser.add_argument('--sample-size', type=int, default=None, help='Number of tasks to process (None for all)')
    args = parser.parse_args()

    # Setup logging
    setup_root_logger()
    
    # Load config
    config = load_config(args.config)
    study_config = config.get('study', {})
    max_runtime_hours = study_config.get('max_runtime_hours', 6)
    min_sample_size = study_config.get('min_sample_size', 40)
    
    # Set seeds
    set_all_seeds(42)
    
    # Load model
    logger.info(f"Loading model: {args.model} on {args.device}")
    try:
        model, tokenizer = load_quantized_model(args.model, args.device)
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        sys.exit(1)
    
    # Load threshold
    try:
        threshold = load_threshold()
        logger.info(f"Loaded threshold: {threshold}")
    except FileNotFoundError:
        logger.error("Threshold file missing. Run pilot study first.")
        sys.exit(1)
    
    # Load tasks
    tasks = []
    with open(args.input, 'r', encoding='utf-8') as f:
        for line in f:
            tasks.append(json.loads(line))
    
    if args.sample_size:
        tasks = tasks[:args.sample_size]
        
    logger.info(f"Loaded {len(tasks)} tasks")
    
    # Initialize runtime monitor
    monitor = create_monitor(max_runtime_seconds=max_runtime_hours * 3600)
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Clear output file if exists
    if output_path.exists():
        output_path.unlink()
    
    # Process tasks
    completed = 0
    skipped = 0
    errors = 0
    
    for i, task in enumerate(tasks):
        task_id = task.get('id', f'task_{i}')
        
        # Check global runtime
        if not monitor.can_continue():
            logger.warning("ERR_TIMEOUT_GLOBAL: Global runtime limit exceeded")
            status = {
                "elapsed_time": monitor.elapsed_time,
                "reason": "Runtime limit exceeded",
                "timestamp": monitor.get_timestamp(),
                "effective_sample_size": completed
            }
            write_runtime_status(status, Path("data/results/runtime_status.json"))
            break
        
        try:
            # Check memory
            mem_usage = check_memory_usage()
            if mem_usage.get('ram_percent', 0) > 90:
                handle_oom_fallback()
            
            # Generate prompt
            prompt = generate_prompt(task)
            
            # Generate trace
            trace_text = generate_cot_trace(model, tokenizer, prompt, args.timeout)
            
            if trace_text is None:
                log_error("ERR_TIMEOUT", "Generation timed out", task_id)
                skipped += 1
                continue
            
            if trace_text.strip() == "":
                log_error("ERR_EMPTY", "Generated empty response", task_id)
                skipped += 1
                continue
            
            # Create trace record
            trace_record = {
                "task_id": task_id,
                "constraint": task.get('constraint', ''),
                "trace": trace_text,
                "timestamp": monitor.get_timestamp(),
                "status": "completed"
            }
            
            # Write immediately to file (Constitution Principle VI)
            write_trace_to_file(trace_record, output_path)
            completed += 1
            
            # Log progress
            if completed % 10 == 0:
                logger.info(f"Processed {completed}/{len(tasks)} tasks")
                
        except MemoryError:
            # Trigger GPU escape hatch
            logger.error("ERR_OOM: Triggering GPU escape hatch")
            # This would invoke T051b logic
            sys.exit(1)
        except Exception as e:
            log_error("ERR_UNKNOWN", f"Unexpected error: {e}", task_id)
            errors += 1
            continue
    
    # Write final runtime status
    status = {
        "elapsed_time": monitor.elapsed_time,
        "reason": "Completed",
        "timestamp": monitor.get_timestamp(),
        "effective_sample_size": completed,
        "skipped": skipped,
        "errors": errors
    }
    write_runtime_status(status, Path("data/results/runtime_status.json"))
    
    logger.info(f"Generation complete. Completed: {completed}, Skipped: {skipped}, Errors: {errors}")
    
    # Check sample size
    if completed < min_sample_size:
        logger.error(f"ERR_UNDERPOWERED: Sample size {completed} < minimum {min_sample_size}")
        underpowered_report = {
            "effective_sample_size": completed,
            "threshold": threshold,
            "reason": f"Sample size {completed} is below minimum required {min_sample_size}",
            "timestamp": monitor.get_timestamp()
        }
        with open("data/results/underpowered_report.json", 'w') as f:
            json.dump(underpowered_report, f, indent=2)
        sys.exit(1)

if __name__ == "__main__":
    main()
