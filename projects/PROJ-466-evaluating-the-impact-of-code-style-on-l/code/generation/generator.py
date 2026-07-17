import os
import json
import logging
import time
import csv
import signal
from pathlib import Path
from typing import List, Dict, Any, Optional
from functools import wraps

from utils.logger import log_memory_usage, log_batch_reduction, log_generation_error, log_timeout_error
from utils.timeout_decorator import TaskTimeoutError, timeout_decorator
from config.loader import load_config, get_config_value
from generation.loader import get_humaneval_tasks

logger = logging.getLogger(__name__)

def get_available_memory_gb() -> float:
    """
    Estimate available memory in GB.
    
    Note: This is a simplified implementation. In production, use psutil.
    """
    # Fallback default if psutil not available
    return 16.0

def calculate_batch_size(available_gb: float, max_gb: float = 7.0) -> int:
    """
    Calculate batch size based on available memory.
    
    Args:
        available_gb: Available memory in GB
        max_gb: Maximum memory to use (default 7GB)
        
    Returns:
        Recommended batch size
    """
    # Simple heuristic: start with 50, reduce if memory is low
    if available_gb >= max_gb:
        return 50
    elif available_gb >= 4.0:
        return 25
    elif available_gb >= 2.0:
        return 10
    else:
        return 1

def _mock_llm_call(prompt: str, style: str, seed: int, temperature: float) -> str:
    """
    Mock LLM call that generates deterministic code based on inputs.
    This simulates the LLM response without requiring an actual API.
    """
    # Deterministic generation based on seed and style
    # In a real implementation, this would call the actual LLM model
    base_code = f"""# Task Style: {style}
# Seed: {seed}
# Temperature: {temperature}

def solution():
    pass
"""
    # Add style-specific modifications
    if style == "pep8":
        base_code += "\n# PEP8 compliant formatting\n"
        base_code += "    # Proper indentation and spacing\n"
    elif style == "minified":
        base_code = base_code.replace("\n", ";").replace("    ", "")
    elif style == "neutral":
        base_code += "\n# Neutral style\n"
    
    return base_code

@timeout_decorator(300)  # 5 minute timeout per task
def generate_samples_for_task(
    task: Dict[str, Any],
    style: str,
    num_samples: int = 20,
    temperature: float = 0.7,
    seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Generate multiple code samples for a single task with a specific style.
    
    Args:
        task: HumanEval task dictionary
        style: Style name (neutral, pep8, minified)
        num_samples: Number of samples to generate
        temperature: Sampling temperature
        seed: Random seed
        
    Returns:
        List of generated samples
    """
    samples = []
    task_id = task.get('problem_id', 'unknown')
    prompt = task.get('prompt', '')
    
    logger.info(f"Generating {num_samples} samples for task {task_id} with style {style}")
    
    for i in range(num_samples):
        # Use a deterministic seed for reproducibility
        sample_seed = seed + i
        try:
            # Simulate LLM call
            code = _mock_llm_call(prompt, style, sample_seed, temperature)
            
            sample = {
                'task_id': task_id,
                'style': style,
                'sample_id': f"{task_id}_{style}_{i}",
                'code': code,
                'pass_status': None  # Will be filled by tester
            }
            samples.append(sample)
            
        except Exception as e:
            log_generation_error(task_id, style, f"Error generating sample {i}: {str(e)}")
            logger.error(f"Error generating sample {i} for {task_id} ({style}): {e}")
            # Continue with next sample rather than failing the whole task
            continue
    
    return samples

def run_generation_pipeline(config_path: Optional[str] = None) -> None:
    """
    Run the full generation pipeline for all tasks and styles.
    Generates samples and immediately writes them to samples_all.csv
    before any testing or filtering occurs.
    
    Args:
        config_path: Optional path to config file
    """
    if config_path is None:
        config_path = "config/analysis.yaml"
    
    config = load_config(config_path)
    
    # Get styles from prompt files
    styles = ['neutral', 'pep8', 'minified']
    output_path = Path("data/processed/samples_all.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Get tasks
    tasks = get_humaneval_tasks()
    
    # Initialize output file
    fieldnames = ['task_id', 'style', 'sample_id', 'code', 'pass_status']
    
    # Track statistics
    total_tasks = len(tasks)
    completed_tasks = 0
    skipped_tasks = 0
    total_samples = 0
    
    # Open file for writing
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for task in tasks:
            task_id = task.get('problem_id', 'unknown')
            logger.info(f"Processing task {task_id} ({completed_tasks + 1}/{total_tasks})")
            
            task_completed = False
            
            for style in styles:
                try:
                    # Generate samples with timeout
                    samples = generate_samples_for_task(task, style)
                    
                    # Immediately write raw samples to CSV
                    for sample in samples:
                        writer.writerow(sample)
                        total_samples += 1
                    
                    task_completed = True
                    logger.info(f"Generated {len(samples)} samples for {task_id} ({style})")
                    
                except TaskTimeoutError:
                    # Log timeout error and skip this task entirely
                    log_timeout_error(task_id, style, 300)
                    logger.warning(f"Timeout exceeded for task {task_id} ({style}). Skipping task.")
                    skipped_tasks += 1
                    # Break out of style loop to skip remaining styles for this task
                    break
                    
                except Exception as e:
                    log_generation_error(task_id, style, str(e))
                    logger.error(f"Error generating samples for {task_id} ({style}): {e}")
                    # Continue with next style
                    continue
          
            if task_completed:
                completed_tasks += 1
            else:
                skipped_tasks += 1
    
    logger.info(f"Generation pipeline complete.")
    logger.info(f"Total tasks: {total_tasks}, Completed: {completed_tasks}, Skipped: {skipped_tasks}")
    logger.info(f"Total samples written: {total_samples}")
    logger.info(f"Output file: {output_path}")

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    run_generation_pipeline()