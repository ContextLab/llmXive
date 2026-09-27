import argparse
import json
import sys
import time
import logging
import signal
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import yaml
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel
import gc

# Import project utilities
from utils.logging_config import get_logger, setup_root_logger
from utils.hashing_utils import compute_dict_hash

# Global timeout exception alias
class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Task generation timed out after 10 minutes")

def check_memory_usage():
    """Check current GPU memory usage and log if high."""
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / (1024 ** 3)
        reserved = torch.cuda.memory_reserved() / (1024 ** 3)
        logger = get_logger(__name__)
        logger.warning(f"GPU Memory - Allocated: {allocated:.2f}GB, Reserved: {reserved:.2f}GB")
        if allocated > 10.0:  # Threshold for concern
            logger.error("High GPU memory usage detected. Consider fallback.")
            return True
    return False

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_threshold(threshold_path: str = "data/pilot/tuned_threshold.json") -> float:
    """
    Load the tuned threshold from the pilot study.
    Raises FileNotFoundError if missing, as per T022 requirements.
    """
    path = Path(threshold_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Tuned threshold file not found at '{threshold_path}'. "
            "Task T019 (tune_threshold.py) must be run first to generate this artifact."
        )
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    if 'optimal_threshold' not in data:
        raise ValueError(f"Missing 'optimal_threshold' key in {threshold_path}")
    
    return float(data['optimal_threshold'])

def load_quantized_model(
    model_name: str = "meta-llama/Meta-Llama-3-8B-Instruct", 
    device: str = "cpu",
    fallback_model: str = "mistralai/Mistral-7B-v0.1"
) -> Tuple[Any, Any]:
    """
    Load a 4-bit quantized model.
    Primary: Llama-3-8B (Int4). Fallback: Mistral-7B (Int4) if OOM.
    """
    logger = get_logger(__name__)
    logger.info(f"Attempting to load model: {model_name} on {device}")

    try:
        # Configure 4-bit quantization
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16 if device == "cpu" else torch.float16
        )

        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=bnb_config,
            device_map="auto" if device == "cuda" else None,
            torch_dtype=torch.float16,
            trust_remote_code=True
        )
        
        if device == "cpu":
            model = model.to("cpu")

        logger.info(f"Successfully loaded {model_name}")
        return model, tokenizer

    except (RuntimeError, OSError) as e:
        if "CUDA out of memory" in str(e) or "OOM" in str(e):
            logger.warning(f"OOM error with {model_name}. Falling back to {fallback_model}.")
            # Fallback logic
            return load_quantized_model(model_name=fallback_model, device=device)
        else:
            # Re-raise if not OOM
            raise e

def generate_prompt(task_record: Dict[str, Any]) -> str:
    """
    Construct the prompt for the model based on the task record.
    Expects 'instruction' or 'prompt' field.
    """
    # Standardize input field
    instruction = task_record.get('instruction') or task_record.get('prompt')
    if not instruction:
        raise ValueError("Task record missing 'instruction' or 'prompt'")
    
    # Format for Llama-3
    prompt = f"""<|begin_of_text|><|start_header_id|>user<|end_header_id|>

    Please solve the following reasoning task step-by-step.
    Task: {instruction}

    Think through the problem logically and provide the final answer.
    <|eot_id|>
    <|start_header_id|>assistant<|end_header_id|>

    """
    return prompt

def generate_cot_trace(
    model: Any, 
    tokenizer: Any, 
    prompt: str, 
    timeout_seconds: int = 600
) -> str:
    """
    Generate a CoT trace with a hard timeout.
    """
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    
    try:
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        
        # Generation parameters for deterministic output
        output = model.generate(
            **inputs,
            max_new_tokens=512,
            temperature=0.0,  # Deterministic
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )
        
        # Decode and clean
        full_response = tokenizer.decode(output[0], skip_special_tokens=True)
        
        # Extract just the assistant part
        if "assistant" in full_response:
            parts = full_response.split("assistant")
            trace = parts[-1].strip()
        else:
            trace = full_response.strip()
        
        return trace

    except TimeoutError:
        raise
    finally:
        signal.alarm(0)  # Cancel alarm

