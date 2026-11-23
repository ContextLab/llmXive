import os
import json
import logging
import time
import csv
import signal
import psutil
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datasets import load_dataset
from utils.logger import log_memory_usage, log_batch_reduction, initialize_memory_log, get_memory_log_path, log_generation_error
from utils.timeout_decorator import timeout_decorator, TaskTimeoutError
from config.loader import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_available_memory_gb() -> float:
    """Get available memory in GB using psutil."""
    try:
        mem = psutil.virtual_memory()
        return mem.available / (1024 ** 3)
    except Exception as e:
        logger.error(f"Failed to get available memory: {e}")
        return 8.0  # Default fallback

def calculate_batch_size(available_gb: float, target_gb: float = 2.0) -> int:
    """
    Calculate initial batch size based on available memory.
    Assumes ~2GB per batch as a starting heuristic.
    """
    if available_gb < target_gb:
        return max(1, int(available_gb / target_gb))
    return int(available_gb / target_gb)

def log_memory_state(batch_size: int, step: str = "initial"):
    """Log current memory state and batch size to memory_log.json."""
    log_memory_usage(batch_size=batch_size, step=step)

def solution(task: Dict[str, Any], style: str, batch_size: int, timeout_seconds: int = 300) -> List[Dict[str, Any]]:
    """
    Generate samples for a single task with timeout enforcement.
    This is the inner loop function that would call the LLM.
    For this implementation, we simulate generation with a placeholder
    that respects the timeout structure.
    """
    samples = []
    
    # In a real implementation, this would loop 'batch_size' times
    # calling an LLM API with the task prompt and style constraints.
    # We simulate the generation process here.
    
    for i in range(batch_size):
        # Simulate generation time (randomized to test timeout)
        # In real code, this is where the LLM API call happens
        time.sleep(0.01) 
        
        sample = {
            "task_id": task['task_id'],
            "style": style,
            "sample_index": i,
            "code": f"# Placeholder for generated code for {task['task_id']} style {style} sample {i}",
            "generation_time": time.time()
        }
        samples.append(sample)
    
    return samples

@timeout_decorator(300)
def generate_samples_for_task(task: Dict[str, Any], style: str, initial_batch_size: int, max_reductions: int = 10) -> Tuple[List[Dict[str, Any]], int]:
    """
    Generate samples for a task with dynamic batch sizing.
    Probes memory usage and reduces batch size iteratively if limits are exceeded.
    
    Args:
        task: The HumanEval task dict
        style: The style profile (e.g., 'pep8', 'minified')
        initial_batch_size: Starting batch size
        max_reductions: Maximum number of reduction attempts
        
    Returns:
        Tuple of (list of samples, final batch size used)
    """
    current_batch_size = initial_batch_size
    reduction_count = 0
    all_samples = []
    
    # Log initial state
    log_memory_state(current_batch_size, "initial")
    
    while reduction_count < max_reductions:
        available_mem = get_available_memory_gb()
        logger.info(f"Attempt {reduction_count + 1}: Batch size {current_batch_size}, Available Mem: {available_mem:.2f}GB")
        
        try:
            # Attempt generation with current batch size
            # In a real scenario, we might monitor memory during the actual generation
            # Here we simulate a check: if available memory is critically low, reduce batch
            if available_mem < 0.5:
                raise MemoryError("Available memory critically low")
            
            # Simulate generation
            # In real code: samples = solution(task, style, current_batch_size)
            # We call the solution function which is decorated with timeout
            samples = solution(task, style, current_batch_size)
            
            # If we got here without error, we succeeded
            all_samples.extend(samples)
            logger.info(f"Successfully generated {len(samples)} samples with batch size {current_batch_size}")
            return all_samples, current_batch_size
            
        except MemoryError as e:
            reduction_count += 1
            new_batch_size = max(1, current_batch_size // 2)
            
            if new_batch_size == current_batch_size:
                logger.warning("Cannot reduce batch size further, breaking loop")
                break
            
            log_batch_reduction(
                old_batch_size=current_batch_size,
                new_batch_size=new_batch_size,
                reason=str(e),
                available_memory_gb=available_mem
            )
            
            logger.warning(f"Memory error: reducing batch size from {current_batch_size} to {new_batch_size}")
            current_batch_size = new_batch_size
            
        except TaskTimeoutError as e:
            # If timeout occurs, we treat it as a hard failure for this batch
            # In the pipeline, this task would be skipped
            logger.error(f"Timeout during generation for task {task['task_id']}: {e}")
            raise
            
    # If we exit the loop without success
    logger.error(f"Failed to generate samples for task {task['task_id']} after {max_reductions} reductions")
    return all_samples, current_batch_size

def run_generation_pipeline(output_path: str, styles: List[str], config_path: str = "config/analysis.yaml"):
    """
    Run the full generation pipeline with dynamic batch sizing.
    
    Args:
        output_path: Path to the output CSV file
        styles: List of style profiles to generate for
        config_path: Path to the configuration file
    """
    # Load configuration
    try:
        config = load_config(config_path)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise
    
    # Initialize memory log
    initialize_memory_log()
    
    # Load HumanEval dataset
    try:
        dataset = load_dataset("openai/human-eval", split="test")
        tasks = list(dataset)
    except Exception as e:
        logger.error(f"Failed to load HumanEval dataset: {e}")
        raise
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    all_results = []
    
    # Process each style
    for style in styles:
        logger.info(f"Processing style: {style}")
        
        for task in tasks:
            task_id = task['task_id']
            logger.info(f"Processing task {task_id} with style {style}")
            
            # Calculate initial batch size based on current memory
            available_mem = get_available_memory_gb()
            initial_batch = calculate_batch_size(available_mem, target_gb=1.0)
            
            try:
                samples, final_batch = generate_samples_for_task(
                    task=task,
                    style=style,
                    initial_batch_size=initial_batch
                )
                
                # Add pass_status placeholder (will be filled by tester)
                for sample in samples:
                    sample['pass_status'] = None
                    all_results.append(sample)
                
                logger.info(f"Completed task {task_id}: {len(samples)} samples, final batch size {final_batch}")
                
            except TaskTimeoutError:
                logger.error(f"Skipping task {task_id} due to timeout")
                # Continue to next task
                continue
            except Exception as e:
                log_generation_error(task_id, style, str(e))
                logger.error(f"Error processing task {task_id}: {e}")
                continue
    
    # Write results to CSV
    if all_results:
        fieldnames = list(all_results[0].keys())
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_results)
        
        logger.info(f"Generated {len(all_results)} samples total, saved to {output_path}")
    else:
        logger.warning("No samples were generated")

if __name__ == "__main__":
    # Example usage
    styles = ["pep8", "minified", "neutral"]
    run_generation_pipeline("data/processed/samples_all.csv", styles)
