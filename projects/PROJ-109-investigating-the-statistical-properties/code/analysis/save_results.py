"""
Result saving module.
Saves statistics and convergence data to JSON.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np

from config import RESULTS_DIR
from utils.logging import get_logger

logger = get_logger("save_results")

def save_statistics_to_json(data: Dict, filename: str):
    """Saves data to a JSON file."""
    path = RESULTS_DIR / filename
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved {filename}")

def load_convergence_stats():
    """Loads convergence stats if they exist."""
    path = RESULTS_DIR / "convergence_stats.json"
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    return {}

def run_save_results_pipeline():
    """Runs the save results pipeline."""
    logger.info("Saving results...")
    # Logic to aggregate and save
    save_statistics_to_json({"status": "complete"}, "statistics.json")

if __name__ == "__main__":
    run_save_results_pipeline()
