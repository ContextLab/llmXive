import os
from pathlib import Path
from typing import List, Dict, Any
from datasets import load_dataset

def download_humaneval() -> Path:
    """
    Download the HumanEval dataset using the datasets library.
    
    Returns:
        Path to the downloaded dataset directory
    """
    cache_dir = Path("data/raw/humaneval")
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load HumanEval dataset
        dataset = load_dataset("openai/human-eval", trust_remote_code=True)
        dataset.save_to_disk(str(cache_dir))
        return cache_dir
    except Exception as e:
        raise RuntimeError(f"Failed to download HumanEval dataset: {e}")

def get_humaneval_tasks() -> List[Dict[str, Any]]:
    """
    Load HumanEval tasks from the dataset.
    
    Returns:
        List of task dictionaries with problem_id, prompt, test, etc.
    """
    cache_dir = Path("data/raw/humaneval")
    
    if not cache_dir.exists():
        download_humaneval()
    
    try:
        dataset = load_dataset("openai/human-eval", trust_remote_code=True)
        tasks = []
        
        # Iterate over all splits (usually just 'test')
        for split in dataset:
            for task in dataset[split]:
                tasks.append(task)
        
        return tasks
    except Exception as e:
        raise RuntimeError(f"Failed to load HumanEval tasks: {e}")
