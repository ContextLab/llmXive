"""
Pilot Study: Generate CoT traces for a small pilot set (N=10) using the filtered dataset.

This script loads the filtered tasks from data/filtered/filtered_tasks.jsonl,
selects a small pilot set (N=10), and generates Chain-of-Thought (CoT) traces
for each task using a lightweight model.

Output: data/pilot/pilot_traces.jsonl
"""
import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

# Import from existing project utilities
from utils.logging_config import get_logger
from utils.hashing_utils import compute_dict_hash
from utils.dataset_integrity import load_and_validate_jsonl

# Configure logging
logger = get_logger(__name__)

# Constants
PILOT_SIZE = 10
DEFAULT_INPUT_PATH = "data/filtered/filtered_tasks.jsonl"
DEFAULT_OUTPUT_DIR = "data/pilot"
DEFAULT_OUTPUT_PATH = "data/pilot/pilot_traces.jsonl"

# Model configuration for pilot (lightweight to ensure fast execution)
# Using a small, fast model suitable for CPU inference
MODEL_NAME = "google/flan-t5-small"
MAX_NEW_TOKENS = 256
TIMEOUT_PER_TASK = 300  # 5 minutes per task for pilot

def load_pilot_tasks(input_path: str, pilot_size: int = PILOT_SIZE) -> List[Dict[str, Any]]:
    """
    Load filtered tasks and select a pilot set.
    
    Args:
        input_path: Path to the filtered tasks JSONL file
        pilot_size: Number of tasks to select for the pilot
        
    Returns:
        List of task records for the pilot set
    """
    logger.info(f"Loading filtered tasks from {input_path}")
    
    try:
        tasks = load_and_validate_jsonl(input_path)
        logger.info(f"Loaded {len(tasks)} total tasks")
    except FileNotFoundError:
        logger.error(f"Filtered tasks file not found: {input_path}")
        logger.error("Please run T015 (01_download_and_filter.py) first to generate filtered data.")
        raise
    except Exception as e:
        logger.error(f"Error loading filtered tasks: {e}")
        raise
    
    # Select pilot set (first N tasks for reproducibility)
    if len(tasks) < pilot_size:
        logger.warning(f"Only {len(tasks)} tasks available, using all for pilot")
        pilot_tasks = tasks
    else:
        pilot_tasks = tasks[:pilot_size]
    
    logger.info(f"Selected {len(pilot_tasks)} tasks for pilot study")
    return pilot_tasks

def generate_prompt(task_record: Dict[str, Any]) -> str:
    """
    Generate a prompt for CoT generation based on task record.
    
    Args:
        task_record: A single task record from the dataset
        
    Returns:
        Formatted prompt string
    """
    # Extract key fields from task record
    question = task_record.get("question", "")
    category = task_record.get("category", "Unknown")
    constraint = task_record.get("constraint", "")
    
    # Build prompt following the dataset's structure
    prompt = f"""Task Category: {category}
Question: {question}
Constraint: {constraint}

Please provide a step-by-step Chain of Thought (CoT) reasoning to solve this task. 
Ensure your reasoning explicitly addresses the constraint provided.
Reasoning:
"""
    return prompt

