import argparse
import json
import sys
import time
import logging
import signal
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from utils
from utils.logging_config import get_logger, setup_root_logger
from utils.hashing_utils import compute_file_hash

# Import from other project modules
# Note: We assume these are importable from the same directory or added to path
# In a real setup, these might be imported as `from code.01_download_and_filter import ...`
# but for simplicity in this script, we define necessary helpers or import directly if available.

# Constants
DEFAULT_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"
DEFAULT_DEVICE = "cpu"
DEFAULT_TIMEOUT = 600  # 10 minutes
DEFAULT_TEMP = 0.0
OUTPUT_DIR = Path("data/traces")
OUTPUT_FILE = OUTPUT_DIR / "cot_traces.jsonl"
THRESHOLD_FILE = Path("data/pilot/tuned_threshold.json")
CONFIG_FILE = Path("config.yaml")

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Task generation timed out")

def check_memory_usage():
    """Check current memory usage and warn if high."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        logger = get_logger(__name__)
        logger.warning(f"Current memory usage: {mem_info.rss / 1024 / 1024:.2f} MB")
        return mem_info.rss / 1024 / 1024
    except ImportError:
        logger = get_logger(__name__)
        logger.warning("psutil not installed, skipping memory check")
        return None

def load_config():
    """Load configuration from config.yaml."""
    import yaml
    config_path = Path(CONFIG_FILE)
    if not config_path.exists():
        logger = get_logger(__name__)
        logger.warning(f"Config file {config_path} not found. Using defaults.")
        return {
            "inference": {
                "model_name": DEFAULT_MODEL,
                "device": DEFAULT_DEVICE,
                "timeout_minutes": DEFAULT_TIMEOUT / 60
            },
            "study": {
                "min_sample_size": 10
            }
        }
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

def load_threshold():
    """Load the tuned threshold from data/pilot/tuned_threshold.json."""
    logger = get_logger(__name__)
    threshold_path = Path(THRESHOLD_FILE)
    
    if not threshold_path.exists():
        logger.error(f"Threshold file {threshold_path} not found. T019 must complete first.")
        raise FileNotFoundError(f"Threshold file {threshold_path} not found. Run T019 first.")
    
    with open(threshold_path, 'r') as f:
        data = json.load(f)
    
    threshold = data.get("optimal_threshold")
    if threshold is None:
        logger.error("optimal_threshold not found in threshold file.")
        raise ValueError("optimal_threshold not found in threshold file.")
    
    logger.info(f"Loaded threshold: {threshold}")
    return threshold

def load_quantized_model(model_name: str, device: str):
    """Load a 4-bit quantized model."""
    from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
    import torch
    
    logger = get_logger(__name__)
    logger.info(f"Loading model: {model_name} on device: {device}")
    
    # Force CPU as per T022 requirement, but allow override if specified in config
    if device == "cuda" and not torch.cuda.is_available():
        logger.warning("CUDA requested but not available, falling back to CPU")
        device = "cpu"
    
    # 4-bit quantization config
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16
    )
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=bnb_config,
            device_map="auto" if device == "cuda" else None,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            low_cpu_mem_usage=True
        )
        
        if device == "cpu":
            model = model.to("cpu")
        
        logger.info("Model loaded successfully")
        return model, tokenizer
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def generate_prompt(task_record: Dict[str, Any]) -> str:
    """Generate a prompt for the LLM based on the task record."""
    # Extract relevant fields from task record
    task_id = task_record.get("task_id", "unknown")
    task_description = task_record.get("task_description", "")
    constraint = task_record.get("constraint", "")
    
    # Format prompt
    prompt = f"""Task ID: {task_id}
    Task Description: {task_description}
    Constraint: {constraint}
    
    Please generate a Chain of Thought (CoT) trace that explicitly addresses the constraint mentioned above.
    Your response should start with "Thought:" and end with "Answer:"."""
    
    return prompt

def generate_cot_trace(model, tokenizer, prompt: str, timeout: int) -> str:
    """Generate a CoT trace with timeout enforcement."""
    logger = get_logger(__name__)
    
    # Set timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)
    
    try:
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        
        # Generate with fixed temperature
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=DEFAULT_TEMP,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id
            )
        
        # Decode output
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract just the generated part (after prompt)
        trace = generated_text[len(prompt):].strip()
        
        logger.info(f"Generated trace length: {len(trace)}")
        return trace
    except TimeoutError:
        logger.error("Generation timed out")
        raise
    finally:
        signal.alarm(0)  # Cancel the alarm

def process_tasks(tasks: List[Dict[str, Any]], model, tokenizer, config: Dict[str, Any], threshold: float) -> List[Dict[str, Any]]:
    """Process all tasks and generate CoT traces."""
    logger = get_logger(__name__)
    results = []
    timeout_minutes = config.get("inference", {}).get("timeout_minutes", 10)
    timeout_seconds = int(timeout_minutes * 60)
    
    for task in tasks:
        task_id = task.get("task_id", "unknown")
        logger.info(f"Processing task: {task_id}")
        
        try:
            # Generate prompt
            prompt = generate_prompt(task)
            
            # Generate trace with timeout
            trace = generate_cot_trace(model, tokenizer, prompt, timeout_seconds)
            
            # Store result
            result = {
                "task_id": task_id,
                "trace": trace,
                "status": "success",
                "timestamp": time.time()
            }
            results.append(result)
            
            # Write immediately to disk (Constitution Principle VI)
            with open(OUTPUT_FILE, 'a') as f:
                f.write(json.dumps(result) + '\n')
            
            logger.info(f"Successfully processed task: {task_id}")
            
        except TimeoutError:
            logger.warning(f"Timeout for task: {task_id}")
            result = {
                "task_id": task_id,
                "trace": "",
                "status": "timeout",
                "error_code": "ERR_TIMEOUT",
                "timestamp": time.time()
            }
            results.append(result)
            
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}")
            result = {
                "task_id": task_id,
                "trace": "",
                "status": "error",
                "error_code": "ERR_GENERAL",
                "error_message": str(e),
                "timestamp": time.time()
            }
            results.append(result)
    
    return results

def write_results(results: List[Dict[str, Any]], output_path: Path):
    """Write all results to output file."""
    logger = get_logger(__name__)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        for result in results:
            f.write(json.dumps(result) + '\n')
    
    logger.info(f"Results written to {output_path}")

def main():
    """Main entry point for CoT generation."""
    parser = argparse.ArgumentParser(description="Generate Chain of Thought traces")
    parser.add_argument("--input", type=str, default="data/filtered/filtered_tasks.jsonl",
                      help="Input file with filtered tasks")
    parser.add_argument("--output", type=str, default=str(OUTPUT_FILE),
                      help="Output file for CoT traces")
    parser.add_argument("--pilot", action="store_true",
                      help="Run in pilot mode (smaller sample)")
    parser.add_argument("--sample-size", type=int, default=None,
                      help="Number of tasks to process (for testing)")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_root_logger()
    logger = get_logger(__name__)
    
    # Load config
    config = load_config()
    
    # Load threshold (required for T022)
    try:
        threshold = load_threshold()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Load tasks
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file {input_path} not found")
        sys.exit(1)
    
    tasks = []
    with open(input_path, 'r') as f:
        for line in f:
            tasks.append(json.loads(line))
    
    # Pilot mode or sample size limit
    if args.pilot:
        tasks = tasks[:10]
        logger.info(f"Pilot mode: processing {len(tasks)} tasks")
    elif args.sample_size:
        tasks = tasks[:args.sample_size]
        logger.info(f"Sample size limit: processing {len(tasks)} tasks")
    
    if not tasks:
        logger.error("No tasks to process")
        sys.exit(1)
    
    # Check memory before starting
    check_memory_usage()
    
    # Load model
    model_name = config.get("inference", {}).get("model_name", DEFAULT_MODEL)
    device = config.get("inference", {}).get("device", DEFAULT_DEVICE)
    
    try:
        model, tokenizer = load_quantized_model(model_name, device)
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        sys.exit(1)
    
    # Process tasks
    logger.info(f"Processing {len(tasks)} tasks")
    results = process_tasks(tasks, model, tokenizer, config, threshold)
    
    # Write results
    output_path = Path(args.output)
    write_results(results, output_path)
    
    # Compute hash of output file
    output_hash = compute_file_hash(output_path)
    logger.info(f"Output file hash: {output_hash}")
    
    # Check minimum sample size
    min_sample_size = config.get("study", {}).get("min_sample_size", 10)
    successful_count = sum(1 for r in results if r.get("status") == "success")
    
    if successful_count < min_sample_size:
        logger.error(f"Underpowered: Effective sample size ({successful_count}) < MVS ({min_sample_size})")
        sys.exit(1)
    
    logger.info(f"Successfully processed {successful_count} tasks out of {len(tasks)}")
    logger.info("CoT generation complete")

if __name__ == "__main__":
    main()