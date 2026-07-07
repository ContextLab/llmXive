import logging
import os
import random
import time
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# Assuming these are imported from config/download in the real file
# Since we are extending, we assume the imports exist or are added here if missing in the "omitted" file
from config import get_config, set_seed, get_paths, ensure_directories
from download import load_model, load_dataset_from_huggingface

logger = logging.getLogger(__name__)

def load_benchmark_dataset(benchmark_name: str, data_dir: Path) -> List[Dict[str, Any]]:
    """Load benchmark dataset (HumanEval or MBPP) from HuggingFace."""
    logger.info(f"Loading {benchmark_name} dataset...")
    try:
        # Using the download utility which fetches from HF
        # Assuming download.py returns the dataset object or we load it directly
        # For this implementation, we assume load_dataset_from_huggingface handles the fetch
        dataset = load_dataset_from_huggingface(benchmark_name, data_dir)
        logger.info(f"Loaded {len(dataset)} tasks from {benchmark_name}")
        return dataset
    except Exception as e:
        logger.error(f"Failed to load dataset {benchmark_name}: {e}")
        raise

def validate_sample(sample_code: str, task_id: str, benchmark_name: str) -> bool:
    """
    Validate a generated sample against benchmark tests.
    In a real implementation, this would run the sample code against test cases.
    For this task, we simulate the validation logic or call a runner.
    Returns True if valid, False otherwise.
    """
    if not sample_code or not sample_code.strip():
        return False
    
    # Placeholder for actual test execution logic
    # In the real system, this would execute the code and check against test cases
    # For the purpose of this task (logging), we assume a validation function exists
    # or we implement a basic syntax check as a proxy if no runner is available yet.
    try:
        compile(sample_code, '<string>', 'exec')
        return True
    except SyntaxError:
        logger.warning(f"Syntax error in sample for {task_id}")
        return False

def generate_sample(model, task: Dict[str, Any], task_id: str, max_attempts: int = 200) -> List[str]:
    """
    Generate samples for a single task until valid samples are found or attempts exhausted.
    Returns list of valid sample codes.
    """
    valid_samples = []
    attempts = 0
    
    while len(valid_samples) < 64 and attempts < max_attempts:
        attempts += 1
        try:
            # Call model generation logic
            # Assuming model has a generate method or we use a specific inference function
            # This is a placeholder for the actual generation call
            generated_text = model.generate(task['prompt'], max_length=512)
            
            if not generated_text:
                logger.debug(f"Generation attempt {attempts} for {task_id} returned empty")
                continue

            if validate_sample(generated_text, task_id, task.get('benchmark', 'unknown')):
                valid_samples.append(generated_text)
                logger.debug(f"Valid sample {len(valid_samples)} obtained for {task_id} (Attempt {attempts})")
            else:
                logger.debug(f"Sample invalid for {task_id} (Attempt {attempts})")
                
        except Exception as e:
            # LOGGING FOR GENERATION FAILURES
            logger.error(f"Generation failure for task {task_id} at attempt {attempts}: {e}")
            # Continue to next attempt as per task requirement to exhaust attempts
            continue

    if len(valid_samples) < 64:
        logger.error(f"Insufficient data for task {task_id}: obtained {len(valid_samples)} valid samples after {attempts} attempts. Flagging dataset.")
        # The pipeline halt logic is assumed to be in the caller (run_generation)
    
    return valid_samples

def process_task(task: Dict[str, Any], model, output_dir: Path, benchmark_name: str) -> bool:
    """
    Process a single task: generate samples, save to disk.
    Returns True if successful, False if halted due to insufficient data.
    """
    task_id = task.get('task_id', 'unknown')
    task_output_dir = output_dir / task_id / 'samples'
    task_output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Processing task {task_id}...")
    
    try:
        valid_samples = generate_sample(model, task, task_id)
        
        if len(valid_samples) < 64:
            logger.critical(f"Task {task_id} failed to generate sufficient samples. Halting pipeline.")
            return False
        
        # Save samples
        for idx, sample in enumerate(valid_samples):
            file_path = task_output_dir / f"sample_{idx}.py"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(sample)
        
        logger.info(f"Saved {len(valid_samples)} samples for {task_id}")
        return True
        
    except Exception as e:
        logger.error(f"Unexpected error processing task {task_id}: {e}")
        return False

def run_generation(model_name: str, benchmark_name: str, seed: int = 42) -> bool:
    """
    Main generation loop.
    Returns False if any task fails to generate sufficient samples.
    """
    set_seed(seed)
    config = get_config()
    paths = get_paths()
    
    ensure_directories()
    
    # Load Model
    logger.info(f"Loading model: {model_name}")
    model = load_model(model_name)
    
    # Load Dataset
    data_dir = paths['data'] / 'raw'
    tasks = load_benchmark_dataset(benchmark_name, data_dir)
    
    output_base = paths['data'] / 'generated' / model_name / benchmark_name
    
    all_success = True
    
    for task in tasks:
        success = process_task(task, model, output_base, benchmark_name)
        if not success:
            all_success = False
            # Per task T012/T016: halt pipeline if insufficient data
            break
    
    return all_success

def main():
    """Entry point for generation script."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Simple argument parsing for demonstration
    import sys
    model_name = sys.argv[1] if len(sys.argv) > 1 else "starcoder"
    benchmark = sys.argv[2] if len(sys.argv) > 2 else "humaneval"
    
    success = run_generation(model_name, benchmark)
    if not success:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