def process_tasks(
    tasks: List[Dict[str, Any]],
    model: Any,
    tokenizer: Any,
    output_path: Path
) -> Dict[str, int]:
    """
    Process a list of tasks, generate traces, and write results incrementally.
    Returns statistics.
    """
    logger = get_logger(__name__)
    stats = {
        "total": len(tasks),
        "generated": 0,
        "timeout": 0,
        "errors": 0,
        "skipped": 0
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'a', encoding='utf-8') as f_out:
        for i, task in enumerate(tasks):
            task_id = task.get('id', f'task_{i}')
            logger.info(f"Processing task {i+1}/{len(tasks)}: {task_id}")

            try:
                prompt = generate_prompt(task)
                trace = generate_cot_trace(model, tokenizer, prompt)
                
                result = {
                    "task_id": task_id,
                    "input": task.get('instruction') or task.get('prompt'),
                    "cot_trace": trace,
                    "status": "success",
                    "timestamp": time.time()
                }
                
                # Write immediately (Constitution Principle VI)
                f_out.write(json.dumps(result) + "\n")
                f_out.flush()
                
                stats["generated"] += 1

            except TimeoutError:
                logger.error(f"ERR_TIMEOUT: Task {task_id} timed out.")
                stats["timeout"] += 1
                # Skip task, do not retry
                continue
            except Exception as e:
                logger.error(f"ERR_EMPTY/GEN: Task {task_id} failed with {str(e)}")
                stats["errors"] += 1
                continue

            # Memory check every 10 tasks
            if i % 10 == 0:
                check_memory_usage()
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

    return stats

def write_results(stats: Dict[str, int], output_path: Path, threshold: float):
    """Write final statistics to a log file."""
    logger = get_logger(__name__)
    report = {
        "stats": stats,
        "threshold_used": threshold,
        "output_file": str(output_path),
        "timestamp": time.time()
    }
    
    stats_path = output_path.parent / "generation_stats.json"
    with open(stats_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Generation complete. Stats saved to {stats_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate CoT traces for filtered tasks")
    parser.add_argument("--input", type=str, default="data/filtered/filtered_tasks.jsonl",
                        help="Path to filtered tasks JSONL")
    parser.add_argument("--output", type=str, default="data/traces/cot_traces.jsonl",
                        help="Path to output traces JSONL")
    parser.add_argument("--config", type=str, default="config.yaml",
                        help="Path to config.yaml")
    parser.add_argument("--threshold-path", type=str, default="data/pilot/tuned_threshold.json",
                        help="Path to tuned threshold JSON")
    parser.add_argument("--model", type=str, default="meta-llama/Meta-Llama-3-8B-Instruct",
                        help="Base model name")
    parser.add_argument("--device", type=str, default="cpu",
                        help="Device to run on (cpu or cuda)")
    parser.add_argument("--sample-size", type=int, default=None,
                        help="Limit processing to N tasks (for testing)")
    
    args = parser.parse_args()

    setup_root_logger()
    logger = get_logger(__name__)

    # 1. Load Threshold (Critical Dependency T019)
    try:
        threshold = load_threshold(args.threshold_path)
        logger.info(f"Loaded tuned threshold: {threshold}")
    except FileNotFoundError as e:
        logger.critical(str(e))
        sys.exit(1)

    # 2. Load Config
    config = load_config(args.config)
    min_sample_size = config.get('study', {}).get('min_sample_size', 10)

    # 3. Load Model (T025: Memory Guard)
    try:
        model, tokenizer = load_quantized_model(model_name=args.model, device=args.device)
    except Exception as e:
        logger.critical(f"Failed to load model: {e}")
        sys.exit(1)

    # 4. Load Tasks
    tasks = []
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    with open(input_path, 'r') as f:
        for line in f:
            if line.strip():
                tasks.append(json.loads(line))
    
    if args.sample_size:
        tasks = tasks[:args.sample_size]
    
    logger.info(f"Loaded {len(tasks)} tasks. Sample size limit: {args.sample_size if args.sample_size else 'None'}")

    # 5. Process Tasks
    output_path = Path(args.output)
    # Clear previous output if exists to ensure idempotency for this run
    if output_path.exists():
        output_path.unlink()
        logger.info(f"Cleared previous output file: {output_path}")

    stats = process_tasks(tasks, model, tokenizer, output_path)

    # 6. Check Underpowered (T027)
    if stats["generated"] < min_sample_size:
        logger.error(f"Underpowered: Generated {stats['generated']} traces, required {min_sample_size}")
        report = {
            "effective_sample_size": stats["generated"],
            "threshold": threshold,
            "reason": f"Generated {stats['generated']} traces < min_sample_size {min_sample_size}",
            "timestamp": time.time()
        }
        report_path = Path("data/results/underpowered_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.error(f"Generated underpowered report: {report_path}")
        sys.exit(1)

    # 7. Write Final Stats
    write_results(stats, output_path, threshold)

    logger.info("Task T022 (Full Mode) completed successfully.")

if __name__ == "__main__":
    main()