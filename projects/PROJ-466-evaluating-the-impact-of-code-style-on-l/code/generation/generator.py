import os
import json
import logging
import time
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from utils.logger import log_memory_usage, log_batch_reduction, log_generation_error, log_timeout_error
from utils.timeout_decorator import timeout_decorator, TaskTimeoutError
from config.loader import load_config, get_config_value

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
    
    # In a real implementation, this would call an LLM API
    # For now, we return placeholder samples that would be generated
    # NOTE: This is a stub - real implementation would use transformers/LLM API
    for i in range(num_samples):
        sample = {
            'task_id': task_id,
            'style': style,
            'sample_id': f"{task_id}_{style}_{i}",
            'code': f"# Placeholder sample {i} for {task_id} with style {style}\n",
            'pass_status': None  # Will be filled by tester
        }
        samples.append(sample)
    
    return samples

def run_generation_pipeline(config_path: Optional[str] = None) -> None:
    """
    Run the full generation pipeline for all tasks and styles.
    
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
    from generation.loader import get_humaneval_tasks
    tasks = get_humaneval_tasks()
    
    # Initialize output file
    fieldnames = ['task_id', 'style', 'sample_id', 'code', 'pass_status']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for task in tasks:
            task_id = task.get('problem_id', 'unknown')
            logger.info(f"Processing task {task_id}")
            
            for style in styles:
                try:
                    samples = generate_samples_for_task(task, style)
                    for sample in samples:
                        writer.writerow(sample)
                except TaskTimeoutError:
                    log_timeout_error(task_id, style, 300)
                    logger.warning(f"Skipping task {task_id} ({style}) due to timeout")
                    continue
                except Exception as e:
                    log_generation_error(task_id, style, str(e))
                    logger.error(f"Error generating samples for {task_id} ({style}): {e}")
                    continue
    
    logger.info(f"Generation pipeline complete. Output: {output_path}")
