"""
Inference Runner: Executes the model on the dataset.
"""
import json
from pathlib import Path
from typing import List, Dict, Any
from code.config import config
from code.utils.logger import get_logger
from code.utils.common import load_json, save_json
from code.prompt_builder import build_guided_prompt, build_blind_prompt
# Note: Inference logic (loading model) is in code/inference.py (T020)
# This runner orchestrates the calls.

logger = get_logger(__name__)

def run_inference(tasks: List[Dict], mode: str = "guided") -> List[Dict]:
    """
    Run inference on a list of tasks.
    """
    results = []
    # Placeholder for actual model invocation
    # This would call code/inference.py
    logger.info(f"Running {mode} inference on {len(tasks)} tasks...")
    
    # Simulate results structure for now
    for task in tasks:
        results.append({
            "task_id": task.get("id"),
            "mode": mode,
            "status": "pending", # To be filled by actual inference
            "output": ""
        })
    
    return results

def save_results(results: List[Dict], output_path: Path):
    """Save inference results."""
    save_json(results, output_path)
    logger.info(f"Saved {len(results)} results to {output_path}")