def generate_cot_trace(
    task_record: Dict[str, Any],
    model_name: str = MODEL_NAME,
    max_new_tokens: int = MAX_NEW_TOKENS,
    timeout: int = TIMEOUT_PER_TASK
) -> Optional[Dict[str, Any]]:
    """
    Generate a CoT trace for a single task using a lightweight model.
    
    This implementation uses a simple, CPU-friendly approach with HuggingFace
    transformers. For a real pilot, we use a small model that can run on CPU.
    
    Args:
        task_record: The task record to generate a trace for
        model_name: Name of the model to use
        max_new_tokens: Maximum number of tokens to generate
        timeout: Timeout in seconds per task
        
    Returns:
        Dictionary containing the trace and metadata, or None if generation fails
    """
    task_id = task_record.get("id", "unknown")
    logger.info(f"Generating CoT trace for task {task_id}")
    
    prompt = generate_prompt(task_record)
    
    start_time = time.time()
    try:
        # Import transformers here to avoid heavy import overhead if not needed
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        import torch
        
        # Check for GPU availability
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {device}")
        
        # Load tokenizer and model
        logger.info(f"Loading model: {model_name}")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        model.to(device)
        model.eval()
        
        # Tokenize input
        inputs = tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        # Generate response with timeout protection
        logger.info(f"Generating response for task {task_id}...")
        with torch.no_grad():
            # Use a thread to handle timeout
            import threading
            import queue
            
            output_queue = queue.Queue()
            
            def generate():
                try:
                    outputs = model.generate(
                        **inputs,
                        max_new_tokens=max_new_tokens,
                        num_return_sequences=1,
                        do_sample=False,  # Deterministic
                        temperature=1.0,
                        pad_token_id=tokenizer.pad_token_id,
                        eos_token_id=tokenizer.eos_token_id
                    )
                    output_queue.put(outputs)
                except Exception as e:
                    output_queue.put(None)
                    logger.error(f"Generation error for task {task_id}: {e}")
            
            thread = threading.Thread(target=generate)
            thread.start()
            thread.join(timeout=timeout)
            
            if thread.is_alive():
                logger.error(f"Timeout generating trace for task {task_id} after {timeout}s")
                return None
            
            outputs = output_queue.get()
            if outputs is None:
                logger.error(f"Generation failed for task {task_id}")
                return None
        
        # Decode response
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        elapsed_time = time.time() - start_time
        
        logger.info(f"Successfully generated trace for task {task_id} in {elapsed_time:.2f}s")
        
        # Construct trace record
        trace_record = {
            "task_id": task_id,
            "prompt": prompt,
            "response": generated_text,
            "model_name": model_name,
            "generation_time_seconds": elapsed_time,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "success",
            "task_category": task_record.get("category"),
            "task_constraint": task_record.get("constraint")
        }
        
        return trace_record
        
    except ImportError as e:
        logger.error(f"Transformers library not available: {e}")
        logger.error("Please install transformers, torch, and other dependencies.")
        raise
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Error generating trace for task {task_id}: {e}")
        return {
            "task_id": task_id,
            "prompt": prompt,
            "response": "",
            "model_name": model_name,
            "generation_time_seconds": elapsed_time,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "error",
            "error_message": str(e),
            "task_category": task_record.get("category"),
            "task_constraint": task_record.get("constraint")
        }

def write_pilot_traces(traces: List[Dict[str, Any]], output_path: str) -> None:
    """
    Write pilot traces to JSONL file.
    
    Args:
        traces: List of trace records
        output_path: Path to output JSONL file
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Writing {len(traces)} pilot traces to {output_path}")
    
    with open(output_path, "w", encoding="utf-8") as f:
        for trace in traces:
            f.write(json.dumps(trace) + "\n")
    
    # Compute and log checksum
    checksum = compute_file_hash(output_path)
    logger.info(f"Pilot traces written successfully. Checksum: {checksum}")
    
    # Log summary statistics
    success_count = sum(1 for t in traces if t.get("status") == "success")
    error_count = len(traces) - success_count
    logger.info(f"Summary: {success_count} successful, {error_count} failed")

def main():
    """Main entry point for pilot study."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate CoT traces for a pilot study")
    parser.add_argument(
        "--input", 
        type=str, 
        default=DEFAULT_INPUT_PATH,
        help=f"Path to filtered tasks JSONL (default: {DEFAULT_INPUT_PATH})"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=DEFAULT_OUTPUT_PATH,
        help=f"Path to output traces JSONL (default: {DEFAULT_OUTPUT_PATH})"
    )
    parser.add_argument(
        "--size", 
        type=int, 
        default=PILOT_SIZE,
        help=f"Number of tasks for pilot (default: {PILOT_SIZE})"
    )
    parser.add_argument(
        "--model", 
        type=str, 
        default=MODEL_NAME,
        help=f"Model name to use (default: {MODEL_NAME})"
    )
    
    args = parser.parse_args()
    
    logger.info("Starting pilot study")
    logger.info(f"Input: {args.input}")
    logger.info(f"Output: {args.output}")
    logger.info(f"Pilot size: {args.size}")
    logger.info(f"Model: {args.model}")
    
    # Load pilot tasks
    pilot_tasks = load_pilot_tasks(args.input, args.size)
    
    if not pilot_tasks:
        logger.error("No tasks found for pilot study")
        sys.exit(1)
    
    # Generate traces
    traces = []
    for i, task in enumerate(pilot_tasks):
        logger.info(f"Processing task {i+1}/{len(pilot_tasks)}")
        trace = generate_cot_trace(task, model_name=args.model)
        if trace:
            traces.append(trace)
    
    if not traces:
        logger.error("No traces were generated")
        sys.exit(1)
    
    # Write results
    write_pilot_traces(traces, args.output)
    
    logger.info("Pilot study completed successfully")

if __name__ == "__main__":
    main()